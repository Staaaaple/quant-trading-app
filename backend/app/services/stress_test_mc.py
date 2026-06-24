"""压力测试 + 蒙特卡洛模拟模块.

功能:
1. 压力测试: 4大历史极端场景回放
   - 2022年熊市 (俄乌冲突+美联储加息)
   - 2020年疫情暴跌 (新冠爆发)
   - 2015年股灾 (A股异常波动)
   - 2018年贸易战 (中美贸易摩擦)

2. 蒙特卡洛模拟: 1000次随机路径
   - 基于历史收益分布生成随机路径
   - 计算VaR、CVaR、最大回撤分布
   - 组合层面聚合模拟

3. 集成到Hybrid引擎Step 5可靠性评估
"""

import logging
from typing import Any
from dataclasses import dataclass

import numpy as np
import pandas as pd

from app.core.config import settings

logger = logging.getLogger(__name__)


# 导入放在函数内避免循环导入
ADOPTION_CONFIDENCE_THRESHOLD = getattr(settings, "ADOPTION_CONFIDENCE_THRESHOLD", 0.65)

@dataclass
class StressScenario:
    """压力测试场景."""
    id: str
    name: str
    description: str
    start_date: str
    end_date: str
    market_regime: str  # bear/crash/volatile
    benchmark_return: float  # 沪深300同期收益 (小数)
    key_events: list[str]


STRESS_SCENARIOS: dict[str, StressScenario] = {
    "2022_bear": StressScenario(
        id="2022_bear",
        name="2022年熊市",
        description="俄乌冲突爆发+美联储激进加息+国内疫情反复",
        start_date="2022-01-01",
        end_date="2022-12-31",
        market_regime="bear",
        benchmark_return=-0.216,  # 沪深300跌21.6%
        key_events=["俄乌冲突", "美联储加息425bp", "上海封城", "房地产危机"],
    ),
    "2020_covid": StressScenario(
        id="2020_covid",
        name="2020年疫情暴跌",
        description="新冠疫情全球爆发，A股春节后千股跌停",
        start_date="2020-01-20",
        end_date="2020-04-30",
        market_regime="crash",
        benchmark_return=-0.096,  # 沪深300跌9.6% (1-4月)
        key_events=["武汉封城", "全球大流行", "美联储紧急降息", "A股千股跌停"],
    ),
    "2015_crash": StressScenario(
        id="2015_crash",
        name="2015年股灾",
        description="A股异常波动，三轮股灾，大量杠杆爆仓",
        start_date="2015-06-15",
        end_date="2015-09-30",
        market_regime="crash",
        benchmark_return=-0.423,  # 沪深300跌42.3%
        key_events=["去杠杆", "千股跌停", "国家队救市", "熔断测试"],
    ),
    "2018_trade_war": StressScenario(
        id="2018_trade_war",
        name="2018年贸易战",
        description="中美贸易摩擦升级，全年阴跌",
        start_date="2018-03-01",
        end_date="2018-12-31",
        market_regime="bear",
        benchmark_return=-0.253,  # 沪深300跌25.3%
        key_events=["301调查", "关税升级", "中兴事件", "华为事件"],
    ),
}


# ═══════════════════════════════════════════════════════════════
# 2. 压力测试核心
# ═══════════════════════════════════════════════════════════════

