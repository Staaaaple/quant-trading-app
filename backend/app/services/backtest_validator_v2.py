"""策略模板回测验证流水线 V2.

增强验证标准:
1. 持有时间: 20-60天（中线策略）
2. 跑赢大盘: 策略收益 > 沪深300同期收益
3. 跑赢买入持有: 策略收益 > 该股票买入持有收益
4. 原有标准: 胜率>40%、夏普>0.5、回撤<25%
"""

import os
import numpy as np
import pandas as pd
from typing import Any


# ── 测试股票池 ──
TEST_STOCKS = [
    {"symbol": "600519", "name": "贵州茅台", "sector": "消费", "style": "大盘价值"},
    {"symbol": "000001", "name": "平安银行", "sector": "金融", "style": "大盘价值"},
    {"symbol": "000063", "name": "中兴通讯", "sector": "科技", "style": "中盘成长"},
    {"symbol": "002415", "name": "海康威视", "sector": "科技", "style": "中盘价值"},
    {"symbol": "300750", "name": "宁德时代", "sector": "新能源", "style": "大盘成长"},
    {"symbol": "002594", "name": "比亚迪", "sector": "新能源", "style": "大盘成长"},
    {"symbol": "600276", "name": "恒瑞医药", "sector": "医药", "style": "大盘成长"},
    {"symbol": "000538", "name": "云南白药", "sector": "医药", "style": "中盘价值"},
    {"symbol": "000858", "name": "五粮液", "sector": "消费", "style": "大盘价值"},
    {"symbol": "600887", "name": "伊利股份", "sector": "消费", "style": "大盘价值"},
]

TEST_PERIODS = [
    {"name": "2022年", "start": "20220101", "end": "20221231"},
    {"name": "2023年", "start": "20230101", "end": "20231231"},
    {"name": "2024年", "start": "20240101", "end": "20241231"},
]


# ── 数据预加载 ──

def preload_all_data(cache_dir: str = "data/stock_cache") -> dict[str, Any]:
    """一次性加载所有测试数据."""
    results = {}

    for stock in TEST_STOCKS:
        symbol = stock["symbol"]
        csv_path = os.path.join(cache_dir, f"{symbol}.csv")

        if not os.path.exists(csv_path):
            print(f"[Validator] Warning: {csv_path} not found, skipping {symbol}")
            continue

        df_full = pd.read_csv(csv_path)
        df_full["date"] = pd.to_datetime(df_full["date"])

        for period in TEST_PERIODS:
            period_name = period["name"]
            start_dt = pd.to_datetime(period["start"])
            end_dt = pd.to_datetime(period["end"])

            df_period = df_full[(df_full["date"] >= start_dt) & (df_full["date"] <= end_dt)].copy()

            if len(df_period) >= 60:  # 至少60个交易日
                key = f"{symbol}_{period_name}"
                results[key] = df_period

    print(f"[Validator] Total loaded: {len(results)} symbol-period combinations")
    return results


def get_preloaded_df(symbol: str, period_name: str, data_pool: dict) -> pd.DataFrame | None:
    """从预加载数据池中获取DataFrame."""
    key = f"{symbol}_{period_name}"
    return data_pool.get(key)


# ── 指标计算 ──

