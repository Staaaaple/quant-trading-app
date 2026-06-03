"""推送系统服务 — 今日操作/寿命预警/周期切换推送生成.

Phase D: 全链路服务
核心原则: 有操作才推，无操作显示"今日持有"

推送类型:
- daily_op: 今日操作（买入/卖出/持有信号）
- lifespan_alert: 寿命预警（策略到期/健康度下降）
- cycle_alert: 周期切换提醒
- rebalance_alert: 再平衡提醒
- weekly_report: 周报
"""

import datetime
from typing import Any


def generate_daily_operation_push(
    user_id: int,
    portfolio: dict[str, Any],
    market_signal: dict[str, Any],
    strategy_signals: list[dict[str, Any]],
) -> dict[str, Any]:
    """生成今日操作推送.

    检查各策略的信号，生成买入/卖出/持有建议.
    核心原则: 只有当有实际操作时才生成推送.

    Args:
        user_id: 用户ID
        portfolio: 组合配置
        market_signal: 市场信号
        strategy_signals: 各策略的今日信号列表

    Returns:
        推送内容，如果没有操作则返回None
    """
    holdings = portfolio.get("holdings", [])
    operations = []
    hold_list = []

    for h in holdings:
        symbol = h.get("symbol", "")
        name = h.get("name", "")
        weight = h.get("weight", 0)
        strategy_type = h.get("strategy_type", "")

        # 查找该标的的策略信号
        signal = _find_signal_for_symbol(symbol, strategy_signals)

        if signal:
            action = signal.get("action", "hold")
            if action in ["buy", "sell"]:
                # 有操作信号
                operations.append({
                    "symbol": symbol,
                    "name": name,
                    "action": action,
                    "action_cn": "买入" if action == "buy" else "卖出",
                    "reason": signal.get("reason", ""),
                    "strategy_name": signal.get("strategy_name", ""),
                    "confidence": signal.get("confidence", 0.5),
                    "suggested_amount": _calculate_operation_amount(
                        portfolio, h, action
                    ),
                    "teaching_card": _get_teaching_card_for_signal(signal),
                })
            else:
                # 持有
                hold_list.append({
                    "symbol": symbol,
                    "name": name,
                    "reason": signal.get("reason", "无明确信号，继续持有"),
                })
        else:
            # 无信号，默认持有
            hold_list.append({
                "symbol": symbol,
                "name": name,
                "reason": "策略未触发信号，继续持有",
            })

    # 如果没有操作，返回"今日持有"
    if not operations:
        return {
            "has_operation": False,
            "title": "今日持有",
            "date": datetime.date.today().isoformat(),
            "summary": "所有标的均无操作信号，继续持有",
            "holdings": hold_list,
            "market_brief": _generate_market_brief(market_signal),
        }

    # 有操作，生成详细推送
    return {
        "has_operation": True,
        "title": f"今日操作提示 ({len(operations)}个信号)",
        "date": datetime.date.today().isoformat(),
        "operations": operations,
        "holdings": hold_list,
        "market_brief": _generate_market_brief(market_signal),
        "priority": _calculate_priority(operations),
    }


