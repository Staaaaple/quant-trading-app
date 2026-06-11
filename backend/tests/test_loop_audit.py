"""循环审核机制测试.

测试场景:
1. SAA审核不通过 → 调节权重 → 重新审核 → 通过
2. 风控审核不通过 → 调节止损 → 重新审核 → 通过
3. 多次重试后仍未通过 → 记录警告
4. 循环审核统计信息验证
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.hybrid_portfolio_designer_v2 import design_portfolio_v2


async def test_loop_audit():
    """测试循环审核机制."""
    print("=" * 70)
    print("循环审核机制测试")
    print("=" * 70)

    # 测试用例1: 稳健型投资者 + 复苏期市场
    profile = {
        "risk_tolerance": 0.6,
        "loss_aversion": 0.6,
        "time_horizon": 0.7,
        "investment_experience": 0.5,
        "income_stability": 0.6,
    }

    market_signal = {
        "macro_score": 0.55,
        "industry_score": 0.6,
        "sentiment_score": 0.5,
        "geo_risk": 0.4,
        "industry_scores": {
            "technology": 0.8,
            "healthcare": 0.6,
            "finance": 0.5,
            "energy": 0.4,
            "consumer": 0.7,
        },
        "social_trends": ["AI投资热潮", "新能源转型"],
    }

    print("\n【测试用例1】稳健型投资者 + 复苏期市场")
    print(f"画像: 风险承受={profile['risk_tolerance']}, 损失厌恶={profile['loss_aversion']}")
    print(f"市场: 宏观评分={market_signal['macro_score']}, 地缘风险={market_signal['geo_risk']}")

    try:
        portfolio = await design_portfolio_v2(
            profile_vector=profile,
            market_signal=market_signal,
            use_rag_gate=True,
        )

        print(f"\n✅ 组合生成成功")
        print(f"   组合ID: {portfolio['portfolio_id']}")
        print(f"   SAA权重: 股票={portfolio['saa']['weights']['stock']:.1%}, "
              f"债券={portfolio['saa']['weights']['bond']:.1%}")
        print(f"   风控: 止损={portfolio['risk_config']['stop_loss']:.1%}, "
              f"最大回撤={portfolio['risk_config']['max_drawdown']:.1%}")

        # 循环审核统计
        stats = portfolio.get("rag_loop_stats", {})
        print(f"\n📊 循环审核统计:")
        print(f"   总审核次数: {stats.get('total_reviews', 0)}")
        print(f"   审核步骤数: {stats.get('total_steps', 0)}")
        print(f"   通过步骤: {stats.get('passed_steps', 0)}")
        print(f"   未通过步骤: {stats.get('failed_steps', 0)}")
        print(f"   通过率: {stats.get('pass_rate', 0):.0%}")
        print(f"   总重试次数: {stats.get('total_retries', 0)}")
        print(f"   平均每步重试: {stats.get('avg_retries_per_step', 0):.1f}")

        # 需要关注的步骤
        attention = stats.get("steps_needing_attention", [])
        if attention:
            print(f"   ⚠️ 需要关注的步骤: {', '.join(attention)}")

        # 详细重试记录
        steps_with_retries = stats.get("steps_with_retries", [])
        if steps_with_retries:
            print(f"\n🔄 重试详情:")
            for step_info in steps_with_retries:
                step = step_info["step"]
                attempts = step_info["attempts"]
                max_retry = step_info["max_retry"]
                passed = "✅" if step_info["passed"] else "❌"
                passed_after = "(重试后通过)" if step_info["passed_after_retry"] else ""
                print(f"   [{passed}] {step}: 尝试{attempts}次, 最大重试{max_retry} {passed_after}")
                if step_info["issues"]:
                    for issue in step_info["issues"][:3]:
                        print(f"       - {issue}")

        # 质检记录详情
        reviews = portfolio.get("rag_reviews", [])
        if reviews:
            print(f"\n📝 质检记录 ({len(reviews)}条):")
            for i, review in enumerate(reviews[:5]):  # 只显示前5条
                step = review.get("step", "unknown")
                passed = "✅通过" if review.get("passed") else "❌不通过"
                retry = review.get("retry", 0)
                score = review.get("score", 0)
                print(f"   {i+1}. [{step}] {passed} (重试{retry}, 分数{score:.2f})")
                if review.get("issues"):
                    for issue in review["issues"][:2]:
                        print(f"       - {issue}")

        print(f"\n{'='*70}")
        print("测试完成!")
        print(f"{'='*70}")

        return portfolio

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_without_rag_gate():
    """测试不使用RAG质检的情况（基准对比）."""
    print("\n" + "=" * 70)
    print("【对比测试】不使用RAG质检")
    print("=" * 70)

    profile = {
        "risk_tolerance": 0.6,
        "loss_aversion": 0.6,
        "time_horizon": 0.7,
    }

    market_signal = {
        "macro_score": 0.55,
        "industry_score": 0.6,
        "sentiment_score": 0.5,
        "geo_risk": 0.4,
        "industry_scores": {"technology": 0.8, "healthcare": 0.6},
        "social_trends": [],
    }

    portfolio = await design_portfolio_v2(
        profile_vector=profile,
        market_signal=market_signal,
        use_rag_gate=False,
    )

    print(f"✅ 组合生成成功 (无RAG质检)")
    print(f"   SAA权重: 股票={portfolio['saa']['weights']['stock']:.1%}")
    print(f"   RAG审核: {portfolio.get('rag_adjusted', False)}")
    print(f"   调节次数: {portfolio.get('rag_adjustment_count', 0)}")

    return portfolio


if __name__ == "__main__":
    # 运行测试
    portfolio_with_rag = asyncio.run(test_loop_audit())
    portfolio_without_rag = asyncio.run(test_without_rag_gate())

    # 对比结果
    if portfolio_with_rag and portfolio_without_rag:
        print("\n" + "=" * 70)
        print("【对比总结】")
        print("=" * 70)
        print(f"有RAG质检:")
        print(f"  - 股票权重: {portfolio_with_rag['saa']['weights']['stock']:.1%}")
        print(f"  - 止损线: {portfolio_with_rag['risk_config']['stop_loss']:.1%}")
        print(f"  - 调节次数: {portfolio_with_rag.get('rag_adjustment_count', 0)}")
        print(f"  - 总重试: {portfolio_with_rag.get('rag_loop_stats', {}).get('total_retries', 0)}")

        print(f"\n无RAG质检:")
        print(f"  - 股票权重: {portfolio_without_rag['saa']['weights']['stock']:.1%}")
        print(f"  - 止损线: {portfolio_without_rag['risk_config']['stop_loss']:.1%}")
        print(f"  - 调节次数: {portfolio_without_rag.get('rag_adjustment_count', 0)}")
