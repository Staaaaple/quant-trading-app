"""Hybrid全链路真实LLM测试 — 使用Qwen3-14B-MLX-4bit.

测试内容:
1. 使用真实问卷数据生成画像
2. 使用市场仪表盘数据
3. 串行RAG质检 vs 并行RAG质检
4. 记录真实LLM的准确率、耗时、调用次数
"""

import pytest
import asyncio
import time
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.hybrid_portfolio_designer_v2 import design_portfolio_v2
from app.services.rag.portfolio_quality_gate import PortfolioQualityGate, ReviewStep
from app.services.rag.rag_call_logger import get_rag_logger


# 真实问卷数据（15题）
REAL_QUESTIONNAIRE = {
    # 基本信息5题
    "capital": "20-100万",
    "age": "36-45",
    "experience": ["股票", "基金"],
    "income_ratio": "10-30%",
    "debt": "有能承受",
    # 情景心理10题
    "loss_aversion_q": "B",  # 卖一半
    "herding_q": "B",  # 研究后决定
    "overconfidence_q": "C",  # 市场好
    "delayed_gratification_q": "B",  # 大部分存
    "anchoring_q": "C",  # 看趋势
    "security_q": "A",  # 完全没问题
    "time_perception_q": "C",  # 1年
    "info_processing_q": "B",  # 研究后决定
    "social_pressure_q": "B",  # 沟通解释
    "sudden_loss_q": "B",  # 减仓
}

# 真实市场仪表盘数据（2024年6月）
REAL_MARKET_SIGNAL = {
    "macro": {
        "cycle_phase": "recovery",
        "gdp_trend": "企稳",
        "gdp_yoy": 4.5,
        "inflation_level": "温和",
        "cpi_yoy": 1.8,
        "liquidity_tightness": "中性",
        "interest_rate_trend": "持平",
        "pmi": 50.5,
        "score": 55,
    },
    "geopolitical": {
        "overall_risk": 50,
        "risk_level": "medium",
        "affected_sectors": ["科技"],
        "safe_haven_demand": "中",
    },
    "industry": {
        "sector_heatmap": {"科技": 65, "消费": 55, "医药": 60, "新能源": 70, "金融": 50},
        "recommended_sectors": ["新能源", "科技", "医药"],
        "avoid_sectors": ["房地产"],
        "policy_tailwind": ["半导体", "新能源"],
        "policy_headwind": ["房地产"],
    },
    "social": {
        "major_themes": ["AI应用", "消费复苏", "新能源"],
        "theme_strength": {"AI应用": 75, "消费复苏": 60, "新能源": 70},
        "consumer_confidence": "中性",
        "employment_outlook": "持平",
    },
    "market_internal": {
        "equity_bond_spread": 3.2,
        "market_sentiment": "中性",
        "style_rotation": "均衡",
        "volatility_regime": "正常",
        "volume_trend": "平稳",
        "northbound_flow": "平稳",
        "margin_balance_trend": "持平",
        "vix": 22,
    },
    "macro_score": 0.55,
    "geo_risk": 0.5,
    "industry_scores": {"科技": 65, "消费": 55, "医药": 60, "新能源": 70, "金融": 50},
    "social_trends": ["AI应用", "消费复苏"],
}


