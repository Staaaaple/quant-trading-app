"""周报生成服务 — 组合表现 + 市场回顾 + 下周展望.

Phase D: 全链路服务
每周五生成并推送周报.
"""

import datetime
from typing import Any


def generate_weekly_report(
    user_id: int,
    portfolio: dict[str, Any],
    market_signal: dict[str, Any],
    performance_data: dict[str, Any],
    lifespan_data: dict[str, Any],
) -> dict[str, Any]:
    """生成完整的周报.

    Args:
        user_id: 用户ID
        portfolio: 组合配置
        market_signal: 市场信号
        performance_data: 本周表现数据
        lifespan_data: 寿命数据

    Returns:
        周报内容
    """
    # 计算周期间
    today = datetime.date.today()
    week_start = today - datetime.timedelta(days=today.weekday())
    week_end = week_start + datetime.timedelta(days=6)

    return {
        "user_id": user_id,
        "portfolio_id": portfolio.get("id"),
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
        "generated_at": datetime.datetime.utcnow().isoformat(),

        # 1. 组合表现
        "performance": _generate_performance_section(performance_data),

        # 2. 市场回顾
        "market_review": _generate_market_review(market_signal),

        # 3. 下周展望
        "outlook": _generate_outlook(market_signal, portfolio),

        # 4. 寿命预警
        "lifespan_alerts": _generate_lifespan_section(lifespan_data),

        # 5. 操作建议
        "recommended_actions": _generate_recommended_actions(
            portfolio, market_signal, lifespan_data
        ),
    }


def _generate_performance_section(performance_data: dict[str, Any]) -> dict[str, Any]:
    """生成本周组合表现."""
    weekly_return = performance_data.get("weekly_return", 0)
    cum_return = performance_data.get("cum_return", 0)
    benchmark_return = performance_data.get("benchmark_return", 0)
    max_drawdown = performance_data.get("max_drawdown", 0)

    # 计算相对收益
    excess_return = weekly_return - benchmark_return

    # 持仓表现
    holding_performances = []
    for h in performance_data.get("holdings", []):
        holding_performances.append({
            "symbol": h.get("symbol", ""),
            "name": h.get("name", ""),
            "weekly_return": h.get("weekly_return", 0),
            "weight": h.get("weight", 0),
            "contribution": h.get("weekly_return", 0) * h.get("weight", 0),
        })

    # 按贡献度排序
    holding_performances.sort(key=lambda x: x["contribution"], reverse=True)

    # 最佳/最差贡献
    best = holding_performances[0] if holding_performances else None
    worst = holding_performances[-1] if holding_performances else None

    return {
        "weekly_return": weekly_return,
        "weekly_return_pct": f"{weekly_return:+.2%}",
        "cum_return": cum_return,
        "cum_return_pct": f"{cum_return:+.2%}",
        "benchmark_return": benchmark_return,
        "benchmark_return_pct": f"{benchmark_return:+.2%}",
        "excess_return": excess_return,
        "excess_return_pct": f"{excess_return:+.2%}",
        "max_drawdown": max_drawdown,
        "max_drawdown_pct": f"{max_drawdown:.2%}",
        "holding_performances": holding_performances,
        "best_contributor": best,
        "worst_contributor": worst,
        "summary": _generate_performance_summary(weekly_return, excess_return),
    }


