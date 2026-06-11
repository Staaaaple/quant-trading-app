"""QuantEvo 端到端全流程测试 - 真实LLM版本.

使用真实 Qwen3-14B-MLX-4bit 模型运行 Hybrid 组合设计的 RAG 循环质检.
记录每次LLM调用的真实耗时、返回结果、修改策略.

注意: 此测试运行时间较长 (每个场景预计 5-15 分钟).
"""

import os
import sys
import time
import json
import asyncio
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any
from datetime import datetime

# 加载 .env 文件
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.profile_service import compute_profile_vector, derive_labels
from app.services.hybrid_portfolio_designer_v2 import design_portfolio_v2


@dataclass
class PipelineReport:
    """完整流水线报告."""
    scenario_name: str
    scenario_description: str
    total_duration_ms: float = 0.0
    profile_vector: dict = field(default_factory=dict)
    labels: dict = field(default_factory=dict)
    market_scenario: str = ""
    final_portfolio: dict = field(default_factory=dict)
    rag_reviews: list = field(default_factory=list)
    rag_loop_stats: dict = field(default_factory=dict)
    overall_passed: bool = False
    timestamp: str = ""
    error: str = ""


# 测试场景
SCENARIOS = [
    {
        "name": "保守型小白_熊市",
        "description": "25岁保守型投资新手，无经验，高损失厌恶，熊市环境",
        "answers": {
            "q1_capital": "小于5万", "q2_age": "18-25岁",
            "q3_experience": ["银行理财/余额宝"], "q4_income_stability": "自由职业/不稳定",
            "q5_debt_pressure": "无负债", "q6_diversification": "只买一种（如只存银行或只买股票）",
            "q7_risk_tolerance": "不能亏，保本第一", "q8_stop_loss": "从不设止损",
            "q9_loss_scenario": "立刻全部清仓", "q10_anchoring": "解套就卖，再也不碰",
            "q11_time_horizon": "1个月", "q12_security_need": "完全没问题，随时可取",
            "q13_herding": "马上跟买，怕错过", "q14_overconfidence": "我眼光好，有天赋",
            "q15_info_processing": "立刻据此操作", "q16_delayed_gratification": "立刻卖出落袋为安",
            "q17_social_pressure": "立刻停止，听他们的", "q18_emotional_stability": "恐慌清仓，再也不投",
        },
        "market_scenario": "bear",
    },
    {
        "name": "稳健型投资者_复苏期",
        "description": "35岁稳健型投资者，有一定经验，中等风险承受，复苏期 (复现之前测试报告场景)",
        "answers": {
            "q1_capital": "20万-100万", "q2_age": "36-45岁",
            "q3_experience": ["银行理财/余额宝", "基金"], "q4_income_stability": "较稳定，偶有奖金",
            "q5_debt_pressure": "10%-30%", "q6_diversification": "4-5种（股票+债券+基金+黄金等）",
            "q7_risk_tolerance": "10%-20%", "q8_stop_loss": "偶尔执行",
            "q9_loss_scenario": "减仓一半", "q10_anchoring": "看趋势决定，不纠结成本",
            "q11_time_horizon": "1年", "q12_security_need": "要卖一部分投资",
            "q13_herding": "先研究一下再决定", "q14_overconfidence": "市场好，运气好",
            "q15_info_processing": "结合多个来源交叉验证", "q16_delayed_gratification": "卖出一半，留一半",
            "q17_social_pressure": "不受影响，按自己节奏", "q18_emotional_stability": "暂停交易，冷静分析原因",
        },
        "market_scenario": "recovery",
    },
]


def generate_market_signal(scenario: str) -> dict[str, Any]:
    """根据场景生成市场信号."""
    signals = {
        "bull": {
            "macro_score": 0.75, "industry_score": 0.70, "sentiment_score": 0.80, "geo_risk": 0.30,
            "vix": 15, "equity_bond_spread": 4.5,
            "industry_scores": {"technology": 0.85, "healthcare": 0.70, "finance": 0.65, "energy": 0.55, "consumer": 0.75},
            "social_trends": ["AI投资热潮", "新能源转型"], "cycle_phase": "expansion",
        },
        "bear": {
            "macro_score": 0.25, "industry_score": 0.30, "sentiment_score": 0.20, "geo_risk": 0.75,
            "vix": 35, "equity_bond_spread": 1.5,
            "industry_scores": {"technology": 0.35, "healthcare": 0.45, "finance": 0.30, "energy": 0.40, "consumer": 0.35},
            "social_trends": ["经济衰退担忧", "地缘政治紧张"], "cycle_phase": "contraction",
        },
        "recovery": {
            "macro_score": 0.55, "industry_score": 0.60, "sentiment_score": 0.55, "geo_risk": 0.40,
            "vix": 22, "equity_bond_spread": 3.0,
            "industry_scores": {"technology": 0.75, "healthcare": 0.65, "finance": 0.55, "energy": 0.50, "consumer": 0.60},
            "social_trends": ["AI投资热潮"], "cycle_phase": "recovery",
        },
        "volatile": {
            "macro_score": 0.50, "industry_score": 0.50, "sentiment_score": 0.45, "geo_risk": 0.60,
            "vix": 28, "equity_bond_spread": 2.5,
            "industry_scores": {"technology": 0.60, "healthcare": 0.55, "finance": 0.50, "energy": 0.65, "consumer": 0.50},
            "social_trends": ["地缘冲突", "通胀担忧"], "cycle_phase": "peak",
        },
    }
    base = signals.get(scenario, signals["recovery"])
    return {
        **base,
        "macro": {"cycle_phase": base["cycle_phase"], "score": int(base["macro_score"] * 100)},
        "geopolitical": {"overall_risk": int(base["geo_risk"] * 100)},
        "market_internal": {"vix": base["vix"], "equity_bond_spread": base["equity_bond_spread"]},
    }