def generate_profile_from_questionnaire(answers: dict) -> dict:
    """将15题问卷答案转换为profile_vector."""
    # 损失厌恶
    loss_aversion_map = {"A": 0.9, "B": 0.6, "C": 0.3, "D": 0.1}
    loss_aversion = loss_aversion_map.get(answers.get("loss_aversion_q", "B"), 0.5)

    # 从众倾向
    herding_map = {"A": 0.9, "B": 0.5, "C": 0.2, "D": 0.1}
    herding_tendency = herding_map.get(answers.get("herding_q", "B"), 0.5)

    # 过度自信
    overconfidence_map = {"A": 0.9, "B": 0.6, "C": 0.3, "D": 0.1}
    overconfidence = overconfidence_map.get(answers.get("overconfidence_q", "C"), 0.5)

    # 延迟满足
    delayed_map = {"A": 0.9, "B": 0.7, "C": 0.4, "D": 0.1}
    delayed_gratification = delayed_map.get(answers.get("delayed_gratification_q", "B"), 0.5)

    # 锚定效应
    anchoring_map = {"A": 0.8, "B": 0.6, "C": 0.3, "D": 0.1}
    anchoring_effect = anchoring_map.get(answers.get("anchoring_q", "C"), 0.5)

    # 资金安全感
    security_map = {"A": 0.9, "B": 0.5, "C": 0.2, "D": 0.4}
    security_need = security_map.get(answers.get("security_q", "A"), 0.5)

    # 时间感知
    time_map = {"A": 0.1, "B": 0.3, "C": 0.6, "D": 0.9}
    time_horizon_score = time_map.get(answers.get("time_perception_q", "C"), 0.5)

    # 综合风险承受
    risk_tolerance = (
        (1 - loss_aversion) * 0.25 +
        (1 - herding_tendency) * 0.15 +
        (1 - overconfidence) * 0.10 +
        delayed_gratification * 0.15 +
        (1 - anchoring_effect) * 0.10 +
        security_need * 0.10 +
        time_horizon_score * 0.15
    )

    return {
        "risk_tolerance": round(min(risk_tolerance, 1.0), 2),
        "loss_aversion": round(loss_aversion, 2),
        "herding_tendency": round(herding_tendency, 2),
        "overconfidence": round(overconfidence, 2),
        "delayed_gratification": round(delayed_gratification, 2),
        "security_need": round(security_need, 2),
        "time_horizon": "long" if time_horizon_score > 0.6 else "medium" if time_horizon_score > 0.3 else "short",
        "experience_level": "intermediate",
        "capital_tier": answers.get("capital", "20-100万"),
    }