def run_stress_test(
    returns: pd.Series,
    scenario_id: str,
    strategy_weights: dict[str, float] | None = None,
) -> dict[str, Any]:
    """对给定收益率序列运行压力测试.

    Args:
        returns: 日收益率序列 (index=date)
        scenario_id: 场景ID
        strategy_weights: 策略权重 {asset: weight}，用于组合层面

    Returns:
        压力测试结果
    """
    scenario = STRESS_SCENARIOS.get(scenario_id)
    if not scenario:
        return {"success": False, "error": f"未知场景: {scenario_id}"}

    # 筛选场景期间的收益率
    mask = (returns.index >= scenario.start_date) & (returns.index <= scenario.end_date)
    period_returns = returns[mask]

    if len(period_returns) < 10:
        return {
            "success": False,
            "error": f"场景期间数据不足: {len(period_returns)} 天",
            "scenario": scenario.__dict__,
        }

    # 计算策略在压力期间的表现
    cumulative = (1 + period_returns).cumprod()
    total_return = cumulative.iloc[-1] - 1

    # 最大回撤
    peak = cumulative.expanding().max()
    drawdown = (cumulative - peak) / peak
    max_drawdown = drawdown.min()

    # 波动率
    volatility = period_returns.std() * (252 ** 0.5)

    # 与基准对比
    benchmark_return = scenario.benchmark_return
    excess_return = total_return - benchmark_return

    # 存活率: 策略是否跑赢基准或跌幅小于基准
    survived = total_return >= benchmark_return or abs(total_return) < abs(benchmark_return) * 1.2

    # 压力评级
    if total_return > 0:
        stress_grade = "A"  # 压力期间正收益
    elif total_return >= benchmark_return:
        stress_grade = "B"  # 跑赢基准
    elif total_return >= benchmark_return * 0.7:
        stress_grade = "C"  # 小幅跑输
    elif total_return >= benchmark_return * 0.5:
        stress_grade = "D"  # 明显跑输
    else:
        stress_grade = "F"  # 严重跑输

    return {
        "success": True,
        "scenario": {
            "id": scenario.id,
            "name": scenario.name,
            "description": scenario.description,
            "period": f"{scenario.start_date}~{scenario.end_date}",
            "market_regime": scenario.market_regime,
            "benchmark_return": round(benchmark_return, 4),
            "key_events": scenario.key_events,
        },
        "strategy_return": round(total_return, 4),
        "benchmark_return": round(benchmark_return, 4),
        "excess_return": round(excess_return, 4),
        "max_drawdown": round(max_drawdown, 4),
        "volatility": round(volatility, 4),
        "survived": survived,
        "stress_grade": stress_grade,
        "trading_days": len(period_returns),
        "daily_returns": period_returns.tolist(),
        "cumulative_curve": cumulative.tolist(),
    }


def run_all_stress_tests(
    returns: pd.Series,
    strategy_weights: dict[str, float] | None = None,
) -> dict[str, Any]:
    """运行所有压力测试场景.

    Returns:
        {
            "overall_grade": "B",
            "survival_rate": 0.75,  # 4个场景中存活3个
            "scenarios": {...},
            "summary": {...},
        }
    """
    results = {}
    grades = []
    survived_count = 0

    for scenario_id in STRESS_SCENARIOS:
        result = run_stress_test(returns, scenario_id, strategy_weights)
        results[scenario_id] = result

        if result.get("success"):
            grades.append(result.get("stress_grade", "F"))
            if result.get("survived", False):
                survived_count += 1

    # 总体评级
    grade_scores = {"A": 4, "B": 3, "C": 2, "D": 1, "F": 0}
    if grades:
        avg_score = sum(grade_scores.get(g, 0) for g in grades) / len(grades)
        overall_grade = ["F", "D", "C", "B", "A"][min(int(avg_score), 4)]
        survival_rate = survived_count / len(grades)
    else:
        overall_grade = "N/A"
        survival_rate = 0.0

    return {
        "success": True,
        "overall_grade": overall_grade,
        "survival_rate": round(survival_rate, 2),
        "total_scenarios": len(STRESS_SCENARIOS),
        "passed_scenarios": survived_count,
        "scenarios": results,
        "summary": {
            "grades": grades,
            "avg_grade_score": round(avg_score, 2) if grades else 0,
        },
    }


# ═══════════════════════════════════════════════════════════════
# 3. 蒙特卡洛模拟核心
# ═══════════════════════════════════════════════════════════════