async def run_scenario(scenario: dict) -> PipelineReport:
    """运行单个测试场景."""
    print(f"\n{'='*80}")
    print(f"【场景】{scenario['name']}")
    print(f"描述: {scenario['description']}")
    print(f"{'='*80}")

    report = PipelineReport(
        scenario_name=scenario['name'],
        scenario_description=scenario['description'],
        market_scenario=scenario['market_scenario'],
        timestamp=datetime.now().isoformat(),
    )
    pipeline_start = time.time()

    try:
        # Step 1: 问卷 → 画像向量
        print("\n📋 Step 1: 问卷 → 画像向量")
        profile_vector = compute_profile_vector(scenario['answers'])
        labels = derive_labels(profile_vector)
        report.profile_vector = profile_vector
        report.labels = labels

        print(f"  风险承受: {profile_vector['risk_tolerance']:.1f}/10 ({labels['risk_label']})")
        print(f"  损失厌恶: {profile_vector['loss_aversion']:.1f}/10")
        print(f"  投资期限: {profile_vector['time_horizon_score']:.1f}/10 ({labels['time_horizon_label']})")
        print(f"  经验水平: {profile_vector['experience_level']:.1f}/10 ({labels['experience_label']})")

        # Step 2: 市场信号
        print("\n📊 Step 2: 市场信号")
        market_signal = generate_market_signal(scenario['market_scenario'])
        print(f"  场景: {scenario['market_scenario']} | 周期: {market_signal['cycle_phase']}")
        print(f"  宏观评分: {market_signal['macro_score']:.0%} | VIX: {market_signal['vix']}")

        # Step 3: Hybrid组合设计 (真实RAG)
        print("\n🎯 Step 3: Hybrid组合设计 (真实RAG循环质检)")
        print(f"  LLM_BACKEND: {os.getenv('LLM_BACKEND', 'mock')}")
        print(f"  QWEN_MLX_MODEL_PATH: {os.getenv('QWEN_MLX_MODEL_PATH', 'N/A')}")
        print("  开始调用 design_portfolio_v2，请耐心等待...")

        portfolio = await design_portfolio_v2(
            profile_vector=profile_vector,
            market_signal=market_signal,
            use_rag_gate=True,
        )

        report.final_portfolio = portfolio
        report.rag_reviews = portfolio.get("rag_reviews", [])
        report.rag_loop_stats = portfolio.get("rag_loop_stats", {})
        report.total_duration_ms = (time.time() - pipeline_start) * 1000

        # 判断整体是否通过
        rag_stats = portfolio.get("rag_loop_stats", {})
        report.overall_passed = rag_stats.get("failed_steps", 0) == 0

        print(f"\n  ✅ 组合生成成功")
        print(f"  组合ID: {portfolio.get('portfolio_id', 'N/A')}")
        print(f"  SAA: 股票={portfolio['saa']['weights']['stock']:.1%}, "
              f"债券={portfolio['saa']['weights']['bond']:.1%}")
        print(f"  风控: 止损={portfolio['risk_config']['stop_loss']:.1%}, "
              f"最大回撤={portfolio['risk_config']['max_drawdown']:.1%}")

    except Exception as e:
        report.error = str(e)
        report.total_duration_ms = (time.time() - pipeline_start) * 1000
        print(f"\n  ❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

    return report


def print_report(report: PipelineReport):
    """打印详细报告."""
    print(f"\n{'='*80}")
    print(f"📊 测试报告: {report.scenario_name}")
    print(f"{'='*80}")
    print(f"总耗时: {report.total_duration_ms / 1000:.1f}s")

    if report.error:
        print(f"\n❌ 错误: {report.error}")
        return

    print(f"\n画像标签:")
    print(f"  风险等级: {report.labels.get('risk_label', '未知')}")
    print(f"  投资期限: {report.labels.get('time_horizon_label', '未知')}")
    print(f"  经验水平: {report.labels.get('experience_label', '未知')}")

    stats = report.rag_loop_stats
    print(f"\nRAG循环质检统计:")
    print(f"  总审核次数: {stats.get('total_reviews', 0)}")
    print(f"  审核步骤数: {stats.get('total_steps', 0)}")
    print(f"  通过步骤: {stats.get('passed_steps', 0)}")
    print(f"  未通过步骤: {stats.get('failed_steps', 0)}")
    print(f"  通过率: {stats.get('pass_rate', 0):.0%}")
    print(f"  总重试次数: {stats.get('total_retries', 0)}")
    print(f"  平均每步重试: {stats.get('avg_retries_per_step', 0):.1f}")

    print(f"\n详细RAG质检记录:")
    for i, review in enumerate(report.rag_reviews):
        step = review.get("step", "unknown")
        passed = "✅通过" if review.get("passed") else "❌不通过"
        retry = review.get("retry", 0)
        score = review.get("score", 0)
        print(f"\n  {i+1}. [{step}] {passed} (重试{retry}, 分数{score:.2f})")

        if review.get("issues"):
            print(f"     问题:")
            for issue in review["issues"]:
                print(f"       - {issue}")

        if review.get("adjustments"):
            print(f"     调节:")
            for adj in review["adjustments"]:
                print(f"       - {adj}")

        if review.get("passed_after_retry"):
            print(f"     🔄 重试后通过")

        if review.get("warning"):
            print(f"     ⚠️ 警告: {review['warning']}")

    # 需要关注的步骤
    steps_attention = stats.get("steps_needing_attention", [])
    if steps_attention:
        print(f"\n⚠️ 需要关注的步骤: {', '.join(steps_attention)}")

    print(f"\n最终组合:")
    saa = report.final_portfolio.get("saa", {})
    risk = report.final_portfolio.get("risk_config", {})
    print(f"  SAA: 股票={saa.get('weights', {}).get('stock', 0):.1%}, "
          f"债券={saa.get('weights', {}).get('bond', 0):.1%}")
    print(f"  风控: 止损={risk.get('stop_loss', 0):.1%}, "
          f"最大回撤={risk.get('max_drawdown', 0):.1%}")
    print(f"\n整体结果: {'✅通过' if report.overall_passed else '⚠️有未通过项'}")


def save_report(report: PipelineReport, output_dir: str = "./test_reports"):
    """保存报告到JSON文件."""
    import os
    os.makedirs(output_dir, exist_ok=True)

    data = {
        "scenario_name": report.scenario_name,
        "scenario_description": report.scenario_description,
        "market_scenario": report.market_scenario,
        "timestamp": report.timestamp,
        "total_duration_ms": report.total_duration_ms,
        "total_duration_seconds": round(report.total_duration_ms / 1000, 1),
        "profile_vector": report.profile_vector,
        "labels": report.labels,
        "final_portfolio": {
            "portfolio_id": report.final_portfolio.get("portfolio_id", ""),
            "saa": report.final_portfolio.get("saa", {}),
            "risk_config": report.final_portfolio.get("risk_config", {}),
            "reliability": report.final_portfolio.get("reliability", {}),
        },
        "rag_reviews": report.rag_reviews,
        "rag_loop_stats": report.rag_loop_stats,
        "overall_passed": report.overall_passed,
        "error": report.error,
    }

    filename = f"{output_dir}/real_llm_report_{report.scenario_name}_{datetime.now().strftime('%H%M%S')}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n💾 报告已保存: {filename}")