@pytest.mark.asyncio
async def test_hybrid_with_real_llm():
    """使用真实LLM测试Hybrid全链路."""
    print("\n" + "="*80)
    print("Hybrid全链路真实LLM测试 — Qwen3-14B-MLX-4bit")
    print("="*80)

    # 1. 生成画像
    print("\n[1] 问卷→画像")
    profile = generate_profile_from_questionnaire(REAL_QUESTIONNAIRE)
    print(f"    风险承受: {profile['risk_tolerance']}")
    print(f"    损失厌恶: {profile['loss_aversion']}")
    print(f"    时间周期: {profile['time_horizon']}")

    # 2. 基础流程（不带RAG）
    print("\n[2] 基础流程（不带RAG）")
    start = time.time()
    portfolio = await design_portfolio_v2(
        profile_vector=profile,
        market_signal=REAL_MARKET_SIGNAL,
        use_rag_gate=False,
    )
    base_time = time.time() - start
    print(f"    耗时: {base_time*1000:.1f}ms")
    print(f"    SAA: {portfolio['saa']['weights']}")

    # 3. 串行RAG质检
    print("\n[3] 串行RAG质检（真实LLM）")
    print("    注意: 这可能需要几分钟...")

    from app.services.rag.llm_service import LLMService

    # 检查LLM可用性
    llm = LLMService()
    status = llm.get_status()
    print(f"    LLM状态: {status}")

    if not status["is_available"]:
        print("    ⚠️ LLM不可用，跳过真实LLM测试")
        pytest.skip("LLM不可用")

    # 创建带真实LLM的质检门控
    gate = PortfolioQualityGate(llm_service=llm)

    serial_results = {}
    serial_start = time.time()

    # SAA审核
    print("    [3.1] SAA审核...")
    t0 = time.time()
    serial_results["saa"] = await gate.review_saa(
        portfolio["saa"], profile, REAL_MARKET_SIGNAL
    )
    serial_results["saa"]._elapsed_ms = (time.time() - t0) * 1000
    print(f"          耗时: {serial_results['saa']._elapsed_ms:.1f}ms | 通过: {serial_results['saa'].passed}")

    # TAA审核
    print("    [3.2] TAA审核...")
    t0 = time.time()
    serial_results["taa"] = await gate.review_taa(
        portfolio["taa"], portfolio["saa"], REAL_MARKET_SIGNAL
    )
    serial_results["taa"]._elapsed_ms = (time.time() - t0) * 1000
    print(f"          耗时: {serial_results['taa']._elapsed_ms:.1f}ms | 通过: {serial_results['taa'].passed}")

    # 风控审核
    print("    [3.3] 风控审核...")
    t0 = time.time()
    serial_results["risk"] = await gate.review_risk_config(
        portfolio["risk_config"], profile
    )
    serial_results["risk"]._elapsed_ms = (time.time() - t0) * 1000
    print(f"          耗时: {serial_results['risk']._elapsed_ms:.1f}ms | 通过: {serial_results['risk'].passed}")

    # 可靠性审核
    print("    [3.4] 可靠性审核...")
    t0 = time.time()
    serial_results["reliability"] = await gate.review_reliability(
        portfolio["reliability"],
        portfolio.get("backtest_summary", {}),
        profile,
    )
    serial_results["reliability"]._elapsed_ms = (time.time() - t0) * 1000
    print(f"          耗时: {serial_results['reliability']._elapsed_ms:.1f}ms | 通过: {serial_results['reliability'].passed}")

    # 最终审核
    print("    [3.5] 最终审核...")
    t0 = time.time()
    serial_results["final"] = await gate.final_review(
        portfolio, profile, REAL_MARKET_SIGNAL
    )
    serial_results["final"]._elapsed_ms = (time.time() - t0) * 1000
    print(f"          耗时: {serial_results['final']._elapsed_ms:.1f}ms | 通过: {serial_results['final'].passed}")

    serial_total = time.time() - serial_start

    # 4. 并行RAG质检
    print("\n[4] 并行RAG质检（真实LLM）")
    parallel_start = time.time()

    # 构建组合用于并行审核
    portfolio_for_parallel = {
        "saa": portfolio["saa"],
        "taa": portfolio["taa"],
        "bindings": portfolio["bindings"],
        "risk_config": portfolio["risk_config"],
        "reliability": portfolio["reliability"],
        "backtest_summary": portfolio.get("backtest_summary", {}),
        "summary": portfolio.get("summary", {}),
    }

    # 模拟回测结果
    backtest_results = {}
    for b in portfolio["bindings"]:
        symbol = b.get("symbol", "")
        backtest_results[symbol] = {
            "return": 15.0,
            "buy_hold_return": 12.0,
            "sharpe": 0.8,
            "max_drawdown": 0.12,
            "win_rate": 0.55,
            "trade_count": 20,
        }

    parallel_results = await gate.review_all_parallel(
        portfolio=portfolio_for_parallel,
        profile_vector=profile,
        market_signal=REAL_MARKET_SIGNAL,
        backtest_results=backtest_results,
    )
    parallel_total = time.time() - parallel_start

    print(f"    并行总耗时: {parallel_total*1000:.1f}ms")
    for step, result in parallel_results.items():
        print(f"    {step}: 通过={result.passed} | 分数={result.score:.2f}")

    # 5. 获取日志统计
    print("\n[5] RAG调用统计")
    logger = get_rag_logger()
    stats = logger.get_stats()
    for k, v in stats.items():
        print(f"    {k}: {v}")

    # 6. 汇总报告
    print("\n" + "="*80)
    print("测试汇总报告")
    print("="*80)

    print(f"\n基础流程耗时: {base_time*1000:.1f}ms")
    print(f"串行RAG耗时: {serial_total*1000:.1f}ms")
    print(f"并行RAG耗时: {parallel_total*1000:.1f}ms")
    print(f"并行加速比: {serial_total/parallel_total:.2f}x")

    print(f"\n串行各步骤耗时:")
    for step, result in serial_results.items():
        elapsed = getattr(result, '_elapsed_ms', 0)
        print(f"  {step}: {elapsed:.1f}ms | 通过={result.passed} | 分数={result.score:.2f}")

    print(f"\n并行各步骤耗时:")
    # 从日志中获取并行各步骤耗时
    step_stats = logger.get_step_stats()
    for step, stat in step_stats.items():
        print(f"  {step}: 平均{stat.get('avg_time_ms', 0):.1f}ms | 调用{stat.get('count', 0)}次")

    # 保存详细报告
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "llm_backend": status["backend"],
        "llm_model_path": status["model_path"],
        "base_time_ms": base_time * 1000,
        "serial_time_ms": serial_total * 1000,
        "parallel_time_ms": parallel_total * 1000,
        "speedup": serial_total / parallel_total if parallel_total > 0 else 0,
        "serial_results": {
            step: {
                "passed": r.passed,
                "score": r.score,
                "issues": r.issues,
                "adjustments": r.adjustments,
                "elapsed_ms": getattr(r, '_elapsed_ms', 0),
            }
            for step, r in serial_results.items()
        },
        "parallel_results": {
            step: {
                "passed": r.passed,
                "score": r.score,
                "issues": r.issues,
                "adjustments": r.adjustments,
            }
            for step, r in parallel_results.items()
        },
        "rag_stats": stats,
    }

    report_path = "logs/rag_calls/real_llm_test_report.json"
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n详细报告已保存: {report_path}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