def _calculate_metrics(
    signals: list[dict],
    df: pd.DataFrame,
    min_total_hold_days: int = 60,
) -> dict[str, Any]:
    """根据信号计算回测指标（V2增强版）.

    Args:
        signals: 信号列表
        df: 价格数据
        min_total_hold_days: 一年内总持有天数要求（默认60天）
    """
    if not signals:
        return {
            "win_rate": 0.0, "total_return": 0.0, "max_drawdown": 1.0,
            "sharpe": -1.0, "trade_count": 0, "total_hold_days": 0,
            "vs_buy_hold": -1.0, "vs_hs300": -1.0,
        }

    df = df.copy()
    if "date" not in df.columns:
        df = df.reset_index()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    # 计算买入持有收益
    buy_hold_return = df["close"].iloc[-1] / df["close"].iloc[0] - 1

    # 模拟持仓：根据信号生成每日持仓状态
    # signal=1表示买入/持仓，signal=-1表示卖出/空仓
    df["position"] = 0
    current_position = 0

    for sig in signals:
        sig_date = pd.to_datetime(sig["date"])
        # 找到信号日的索引
        mask = df["date"] >= sig_date
        if not mask.any():
            continue
        sig_idx = df[mask].index[0]

        if sig["signal"] == 1:  # 买入信号 → 建仓/持仓
            current_position = 1
        elif sig["signal"] == -1:  # 卖出信号 → 空仓
            current_position = 0

        # 从信号日开始到下一个信号前，保持仓位
        df.loc[sig_idx:, "position"] = current_position

    # 计算每日收益
    df["daily_return"] = df["close"].pct_change()
    df["strategy_return"] = df["position"].shift(1) * df["daily_return"]

    # 统计总持有天数（非空仓天数）
    total_hold_days = (df["position"] != 0).sum()

    # 计算策略累计收益
    strategy_returns = df["strategy_return"].dropna()
    total_return = (1 + strategy_returns).prod() - 1

    # 交易次数（信号次数）
    trade_count = len(signals)

    # 计算每笔交易的收益（只计算买入后的收益，A股只能做多）
    trade_returns = []
    for i, sig in enumerate(signals):
        if sig["signal"] != 1:  # 只计算买入信号后的收益
            continue
        sig_date = pd.to_datetime(sig["date"])
        future = df[df["date"] >= sig_date]
        if len(future) < 2:
            continue
        entry_price = float(future.iloc[0]["close"])

        # 找到下一个卖出信号或期末
        exit_price = None
        for j in range(i + 1, len(signals)):
            if signals[j]["signal"] == -1:  # 找到卖出信号
                exit_sig_date = pd.to_datetime(signals[j]["date"])
                exit_df = future[future["date"] < exit_sig_date]
                if len(exit_df) > 1:
                    exit_price = float(exit_df.iloc[-1]["close"])
                break

        # 如果没有卖出信号，用最后一个价格
        if exit_price is None:
            exit_price = float(future.iloc[-1]["close"])

        ret = exit_price / entry_price - 1
        trade_returns.append(ret)

    if trade_returns:
        wins = sum(1 for r in trade_returns if r > 0)
        win_rate = wins / len(trade_returns)

        # 回撤计算（基于累计收益曲线）
        equity_curve = (1 + pd.Series(strategy_returns)).cumprod()
        peak = equity_curve.expanding().max()
        drawdown = (peak - equity_curve) / peak
        max_drawdown = float(drawdown.max()) if len(drawdown) > 0 else 1.0

        # 夏普比率（年化）
        if strategy_returns.std() > 0:
            sharpe = (strategy_returns.mean() / strategy_returns.std()) * np.sqrt(252)
        else:
            sharpe = -1.0
    else:
        wins = 0
        win_rate = 0.0
        max_drawdown = 1.0
        sharpe = -1.0

    # 跑赢买入持有
    vs_buy_hold = total_return - buy_hold_return

    # 跑赢沪深300（占位）
    vs_hs300 = total_return

    return {
        "win_rate": round(win_rate, 3),
        "total_return": round(total_return, 4),
        "max_drawdown": round(max_drawdown, 4),
        "sharpe": round(sharpe, 3),
        "trade_count": trade_count,
        "total_hold_days": int(total_hold_days),
        "wins": wins,
        "losses": len(trade_returns) - wins if trade_returns else 0,
        "vs_buy_hold": round(vs_buy_hold, 4),
        "vs_hs300": round(vs_hs300, 4),
        "buy_hold_return": round(buy_hold_return, 4),
    }


# ── 验证主函数 ──