def monte_carlo_simulation(
    returns: pd.Series,
    n_simulations: int = 1000,
    n_days: int = 252,
    initial_value: float = 100000,
    confidence: float = 0.95,
    strategy_weights: dict[str, float] | None = None,
) -> dict[str, Any]:
    """蒙特卡洛模拟.

    Args:
        returns: 历史日收益率序列
        n_simulations: 模拟次数 (默认1000)
        n_days: 模拟天数 (默认252=1年)
        initial_value: 初始资金
        confidence: 置信水平
        strategy_weights: 组合权重

    Returns:
        蒙特卡洛模拟结果
    """
    returns_arr = returns.dropna().values

    if len(returns_arr) < 30:
        return {
            "success": False,
            "error": f"历史数据不足: {len(returns_arr)} 天，需要至少30天",
        }

    # 统计参数
    mean_return = np.mean(returns_arr)
    std_return = np.std(returns_arr, ddof=1)
    skewness = pd.Series(returns_arr).skew()
    kurtosis = pd.Series(returns_arr).kurtosis()

    # 使用对数收益率进行模拟（更稳定）
    log_returns = np.log1p(returns_arr)
    mean_log = np.mean(log_returns)
    std_log = np.std(log_returns, ddof=1)

    # 生成随机路径 (使用几何布朗运动)
    np.random.seed(42)
    dt = 1 / 252  # 日度

    # 模拟路径: dS/S = μdt + σdW
    random_shocks = np.random.standard_normal((n_simulations, n_days))
    drift = (mean_log - 0.5 * std_log**2) * dt
    diffusion = std_log * np.sqrt(dt) * random_shocks

    daily_returns = drift + diffusion
    log_cumulative = np.cumsum(daily_returns, axis=1)
    price_paths = initial_value * np.exp(log_cumulative)

    # 最终价值分布
    final_values = price_paths[:, -1]
    final_returns = (final_values - initial_value) / initial_value

    # 最大回撤分布
    max_drawdowns = np.zeros(n_simulations)
    for i in range(n_simulations):
        peak = np.maximum.accumulate(price_paths[i])
        dd = (peak - price_paths[i]) / peak
        max_drawdowns[i] = np.max(dd)

    # 统计指标
    alpha = 1 - confidence

    # VaR / CVaR
    var_threshold = np.percentile(final_returns, alpha * 100)
    cvar_threshold = np.mean(final_returns[final_returns <= var_threshold])

    # 回撤分位数
    dd_median = np.median(max_drawdowns)
    dd_95 = np.percentile(max_drawdowns, confidence * 100)
    dd_99 = np.percentile(max_drawdowns, 99)

    # 收益分位数
    return_median = np.median(final_returns)
    return_5 = np.percentile(final_returns, 5)
    return_95 = np.percentile(final_returns, 95)

    # 正收益概率
    prob_profit = np.mean(final_returns > 0)

    # 路径采样 (前50条用于展示)
    sample_paths = [
        {
            "day": list(range(n_days + 1)),
            "value": [initial_value] + price_paths[i].tolist(),
        }
        for i in range(min(50, n_simulations))
    ]

    return {
        "success": True,
        "parameters": {
            "n_simulations": n_simulations,
            "n_days": n_days,
            "initial_value": initial_value,
            "confidence": confidence,
            "historical_mean_daily": round(mean_return, 6),
            "historical_std_daily": round(std_return, 6),
            "historical_skewness": round(skewness, 3),
            "historical_kurtosis": round(kurtosis, 3),
        },
        "final_value_distribution": {
            "mean": round(float(np.mean(final_values)), 2),
            "median": round(float(np.median(final_values)), 2),
            "std": round(float(np.std(final_values)), 2),
            "min": round(float(np.min(final_values)), 2),
            "max": round(float(np.max(final_values)), 2),
            "q5": round(float(np.percentile(final_values, 5)), 2),
            "q95": round(float(np.percentile(final_values, 95)), 2),
        },
        "return_distribution": {
            "mean": round(float(np.mean(final_returns)), 4),
            "median": round(return_median, 4),
            "std": round(float(np.std(final_returns)), 4),
            "q5": round(return_5, 4),
            "q95": round(return_95, 4),
            "prob_profit": round(float(prob_profit), 4),
        },
        "risk_metrics": {
            "VaR_95": round(var_threshold, 4),
            "CVaR_95": round(cvar_threshold, 4),
            "max_drawdown_median": round(float(dd_median), 4),
            "max_drawdown_95": round(float(dd_95), 4),
            "max_drawdown_99": round(float(dd_99), 4),
        },
        "sample_paths": sample_paths,
        "histogram_bins": {
            "returns": np.histogram(final_returns, bins=50)[0].tolist(),
            "bin_edges": np.histogram(final_returns, bins=50)[1].tolist(),
        },
    }


def multi_asset_monte_carlo(
    asset_returns: dict[str, pd.Series],
    asset_weights: dict[str, float],
    n_simulations: int = 1000,
    n_days: int = 252,
    initial_value: float = 100000,
    confidence: float = 0.95,
) -> dict[str, Any]:
    """多资产组合蒙特卡洛模拟.

    Args:
        asset_returns: {asset_id: returns_series}
        asset_weights: {asset_id: weight}
        n_simulations: 模拟次数
        n_days: 模拟天数
        initial_value: 初始资金
        confidence: 置信水平

    Returns:
        组合层面蒙特卡洛结果
    """
    # 对齐收益率序列
    aligned = pd.DataFrame(asset_returns).dropna()

    if len(aligned) < 30:
        return {
            "success": False,
            "error": f"对齐后数据不足: {len(aligned)} 天",
        }

    # 计算组合日收益率
    weights = np.array([asset_weights.get(col, 0) for col in aligned.columns])
    weights = weights / weights.sum()  # 归一化

    portfolio_returns = aligned.dot(weights)

    # 运行单资产蒙特卡洛
    return monte_carlo_simulation(
        returns=portfolio_returns,
        n_simulations=n_simulations,
        n_days=n_days,
        initial_value=initial_value,
        confidence=confidence,
    )


