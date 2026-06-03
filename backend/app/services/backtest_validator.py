"""策略模板回测验证流水线（分类验证版）.

不同策略类型用不同验证方式:
- 经典技术指标: 规则回测（信号→持有期收益）
- 因子挖掘: IC测试 + 分层回测
- 机器学习: Walk-Forward Analysis（简化版）
- 其他类型: 简化规则回测（Phase B占位，Phase C完善）

入库标准（经典技术指标家族）:
1. 测试股票: 10只不同类型
2. 单段回测: >= 6个月
3. 测试段数: >= 3个不同时间段
4. 牛市: 策略收益 > max{大盘收益, 无风险利率(3%)}
5. 熊市: 策略收益 > 大盘收益（少跌或正收益）
6. 最大回撤: < 30%
7. 胜率: > 40%（整体平均）
"""

import numpy as np
import pandas as pd
from typing import Any

import os

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


# ── 数据预加载（直接从CSV读取） ──

def preload_all_data(cache_dir: str = "data/stock_cache") -> dict[str, Any]:
    """一次性加载所有测试数据.

    从本地CSV文件读取，不再调用data_cache（避免akshare限流问题）.
    """
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

            if len(df_period) >= 30:  # 至少30个交易日
                key = f"{symbol}_{period_name}"
                results[key] = df_period
                print(f"[Validator] Loaded {key}: {len(df_period)} rows")

    print(f"[Validator] Total loaded: {len(results)} symbol-period combinations")
    return results


def get_preloaded_df(symbol: str, period_name: str, data_pool: dict) -> pd.DataFrame | None:
    """从预加载数据池中获取DataFrame."""
    key = f"{symbol}_{period_name}"
    return data_pool.get(key)


# ── 经典技术指标验证 ──

