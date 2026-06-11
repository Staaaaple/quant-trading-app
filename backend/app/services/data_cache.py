"""数据缓存层 — 避免重复调用akshare.

10只股票 × 3段时间的数据一次性获取，保存到本地SQLite缓存表，
35个策略共用同一份数据做回测.
"""

import os
import json
import hashlib
import time
from datetime import datetime, timedelta
from typing import Any

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


# ── 备用数据源 ──

def _fetch_from_eastmoney(symbol: str, start: str, end: str) -> pd.DataFrame | None:
    """东方财富接口（主要）."""
    try:
        time.sleep(5)  # 5秒间隔，降低被封概率
        df = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date=start, end_date=end, adjust="qfq")
        if df is not None and not df.empty:
            return df
    except Exception as e:
        print(f"[DataCache] Eastmoney failed for {symbol}: {e}")
    return None


def _add_exchange_prefix(symbol: str) -> str:
    """为新浪财经/网易接口补充 sh/sz 前缀."""
    if symbol.startswith(("sh", "sz")):
        return symbol
    if symbol.startswith("6"):
        return f"sh{symbol}"
    return f"sz{symbol}"


def _fetch_from_sina(symbol: str, start: str, end: str) -> pd.DataFrame | None:
    """新浪接口（备用）."""
    try:
        # 新浪接口格式不同，需要转换
        start_fmt = f"{start[:4]}-{start[4:6]}-{start[6:]}"
        end_fmt = f"{end[:4]}-{end[4:6]}-{end[6:]}"
        sina_symbol = _add_exchange_prefix(symbol)
        df = ak.stock_zh_a_daily(symbol=sina_symbol, start_date=start_fmt, end_date=end_fmt)
        if df is not None and not df.empty:
            # 新浪返回英文列名，与 get_ohlcv 下游标准化保持一致
            return df
    except Exception as e:
        print(f"[DataCache] Sina failed for {symbol}: {e}")
    return None


def _fetch_from_tencent(symbol: str, start: str, end: str) -> pd.DataFrame | None:
    """腾讯接口（已失效，保留函数签名避免外部调用报错）."""
    # ak.stock_zh_a_hist_tx 当前返回 ValueError: invalid literal for int() with base 10: 'i'
    # 直接返回 None 避免无效请求和错误日志刷屏
    return None


def _fetch_etf_from_cache_or_placeholder(symbol: str, start: str, end: str) -> pd.DataFrame | None:
    """ETF历史数据占位（当前akshare无可用免费ETF历史接口）."""
    print(f"[DataCache] ETF historical data ({symbol}) is not available via akshare currently")
    return None


def _fetch_from_163(symbol: str, start: str, end: str) -> pd.DataFrame | None:
    """网易接口（备用）."""
    try:
        # 网易接口需要转换日期格式
        start_fmt = f"{start[:4]}-{start[4:6]}-{start[6:]}"
        end_fmt = f"{end[:4]}-{end[4:6]}-{end[6:]}"
        netease_symbol = _add_exchange_prefix(symbol)
        df = ak.stock_zh_a_daily(symbol=netease_symbol, start_date=start_fmt, end_date=end_fmt)
        if df is not None and not df.empty:
            # 网易/新浪返回英文列名，与 get_ohlcv 下游标准化保持一致
            return df
    except Exception as e:
        print(f"[DataCache] 163 failed for {symbol}: {e}")
    return None


def fetch_ohlcv_with_fallback(symbol: str, start: str, end: str) -> pd.DataFrame | None:
    """带备用接口的数据获取."""
    # 尝试多个接口（按当前可用性排序）
    sources = [
        ("sina", _fetch_from_sina),            # 新浪当前可用
        ("163", _fetch_from_163),              # 网易备用（同新浪接口）
        ("eastmoney", _fetch_from_eastmoney),  # 东财数据质量高但当前被封
    ]

    for source_name, fetch_func in sources:
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
    """从缓存获取数据."""
    key = _make_cache_key(symbol, start, end)
    db = CacheSession()
    try:
        record = db.query(CachedData).filter(CachedData.cache_key == key).first()
        if record:
            # 检查缓存是否过期（7天）
            age = datetime.utcnow() - record.created_at
            if age.days < 7:
                df = pd.read_json(record.data_json)
                print(f"[DataCache] Cache hit for {symbol} ({record.source}), rows={record.row_count}")
                return df
            else:
                # 删除过期缓存
                db.delete(record)
                db.commit()
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