# ═══════════════════════════════════════════════════════════════
# 4. 组合层面压力测试 + 蒙特卡洛
# ═══════════════════════════════════════════════════════════════

def evaluate_portfolio_reliability_v2(
    bindings: list[dict],
    risk_config: dict,
    market_cycle: str,
    backtest_results: dict[str, dict] | None = None,
    saa_weights: dict[str, float] | None = None,
    historical_returns: pd.DataFrame | None = None,
) -> dict[str, Any]:
    """增强版组合可靠性评估（含压力测试+蒙特卡洛）.

    Args:
        bindings: 组合绑定列表
        risk_config: 风控配置
        market_cycle: 市场周期
        backtest_results: 回测结果
        saa_weights: SAA权重
        historical_returns: 历史收益率DataFrame (columns=symbol)

    Returns:
        完整可靠性评估
    """
    from app.services.buy_hold_benchmark import (
        validate_portfolio_against_benchmark,
        compare_portfolio_to_benchmarks,
    )

    # ── 多基准综合评分作为置信度核心输入 ──
    benchmark_comparison = None
    benchmark_score = 0.5  # 默认中性
    if backtest_results and saa_weights:
        try:
            benchmark_comparison = compare_portfolio_to_benchmarks(
                portfolio_bindings=bindings,
                saa_weights=saa_weights,
                backtest_results=backtest_results,
            )
            benchmark_score = benchmark_comparison.get("overall_score", 0.5)
        except Exception as e:
            logger.warning(f"[Reliability] 多基准对比失败: {e}")

    # 把 0-1 的 benchmark_score 映射到 0.2-0.8 的基础置信度
    base_confidence = 0.2 + benchmark_score * 0.6

    n_strategies = len(bindings)
    if n_strategies >= 5:
        base_confidence += 0.05
    elif n_strategies < 3:
        base_confidence -= 0.05

    stop_loss = risk_config.get("stop_loss", 0.08)
    max_drawdown = risk_config.get("max_drawdown", 0.15)
    if stop_loss <= 0.05:
        base_confidence += 0.03
    if max_drawdown <= 0.1:
        base_confidence += 0.03

    if market_cycle in ["expansion", "recovery"]:
        base_confidence += 0.02
    elif market_cycle in ["contraction", "peak"]:
        base_confidence -= 0.02

    result = {
        "backtest_available": True,
        "stress_test_available": False,
        "monte_carlo_available": False,
        "confidence": round(base_confidence, 2),
        "reliability_level": _get_reliability_level(base_confidence),
    }

    if benchmark_comparison is not None:
        result["benchmark_comparison"] = benchmark_comparison

    # ── 买入持有基准校验（保留作为明细参考） ──
    benchmark_validation = None
    if backtest_results and saa_weights:
        try:
            benchmark_validation = validate_portfolio_against_benchmark(
                portfolio_bindings=bindings,
                saa_weights=saa_weights,
                backtest_results=backtest_results,
            )
            result["benchmark_validation"] = benchmark_validation
            result["passed_benchmark"] = benchmark_validation.get("passed", True)
        except Exception as e:
            logger.warning(f"[Reliability] 基准校验失败: {e}")

    # ── 压力测试 ──
    stress_test_result = None
    if historical_returns is not None and not historical_returns.empty:
        try:
            # 计算组合历史收益率
            weights = {}
            for b in bindings:
                sym = b.get("symbol", "")
                if sym:
                    weights[sym] = b.get("weight", 0)

            # 对齐并计算组合收益
            available_cols = [c for c in weights if c in historical_returns.columns]
            if available_cols:
                aligned = historical_returns[available_cols].dropna()
                w = np.array([weights[c] for c in available_cols])
                w = w / w.sum()
                portfolio_returns = aligned.dot(w)

                # 运行压力测试
                stress_test_result = run_all_stress_tests(portfolio_returns)
                result["stress_test"] = stress_test_result
                result["stress_test_available"] = True

                # 压力测试影响置信度
                if stress_test_result.get("success"):
                    survival_rate = stress_test_result.get("survival_rate", 0)
                    if survival_rate >= 0.75:
                        base_confidence += 0.05
                    elif survival_rate < 0.5:
                        base_confidence -= 0.1
        except Exception as e:
            logger.warning(f"[Reliability] 压力测试失败: {e}")

    # ── 蒙特卡洛模拟 ──
    monte_carlo_result = None
    if historical_returns is not None and not historical_returns.empty:
        try:
            available_cols = [c for c in weights if c in historical_returns.columns]
            if available_cols:
                aligned = historical_returns[available_cols].dropna()
                w = np.array([weights[c] for c in available_cols])
                w = w / w.sum()
                portfolio_returns = aligned.dot(w)

                # 运行蒙特卡洛
                monte_carlo_result = monte_carlo_simulation(
                    returns=portfolio_returns,
                    n_simulations=1000,
                    n_days=252,
                    initial_value=100000,
                    confidence=0.95,
                )
                result["monte_carlo"] = monte_carlo_result
                result["monte_carlo_available"] = True

                # 蒙特卡洛影响置信度
                if monte_carlo_result.get("success"):
                    prob_profit = monte_carlo_result.get("return_distribution", {}).get("prob_profit", 0)
                    var_95 = monte_carlo_result.get("risk_metrics", {}).get("VaR_95", -1)
                    if prob_profit >= 0.7 and var_95 >= -0.15:
                        base_confidence += 0.05
                    elif prob_profit < 0.5:
                        base_confidence -= 0.1
        except Exception as e:
            logger.warning(f"[Reliability] 蒙特卡洛失败: {e}")

    confidence = max(0.05, min(0.95, base_confidence))
    confidence = round(confidence, 4)
    result["confidence"] = confidence
    result["reliability_level"] = _get_reliability_level(confidence)

    # ── 采纳状态 ──
    adopted = confidence >= ADOPTION_CONFIDENCE_THRESHOLD
    if adopted:
        reason = f"置信度 {confidence:.1%} 达到采纳阈值 {ADOPTION_CONFIDENCE_THRESHOLD:.1%}，建议采纳"
    else:
        reason = f"置信度 {confidence:.1%} 未达到采纳阈值 {ADOPTION_CONFIDENCE_THRESHOLD:.1%}，建议调整后再评估"

    result["adoption_status"] = {
        "adopted": bool(adopted),
        "threshold": ADOPTION_CONFIDENCE_THRESHOLD,
        "confidence": confidence,
        "reason": reason,
    }

    return result


