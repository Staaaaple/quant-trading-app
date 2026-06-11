"""QuantEvo 端到端全流程测试 - 完整6步 + 真实LLM.

直接调用 design_portfolio_v2，走完整6步流程：
SAA → TAA → 绑定 → 风控 → 可靠性 → 最终审核
输出完整组合数据（资产配置/策略/标的/回测）
"""

import os
import sys
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
from app.services.hybrid_portfolio_designer_v2 import design_portfolio_v2


def generate_market_signal(scenario: str):
    signals = {
        "recovery": {
            "macro_score": 0.55, "industry_score": 0.60, "sentiment_score": 0.55, "geo_risk": 0.40,
            "vix": 22, "equity_bond_spread": 3.0,
            "industry_scores": {
                "technology": 0.75, "healthcare": 0.65, "finance": 0.55,
                "energy": 0.50, "consumer": 0.60, "industrial": 0.55,
            },
            "social_trends": ["AI投资热潮", "新能源转型"],
            "macro": {"cycle_phase": "recovery", "score": 55},
            "geopolitical": {"overall_risk": 40},
            "market_internal": {"vix": 22, "equity_bond_spread": 3.0},
        },
    }
    return signals.get(scenario, signals["recovery"])


async def run_full_test():
    print("=" * 80)
    print("QuantEvo 完整6步全流程测试 - 真实LLM")
    print(f"LLM_BACKEND: {os.getenv('LLM_BACKEND', 'mock')}")
    print(f"模型: Qwen3-14B-MLX-4bit")
    print("=" * 80)

    # 场景: 稳健型投资者 + 复苏期
    scenario_name = "稳健型投资者_复苏期"
    answers = {
        "q1_capital": "20万-100万", "q2_age": "36-45岁",
        "q3_experience": ["银行理财/余额宝", "基金"],
        "q4_income_stability": "较稳定，偶有奖金",
        "q5_debt_pressure": "10%-30%",
        "q6_diversification": "4-5种（股票+债券+基金+黄金等）",
        "q7_risk_tolerance": "10%-20%",
        "q8_stop_loss": "偶尔执行",
        "q9_loss_scenario": "减仓一半",
        "q10_anchoring": "看趋势决定，不纠结成本",
        "q11_time_horizon": "1年",
        "q12_security_need": "要卖一部分投资",
        "q13_herding": "先研究一下再决定",
        "q14_overconfidence": "市场好，运气好",
        "q15_info_processing": "结合多个来源交叉验证",
        "q16_delayed_gratification": "卖出一半，留一半",
        "q17_social_pressure": "不受影响，按自己节奏",
        "q18_emotional_stability": "暂停交易，冷静分析原因",
    }

    print(f"\n【场景】{scenario_name}")
    print("-" * 80)

    # Step 1: 问卷 → 画像
    print("\n📋 Step 1: 问卷 → 画像向量")
    profile_vector = compute_profile_vector(answers)
    labels = derive_labels(profile_vector)
    print(f"  风险承受: {profile_vector['risk_tolerance']:.1f}/10 ({labels['risk_label']})")
    print(f"  损失厌恶: {profile_vector['loss_aversion']:.1f}/10")
    print(f"  投资期限: {profile_vector['time_horizon_score']:.1f}/10 ({labels['time_horizon_label']})")
    print(f"  经验水平: {profile_vector['experience_level']:.1f}/10 ({labels['experience_label']})")

    # Step 2: 市场信号
    print("\n📊 Step 2: 市场信号")
    market_signal = generate_market_signal("recovery")
    print(f"  周期: {market_signal['macro']['cycle_phase']}")
    print(f"  宏观评分: {market_signal['macro_score']:.0%}")
    print(f"  VIX: {market_signal['vix']}")
    print(f"  地缘风险: {market_signal['geo_risk']:.0%}")

    # Step 3-8: 完整Hybrid组合设计（含6步RAG质检）
    print("\n🎯 Step 3-8: Hybrid组合设计（完整6步 + RAG循环质检）")
    print("  开始调用 design_portfolio_v2，请耐心等待...")
    print(f"  预计耗时: 5-15分钟（每步LLM约60-120秒）\n")

    start_time = datetime.now()
    try:
        portfolio = await design_portfolio_v2(
            profile_vector=profile_vector,
            market_signal=market_signal,
            use_rag_gate=True,
        )
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        print(f"\n{'='*80}")
        print("✅ 组合生成成功!")
        print(f"{'='*80}")
        print(f"总耗时: {duration:.1f}s")

        # ── RAG质检统计 ──
        rag_stats = portfolio.get("rag_loop_stats", {})
        rag_reviews = portfolio.get("rag_reviews", [])

        print(f"\n📊 RAG质检统计:")
        print(f"  总审核次数: {rag_stats.get('total_reviews', 0)}")
        print(f"  审核步骤数: {rag_stats.get('total_steps', 0)}")
        print(f"  通过步骤: {rag_stats.get('passed_steps', 0)}")
        print(f"  未通过步骤: {rag_stats.get('failed_steps', 0)}")
        print(f"  总重试次数: {rag_stats.get('total_retries', 0)}")

        print(f"\n📋 详细质检记录:")
        for i, review in enumerate(rag_reviews):
            step = review.get("step", "unknown")
            passed = "✅" if review.get("passed") else "❌"
            retry = review.get("retry", 0)
            score = review.get("score", 0)
            print(f"\n  {i+1}. [{step}] {passed} 重试{retry} 分数{score:.2f}")
            if review.get("issues"):
                for issue in review["issues"][:2]:
                    print(f"      问题: {issue}")
            if review.get("adjustments"):
                for adj in review["adjustments"][:2]:
                    print(f"      调节: {adj}")
            if review.get("theory_cited"):
                print(f"      理论: {review['theory_cited']}")

        # ── 最终组合详情 ──
        print(f"\n{'='*80}")
        print("📦 最终组合详情")
        print(f"{'='*80}")

        # SAA
        saa = portfolio.get("saa", {})
        weights = saa.get("weights", {})
        print(f"\n【战略资产配置 SAA】")
        print(f"  股票:  {weights.get('stock', 0):.1%}")
        print(f"  债券:  {weights.get('bond', 0):.1%}")
        print(f"  商品:  {weights.get('commodity', 0):.1%}")
        print(f"  现金:  {weights.get('cash', 0):.1%}")
        print(f"  配置理由: {saa.get('rationale', 'N/A')[:80]}...")

        # TAA
        taa = portfolio.get("taa", {})
        sector_weights = taa.get("sector_weights", {})
        print(f"\n【战术资产配置 TAA】")
        if sector_weights:
            for sector, weight in sorted(sector_weights.items(), key=lambda x: -x[1])[:5]:
                print(f"  {sector}: {weight:.1%}")
        else:
            print(f"  行业配置: {taa}")

        # 策略绑定
        bindings = portfolio.get("bindings", [])
        print(f"\n【策略-标的绑定】({len(bindings)}个)")
        for i, b in enumerate(bindings[:5]):
            print(f"\n  {i+1}. {b.get('symbol', 'N/A')} - {b.get('name', 'N/A')}")
            print(f"      策略: {b.get('strategy_name', 'N/A')} ({b.get('strategy_family', 'N/A')})")
            print(f"      权重: {b.get('weight', 0):.1%}")
            print(f"      行业: {b.get('sector_name', 'N/A')}")

        # 风控
        risk = portfolio.get("risk_config", {})
        print(f"\n【风控配置】")
        print(f"  止损线:        {risk.get('stop_loss', 0):.1%}")
        print(f"  单票仓位上限:  {risk.get('max_position', 0):.1%}")
        print(f"  最大回撤硬止损: {risk.get('max_drawdown', 0):.1%}")
        print(f"  再平衡阈值:    {risk.get('rebalance_threshold', 0):.1%}")

        # 可靠性
        reliability = portfolio.get("reliability", {})
        print(f"\n【可靠性评估】")
        print(f"  置信度: {reliability.get('confidence', 0):.2f}")
        print(f"  等级:   {reliability.get('reliability_level', 'N/A')}")

        # 回测摘要
        bt = portfolio.get("backtest_summary", {})
        print(f"\n【回测摘要】")
        print(f"  标的数量: {bt.get('n_assets', 0)}")
        print(f"  组合收益: {bt.get('portfolio_return', 0):.2f}%")
        print(f"  买入持有: {bt.get('buy_hold_return', 0):.2f}%")
        print(f"  夏普比率: {bt.get('sharpe', 0):.2f}")
        print(f"  最大回撤: {bt.get('max_drawdown', 0):.2f}%")
        print(f"  胜率:     {bt.get('win_rate', 0):.1%}")

        # 组合寿命
        print(f"\n【组合寿命】")
        print(f"  寿命:   {portfolio.get('portfolio_lifespan', 0)}个月")
        print(f"  健康度: {portfolio.get('portfolio_health', 0)}/100")

        # 保存完整报告
        output_dir = "./test_reports"
        os.makedirs(output_dir, exist_ok=True)
        filename = f"{output_dir}/full_6steps_{scenario_name}_{datetime.now().strftime('%H%M%S')}.json"

        # 清理后保存
        save_data = {
            "scenario": scenario_name,
            "timestamp": datetime.now().isoformat(),
            "total_duration_s": duration,
            "profile": {
                "vector": profile_vector,
                "labels": labels,
            },
            "portfolio": {
                "portfolio_id": portfolio.get("portfolio_id"),
                "saa": saa,
                "taa": taa,
                "bindings": bindings,
                "risk_config": risk,
                "reliability": reliability,
                "backtest_summary": bt,
                "portfolio_lifespan": portfolio.get("portfolio_lifespan"),
                "portfolio_health": portfolio.get("portfolio_health"),
            },
            "rag_stats": rag_stats,
            "rag_reviews": rag_reviews,
        }
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
        print(f"\n💾 完整报告已保存: {filename}")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(run_full_test())
