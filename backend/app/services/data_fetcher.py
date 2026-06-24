"""多源股票数据获取器 — 适配各种免费API.

支持数据源:
- akshare stock_zh_a_daily (新浪) — 当前可用
- akshare stock_zh_a_hist (东方财富) — 当前被封
- ~~akshare stock_zh_a_hist_tx (腾讯) — 已失效~~

统一输出格式: DataFrame with columns [date, open, high, low, close, volume]
"""

import time
from typing import Any

import pandas as pd
import akshare as ak


# ── 股票代码交易所映射 ──
# 新浪接口需要 sh/sz 前缀
EXCHANGE_MAP = {
    "600519": "sh600519",  # 茅台
    "000001": "sz000001",  # 平安银行
    "000063": "sz000063",  # 中兴通讯
    "002415": "sz002415",  # 海康威视
    "300750": "sz300750",  # 宁德时代
    "002594": "sz002594",  # 比亚迪
    "600276": "sh600276",  # 恒瑞医药
    "000538": "sz000538",  # 云南白药
    "000858": "sz000858",  # 五粮液
    "600887": "sh600887",  # 伊利股份
}


def _add_exchange_prefix(symbol: str) -> str:
    """为需要交易所前缀的接口补充 sh/sz."""
    if symbol.startswith(("sh", "sz")):
        return symbol
    # 上海：主板 60/68/69、科创板、ETF（50/51/52/56/58/59）
    if symbol.startswith(("60", "68", "69", "50", "51", "52", "56", "58", "59")):
        return f"sh{symbol}"
    # 深圳：主板 00、创业板 30、ETF（15/16）、指数 39
    if symbol.startswith(("00", "30", "39", "15", "16")):
        return f"sz{symbol}"
    # 默认深圳
    return f"sz{symbol}"


# ── 新浪接口获取 ──

def fetch_from_sina(symbol: str, start: str, end: str) -> pd.DataFrame | None:
    """新浪接口获取股票数据.

    Args:
        symbol: 6位数字代码如 '600519'，或已带 sh/sz 前缀
        start: YYYYMMDD 或 YYYY-MM-DD
        end: YYYYMMDD 或 YYYY-MM-DD
    """
    sina_symbol = EXCHANGE_MAP.get(symbol, _add_exchange_prefix(symbol))

    # 新浪需要 YYYY-MM-DD
    start_fmt = start if "-" in start else f"{start[:4]}-{start[4:6]}-{start[6:]}"
    end_fmt = end if "-" in end else f"{end[:4]}-{end[4:6]}-{end[6:]}"

    try:
        df = ak.stock_zh_a_daily(symbol=sina_symbol, start_date=start_fmt, end_date=end_fmt)
        if df is None or df.empty:
            return None

        # 新浪返回英文列名，标准化确保一致
        col_map = {
            "date": "date",
            "open": "open",
            "high": "high",
            "low": "low",
            "close": "close",
            "volume": "volume",
        }
        df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})

        # 确保date列存在
        if "date" not in df.columns:
            df = df.reset_index()
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")

        return df[["date", "open", "high", "low", "close", "volume"]]
    except Exception as e:
        print(f"[DataFetcher] Sina failed for {symbol}: {e}")
        return None


# ── 东方财富接口获取（当前大概率失效，保留作未来恢复） ──

def fetch_from_eastmoney(symbol: str, start: str, end: str) -> pd.DataFrame | None:
    """东方财富接口获取股票数据（当前被封，保留接口）."""
    try:
        time.sleep(5)  # 5秒间隔，降低被封概率
        start_fmt = start.replace("-", "")
        end_fmt = end.replace("-", "")
        df = ak.stock_zh_a_hist(
            symbol=symbol, period="daily", start_date=start_fmt, end_date=end_fmt, adjust="qfq"
        )
        if df is None or df.empty:
            return None

        col_map = {
            "日期": "date",
            "开盘": "open",
            "最高": "high",
            "最低": "low",
            "收盘": "close",
            "成交量": "volume",
        }
        df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
        return df[["date", "open", "high", "low", "close", "volume"]]
    except Exception as e:
        print(f"[DataFetcher] Eastmoney failed for {symbol}: {e}")
        return None


# ── ETF 数据获取 ──