async def main():
    """运行所有测试场景."""
    print("=" * 80)
    print("QuantEvo 端到端全流程测试 - 真实LLM版本")
    print(f"LLM_BACKEND: {os.getenv('LLM_BACKEND', 'mock')}")
    print(f"模型路径: {os.getenv('QWEN_MLX_MODEL_PATH', 'N/A')}")
    print("=" * 80)

    all_reports = []
    summary = []

    for scenario in SCENARIOS:
        report = await run_scenario(scenario)
        print_report(report)
        save_report(report)
        all_reports.append(report)

        summary.append({
            "场景": scenario["name"],
            "风险等级": report.labels.get("risk_label", "未知"),
            "市场": scenario["market_scenario"],
            "LLM调用": report.rag_loop_stats.get("total_reviews", 0),
            "总重试": report.rag_loop_stats.get("total_retries", 0),
            "通过": report.rag_loop_stats.get("passed_steps", 0),
            "未通过": report.rag_loop_stats.get("failed_steps", 0),
            "总耗时(s)": round(report.total_duration_ms / 1000, 1),
            "结果": "✅通过" if report.overall_passed else "⚠️有警告" if not report.error else "❌失败",
        })

    # 汇总表
    print(f"\n{'='*80}")
    print("📋 测试汇总")
    print(f"{'='*80}")
    print(f"{'场景':<20} {'风险等级':<8} {'市场':<10} {'LLM调用':<8} {'重试':<6} {'通过':<6} {'未通过':<8} {'耗时(s)':<10} {'结果'}")
    print("-" * 80)
    for s in summary:
        print(f"{s['场景']:<20} {s['风险等级']:<8} {s['市场']:<10} "
              f"{s['LLM调用']:<8} {s['总重试']:<6} {s['通过']:<6} "
              f"{s['未通过']:<8} {s['总耗时(s)']:<10} {s['结果']}")

    print(f"\n{'='*80}")
    print("✅ 所有场景测试完成!")
    print(f"{'='*80}")


if __name__ == "__main__":
    asyncio.run(main())