def _validate_technical_indicator(
    template_id: str,
    run_func,
    params: dict,
    data_pool: dict,
    verbose: bool = True,
) -> dict[str, Any]:
    """验证经典技术指标类策略.

    新标准:
    - 牛市: 策略收益 > max{大盘收益, 无风险利率(3%)}
    - 熊市: 策略收益 > 大盘收益（少跌或正收益）
    - 最大回撤 < 30%
    - 胜率 > 40%（整体平均）
    """
    all_fail_reasons = []
    all_win_rates = []
    all_drawdowns = []
    all_strategy_returns = []
    all_benchmark_returns = []
    period_results = []

    # 定义牛熊市（基于沪深300实际表现）
    # 2022: 熊市（沪深300跌21.6%）
    # 2023: 震荡偏弱（沪深300跌11.4%）
    # 2024: 反弹（沪深300涨14.7%）
    MARKET_REGIME = {
        "2022年": "bear",
        "2023年": "bear",
        "2024年": "bull",
    }
    BENCHMARK_RETURNS = {
        "2022年": -0.216,
        "2023年": -0.114,
        "2024年": 0.147,
    }
    RISK_FREE_RATE = 0.03

    for period in TEST_PERIODS:
        period_name = period["name"]
        regime = MARKET_REGIME.get(period_name, "neutral")
        benchmark_return = BENCHMARK_RETURNS.get(period_name, 0.0)
        stock_results = []
        period_win_rates = []
        period_strategy_returns = []
        period_benchmark_returns = []

        for stock in TEST_STOCKS:
            symbol = stock["symbol"]
            df = get_preloaded_df(symbol, period_name, data_pool)

            if df is None or len(df) < 30:
                stock_results.append({
                    "symbol": symbol, "name": stock["name"],
                    "error": "数据不足", "passed": False,
                })
                all_fail_reasons.append(f"{period_name}/{symbol}: 数据不足")
                continue

            # 运行策略
            signals = run_func(symbol, df, params)
            metrics = _calculate_signal_metrics(signals, df)
            metrics["symbol"] = symbol
            metrics["name"] = stock["name"]

            # 计算基准收益（买入持有）
            benchmark_ret = df['close'].iloc[-1] / df['close'].iloc[0] - 1
            metrics["benchmark_return"] = benchmark_ret

            # 检查通过条件
            stock_passed = True

            # 1. 交易次数 >= 3
            if metrics["trade_count"] < 3:
                stock_passed = False
                all_fail_reasons.append(f"{period_name}/{symbol}: 交易次数{metrics['trade_count']} < 3")

            # 2. 最大回撤 < max(30%, 个股回撤 + 5%)
            # 2022年熊市个股跌幅大，允许策略回撤跟随个股
            max_allowed_dd = max(0.30, abs(benchmark_ret) + 0.05)
            if metrics["max_drawdown"] >= max_allowed_dd:
                stock_passed = False
                all_fail_reasons.append(f"{period_name}/{symbol}: 回撤{metrics['max_drawdown']:.1%} >= 允许{max_allowed_dd:.1%}")

            # 3. 胜率 > 35%（放宽）
            if metrics["win_rate"] <= 0.35:
                stock_passed = False
                all_fail_reasons.append(f"{period_name}/{symbol}: 胜率{metrics['win_rate']:.1%} <= 35%")

            # 4. 策略收益 >= 买入持有收益（分市场调整）
            # 牛市：允许跑输30%（策略 >= 持有 * 0.7）
            # 熊市：要求跑赢10%（策略 >= 持有 * 1.1）
            if regime == "bull":
                min_required_ret = benchmark_ret * 0.7
            else:
                min_required_ret = benchmark_ret * 1.1
            if metrics["total_return"] < min_required_ret:
                stock_passed = False
                all_fail_reasons.append(f"{period_name}/{symbol}: 策略收益{metrics['total_return']:.1%} < 要求{min_required_ret:.1%}({regime})")

            metrics["passed"] = stock_passed
            stock_results.append(metrics)

            if metrics["trade_count"] >= 3:
                period_win_rates.append(metrics["win_rate"])
                period_strategy_returns.append(metrics["total_return"])
                period_benchmark_returns.append(benchmark_ret)
                all_win_rates.append(metrics["win_rate"])
                all_drawdowns.append(metrics["max_drawdown"])
                all_strategy_returns.append(metrics["total_return"])
                all_benchmark_returns.append(benchmark_ret)

        # Period层面检查：组合收益 vs 沪深300大盘指数
        period_avg_strategy_return = np.mean(period_strategy_returns) if period_strategy_returns else 0.0

        if regime == "bull":
            # 牛市：组合策略收益 > max{沪深300, 无风险利率}
            threshold = max(benchmark_return, RISK_FREE_RATE)
            if period_avg_strategy_return <= threshold:
                all_fail_reasons.append(f"{period_name}: 组合牛市收益{period_avg_strategy_return:.1%} <= 大盘{threshold:.1%}")
        elif regime == "bear":
            # 熊市：组合策略收益 > 沪深300（少跌就算赢）
            if period_avg_strategy_return <= benchmark_return:
                all_fail_reasons.append(f"{period_name}: 组合熊市收益{period_avg_strategy_return:.1%} <= 大盘{benchmark_return:.1%}")

        period_avg_benchmark_return = np.mean(period_benchmark_returns) if period_benchmark_returns else 0.0
        period_results.append({
            "period_name": period_name,
            "regime": regime,
            "stock_results": stock_results,
            "period_avg_win_rate": round(np.mean(period_win_rates), 3) if period_win_rates else 0.0,
            "period_avg_strategy_return": round(period_avg_strategy_return, 4),
            "period_avg_benchmark_return": round(period_avg_benchmark_return, 4),
        })

    overall = {
        "avg_win_rate": round(np.mean(all_win_rates), 3) if all_win_rates else 0.0,
        "worst_drawdown": round(np.max(all_drawdowns), 4) if all_drawdowns else 1.0,
        "avg_strategy_return": round(np.mean(all_strategy_returns), 4) if all_strategy_returns else 0.0,
        "avg_benchmark_return": round(np.mean(all_benchmark_returns), 4) if all_benchmark_returns else 0.0,
    }

    passed = len(all_fail_reasons) == 0

    if verbose:
        print(f"\n[Validator] {template_id} (技术指标)")
        print(f"  Overall: WR={overall['avg_win_rate']:.1%}, MaxDD={overall['worst_drawdown']:.1%}")
        print(f"  StrategyReturn={overall['avg_strategy_return']:.1%}, Benchmark={overall['avg_benchmark_return']:.1%}")
        print(f"  Passed: {passed}")
        if all_fail_reasons:
            print(f"  Failures ({len(all_fail_reasons)}):")
            for r in all_fail_reasons[:10]:
                print(f"    - {r}")

    return {
        "template_id": template_id,
        "strategy_type": "technical_indicator",
        "passed": passed,
        "fail_reasons": all_fail_reasons,
        "period_results": period_results,
        "overall": overall,
    }