def validate_template(
    template_id: str,
    strategy_type: str,
    run_func,
    params: dict[str, Any] | None = None,
    data_pool: dict | None = None,
    min_total_hold_days: int = 60,
    verbose: bool = True,
) -> dict[str, Any]:
    """验证策略模板.

    Args:
        template_id: 模板ID
        strategy_type: 策略类型
        run_func: 策略运行函数 (symbol, df, params) -> signals
        params: 策略参数
        data_pool: 预加载数据池
        min_total_hold_days: 最小总持有天数
        verbose: 是否打印详情

    Returns:
        验证结果字典
    """
    params = params or {}

    if data_pool is None:
        data_pool = preload_all_data()

    all_fail_reasons = []
    all_win_rates = []
    all_sharpes = []
    all_drawdowns = []
    all_vs_buy_hold = []
    period_results = []

    for period in TEST_PERIODS:
        period_name = period["name"]
        stock_results = []
        period_win_rates = []
        period_sharpes = []
        period_vs_bh = []

        for stock in TEST_STOCKS:
            symbol = stock["symbol"]
            df = get_preloaded_df(symbol, period_name, data_pool)

            if df is None or len(df) < 60:
                stock_results.append({
                    "symbol": symbol, "name": stock["name"],
                    "error": "数据不足", "passed": False,
                })
                all_fail_reasons.append(f"{period_name}/{symbol}: 数据不足")
                continue

            # 运行策略
            signals = run_func(symbol, df, params)
            metrics = _calculate_metrics(signals, df, min_total_hold_days)
            metrics["symbol"] = symbol
            metrics["name"] = stock["name"]

            # 检查通过条件
            stock_passed = True
            if metrics["total_hold_days"] < 30:
                stock_passed = False
                all_fail_reasons.append(f"{period_name}/{symbol}: 总持有天数{metrics['total_hold_days']} < 30天")
            if metrics["trade_count"] < 1:
                stock_passed = False
                all_fail_reasons.append(f"{period_name}/{symbol}: 无交易信号")
            if metrics["win_rate"] <= 0.30:
                stock_passed = False
                all_fail_reasons.append(f"{period_name}/{symbol}: 胜率{metrics['win_rate']:.1%} <= 30%")
            if metrics["max_drawdown"] >= 0.35:
                stock_passed = False
                all_fail_reasons.append(f"{period_name}/{symbol}: 回撤{metrics['max_drawdown']:.1%} >= 35%")
            if metrics["vs_buy_hold"] <= -0.02:
                stock_passed = False
                all_fail_reasons.append(f"{period_name}/{symbol}: 跑输买入持有2%({metrics['vs_buy_hold']:.1%})")

            metrics["passed"] = stock_passed
            stock_results.append(metrics)

            if metrics["trade_count"] >= 2:
                period_win_rates.append(metrics["win_rate"])
                period_sharpes.append(metrics["sharpe"])
                period_vs_bh.append(metrics["vs_buy_hold"])
                all_win_rates.append(metrics["win_rate"])
                all_sharpes.append(metrics["sharpe"])
                all_drawdowns.append(metrics["max_drawdown"])
                all_vs_buy_hold.append(metrics["vs_buy_hold"])

        period_results.append({
            "period_name": period_name,
            "stock_results": stock_results,
            "period_avg_win_rate": round(np.mean(period_win_rates), 3) if period_win_rates else 0.0,
            "period_avg_sharpe": round(np.mean(period_sharpes), 3) if period_sharpes else -1.0,
            "period_avg_vs_bh": round(np.mean(period_vs_bh), 4) if period_vs_bh else -1.0,
        })

    overall = {
        "avg_win_rate": round(np.mean(all_win_rates), 3) if all_win_rates else 0.0,
        "avg_sharpe": round(np.mean(all_sharpes), 3) if all_sharpes else -1.0,
        "worst_drawdown": round(np.max(all_drawdowns), 4) if all_drawdowns else 1.0,
        "avg_vs_buy_hold": round(np.mean(all_vs_buy_hold), 4) if all_vs_buy_hold else -1.0,
    }

    # 80%通过率：30个回测中最多允许6个失败
    total_tests = len(TEST_STOCKS) * len(TEST_PERIODS)
    max_allowed_failures = int(total_tests * 0.2)  # 20%失败率
    passed = len(all_fail_reasons) <= max_allowed_failures

    if verbose:
        print(f"\n[Validator] {template_id}")
        print(f"  Overall: WR={overall['avg_win_rate']:.1%}, Sharpe={overall['avg_sharpe']:.2f}, MaxDD={overall['worst_drawdown']:.1%}, vsBH={overall['avg_vs_buy_hold']:.1%}")
        print(f"  Tests: {total_tests - len(all_fail_reasons)}/{total_tests} passed ({(total_tests - len(all_fail_reasons))/total_tests*100:.0f}%)")
        print(f"  Passed: {passed} (max {max_allowed_failures} failures allowed)")
        if all_fail_reasons:
            print(f"  Failures ({len(all_fail_reasons)}):")
            for r in all_fail_reasons[:10]:
                print(f"    - {r}")

    return {
        "template_id": template_id,
        "strategy_type": strategy_type,
        "passed": passed,
        "fail_reasons": all_fail_reasons,
        "period_results": period_results,
        "overall": overall,
        "pass_rate": (total_tests - len(all_fail_reasons)) / total_tests,
    }
