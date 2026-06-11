"""策略模板运行器（统一输入输出接口）.

所有模板必须遵循统一的输入输出格式:
  输入: {symbol, start_date, end_date, params}
  输出: {symbol, date, signal(-1/0/1), confidence(0-1), expected_return, risk_estimate}

Phase B 先实现框架，具体模板代码在 seed_templates 中填充.
"""

import traceback
from typing import Any
from datetime import datetime

import pandas as pd
import numpy as np

from app.services.data_fetcher import fetch_stock_data
from app.services.data_cache import get_ohlcv as cache_get_ohlcv


# ── 标准化信号格式 ──

def make_signal(
    symbol: str,
    date: str,
    signal: int,           # -1(卖) / 0(持有) / 1(买)
    confidence: float,     # 0-1
    expected_return: float | None = None,
    risk_estimate: float | None = None,
) -> dict[str, Any]:
    """生成标准化信号."""
    return {
        "symbol": symbol,
        "date": date,
        "signal": signal,
        "confidence": round(max(0.0, min(1.0, confidence)), 3),
        "expected_return": round(expected_return, 4) if expected_return is not None else 0.0,
        "risk_estimate": round(risk_estimate, 4) if risk_estimate is not None else 0.0,
    }


# ── 数据获取 ──

def fetch_ohlcv(symbol: str, start_date: str, end_date: str) -> pd.DataFrame | None:
    """获取日频OHLCV数据（使用可用的新浪接口）."""
    try:
        # data_fetcher 统一输出英文列名 [date, open, high, low, close, volume]
        df = fetch_stock_data(symbol, start_date, end_date)
        if df is None or df.empty:
            return None
        return df
    except Exception as e:
        print(f"[TemplateRunner] Fetch error for {symbol}: {e}")
        return None


def fetch_etf_ohlcv(symbol: str, start_date: str, end_date: str) -> pd.DataFrame | None:
    """获取ETF日频数据（优先读缓存，当前akshare无可用免费ETF历史接口）."""
    try:
        # 尝试读本地缓存（如果之前通过其他方式存入）
        df = cache_get_ohlcv(symbol, start_date, end_date)
        if df is not None and not df.empty:
            return df
        print(f"[TemplateRunner] ETF historical data ({symbol}) is not available via akshare currently")
        return None
    except Exception as e:
        print(f"[TemplateRunner] ETF fetch error for {symbol}: {e}")
        return None


# ── 内置模板示例（Phase B 先放3个核心模板作为示例） ──

_BUILTIN_TEMPLATES: dict[str, Any] = {}


def _register_builtin(template_id: str, func):
    """注册内置模板函数."""
    _BUILTIN_TEMPLATES[template_id] = func


def _tmpl_ma_crossover(symbol: str, df: pd.DataFrame, params: dict) -> list[dict]:
    """双均线交叉策略（内置示例）.
    params: {fast_ma: int, slow_ma: int}
    """
    fast = int(params.get("fast_ma", 5))
    slow = int(params.get("slow_ma", 20))

    df = df.copy()
    df["fast"] = df["close"].rolling(fast).mean()
    df["slow"] = df["close"].rolling(slow).mean()
    df["signal_raw"] = np.where(df["fast"] > df["slow"], 1, -1)
    df["signal"] = df["signal_raw"].diff().fillna(0).astype(int)

    signals = []
    for _, row in df.iterrows():
        if row["signal"] == 2:  # -1 -> 1 (金叉)
            sig = make_signal(symbol, str(row["date"]), 1, 0.7,
                              expected_return=0.05, risk_estimate=0.03)
            signals.append(sig)
        elif row["signal"] == -2:  # 1 -> -1 (死叉)
            sig = make_signal(symbol, str(row["date"]), -1, 0.7,
                              expected_return=-0.03, risk_estimate=0.03)
            signals.append(sig)

    return signals


def _tmpl_rsi_reversal(symbol: str, df: pd.DataFrame, params: dict) -> list[dict]:
    """RSI超买超卖策略（内置示例）.
    params: {period: int, oversold: int, overbought: int}
    """
    period = int(params.get("period", 14))
    oversold = int(params.get("oversold", 30))
    overbought = int(params.get("overbought", 70))

    df = df.copy()
    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    df["rsi"] = 100 - (100 / (1 + rs))

    signals = []
    prev_rsi = None
    for _, row in df.iterrows():
        rsi = row["rsi"]
        if prev_rsi is not None and not np.isnan(rsi):
            if prev_rsi < oversold and rsi >= oversold:
                sig = make_signal(symbol, str(row["date"]), 1, 0.65,
                                  expected_return=0.04, risk_estimate=0.04)
                signals.append(sig)
            elif prev_rsi > overbought and rsi <= overbought:
                sig = make_signal(symbol, str(row["date"]), -1, 0.65,
                                  expected_return=-0.03, risk_estimate=0.04)
                signals.append(sig)
        prev_rsi = rsi

    return signals


