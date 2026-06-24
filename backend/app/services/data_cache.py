"""数据缓存层 — 避免重复调用akshare.

10只股票 × 3段时间的数据一次性获取，保存到本地SQLite缓存表，
35个策略共用同一份数据做回测.
"""

import os
import json
import hashlib
import time
import random
from datetime import datetime, timedelta
from typing import Any, Callable

import pandas as pd
import akshare as ak
from sqlalchemy import Column, Integer, String, Text, DateTime, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# 缓存数据库（独立于主数据库）
CACHE_DB_PATH = os.path.join(os.path.dirname(__file__), "../../data_cache.db")
os.makedirs(os.path.dirname(CACHE_DB_PATH), exist_ok=True)

cache_engine = create_engine(f"sqlite:///{CACHE_DB_PATH}", connect_args={"check_same_thread": False})
CacheSession = sessionmaker(autocommit=False, autoflush=False, bind=cache_engine)
CacheBase = declarative_base()


class CachedData(CacheBase):
    __tablename__ = "cached_ohlcv"

    id = Column(Integer, primary_key=True)
    cache_key = Column(String(64), unique=True, index=True, nullable=False)
    symbol = Column(String(16), nullable=False)
    start_date = Column(String(8), nullable=False)
    end_date = Column(String(8), nullable=False)
    source = Column(String(32), nullable=False)  # 哪个akshare接口
    data_json = Column(Text, nullable=False)     # DataFrame转JSON
    row_count = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# 建表
CacheBase.metadata.create_all(bind=cache_engine)


# ── 标的类型判断 ──

def _is_etf(symbol: str) -> bool:
    """判断是否为ETF代码（15/16/51/56/58/59开头）."""
    return bool(symbol) and symbol[:2] in ("15", "16", "51", "56", "58", "59")


# ── 备用数据源 ──

def _add_exchange_prefix(symbol: str) -> str:
    """为新浪财经/网易接口补充 sh/sz 前缀."""
    if symbol.startswith(("sh", "sz")):
        return symbol
    # 简单判断：6 开头为沪市(sh)，其余为深市(sz)
    if symbol.startswith("6"):
        return f"sh{symbol}"
    return f"sz{symbol}"


def _retry_fetch(
    fetch_func: Callable[..., pd.DataFrame | None],
    symbol: str,
    start: str,
    end: str,
    max_retries: int = 3,
    base_delay: float = 2.0,
) -> pd.DataFrame | None:
    """带重试和指数退避的数据获取.

    东方财富/新浪等免费接口对高频请求敏感，RemoteDisconnected 时重试。
    """
    last_error = None
    for attempt in range(max_retries):
        try:
            # 请求前随机抖动，避免固定节奏触发限流
            if attempt > 0:
                delay = base_delay * (2 ** (attempt - 1)) + random.uniform(0, 1)
                print(f"[DataCache] Retry {attempt}/{max_retries} for {symbol} after {delay:.1f}s")
                time.sleep(delay)
            else:
                time.sleep(random.uniform(0.3, 0.8))

            df = fetch_func(symbol, start, end)
            if df is not None and not df.empty:
                return df
        except Exception as e:
            last_error = e
            print(f"[DataCache] Attempt {attempt + 1} failed for {symbol}: {e}")

    if last_error:
        print(f"[DataCache] All {max_retries} attempts failed for {symbol}: {last_error}")
    return None


def _fetch_stock_from_eastmoney(symbol: str, start: str, end: str) -> pd.DataFrame | None:
    """东方财富个股接口."""
    return _retry_fetch(
        lambda s, st, ed: ak.stock_zh_a_hist(symbol=s, period="daily", start_date=st, end_date=ed, adjust="qfq"),
        symbol, start, end,
        max_retries=3, base_delay=3.0,
    )


def _fetch_stock_from_sina(symbol: str, start: str, end: str) -> pd.DataFrame | None:
    """新浪个股接口."""
    return _retry_fetch(
        lambda s, st, ed: __fetch_sina_stock_raw(s, st, ed),
        symbol, start, end,
        max_retries=3, base_delay=2.0,
    )


