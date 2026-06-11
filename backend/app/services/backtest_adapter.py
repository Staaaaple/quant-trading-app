"""回测适配器 — 支持多资产类型回测.

支持: 个股(A股) / ETF / 基金 / 债券 / 期货ETF
"""

from typing import Any
import pandas as pd
import akshare as ak
from sqlalchemy.orm import Session

from app.services.backtest_service import (
    fetch_stock_data,
    _normalize_akquant_df,
    _extract_metrics,
    _extract_trades,
    _df_to_candles,
    _write_strategy_to_temp_file,
    _run_benchmark,
    AkshareProxyError,
    AkshareDataError,
)
from app.services.data_cache import get_ohlcv as cache_get_ohlcv


# ═══════════════════════════════════════════════════════════════
# 资产类型枚举
# ═══════════════════════════════════════════════════════════════

ASSET_TYPES = {
    "stock": "个股(A股)",
    "etf": "ETF",
    "fund": "基金",
    "bond": "债券",
    "futures_etf": "期货ETF",
}


# ═══════════════════════════════════════════════════════════════
# 数据获取适配器
# ═══════════════════════════════════════════════════════════════

def fetch_etf_data(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """获取ETF历史数据（优先读缓存，当前akshare无可用免费ETF历史接口）."""
    try:
        # 优先尝试本地缓存
        start_fmt = start_date.replace("-", "")
        end_fmt = end_date.replace("-", "")
        df = cache_get_ohlcv(symbol, start_fmt, end_fmt)
        if df is not None and not df.empty:
            return _normalize_akquant_df(df, symbol)

        # 当前akshare ETF历史接口 fund_etf_hist_em 已被封
        raise AkshareDataError(
            f"ETF {symbol} 历史数据当前无法通过akshare获取，"
            f"请先通过其他方式将数据写入data_cache缓存"
        )
    except AkshareDataError:
        raise
    except Exception as e:
        raise AkshareDataError(f"获取ETF数据失败: {e}")


def fetch_fund_data(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """获取基金历史数据(NAV)."""
    try:
        # 基金净值数据
        df = ak.fund_open_fund_daily_em()
        # 筛选特定基金
        df = df[df["基金代码"] == symbol].copy()
        if df.empty:
            raise ValueError(f"基金 {symbol} 无数据")
        # 标准化列名
        df = df.rename(columns={
            "净值日期": "date",
            "单位净值": "close",
            "累计净值": "nav_cum",
        })
        df["open"] = df["close"]
        df["high"] = df["close"]
        df["low"] = df["close"]
        df["volume"] = 0
        return _normalize_akquant_df(df, symbol)
    except Exception as e:
        raise AkshareDataError(f"获取基金数据失败: {e}")


def fetch_bond_data(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """获取债券历史数据（使用中美债券利率接口）."""
    try:
        # bond_zh_yield 接口已不存在，改用 bond_zh_us_rate 取中国10年期国债收益率
        df = ak.bond_zh_us_rate()
        if df is None or df.empty:
            raise ValueError(f"债券 {symbol} 无数据")

        # 取中国国债收益率10年作为债券代理价格
        df = df.rename(columns={
            "日期": "date",
            "中国国债收益率10年": "close",
        })
        df["date"] = pd.to_datetime(df["date"])
        # 按日期范围过滤
        df = df[(df["date"] >= start_date) & (df["date"] <= end_date)].copy()
        if df.empty:
            raise ValueError(f"债券 {symbol} 在指定日期范围无数据")

        df["open"] = df["close"]
        df["high"] = df["close"]
        df["low"] = df["close"]
        df["volume"] = 0
        return _normalize_akquant_df(df, symbol)
    except Exception as e:
        raise AkshareDataError(f"获取债券数据失败: {e}")


def fetch_futures_etf_data(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """获取期货ETF数据."""
    # 期货ETF用ETF接口获取
    return fetch_etf_data(symbol, start_date, end_date)


# ═══════════════════════════════════════════════════════════════
# 统一数据获取入口
# ═══════════════════════════════════════════════════════════════

def fetch_asset_data(
    symbol: str,
    asset_type: str,
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    """根据资产类型获取数据.

    Args:
        symbol: 标的代码
        asset_type: stock/etf/fund/bond/futures_etf
        start_date: 开始日期 YYYY-MM-DD
        end_date: 结束日期 YYYY-MM-DD

    Returns:
        标准化后的DataFrame
    """
    fetchers = {
        "stock": fetch_stock_data,
        "etf": fetch_etf_data,
        "fund": fetch_fund_data,
        "bond": fetch_bond_data,
        "futures_etf": fetch_futures_etf_data,
    }

    fetcher = fetchers.get(asset_type)
    if not fetcher:
        raise ValueError(f"不支持的资产类型: {asset_type}")

    return fetcher(symbol, start_date, end_date)


# ═══════════════════════════════════════════════════════════════
# 回测运行适配器
# ═══════════════════════════════════════════════════════════════

def run_backtest_multi_asset(
    symbols: list[str],
    asset_types: list[str],
    strategy_code: str,
    start_date: str,
    end_date: str,
    initial_cash: float = 100000,
    **kwargs,
) -> dict[str, Any]:
    """多资产回测.

    Args:
        symbols: 标的代码列表
        asset_types: 资产类型列表（与symbols一一对应）
        strategy_code: 策略源码
        start_date: 开始日期
        end_date: 结束日期
        initial_cash: 初始资金

    Returns:
        {
            "metrics": {...},
            "trades": [...],
            "candles": {...},
            "benchmark": {...},
        }
    """
    import akquant

    # 获取数据
    data_frames = {}
    for symbol, asset_type in zip(symbols, asset_types):
        df = fetch_asset_data(symbol, asset_type, start_date, end_date)
        data_frames[symbol] = df

    if len(data_frames) == 1:
        data_input = list(data_frames.values())[0]
    else:
        data_input = data_frames

    # 写入策略临时文件
    tmp_path = _write_strategy_to_temp_file(strategy_code)

    try:
        # 运行回测
        result = akquant.run_backtest(
            data=data_input,
            strategy_source=tmp_path,
            symbols=symbols,
            initial_cash=initial_cash,
            start_time=start_date,
            end_time=end_date,
            show_progress=False,
            **kwargs,
        )

        metrics = _extract_metrics(result)
        trades = _extract_trades(result)
        candles = {sym: _df_to_candles(df) for sym, df in data_frames.items()}

        # 基准对照
        benchmark = _run_benchmark(
            data_input=data_input,
            symbols=symbols,
            initial_cash=initial_cash,
            start_date=start_date,
            end_date=end_date,
        )

        return {
            "success": True,
            "metrics": metrics,
            "trades": trades,
            "candles": candles,
            "benchmark": benchmark,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }
    finally:
        import os
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


# ═══════════════════════════════════════════════════════════════
# Walk-Forward验证
# ═══════════════════════════════════════════════════════════════

def walk_forward_validation(
    symbol: str,
    asset_type: str,
    strategy_code: str,
    start_date: str,
    end_date: str,
    train_ratio: float = 0.6,
    val_ratio: float = 0.2,
    initial_cash: float = 100000,
) -> dict[str, Any]:
    """Walk-Forward验证.

    训练60% / 验证20% / 测试20%

    Returns:
        {
            "train": {"metrics": {...}, "period": "2020-01-01~2021-06-30"},
            "validation": {"metrics": {...}, "period": "2021-07-01~2022-03-31"},
            "test": {"metrics": {...}, "period": "2022-04-01~2022-12-31"},
        }
    """
    # 获取完整数据
    df = fetch_asset_data(symbol, asset_type, start_date, end_date)

    # 计算分割点
    total_len = len(df)
    train_end = int(total_len * train_ratio)
    val_end = int(total_len * (train_ratio + val_ratio))

    train_df = df.iloc[:train_end]
    val_df = df.iloc[train_end:val_end]
    test_df = df.iloc[val_end:]

    periods = {
        "train": train_df,
        "validation": val_df,
        "test": test_df,
    }

    results = {}
    for period_name, period_df in periods.items():
        if len(period_df) < 30:
            results[period_name] = {
                "success": False,
                "error": "数据不足30天",
            }
            continue

        period_start = period_df.index[0].strftime("%Y-%m-%d")
        period_end = period_df.index[-1].strftime("%Y-%m-%d")

        result = run_backtest_multi_asset(
            symbols=[symbol],
            asset_types=[asset_type],
            strategy_code=strategy_code,
            start_date=period_start,
            end_date=period_end,
            initial_cash=initial_cash,
        )

        results[period_name] = {
            **result,
            "period": f"{period_start}~{period_end}",
        }

    return results


# ═══════════════════════════════════════════════════════════════
# 蒙特卡洛模拟
# ═══════════════════════════════════════════════════════════════

def monte_carlo_simulation(
    returns: list[float],
    n_simulations: int = 1000,
    n_days: int = 252,
    initial_value: float = 100000,
    confidence: float = 0.95,
) -> dict[str, Any]:
    """蒙特卡洛模拟.

    Args:
        returns: 历史收益率序列
        n_simulations: 模拟次数
        n_days: 模拟天数
        initial_value: 初始价值
        confidence: 置信区间

    Returns:
        {
            "mean_final": 105000,
            "median_final": 104000,
            "std_final": 15000,
            " VaR_95": -5000,
            "max_drawdown_95": 0.15,
            "paths": [[...], [...], ...],  # 前100条路径
        }
    """
    import numpy as np

    returns = np.array(returns)
    mean_return = np.mean(returns)
    std_return = np.std(returns)

    # 生成随机路径
    np.random.seed(42)
    simulations = np.random.normal(
        mean_return,
        std_return,
        (n_simulations, n_days),
    )

    # 计算累积收益
    cumulative_returns = np.cumprod(1 + simulations, axis=1)
    final_values = initial_value * cumulative_returns[:, -1]

    # 计算最大回撤
    peak = np.maximum.accumulate(cumulative_returns, axis=1)
    drawdowns = (peak - cumulative_returns) / peak
    max_drawdowns = np.max(drawdowns, axis=1)

    # 置信区间
    alpha = 1 - confidence
    var_threshold = np.percentile(final_values - initial_value, alpha * 100)
    dd_threshold = np.percentile(max_drawdowns, confidence * 100)

    return {
        "mean_final": round(float(np.mean(final_values)), 2),
        "median_final": round(float(np.median(final_values)), 2),
        "std_final": round(float(np.std(final_values)), 2),
        "VaR_95": round(float(var_threshold), 2),
        "max_drawdown_95": round(float(dd_threshold), 4),
        "paths": [
            (initial_value * cumulative_returns[i]).tolist()
            for i in range(min(100, n_simulations))
        ],
    }


# ═══════════════════════════════════════════════════════════════
# 压力测试
# ═══════════════════════════════════════════════════════════════

STRESS_SCENARIOS = {
    "2022_bear": {
        "name": "2022年熊市",
        "description": "俄乌冲突+美联储加息+疫情反复",
        "start": "2022-01-01",
        "end": "2022-12-31",
    },
    "2020_covid": {
        "name": "2020年疫情暴跌",
        "description": "新冠疫情全球爆发",
        "start": "2020-01-20",
        "end": "2020-04-30",
    },
    "2015_crash": {
        "name": "2015年股灾",
        "description": "A股异常波动",
        "start": "2015-06-15",
        "end": "2015-09-30",
    },
    "2018_trade_war": {
        "name": "2018年贸易战",
        "description": "中美贸易摩擦",
        "start": "2018-03-01",
        "end": "2018-12-31",
    },
}


def stress_test(
    symbol: str,
    asset_type: str,
    strategy_code: str,
    scenario: str,
    initial_cash: float = 100000,
) -> dict[str, Any]:
    """压力测试.

    Args:
        scenario: 场景名称 (2022_bear/2020_covid/2015_crash/2018_trade_war)

    Returns:
        {
            "scenario": {...},
            "result": {...},
        }
    """
    scenario_info = STRESS_SCENARIOS.get(scenario)
    if not scenario_info:
        return {
            "success": False,
            "error": f"未知场景: {scenario}",
        }

    result = run_backtest_multi_asset(
        symbols=[symbol],
        asset_types=[asset_type],
        strategy_code=strategy_code,
        start_date=scenario_info["start"],
        end_date=scenario_info["end"],
        initial_cash=initial_cash,
    )

    return {
        "success": True,
        "scenario": scenario_info,
        "result": result,
    }


def run_all_stress_tests(
    symbol: str,
    asset_type: str,
    strategy_code: str,
    initial_cash: float = 100000,
) -> dict[str, Any]:
    """运行所有压力测试场景."""
    results = {}
    for scenario_id in STRESS_SCENARIOS:
        results[scenario_id] = stress_test(
            symbol=symbol,
            asset_type=asset_type,
            strategy_code=strategy_code,
            scenario=scenario_id,
            initial_cash=initial_cash,
        )

    return {
        "success": True,
        "scenarios": results,
    }
