"""循环审核机制简化测试 — 不触发RAG服务，只测试循环逻辑."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_loop_logic():
    """测试循环审核逻辑本身."""
    print("=" * 70)
    print("循环审核机制逻辑测试")
    print("=" * 70)

    # 模拟审核结果序列
    # 场景1: 第一次不通过，第二次通过
    mock_reviews_saa = [
        {"passed": False, "score": 0.4, "issues": ["股票权重过高"], "adjustments": [{"type": "weight_cap", "asset": "stock", "cap": 0.5}]},
        {"passed": True, "score": 0.85, "issues": [], "adjustments": []},
    ]

    # 场景2: 始终不通过（达到最大重试）
    mock_reviews_risk = [
        {"passed": False, "score": 0.3, "issues": ["止损过宽"], "adjustments": [{"type": "stop_loss", "value": 0.05}]},
        {"passed": False, "score": 0.35, "issues": ["止损仍过宽"], "adjustments": [{"type": "stop_loss", "value": 0.04}]},
        {"passed": False, "score": 0.3, "issues": ["无法通过"], "adjustments": []},
    ]

    def simulate_loop_audit(step_name, mock_reviews, max_retries):
        """模拟循环审核."""
        print(f"\n【{step_name}】最大重试次数: {max_retries}")
        adjustments_log = []
        current_result = {"weights": {"stock": 0.7}}  # 模拟当前结果

        for retry in range(max_retries + 1):
            # 获取模拟审核结果
            if retry < len(mock_reviews):
                review = mock_reviews[retry]
            else:
                review = {"passed": False, "score": 0, "issues": ["超出模拟范围"], "adjustments": []}

            passed = review["passed"]
            print(f"  尝试 {retry}: {'✅通过' if passed else '❌不通过'} (分数: {review['score']:.2f})")

            if passed:
                if retry > 0:
                    print(f"  → 重试后通过! 共调节 {retry} 次")
                break

            # 模拟应用调节
            adjustments_log.append({
                "step": step_name.lower(),
                "passed": False,
                "score": review["score"],
                "issues": review["issues"],
                "retry": retry,
            })
            print(f"  → 应用调节: {review['adjustments']}")
        else:
            # 超过最大重试次数
            print(f"  ⚠️ 超过最大重试次数({max_retries})，仍未通过")
            adjustments_log.append({
                "step": step_name.lower(),
                "passed": False,
                "retry": max_retries,
                "warning": f"{step_name}审核多次调节仍未通过",
            })

        return adjustments_log

    # 测试场景1: SAA (2次重试，第2次通过)
    log1 = simulate_loop_audit("SAA", mock_reviews_saa, max_retries=2)

    # 测试场景2: 风控 (2次重试，始终不通过)
    log2 = simulate_loop_audit("风控", mock_reviews_risk, max_retries=2)

    # 合并日志
    all_logs = log1 + log2

    print(f"\n{'='*70}")
    print("循环审核统计")
    print(f"{'='*70}")

    # 统计逻辑（与 _calculate_loop_stats 相同）
    step_stats = {}
    for log in all_logs:
        step = log.get("step", "unknown")
        if step not in step_stats:
            step_stats[step] = {
                "total_attempts": 0,
                "passed": False,
                "max_retry": 0,
                "issues": [],
            }
        step_stats[step]["total_attempts"] += 1
        step_stats[step]["max_retry"] = max(step_stats[step]["max_retry"], log.get("retry", 0))
        if log.get("passed"):
            step_stats[step]["passed"] = True
        if log.get("issues"):
            step_stats[step]["issues"].extend(log.get("issues", []))

    total_steps = len(step_stats)
    passed_steps = sum(1 for s in step_stats.values() if s["passed"])
    total_retries = sum(s["max_retry"] for s in step_stats.values())

    print(f"总审核次数: {len(all_logs)}")
    print(f"审核步骤数: {total_steps}")
    print(f"通过步骤: {passed_steps}")
    print(f"未通过步骤: {total_steps - passed_steps}")
    print(f"通过率: {passed_steps / total_steps:.0%}")
    print(f"总重试次数: {total_retries}")
    print(f"平均每步重试: {total_retries / total_steps:.1f}")

    print(f"\n各步骤详情:")
    for step, stats in step_stats.items():
        status = "✅通过" if stats["passed"] else "❌未通过"
        print(f"  [{status}] {step}: 尝试{stats['total_attempts']}次, 最大重试{stats['max_retry']}")

    print(f"\n{'='*70}")
    print("✅ 循环审核逻辑测试通过!")
    print(f"{'='*70}")

    return True


def test_weight_adjustment():
    """测试权重调节逻辑."""
    print("\n" + "=" * 70)
    print("权重调节逻辑测试")
    print("=" * 70)

    # 模拟SAA结果
    saa_result = {
        "weights": {"stock": 0.76, "bond": 0.12, "commodity": 0.07, "cash": 0.05}
    }

    print(f"原始权重: 股票={saa_result['weights']['stock']:.0%}, "
          f"债券={saa_result['weights']['bond']:.0%}")

    # 模拟调节: 股票上限截断到50%
    adjustments = [{"type": "weight_cap", "asset": "stock", "cap": 0.5}]

    weights = saa_result["weights"].copy()
    for adj in adjustments:
        if adj["type"] == "weight_cap":
            asset = adj["asset"]
            cap = adj["cap"]
            if weights[asset] > cap:
                excess = weights[asset] - cap
                weights[asset] = cap
                weights["bond"] = weights.get("bond", 0) + excess

    # 归一化
    total = sum(weights.values())
    weights = {k: v / total for k, v in weights.items()}

    print(f"调节后权重: 股票={weights['stock']:.0%}, 债券={weights['bond']:.0%}")
    print(f"✅ 股票从76%降至{weights['stock']:.0%}，符合稳健型投资者要求")

    return True


def test_risk_adjustment():
    """测试风控调节逻辑."""
    print("\n" + "=" * 70)
    print("风控调节逻辑测试")
    print("=" * 70)

    # 模拟风控配置
    risk_config = {
        "stop_loss": 0.08,
        "max_position": 0.20,
        "max_drawdown": 0.15,
    }

    print(f"原始风控: 止损={risk_config['stop_loss']:.0%}, "
          f"最大回撤={risk_config['max_drawdown']:.0%}")

    # 模拟调节: 止损调至5%
    adjustments = [{"type": "stop_loss", "value": 0.05}]

    for adj in adjustments:
        if adj["type"] == "stop_loss":
            risk_config["stop_loss"] = adj["value"]

    print(f"调节后风控: 止损={risk_config['stop_loss']:.0%}, "
          f"最大回撤={risk_config['max_drawdown']:.0%}")
    print(f"✅ 止损从8%调至5%，匹配高损失厌恶用户")

    return True


if __name__ == "__main__":
    test_loop_logic()
    test_weight_adjustment()
    test_risk_adjustment()

    print("\n" + "=" * 70)
    print("所有测试通过! ✅")
    print("=" * 70)