def __fetch_sina_stock_raw(symbol: str, start: str, end: str) -> pd.DataFrame | None:
    """新浪个股原始获取（用于重试封装）."""
    start_fmt = f"{start[:4]}-{start[4:6]}-{start[6:]}"
    end_fmt = f"{end[:4]}-{end[4:6]}-{end[6:]}"
    sina_symbol = _add_exchange_prefix(symbol)
    df = ak.stock_zh_a_daily(symbol=sina_symbol, start_date=start_fmt, end_date=end_fmt)
    if df is not None and not df.empty:
        return df
    return None


def _fetch_etf_from_eastmoney(symbol: str, start: str, end: str) -> pd.DataFrame | None:
    """东方财富ETF接口（fund_etf_hist_em）."""
    return _retry_fetch(
        lambda s, st, ed: ak.fund_etf_hist_em(symbol=s, period="daily", start_date=st, end_date=ed, adjust="qfq"),
        symbol, start, end,
        max_retries=3, base_delay=3.0,
    )


def _fetch_etf_from_sina(symbol: str, start: str, end: str) -> pd.DataFrame | None:
    """新浪ETF接口（fund_etf_hist_sina）."""
    return _retry_fetch(
        lambda s, st, ed: __fetch_sina_etf_raw(s, st, ed),
        symbol, start, end,
        max_retries=3, base_delay=2.0,
    )


def __fetch_sina_etf_raw(symbol: str, start: str, end: str) -> pd.DataFrame | None:
    """新浪ETF原始获取（用于重试封装）."""
    sina_symbol = _add_exchange_prefix(symbol)
    df = ak.fund_etf_hist_sina(symbol=sina_symbol)
    if df is not None and not df.empty:
        df["date"] = pd.to_datetime(df["date"])
        start_dt = pd.to_datetime(start)
        end_dt = pd.to_datetime(end)
        df = df[(df["date"] >= start_dt) & (df["date"] <= end_dt)].copy()
        if not df.empty:
            return df
    return None


def _fetch_from_tencent(symbol: str, start: str, end: str) -> pd.DataFrame | None:
    """腾讯接口（已失效，保留函数签名避免外部调用报错）."""
    return None


def fetch_ohlcv_with_fallback(symbol: str, start: str, end: str) -> pd.DataFrame | None:
    """带备用接口的数据获取."""
    # ETF 使用专门接口（东财ETF接口目前可用性较好）
    if _is_etf(symbol):
        sources = [
            ("eastmoney_etf", _fetch_etf_from_eastmoney),
            ("sina_etf", _fetch_etf_from_sina),
        ]
    else:
        sources = [
            ("eastmoney", _fetch_stock_from_eastmoney),
            ("sina", _fetch_stock_from_sina),
        ]

    for idx, (source_name, fetch_func) in enumerate(sources):
        # 数据源之间增加间隔，降低被限流概率
        if idx > 0:
            time.sleep(random.uniform(1.0, 2.0))
        df = fetch_func(symbol, start, end)
        if df is not None and not df.empty and len(df) >= 20:
            print(f"[DataCache] {symbol} fetched from {source_name}, rows={len(df)}")
            return df, source_name

    print(f"[DataCache] All sources failed for {symbol}")
    return None, None


# ── 缓存管理 ──

def _make_cache_key(symbol: str, start: str, end: str) -> str:
    return hashlib.md5(f"{symbol}:{start}:{end}".encode()).hexdigest()