def fetch_etf_from_eastmoney(symbol: str, start: str, end: str) -> pd.DataFrame | None:
    """东方财富ETF接口."""
    try:
        df = ak.fund_etf_hist_em(symbol=symbol, period="daily", start_date=start, end_date=end, adjust="qfq")
        if df is None or df.empty:
            return None

        col_map = {
            "日期": "date",
            "开盘": "open",
            "最高": "high",
            "最低": "low",
            "收盘": "close",
            "成交量": "volume",
        }
        df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
        return df[["date", "open", "high", "low", "close", "volume"]]
    except Exception as e:
        print(f"[DataFetcher] Eastmoney ETF failed for {symbol}: {e}")
        return None


def fetch_etf_from_sina(symbol: str, start: str, end: str) -> pd.DataFrame | None:
    """新浪ETF接口."""
    try:
        sina_symbol = _add_exchange_prefix(symbol)
        df = ak.fund_etf_hist_sina(symbol=sina_symbol)
        if df is None or df.empty:
            return None

        # 确保 date 列是 datetime 类型，与 start/end 一致
        df["date"] = pd.to_datetime(df["date"])
        start_dt = pd.to_datetime(start)
        end_dt = pd.to_datetime(end)
        df = df[(df["date"] >= start_dt) & (df["date"] <= end_dt)].copy()
        if df.empty:
            return None

        df["date"] = df["date"].dt.strftime("%Y-%m-%d")
        return df[["date", "open", "high", "low", "close", "volume"]]
    except Exception as e:
        print(f"[DataFetcher] Sina ETF failed for {symbol}: {e}")
        return None


# ── 统一入口 ──

def fetch_stock_data(symbol: str, start: str, end: str) -> pd.DataFrame | None:
    """获取股票/ETF数据（自动选择可用接口）.

    Args:
        symbol: 6位股票/ETF代码或带前缀代码
        start: 开始日期 YYYYMMDD 或 YYYY-MM-DD
        end: 结束日期 YYYYMMDD 或 YYYY-MM-DD

    Returns:
        DataFrame with [date, open, high, low, close, volume]
    """
    # ETF 代码判断
    if symbol[:2] in ("15", "16", "51", "56", "58", "59"):
        df = fetch_etf_from_eastmoney(symbol, start, end)
        if df is not None and not df.empty:
            return df
        df = fetch_etf_from_sina(symbol, start, end)
        if df is not None and not df.empty:
            return df
        return None

    # 个股：优先新浪
    df = fetch_from_sina(symbol, start, end)
    if df is not None and not df.empty:
        return df

    # 新浪失败尝试东财
    time.sleep(2)
    df = fetch_from_eastmoney(symbol, start, end)
    if df is not None and not df.empty:
        return df

    return None


# ── 批量获取（带间隔） ──

def batch_fetch_stocks(
    stocks: list[dict],
    start: str,
    end: str,
    interval: float = 3.0,
) -> dict[str, pd.DataFrame]:
    """批量获取多只股票数据.

    Args:
        stocks: [{"symbol": "600519", "name": "茅台"}, ...]
        start: YYYYMMDD
        end: YYYYMMDD
        interval: 请求间隔秒数

    Returns:
        {symbol: DataFrame, ...}
    """
    results = {}
    for i, stock in enumerate(stocks):
        symbol = stock["symbol"]
        name = stock.get("name", symbol)
        print(f"[{i+1}/{len(stocks)}] Fetching {symbol} ({name})...")

        df = fetch_stock_data(symbol, start, end)
        if df is not None:
            results[symbol] = df
            print(f"  ✓ {len(df)} rows")
        else:
            print(f"  ✗ Failed")

        # 间隔避免限流
        if i < len(stocks) - 1:
            time.sleep(interval)

    print(f"\n[DataFetcher] Total: {len(results)}/{len(stocks)} succeeded")
    return results


# ── 保存/加载 ──

def save_to_csv(symbol: str, df: pd.DataFrame, out_dir: str = "data/stock_cache") -> str:
    """保存到CSV."""
    import os
    os.makedirs(out_dir, exist_ok=True)
    path = f"{out_dir}/{symbol}.csv"
    df.to_csv(path, index=False)
    return path


def load_from_csv(symbol: str, cache_dir: str = "data/stock_cache") -> pd.DataFrame | None:
    """从CSV加载."""
    import os
    path = f"{cache_dir}/{symbol}.csv"
    if os.path.exists(path):
        return pd.read_csv(path)
    return None