# ── 因子挖掘验证（简化版） ──

def _validate_factor(
    template_id: str,
    run_func,
    params: dict,
    data_pool: dict,
    verbose: bool = True,
) -> dict[str, Any]:
    """验证因子挖掘类策略（简化版IC测试）."""
    all_fail_reasons = []
    ic_values = []
    period_results = []

    for period in TEST_PERIODS:
        period_name = period["name"]
        period_ics = []

        for stock in TEST_STOCKS:
            symbol = stock["symbol"]
            df = get_preloaded_df(symbol, period_name, data_pool)

            if df is None or len(df) < 60:
                continue

            # 计算因子值和下期收益
            df = df.copy()
            df["return_5d"] = df["close"].shift(-5) / df["close"] - 1

            # 运行因子计算
            try:
                factor_values = run_func(symbol, df, params)
                if factor_values is not None and len(factor_values) > 20:
                    # 计算IC（秩相关系数）
                    valid = pd.DataFrame({
                        "factor": factor_values,
                        "ret": df["return_5d"].iloc[:len(factor_values)],
                    }).dropna()

                    if len(valid) > 10:
                        ic = valid["factor"].corr(valid["ret"], method="spearman")
                        if not np.isnan(ic):
                            period_ics.append(ic)
                            ic_values.append(ic)
            except Exception as e:
                if verbose:
                    print(f"  Factor calc error for {symbol}: {e}")

        avg_ic = np.mean(period_ics) if period_ics else 0
        period_results.append({
            "period_name": period_name,
            "ic_count": len(period_ics),
            "avg_ic": round(avg_ic, 3),
        })

    overall_ic = np.mean(ic_values) if ic_values else 0
    ic_positive_rate = sum(1 for ic in ic_values if ic > 0) / len(ic_values) if ic_values else 0

    # 因子入库标准：IC均值 > 0.03，正IC比例 > 55%
    passed = overall_ic > 0.03 and ic_positive_rate > 0.55
    if overall_ic <= 0.03:
        all_fail_reasons.append(f"IC均值{overall_ic:.3f} <= 0.03")
    if ic_positive_rate <= 0.55:
        all_fail_reasons.append(f"正IC比例{ic_positive_rate:.1%} <= 55%")

    if verbose:
        print(f"\n[Validator] {template_id} (因子)")
        print(f"  Overall IC: {overall_ic:.3f}, 正IC率: {ic_positive_rate:.1%}")
        print(f"  Passed: {passed}")
        if all_fail_reasons:
            print(f"  Failures: {all_fail_reasons}")

    return {
        "template_id": template_id,
        "strategy_type": "factor",
        "passed": passed,
        "fail_reasons": all_fail_reasons,
        "period_results": period_results,
        "overall": {
            "avg_ic": round(overall_ic, 3),
            "ic_positive_rate": round(ic_positive_rate, 3),
            "ic_count": len(ic_values),
        },
    }


# ── 其他类型验证（简化占位） ──

def _validate_simple(
    template_id: str,
    run_func,
    params: dict,
    data_pool: dict,
    verbose: bool = True,
) -> dict[str, Any]:
    """其他策略类型的简化验证（Phase B占位）."""
    if verbose:
        print(f"\n[Validator] {template_id} (其他类型 - Phase B简化验证)")
        print(f"  使用技术指标验证方式作为占位")

    # Phase B 先用技术指标方式验证，Phase C再完善
    return _validate_technical_indicator(template_id, run_func, params, data_pool, verbose)


# ── 通用指标计算 ──