def get_cached_data(symbol: str, start: str, end: str) -> pd.DataFrame | None:
    """从缓存获取数据（支持范围覆盖裁剪）.

    如果缓存的日期范围覆盖了请求范围，则裁剪后返回，避免重复请求外部接口。
    """
    db = CacheSession()
    try:
        records = (
            db.query(CachedData)
            .filter(CachedData.symbol == symbol)
            .order_by(CachedData.created_at.desc())
            .all()
        )
        for record in records:
            # 检查缓存是否过期（7天）
            age = datetime.utcnow() - record.created_at
            if age.days >= 7:
                db.delete(record)
                db.commit()
                continue

            # 缓存范围覆盖请求范围时才使用（允许前后5天边界误差）
            try:
                cache_start = datetime.strptime(record.start_date, "%Y%m%d")
                cache_end = datetime.strptime(record.end_date, "%Y%m%d")
                req_start = datetime.strptime(start, "%Y%m%d")
                req_end = datetime.strptime(end, "%Y%m%d")
                if cache_start <= req_start + timedelta(days=5) and cache_end >= req_end - timedelta(days=5):
                    from io import StringIO
                    df = pd.read_json(StringIO(record.data_json))
                    if "date" in df.columns:
                        df["date"] = pd.to_datetime(df["date"])
                        df = df[(df["date"] >= req_start) & (df["date"] <= req_end)].copy()
                    if not df.empty and len(df) >= 20:
                        print(f"[DataCache] Cache hit for {symbol} ({record.source}), rows={len(df)}")
                        return df
            except Exception as e:
                print(f"[DataCache] Cache parse failed for {symbol}: {e}")
    finally:
        db.close()
    return None


def save_cached_data(symbol: str, start: str, end: str, df: pd.DataFrame, source: str) -> None:
    """保存数据到缓存."""
    key = _make_cache_key(symbol, start, end)
    db = CacheSession()
    try:
        # 删除旧记录
        db.query(CachedData).filter(CachedData.cache_key == key).delete()
        # 插入新记录
        record = CachedData(
            cache_key=key,
            symbol=symbol,
            start_date=start,
            end_date=end,
            source=source,
            data_json=df.to_json(),
            row_count=len(df),
        )
        db.add(record)
        db.commit()
    finally:
        db.close()


# ── 主入口 ──

def get_ohlcv(symbol: str, start: str, end: str, force_refresh: bool = False) -> pd.DataFrame | None:
    """获取OHLCV数据（带缓存和备用接口）.

    Args:
        symbol: 股票代码
        start: 开始日期 YYYYMMDD
        end: 结束日期 YYYYMMDD
        force_refresh: 强制刷新缓存

    Returns:
        DataFrame或None
    """
    if not force_refresh:
        cached = get_cached_data(symbol, start, end)
        if cached is not None:
            return cached

    # 从网络获取
    result = fetch_ohlcv_with_fallback(symbol, start, end)
    if result is None or result[0] is None:
        return None

    df, source = result

    # 标准化列名
    col_map = {
        "日期": "date", "开盘": "open", "收盘": "close",
        "最高": "high", "最低": "low", "成交量": "volume",
    }
    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})

    # 确保date列存在
    if "date" not in df.columns and df.index.name == "date":
        df = df.reset_index()

    # 保存到缓存
    save_cached_data(symbol, start, end, df, source)

    return df


# ── 批量获取 ──

def batch_fetch(stocks: list[dict], periods: list[dict], force_refresh: bool = False) -> dict[str, Any]:
    """批量获取多股票多时间段数据.

    Returns:
        {"symbol_period": df, ...}
    """
    results = {}
    total = len(stocks) * len(periods)
    fetched = 0

    for stock in stocks:
        symbol = stock["symbol"]
        for period in periods:
            key = f"{symbol}_{period['name']}"
            df = get_ohlcv(symbol, period["start"], period["end"], force_refresh)
            if df is not None:
                results[key] = df
                fetched += 1

    print(f"[DataCache] Batch fetch: {fetched}/{total} succeeded")
    return results


# ── 缓存统计 ──

def cache_stats() -> dict[str, Any]:
    """查看缓存统计."""
    db = CacheSession()
    try:
        from sqlalchemy import func
        total = db.query(CachedData).count()
        total_rows = db.query(func.sum(CachedData.row_count)).scalar() or 0
        sources = {}
        for r in db.query(CachedData.source, func.count(CachedData.id)).group_by(CachedData.source).all():
            sources[r[0]] = r[1]
        return {
            "total_symbols": total,
            "total_rows": total_rows,
            "sources": sources,
            "db_path": CACHE_DB_PATH,
        }
    finally:
        db.close()