def generate_lifespan_alert(
    portfolio: dict[str, Any],
    lifespan_data: dict[str, Any],
) -> dict[str, Any] | None:
    """生成寿命预警推送.

    当策略寿命低于阈值时生成预警.

    Returns:
        如果有预警则返回内容，否则返回None
    """
    alerts = []
    holdings = portfolio.get("holdings", [])

    for h in holdings:
        symbol = h.get("symbol", "")
        name = h.get("name", "")
        remaining_months = h.get("lifespan_months", 12)
        health_score = h.get("health_score", 100)

        # 红色预警: 寿命<3月 或 健康度下降>40%
        if remaining_months < 3:
            alerts.append({
                "level": "red",
                "level_cn": "紧急",
                "symbol": symbol,
                "name": name,
                "type": "lifespan_critical",
                "message": f"{name} 策略寿命仅剩 {remaining_months:.1f} 个月，建议尽快替换",
                "remaining_months": remaining_months,
                "recommended_action": "查看替代方案",
            })
        # 黄色预警: 寿命<6月 或 健康度下降>20%
        elif remaining_months < 6:
            alerts.append({
                "level": "yellow",
                "level_cn": "提醒",
                "symbol": symbol,
                "name": name,
                "type": "lifespan_warning",
                "message": f"{name} 策略寿命剩余 {remaining_months:.1f} 个月，请关注",
                "remaining_months": remaining_months,
                "recommended_action": "关注替代方案",
            })

    # 组合层面预警
    portfolio_lifespan = lifespan_data.get("portfolio_lifespan", 12)
    portfolio_health = lifespan_data.get("portfolio_health", 100)

    if portfolio_lifespan < 3:
        alerts.append({
            "level": "red",
            "level_cn": "紧急",
            "type": "portfolio_critical",
            "message": f"组合整体寿命仅剩 {portfolio_lifespan:.1f} 个月，建议全面调仓",
            "portfolio_lifespan": portfolio_lifespan,
            "recommended_action": "重新生成组合",
        })

    if not alerts:
        return None

    return {
        "title": f"寿命预警 ({len(alerts)}条)",
        "date": datetime.date.today().isoformat(),
        "alerts": alerts,
        "portfolio_lifespan": portfolio_lifespan,
        "portfolio_health": portfolio_health,
        "priority": "high" if any(a["level"] == "red" for a in alerts) else "normal",
    }


def generate_cycle_alert(
    old_cycle: str,
    new_cycle: str,
    market_signal: dict[str, Any],
) -> dict[str, Any] | None:
    """生成周期切换提醒.

    当市场周期发生变化时提醒用户调整组合.
    """
    if old_cycle == new_cycle:
        return None

    cycle_names = {
        "expansion": "扩张期",
        "peak": "顶部期",
        "contraction": "收缩期",
        "recovery": "复苏期",
    }

    cycle_advice = {
        ("recovery", "expansion"): "经济进入扩张期，适合增配股票，关注周期性行业。",
        ("expansion", "peak"): "经济接近顶部，建议逐步降低股票仓位，增配债券和现金。",
        ("peak", "contraction"): "经济进入收缩期，以防御为主，关注避险资产。",
        ("contraction", "recovery"): "经济开始复苏，可逐步建仓，关注前期超跌的优质资产。",
    }

    old_name = cycle_names.get(old_cycle, old_cycle)
    new_name = cycle_names.get(new_cycle, new_cycle)

    advice = cycle_advice.get(
        (old_cycle, new_cycle),
        f"市场周期从 {old_name} 切换到 {new_name}，建议关注组合配置是否需要调整。"
    )

    return {
        "title": "市场周期切换",
        "date": datetime.date.today().isoformat(),
        "old_cycle": old_cycle,
        "old_cycle_cn": old_name,
        "new_cycle": new_cycle,
        "new_cycle_cn": new_name,
        "message": f"市场周期已从 {old_name} 切换到 {new_name}",
        "advice": advice,
        "recommended_action": "查看组合调整建议",
        "priority": "high",
    }