def _generate_market_review(market_signal: dict[str, Any]) -> dict[str, Any]:
    """生成市场回顾."""
    cycle = market_signal.get("market_cycle", "")
    composite_score = market_signal.get("composite_score", 0.5)

    cycle_names = {
        "expansion": "扩张期",
        "peak": "顶部期",
        "contraction": "收缩期",
        "recovery": "复苏期",
    }

    # 五层信号回顾
    layers = []
    layer_names = {
        "macro": "宏观层",
        "geo": "地缘政治",
        "industry": "行业景气",
        "social": "社会实事",
        "internal": "资产内部",
    }

    for key, name in layer_names.items():
        layer_data = market_signal.get(key, {})
        score = layer_data.get("score", 0.5) if isinstance(layer_data, dict) else 0.5
        trend = layer_data.get("trend", "stable") if isinstance(layer_data, dict) else "stable"

        trend_icons = {
            "up": "↑",
            "down": "↓",
            "stable": "→",
        }

        layers.append({
            "name": name,
            "score": score,
            "score_pct": f"{score:.0%}",
            "trend": trend,
            "trend_icon": trend_icons.get(trend, "→"),
        })

    # 生成市场综述
    if composite_score > 0.6:
        mood = "偏乐观"
        summary = "本周市场整体表现积极，多项指标向好。"
    elif composite_score > 0.4:
        mood = "中性"
        summary = "本周市场震荡整理，多空因素交织。"
    else:
        mood = "偏谨慎"
        summary = "本周市场承压，需关注风险因素。"

    return {
        "market_cycle": cycle,
        "market_cycle_cn": cycle_names.get(cycle, cycle),
        "composite_score": composite_score,
        "composite_score_pct": f"{composite_score:.0%}",
        "mood": mood,
        "summary": summary,
        "layers": layers,
        "major_events": market_signal.get("major_events", []),
    }


def _generate_outlook(
    market_signal: dict[str, Any],
    portfolio: dict[str, Any],
) -> dict[str, Any]:
    """生成下周展望."""
    cycle = market_signal.get("market_cycle", "")
    next_cycle_prob = market_signal.get("next_cycle_probability", {})

    # 预测下周周期
    predicted_cycle = max(next_cycle_prob, key=next_cycle_prob.get, default=cycle)
    predicted_prob = next_cycle_prob.get(predicted_cycle, 0.5)

    cycle_outlooks = {
        "expansion": {
            "title": "扩张期延续",
            "content": "经济扩张趋势有望延续，关注企业盈利数据和政策动向。",
            "opportunities": ["周期性行业", "成长股", "科技板块"],
            "risks": ["通胀压力", "政策收紧预期"],
        },
        "peak": {
            "title": "顶部风险增加",
            "content": "市场可能接近阶段性顶部，建议提高警惕，控制仓位。",
            "opportunities": ["防御性板块", "高股息标的"],
            "risks": ["回调风险", "估值压力"],
        },
        "contraction": {
            "title": "收缩期防御",
            "content": "经济收缩期以防御为主，关注政策刺激和底部信号。",
            "opportunities": ["债券", "黄金", "公用事业"],
            "risks": ["盈利下滑", "流动性收紧"],
        },
        "recovery": {
            "title": "复苏期布局",
            "content": "经济复苏迹象显现，可逐步增加风险资产配置。",
            "opportunities": ["前期超跌优质资产", "金融板块", "消费复苏"],
            "risks": ["复苏不及预期", "外部冲击"],
        },
    }

    outlook = cycle_outlooks.get(predicted_cycle, cycle_outlooks["recovery"])

    # 根据组合配置生成个性化建议
    risk_label = portfolio.get("risk_label", "稳健型")
    personalized_advice = _get_personalized_outlook_advice(risk_label, predicted_cycle)

    return {
        "predicted_cycle": predicted_cycle,
        "predicted_cycle_cn": _cycle_to_cn(predicted_cycle),
        "prediction_confidence": predicted_prob,
        "title": outlook["title"],
        "content": outlook["content"],
        "opportunities": outlook["opportunities"],
        "risks": outlook["risks"],
        "personalized_advice": personalized_advice,
        "key_dates": market_signal.get("key_dates_next_week", []),
    }


def _generate_lifespan_section(lifespan_data: dict[str, Any]) -> dict[str, Any]:
    """生成寿命预警部分."""
    portfolio_lifespan = lifespan_data.get("portfolio_lifespan", 12)
    portfolio_health = lifespan_data.get("portfolio_health", 100)
    holding_lifespans = lifespan_data.get("holdings", [])

    alerts = []
    for h in holding_lifespans:
        remaining = h.get("lifespan_months", 12)
        if remaining < 3:
            alerts.append({
                "level": "red",
                "symbol": h.get("symbol", ""),
                "name": h.get("name", ""),
                "message": f"寿命仅剩 {remaining:.1f} 个月",
            })
        elif remaining < 6:
            alerts.append({
                "level": "yellow",
                "symbol": h.get("symbol", ""),
                "name": h.get("name", ""),
                "message": f"寿命剩余 {remaining:.1f} 个月",
            })

    return {
        "portfolio_lifespan": portfolio_lifespan,
        "portfolio_health": portfolio_health,
        "alerts": alerts,
        "alert_count": len(alerts),
        "has_alert": len(alerts) > 0,
    }