def _get_reliability_level(confidence: float) -> str:
    """获取可靠性等级."""
    if confidence >= 0.8:
        return "高"
    elif confidence >= 0.6:
        return "中"
    else:
        return "低"


# ═══════════════════════════════════════════════════════════════
# 5. 便捷函数
# ═══════════════════════════════════════════════════════════════

def get_stress_scenario_summary() -> list[dict[str, Any]]:
    """获取所有压力测试场景摘要."""
    return [
        {
            "id": s.id,
            "name": s.name,
            "period": f"{s.start_date}~{s.end_date}",
            "market_regime": s.market_regime,
            "benchmark_return": f"{s.benchmark_return:+.1%}",
            "key_events": s.key_events,
        }
        for s in STRESS_SCENARIOS.values()
    ]


def format_mc_summary(mc_result: dict[str, Any]) -> str:
    """格式化蒙特卡洛结果摘要."""
    if not mc_result.get("success"):
        return f"蒙特卡洛模拟失败: {mc_result.get('error', '未知错误')}"

    params = mc_result.get("parameters", {})
    ret_dist = mc_result.get("return_distribution", {})
    risk = mc_result.get("risk_metrics", {})
    val_dist = mc_result.get("final_value_distribution", {})

    lines = [
        "═" * 60,
        f"蒙特卡洛模拟结果 ({params.get('n_simulations', 1000)}次模拟, {params.get('n_days', 252)}天)",
        "═" * 60,
        f"  初始资金: ¥{params.get('initial_value', 100000):,.0f}",
        "",
        "  收益分布:",
        f"    均值: {ret_dist.get('mean', 0):+.2%}",
        f"    中位数: {ret_dist.get('median', 0):+.2%}",
        f"    5%分位: {ret_dist.get('q5', 0):+.2%}",
        f"    95%分位: {ret_dist.get('q95', 0):+.2%}",
        f"    正收益概率: {ret_dist.get('prob_profit', 0):.1%}",
        "",
        "  风险指标:",
        f"    VaR(95%): {risk.get('VaR_95', 0):+.2%}",
        f"    CVaR(95%): {risk.get('CVaR_95', 0):+.2%}",
        f"    最大回撤中位数: {risk.get('max_drawdown_median', 0):.2%}",
        f"    最大回撤(95%): {risk.get('max_drawdown_95', 0):.2%}",
        "",
        "  最终价值分布:",
        f"    均值: ¥{val_dist.get('mean', 0):,.0f}",
        f"    中位数: ¥{val_dist.get('median', 0):,.0f}",
        f"    5%分位: ¥{val_dist.get('q5', 0):,.0f}",
        f"    95%分位: ¥{val_dist.get('q95', 0):,.0f}",
        "═" * 60,
    ]
    return "\n".join(lines)