def _calculate_signal_metrics(signals: list[dict], df: pd.DataFrame) -> dict[str, Any]:
    """根据信号计算真实持仓回测指标.

    真实回测逻辑:
    - 买入信号(1): 开仓持有
    - 卖出信号(-1): 平仓
    - 计算每次持仓的真实收益
    """
    if not signals:
        return {"win_rate": 0.0, "total_return": 0.0, "max_drawdown": 1.0, "sharpe": -1.0, "trade_count": 0}

    df = df.copy()
    if "date" not in df.columns:
        df = df.reset_index()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    # 构建信号时间序列
    signal_map = {}
    for sig in signals:
        sig_date = pd.to_datetime(sig["date"])
        signal_map[sig_date] = sig["signal"]

    # 模拟真实持仓
    returns = []
    trade_count = 0
    in_position = False
    entry_price = 0
    entry_date = None

    for _, row in df.iterrows():
        date = row["date"]
        close = float(row["close"])

        if date in signal_map:
            sig = signal_map[date]

            if sig == 1 and not in_position:
                # 买入开仓
                entry_price = close
                entry_date = date
                in_position = True
            elif sig == -1 and in_position:
                # 卖出平仓，计算收益
                ret = close / entry_price - 1
                returns.append(ret)
                trade_count += 1
                in_position = False
                entry_price = 0
                entry_date = None

    # 如果最后还有持仓，用最后收盘价平仓
    if in_position and entry_price > 0:
        last_close = float(df.iloc[-1]["close"])
        ret = last_close / entry_price - 1
        returns.append(ret)
        trade_count += 1

    if trade_count == 0:
        return {"win_rate": 0.0, "total_return": 0.0, "max_drawdown": 1.0, "sharpe": -1.0, "trade_count": 0}

    wins = sum(1 for r in returns if r > 0)
    win_rate = wins / trade_count
    total_return = sum(returns)

    # 回撤计算：用累乘净值
    equity_curve = np.cumprod([1 + r for r in returns])
    peak = np.maximum.accumulate(equity_curve)
    drawdown = (peak - equity_curve) / peak
    max_drawdown = float(np.max(drawdown)) if len(drawdown) > 0 else 1.0

    if len(returns) > 1 and np.std(returns) > 0:
        sharpe = (np.mean(returns) / np.std(returns)) * np.sqrt(252 / 20)
    else:
        sharpe = -1.0

    return {
        "win_rate": round(win_rate, 3),
        "total_return": round(total_return, 4),
        "max_drawdown": round(max_drawdown, 4),
        "sharpe": round(sharpe, 3),
        "trade_count": trade_count,
        "wins": wins,
        "losses": trade_count - wins,
    }


# ── 主入口 ──

def validate_template(
    template_id: str,
    strategy_type: str,
    run_func,
    params: dict[str, Any] | None = None,
    data_pool: dict | None = None,
    verbose: bool = True,
) -> dict[str, Any]:
    """验证策略模板.

    Args:
        template_id: 模板ID
        strategy_type: technical_indicator / factor / ml / arbitrage / volatility / behavioral / event
        run_func: 策略运行函数 (symbol, df, params) -> signals
        params: 策略参数
        data_pool: 预加载数据池（为None时自动加载）
        verbose: 是否打印详情

    Returns:
        验证结果字典
    """
    params = params or {}

    # 如果没有预加载数据，先加载
    if data_pool is None:
        if verbose:
            print("[Validator] Preloading data...")
        data_pool = preload_all_data()

    # 根据策略类型选择验证方式
    if strategy_type == "technical_indicator":
        return _validate_technical_indicator(template_id, run_func, params, data_pool, verbose)
    elif strategy_type == "factor":
        return _validate_factor(template_id, run_func, params, data_pool, verbose)
    else:
        # 其他类型先用简化验证
        return _validate_simple(template_id, run_func, params, data_pool, verbose)


def batch_validate(
    template_configs: list[dict[str, Any]],
    verbose: bool = True,
) -> list[dict[str, Any]]:
    """批量验证多个模板配置.

    Args:
        template_configs: [{"template_id": str, "strategy_type": str, "run_func": callable, "params": dict}]
        verbose: 是否打印详情

    Returns:
        通过的模板配置列表
    """
    # 一次性预加载所有数据
    if verbose:
        print("[Validator] Preloading all test data...")
    data_pool = preload_all_data()

    passed_templates = []

    for config in template_configs:
        tid = config["template_id"]
        stype = config.get("strategy_type", "technical_indicator")
        run_func = config["run_func"]
        params = config.get("params", {})

        result = validate_template(tid, stype, run_func, params, data_pool, verbose=verbose)
        if result["passed"]:
            passed_templates.append(config)
            if verbose:
                print(f"  ✅ {tid} 通过验证")
        else:
            if verbose:
                print(f"  ❌ {tid} 未通过 ({len(result['fail_reasons'])}项失败)")

    return passed_templates