def _generate_recommended_actions(
    portfolio: dict[str, Any],
    market_signal: dict[str, Any],
    lifespan_data: dict[str, Any],
) -> list[dict[str, Any]]:
    """生成操作建议."""
    actions = []

    # 检查是否需要再平衡
    deviations = portfolio.get("weight_deviations", [])
    threshold = 0.08  # 8%阈值
    significant_devs = [d for d in deviations if abs(d.get("deviation", 0)) > threshold]

    if significant_devs:
        actions.append({
            "priority": "normal",
            "action": "执行再平衡",
            "reason": f"{len(significant_devs)} 个标的大幅偏离目标权重",
        })

    # 检查寿命预警
    alerts = lifespan_data.get("holdings", [])
    critical = [a for a in alerts if a.get("lifespan_months", 12) < 3]
    if critical:
        actions.append({
            "priority": "high",
            "action": "关注寿命到期策略",
            "reason": f"{len(critical)} 个策略寿命即将到期",
        })

    # 检查周期变化
    current_cycle = market_signal.get("market_cycle", "")
    portfolio_cycle = portfolio.get("market_cycle", "")
    if current_cycle != portfolio_cycle:
        actions.append({
            "priority": "high",
            "action": "审视组合配置",
            "reason": f"市场周期从 {portfolio_cycle} 切换到 {current_cycle}",
        })

    if not actions:
        actions.append({
            "priority": "low",
            "action": "持有观望",
            "reason": "当前无明确操作信号，继续持有",
        })

    return actions


def _generate_performance_summary(weekly_return: float, excess_return: float) -> str:
    """生成表现摘要."""
    if weekly_return > 0.02:
        return "本周表现优秀，大幅跑赢基准"
    elif weekly_return > 0:
        return "本周表现良好，实现正收益"
    elif weekly_return > -0.02:
        return "本周小幅回调，属正常波动"
    else:
        return "本周表现较弱，建议关注市场变化"


def _get_personalized_outlook_advice(risk_label: str, predicted_cycle: str) -> str:
    """生成个性化的展望建议."""
    advice_map = {
        ("保守型", "expansion"): "虽然市场向好，但建议保持稳健配置，不追涨。",
        ("保守型", "peak"): "顶部风险增加，建议进一步降低股票仓位。",
        ("保守型", "contraction"): "收缩期以防御为主，增配债券和现金。",
        ("保守型", "recovery"): "复苏期可小幅增配，但仍以稳健为主。",
        ("稳健型", "expansion"): "扩张期适合适度增配股票，把握上涨机会。",
        ("稳健型", "peak"): "顶部区域建议逐步获利了结，降低风险暴露。",
        ("稳健型", "contraction"): "收缩期保持防御，关注避险资产。",
        ("稳健型", "recovery"): "复苏期可逐步建仓，关注优质资产。",
        ("积极型", "expansion"): "扩张期积极增配，把握上涨行情。",
        ("积极型", "peak"): "顶部区域注意风险控制，保留部分现金。",
        ("积极型", "contraction"): "收缩期寻找超跌机会，为反弹布局。",
        ("积极型", "recovery"): "复苏期积极布局，增配成长型资产。",
        ("激进型", "expansion"): "全力做多，把握扩张期机会。",
        ("激进型", "peak"): "顶部区域可适度对冲，但保持高仓位。",
        ("激进型", "contraction"): "收缩期逆向布局，买入超跌资产。",
        ("激进型", "recovery"): "复苏期全力进攻，最大化收益。",
    }

    return advice_map.get(
        (risk_label, predicted_cycle),
        "建议根据自身风险承受能力调整配置。"
    )


def _cycle_to_cn(cycle: str) -> str:
    """周期英文转中文."""
    mapping = {
        "expansion": "扩张期",
        "peak": "顶部期",
        "contraction": "收缩期",
        "recovery": "复苏期",
    }
    return mapping.get(cycle, cycle)