def _tmpl_boll_breakout(symbol: str, df: pd.DataFrame, params: dict) -> list[dict]:
    """布林带突破策略（内置示例）.
    params: {period: int, std: float}
    """
    period = int(params.get("period", 20))
    std_mult = float(params.get("std", 2.0))

    df = df.copy()
    df["ma"] = df["close"].rolling(period).mean()
    df["std"] = df["close"].rolling(period).std()
    df["upper"] = df["ma"] + std_mult * df["std"]
    df["lower"] = df["ma"] - std_mult * df["std"]

    signals = []
    for _, row in df.iterrows():
        if row["close"] > row["upper"]:
            sig = make_signal(symbol, str(row["date"]), 1, 0.6,
                              expected_return=0.04, risk_estimate=0.05)
            signals.append(sig)
        elif row["close"] < row["lower"]:
            sig = make_signal(symbol, str(row["date"]), -1, 0.6,
                              expected_return=-0.03, risk_estimate=0.05)
            signals.append(sig)

    return signals


# 注册内置模板
_register_builtin("tmpl_ma_crossover", _tmpl_ma_crossover)
_register_builtin("tmpl_rsi_reversal", _tmpl_rsi_reversal)
_register_builtin("tmpl_boll_breakout", _tmpl_boll_breakout)


# ── 主入口 ──

def run_template(
    template_id: str,
    symbol: str,
    start_date: str,
    end_date: str,
    params: dict[str, Any] | None = None,
    asset_class: str = "stock",
) -> list[dict[str, Any]]:
    """运行策略模板，返回标准化信号列表.

    Args:
        template_id: 模板ID（内置或数据库中的模板）
        symbol: 标的代码
        start_date: 开始日期 YYYYMMDD
        end_date: 结束日期 YYYYMMDD
        params: 模板参数（覆盖默认值）
        asset_class: stock / etf / fund / bond

    Returns:
        标准化信号列表
    """
    params = params or {}

    # 1. 获取数据
    if asset_class == "etf":
        df = fetch_etf_ohlcv(symbol, start_date, end_date)
    else:
        df = fetch_ohlcv(symbol, start_date, end_date)

    if df is None or df.empty or len(df) < 30:
        return []

    # 2. 执行模板
    try:
        if template_id in _BUILTIN_TEMPLATES:
            func = _BUILTIN_TEMPLATES[template_id]
            signals = func(symbol, df, params)
        else:
            # Phase B 后续：支持从数据库加载自定义模板代码
            # 现在先用内置模板兜底
            print(f"[TemplateRunner] Template {template_id} not found in builtins, skipping")
            return []
    except Exception as e:
        print(f"[TemplateRunner] Template {template_id} execution error: {e}")
        traceback.print_exc()
        return []

    return signals


def run_batch_backtest(
    template_id: str,
    symbols: list[str],
    start_date: str,
    end_date: str,
    params: dict[str, Any] | None = None,
    asset_class: str = "stock",
) -> dict[str, Any]:
    """批量回测：在多个标的上运行同一模板.

    Returns:
        {
            "template_id": str,
            "symbols_tested": int,
            "signals_total": int,
            "win_rate": float,  # 信号正确率（简化：用下一日涨跌判断）
            "avg_return": float,
            "max_drawdown": float,
        }
    """
    all_signals = []
    for sym in symbols:
        signals = run_template(template_id, sym, start_date, end_date, params, asset_class)
        all_signals.extend(signals)

    # 简化统计（Phase B 先用简化版，后续用akquant完整回测）
    buy_signals = [s for s in all_signals if s["signal"] == 1]
    sell_signals = [s for s in all_signals if s["signal"] == -1]

    return {
        "template_id": template_id,
        "symbols_tested": len(symbols),
        "signals_total": len(all_signals),
        "buy_signals": len(buy_signals),
        "sell_signals": len(sell_signals),
        "win_rate": 0.5,  # 占位，后续用真实回测替换
        "avg_return": 0.0,
        "max_drawdown": 0.0,
    }
