"""QuantEvo 端到端全流程测试 - 真实LLM同步版本.

使用真实 Qwen3-14B-MLX-4bit 模型，同步调用避免asyncio问题.
"""

import os
import sys
import time
import json
import asyncio
from pathlib import Path
from datetime import datetime

# 加载 .env
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.profile_service import compute_profile_vector, derive_labels
from app.services.saa_engine import calculate_saa, get_risk_level_from_profile
from app.services.taa_engine import calculate_taa
from app.services.hybrid_portfolio_designer_v2 import (
    _generate_risk_config, _evaluate_reliability, _summarize_backtests,
    _calculate_portfolio_lifespan, _calculate_portfolio_health,
    _calculate_loop_stats, DEFAULT_STRATEGY_TEMPLATES
)
from app.services.rag.portfolio_quality_gate import PortfolioQualityGate, ReviewStep
from app.services.rag.adjustment_engine import apply_adjustments


def generate_market_signal(scenario: str):
    signals = {
        "bull": {"macro_score": 0.75, "industry_score": 0.70, "sentiment_score": 0.80, "geo_risk": 0.30,
                 "vix": 15, "equity_bond_spread": 4.5,
                 "industry_scores": {"technology": 0.85, "healthcare": 0.70, "finance": 0.65, "energy": 0.55, "consumer": 0.75},
                 "social_trends": ["AI投资热潮", "新能源转型"], "cycle_phase": "expansion"},
        "bear": {"macro_score": 0.25, "industry_score": 0.30, "sentiment_score": 0.20, "geo_risk": 0.75,
                 "vix": 35, "equity_bond_spread": 1.5,
                 "industry_scores": {"technology": 0.35, "healthcare": 0.45, "finance": 0.30, "energy": 0.40, "consumer": 0.35},
                 "social_trends": ["经济衰退担忧", "地缘政治紧张"], "cycle_phase": "contraction"},
        "recovery": {"macro_score": 0.55, "industry_score": 0.60, "sentiment_score": 0.55, "geo_risk": 0.40,
                     "vix": 22, "equity_bond_spread": 3.0,
                     "industry_scores": {"technology": 0.75, "healthcare": 0.65, "finance": 0.55, "energy": 0.50, "consumer": 0.60},
                     "social_trends": ["AI投资热潮"], "cycle_phase": "recovery"},
    }
    base = signals.get(scenario, signals["recovery"])
    return {
        **base,
        "macro": {"cycle_phase": base["cycle_phase"], "score": int(base["macro_score"] * 100)},
        "geopolitical": {"overall_risk": int(base["geo_risk"] * 100)},
        "market_internal": {"vix": base["vix"], "equity_bond_spread": base["equity_bond_spread"]},
    }