def generate_rebalance_alert(
    portfolio: dict[str, Any],
    deviation_data: dict[str, Any],
) -> dict[str, Any] | None:
    """生成再平衡提醒.

    当权重偏离度超过阈值时提醒.
    """
    deviations = deviation_data.get("deviations", [])
    threshold = deviation_data.get("threshold", 0.05)

    significant_deviations = [
        d for d in deviations
        if abs(d.get("deviation", 0)) > threshold
    ]

    if not significant_deviations:
        return None

    # 生成调整建议
    adjustments = []
    for d in significant_deviations:
        symbol = d.get("symbol", "")
        name = d.get("name", "")
        current = d.get("current_weight", 0)
        target = d.get("target_weight", 0)
        deviation = d.get("deviation", 0)

        if deviation > 0:
            action = "卖出"
            amount = deviation * portfolio.get("total_value", 0)
        else:
            action = "买入"
            amount = abs(deviation) * portfolio.get("total_value", 0)

        adjustments.append({
            "symbol": symbol,
            "name": name,
            "action": action,
            "current_weight": round(current * 100, 1),
            "target_weight": round(target * 100, 1),
            "deviation": round(deviation * 100, 1),
            "suggested_amount": round(amount, 2),
        })

    return {
        "title": "再平衡提醒",
        "date": datetime.date.today().isoformat(),
        "trigger_reason": "权重偏离度超过阈值",
        "threshold": threshold,
        "deviations": adjustments,
        "summary": f"{len(adjustments)} 个标的大幅偏离目标权重",
        "recommended_action": "执行再平衡",
        "priority": "normal",
    }


def _find_signal_for_symbol(
    symbol: str,
    strategy_signals: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """查找标的对应的策略信号."""
    for s in strategy_signals:
        if s.get("symbol") == symbol:
            return s
    return None


def _calculate_operation_amount(
    portfolio: dict[str, Any],
    holding: dict[str, Any],
    action: str,
) -> float:
    """计算建议操作金额."""
    total_value = portfolio.get("total_value", 100000)
    weight = holding.get("weight", 0)

    if action == "buy":
        # 买入: 按目标权重的10-20%
        return total_value * weight * 0.15
    else:
        # 卖出: 按当前持仓的30-50%
        return total_value * weight * 0.40


def _get_teaching_card_for_signal(signal: dict[str, Any]) -> dict[str, Any]:
    """为操作信号生成教学卡片."""
    concept = signal.get("concept", "")

    teaching_cards = {
        "golden_cross": {
            "title": "什么是金叉？",
            "content": "短期均线上穿长期均线，通常被视为买入信号。表明短期趋势转强。",
        },
        "death_cross": {
            "title": "什么是死叉？",
            "content": "短期均线下穿长期均线，通常被视为卖出信号。表明短期趋势转弱。",
        },
        "overbought": {
            "title": "超买信号",
            "content": "RSI等指标进入超买区域（>70），表明上涨动能可能衰竭，考虑减仓。",
        },
        "oversold": {
            "title": "超卖信号",
            "content": "RSI等指标进入超卖区域（<30），表明下跌动能可能衰竭，考虑建仓。",
        },
        "momentum": {
            "title": "动量信号",
            "content": "价格突破前期高点，动量转强，适合顺势操作。",
        },
    }

    return teaching_cards.get(concept, {
        "title": "策略信号",
        "content": f"该策略触发了{signal.get('action', '操作')}信号，建议关注。",
    })


def _generate_market_brief(market_signal: dict[str, Any]) -> str:
    """生成市场简报."""
    cycle = market_signal.get("market_cycle", "")
    composite_score = market_signal.get("composite_score", 0.5)

    cycle_names = {
        "expansion": "扩张期",
        "peak": "顶部期",
        "contraction": "收缩期",
        "recovery": "复苏期",
    }

    cycle_name = cycle_names.get(cycle, cycle)

    if composite_score > 0.6:
        mood = "偏乐观"
    elif composite_score > 0.4:
        mood = "中性"
    else:
        mood = "偏谨慎"

    return f"当前市场处于{cycle_name}，综合评分{composite_score:.0%}，整体{mood}"


def _calculate_priority(operations: list[dict[str, Any]]) -> str:
    """计算推送优先级."""
    high_confidence = sum(1 for op in operations if op.get("confidence", 0) > 0.8)
    sell_ops = sum(1 for op in operations if op.get("action") == "sell")

    if sell_ops > 0 or high_confidence >= 2:
        return "high"
    return "normal"