async def run_async():
    """异步运行完整测试."""
    print("=" * 80)
    print("QuantEvo 端到端全流程测试 - 真实LLM版本")
    print(f"LLM_BACKEND: {os.getenv('LLM_BACKEND', 'mock')}")
    print("=" * 80)

    # 场景: 稳健型投资者 + 复苏期 (复现之前的测试)
    scenario_name = "稳健型投资者_复苏期"
    answers = {
        "q1_capital": "20万-100万", "q2_age": "36-45岁",
        "q3_experience": ["银行理财/余额宝", "基金"], "q4_income_stability": "较稳定，偶有奖金",
        "q5_debt_pressure": "10%-30%", "q6_diversification": "4-5种（股票+债券+基金+黄金等）",
        "q7_risk_tolerance": "10%-20%", "q8_stop_loss": "偶尔执行",
        "q9_loss_scenario": "减仓一半", "q10_anchoring": "看趋势决定，不纠结成本",
        "q11_time_horizon": "1年", "q12_security_need": "要卖一部分投资",
        "q13_herding": "先研究一下再决定", "q14_overconfidence": "市场好，运气好",
        "q15_info_processing": "结合多个来源交叉验证", "q16_delayed_gratification": "卖出一半，留一半",
        "q17_social_pressure": "不受影响，按自己节奏", "q18_emotional_stability": "暂停交易，冷静分析原因",
    }
    market_scenario = "recovery"

    print(f"\n【场景】{scenario_name}")
    print("-" * 80)

    pipeline_start = time.time()
    adjustments_log = []

    # Step 1: 问卷 → 画像
    print("\n📋 Step 1: 问卷 → 画像向量")
    profile_vector = compute_profile_vector(answers)
    labels = derive_labels(profile_vector)
    print(f"  风险承受: {profile_vector['risk_tolerance']:.1f}/10 ({labels['risk_label']})")
    print(f"  损失厌恶: {profile_vector['loss_aversion']:.1f}/10")

    # Step 2: 市场信号
    print("\n📊 Step 2: 市场信号")
    market_signal = generate_market_signal(market_scenario)
    print(f"  周期: {market_signal['cycle_phase']} | 宏观: {market_signal['macro_score']:.0%}")

    # Step 3: SAA
    print("\n🎯 Step 3: Hybrid组合设计")
    risk_level = get_risk_level_from_profile(profile_vector)
    saa_result = calculate_saa(
        risk_tolerance=risk_level,
        market_cycle=market_signal["cycle_phase"],
        macro_score=market_signal["macro_score"],
        geo_risk=market_signal["geo_risk"],
    )
    print(f"\n  [SAA初始] 股票={saa_result['weights']['stock']:.1%}, 债券={saa_result['weights']['bond']:.1%}")

    # 初始化RAG质检
    print("\n  初始化RAG质检服务...")
    gate = PortfolioQualityGate()

    # SAA循环质检
    print("\n  [RAG] SAA审核开始 (真实LLM)...")
    max_retries = PortfolioQualityGate.MAX_RETRIES[ReviewStep.SAA]
    for retry in range(max_retries + 1):
        review_start = time.time()
        review = await gate.review_saa(saa_result, profile_vector, market_signal)
        review_time = time.time() - review_start

        print(f"\n    尝试 {retry}: {'✅通过' if review.passed else '❌不通过'}")
        print(f"    LLM耗时: {review_time:.1f}s")
        print(f"    分数: {review.score:.2f}")
        print(f"    PromptTokens: ~{len(gate._build_saa_review_query(saa_result, profile_vector, market_signal))}")

        if review.issues:
            print(f"    问题: {review.issues}")
        if review.adjustments:
            print(f"    调节: {review.adjustments}")
        if review.theory_cited:
            print(f"    引用理论: {review.theory_cited}")

        if review.passed:
            adjustments_log.append({
                "step": "saa", "passed": True, "score": review.score,
                "retry": retry, "llm_time_s": review_time,
            })
            break

        # 应用调节
        saa_result, _ = apply_adjustments("saa", saa_result, review.adjustments)
        adjustments_log.append({
            "step": "saa", "passed": False, "score": review.score,
            "retry": retry, "llm_time_s": review_time,
            "issues": review.issues, "adjustments": review.adjustments,
            "theory_cited": review.theory_cited,
        })
        print(f"    [调节后] 股票={saa_result['weights']['stock']:.1%}, 债券={saa_result['weights']['bond']:.1%}")
    else:
        print(f"    ⚠️ 超过最大重试次数({max_retries})")

    print(f"\n  [SAA最终] 股票={saa_result['weights']['stock']:.1%}, 债券={saa_result['weights']['bond']:.1%}")

    # TAA
    print("\n  [TAA] 计算战术配置...")
    taa_result = calculate_taa(
        saa_weights=saa_result["weights"],
        market_cycle=market_signal["cycle_phase"],
        industry_scores=market_signal["industry_scores"],
        social_trends=market_signal["social_trends"],
        market_signal=market_signal,
    )

    # 风控
    print("\n  [风控] 生成配置...")
    risk_config = _generate_risk_config(profile_vector, saa_result)
    print(f"  [风控初始] 止损={risk_config['stop_loss']:.1%}, 最大回撤={risk_config['max_drawdown']:.1%}")

    # 风控循环质检
    print("\n  [RAG] 风控审核开始 (真实LLM)...")
    max_risk_retries = PortfolioQualityGate.MAX_RETRIES[ReviewStep.RISK_CONFIG]
    for retry in range(max_risk_retries + 1):
        review_start = time.time()
        review = await gate.review_risk_config(risk_config, profile_vector)
        review_time = time.time() - review_start

        print(f"\n    尝试 {retry}: {'✅通过' if review.passed else '❌不通过'}")
        print(f"    LLM耗时: {review_time:.1f}s")

        if review.issues:
            print(f"    问题: {review.issues}")
        if review.adjustments:
            print(f"    调节: {review.adjustments}")

        if review.passed:
            adjustments_log.append({
                "step": "risk", "passed": True, "score": review.score,
                "retry": retry, "llm_time_s": review_time,
            })
            break

        risk_config, _ = apply_adjustments("risk_config", risk_config, review.adjustments)
        adjustments_log.append({
            "step": "risk", "passed": False, "score": review.score,
            "retry": retry, "llm_time_s": review_time,
            "issues": review.issues, "adjustments": review.adjustments,
        })
        print(f"    [调节后] 止损={risk_config['stop_loss']:.1%}, 最大回撤={risk_config['max_drawdown']:.1%}")

    print(f"\n  [风控最终] 止损={risk_config['stop_loss']:.1%}, 最大回撤={risk_config['max_drawdown']:.1%}")

    # 组装组合
    portfolio = {
        "portfolio_id": f"pf_{hash(str(profile_vector)) % 10000:04d}",
        "saa": saa_result,
        "taa": taa_result,
        "risk_config": risk_config,
        "reliability": {"confidence": 0.65},
    }

    # 最终审核
    print("\n  [RAG] 最终审核 (真实LLM)...")
    review_start = time.time()
    final_review = await gate.final_review(portfolio, profile_vector, market_signal)
    review_time = time.time() - review_start

    print(f"\n    结果: {'✅通过' if final_review.passed else '❌不通过'}")
    print(f"    LLM耗时: {review_time:.1f}s")
    if final_review.issues:
        print(f"    问题: {final_review.issues}")

    adjustments_log.append({
        "step": "final", "passed": final_review.passed, "score": final_review.score,
        "retry": 0, "llm_time_s": review_time,
    })

    # 统计
    total_time = time.time() - pipeline_start
    total_llm_time = sum(a.get("llm_time_s", 0) for a in adjustments_log)
    total_llm_calls = len(adjustments_log)
    passed_calls = sum(1 for a in adjustments_log if a["passed"])

    print(f"\n{'='*80}")
    print("📊 测试报告")
    print(f"{'='*80}")
    print(f"总耗时: {total_time:.1f}s")
    print(f"LLM调用次数: {total_llm_calls}")
    print(f"LLM总耗时: {total_llm_time:.1f}s")
    print(f"平均LLM耗时: {total_llm_time/total_llm_calls:.1f}s")
    print(f"通过: {passed_calls} | 未通过: {total_llm_calls - passed_calls}")

    print(f"\n详细记录:")
    for i, log in enumerate(adjustments_log):
        status = "✅" if log["passed"] else "❌"
        print(f"  {i+1}. [{log['step']}] {status} 重试{log['retry']} 耗时{log['llm_time_s']:.1f}s")
        if "issues" in log and log["issues"]:
            print(f"      问题: {log['issues']}")
        if "adjustments" in log and log["adjustments"]:
            print(f"      调节: {log['adjustments']}")

    # 保存报告
    report = {
        "scenario": scenario_name,
        "timestamp": datetime.now().isoformat(),
        "total_time_s": total_time,
        "llm_stats": {
            "total_calls": total_llm_calls,
            "total_time_s": total_llm_time,
            "avg_time_s": total_llm_time / total_llm_calls,
            "passed": passed_calls,
            "failed": total_llm_calls - passed_calls,
        },
        "profile": {
            "risk_tolerance": profile_vector['risk_tolerance'],
            "loss_aversion": profile_vector['loss_aversion'],
            "risk_label": labels['risk_label'],
        },
        "portfolio": {
            "saa": saa_result,
            "risk_config": risk_config,
        },
        "logs": adjustments_log,
    }

    output_dir = "./test_reports"
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{output_dir}/real_llm_sync_{scenario_name}_{datetime.now().strftime('%H%M%S')}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n💾 报告已保存: {filename}")


if __name__ == "__main__":
    asyncio.run(run_async())
