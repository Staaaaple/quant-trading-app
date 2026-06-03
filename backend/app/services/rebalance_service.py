"""调仓提醒服务 — 5种触发检测 + 替代方案推荐.

Phase D: 全链路服务

再平衡触发条件:
1. time_based: 定期再平衡（季度/月度）
2. deviation_based: 权重偏离度 > 阈值
3. lifespan_based: 任一组件寿命 < 3个月
4. health_based: 组合健康度下降 > 20%
5. cycle_based: 市场周期阶段切换

替代方案推荐:
- 当策略到期/失效时，推荐3个替代策略
- 对比维度: 夏普/回撤/寿命/同质化
"""

import datetime
from typing import Any


# 再平衡触发条件配置
REBALANCE_TRIGGERS = {
    "time_based": {
        "name": "定期再平衡",
        "description": "按固定周期执行再平衡",
        "default_interval_months": 3,  # 季度
    },
    "deviation_based": {
        "name": "偏离度再平衡",
        "description": "权重偏离目标超过阈值时触发",
        "thresholds": {
            "conservative": 0.05,  # 保守型 5%
            "moderate": 0.08,      # 稳健型 8%
            "aggressive": 0.10,    # 积极型 10%
            "very_aggressive": 0.15,  # 激进型 15%
        },
    },
    "lifespan_based": {
        "name": "寿命到期再平衡",
        "description": "任一组件寿命低于3个月时触发",
        "threshold_months": 3,
    },
    "health_based": {
        "name": "健康度下降再平衡",
        "description": "组合健康度下降超过20%时触发",
        "threshold_pct": 0.20,
    },
    "cycle_based": {
        "name": "周期切换再平衡",
        "description": "市场周期阶段发生变化时触发",
    },
}


def check_rebalance_triggers(
    portfolio: dict[str, Any],
    market_signal: dict[str, Any],
    lifespan_data: dict[str, Any],
    last_rebalance_date: str | None = None,
) -> dict[str, Any]:
    """检查所有再平衡触发条件.

    Args:
        portfolio: 组合配置
        market_signal: 市场信号
        lifespan_data: 寿命数据
        last_rebalance_date: 上次再平衡日期 (YYYY-MM-DD)

    Returns:
        触发检测结果
    """
    triggers = []
    risk_label = portfolio.get("risk_label", "moderate")

    # 1. 定期再平衡检查
    if last_rebalance_date:
        last_date = datetime.datetime.strptime(last_rebalance_date, "%Y-%m-%d").date()
        days_since = (datetime.date.today() - last_date).days
        interval_days = REBALANCE_TRIGGERS["time_based"]["default_interval_months"] * 30

        if days_since >= interval_days:
            triggers.append({
                "type": "time_based",
                "name": "定期再平衡",
                "triggered": True,
                "message": f"距离上次再平衡已 {days_since} 天，建议执行季度再平衡",
                "days_since": days_since,
                "priority": "normal",
            })

    # 2. 偏离度检查
    deviations = portfolio.get("weight_deviations", [])
    threshold = REBALANCE_TRIGGERS["deviation_based"]["thresholds"].get(
        risk_label, 0.08
    )
    significant_devs = [
        d for d in deviations
        if abs(d.get("deviation", 0)) > threshold
    ]

    if significant_devs:
        triggers.append({
            "type": "deviation_based",
            "name": "偏离度再平衡",
            "triggered": True,
            "message": f"{len(significant_devs)} 个标的大幅偏离目标权重（阈值 {threshold:.0%}）",
            "deviations": significant_devs,
            "threshold": threshold,
            "priority": "normal",
        })

    # 3. 寿命到期检查
    holdings = portfolio.get("holdings", [])
    expired_holdings = [
        h for h in holdings
        if h.get("lifespan_months", 12) < REBALANCE_TRIGGERS["lifespan_based"]["threshold_months"]
    ]

    if expired_holdings:
        triggers.append({
            "type": "lifespan_based",
            "name": "寿命到期再平衡",
            "triggered": True,
            "message": f"{len(expired_holdings)} 个策略寿命即将到期",
            "expired_holdings": expired_holdings,
            "priority": "high",
        })

    # 4. 健康度下降检查
    health_drop = lifespan_data.get("health_drop", 0)
    if health_drop > REBALANCE_TRIGGERS["health_based"]["threshold_pct"]:
        triggers.append({
            "type": "health_based",
            "name": "健康度下降再平衡",
            "triggered": True,
            "message": f"组合健康度下降 {health_drop:.0%}，建议检查并调仓",
            "health_drop": health_drop,
            "priority": "high",
        })

    # 5. 周期切换检查
    current_cycle = market_signal.get("market_cycle", "")
    portfolio_cycle = portfolio.get("market_cycle", "")
    if current_cycle and portfolio_cycle and current_cycle != portfolio_cycle:
        triggers.append({
            "type": "cycle_based",
            "name": "周期切换再平衡",
            "triggered": True,
            "message": f"市场周期从 {portfolio_cycle} 切换到 {current_cycle}，建议调整配置",
            "old_cycle": portfolio_cycle,
            "new_cycle": current_cycle,
            "priority": "high",
        })

    return {
        "has_trigger": len(triggers) > 0,
        "trigger_count": len(triggers),
        "triggers": triggers,
        "highest_priority": _get_highest_priority(triggers),
        "recommended_action": "执行再平衡" if triggers else "无需操作",
    }


def generate_alternative_strategies(
    target_holding: dict[str, Any],
    strategy_pool: list[dict[str, Any]],
    profile: dict[str, Any],
    market_signal: dict[str, Any],
    top_n: int = 3,
) -> list[dict[str, Any]]:
    """生成替代策略推荐.

    当策略到期或失效时，推荐替代方案.

    Args:
        target_holding: 需要替换的持仓
        strategy_pool: 策略池
        profile: 用户画像
        market_signal: 市场信号
        top_n: 推荐数量

    Returns:
        替代策略列表（按匹配度排序）
    """
    risk_label = profile.get("risk_label", "moderate")
    current_cycle = market_signal.get("market_cycle", "recovery")
    asset_class = target_holding.get("asset_class", "stock")

    candidates = []
    for s in strategy_pool:
        # 基础筛选
        if s.get("asset_class") != asset_class:
            continue

        # 风险等级匹配
        strategy_risk = s.get("risk_level", "medium")
        if not _risk_match(strategy_risk, risk_label):
            continue

        # 周期适配
        suitable_cycles = s.get("suitable_cycles", [])
        if current_cycle not in suitable_cycles:
            continue

        # 寿命检查
        lifespan = s.get("lifespan_months", 0)
        if lifespan < 3:
            continue

        # 计算匹配分数
        score = _calculate_strategy_match_score(
            s, target_holding, profile, market_signal
        )

        candidates.append({
            "strategy_id": s.get("id", ""),
            "name": s.get("name", ""),
            "family": s.get("family", ""),
            "risk_level": strategy_risk,
            "sharpe_ratio": s.get("sharpe_ratio", 0),
            "max_drawdown": s.get("max_drawdown", 0),
            "win_rate": s.get("win_rate", 0),
            "lifespan_months": lifespan,
            "health_score": s.get("health_score", 0),
            "match_score": score,
            "advantages": _generate_advantages(s, target_holding),
        })

    # 按匹配分数排序
    candidates.sort(key=lambda x: x["match_score"], reverse=True)
    return candidates[:top_n]


def generate_rebalance_plan(
    portfolio: dict[str, Any],
    triggers: list[dict[str, Any]],
    alternatives: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    """生成完整的调仓方案.

    Args:
        portfolio: 当前组合
        triggers: 触发条件列表
        alternatives: 替代策略 {symbol: [替代方案]}

    Returns:
        调仓方案
    """
    holdings = portfolio.get("holdings", [])
    adjustments = []

    # 处理寿命到期的持仓
    for trigger in triggers:
        if trigger["type"] == "lifespan_based":
            for h in trigger.get("expired_holdings", []):
                symbol = h.get("symbol", "")
                alt_strategies = alternatives.get(symbol, [])

                if alt_strategies:
                    # 推荐最佳替代
                    best_alt = alt_strategies[0]
                    adjustments.append({
                        "symbol": symbol,
                        "name": h.get("name", ""),
                        "action": "替换策略",
                        "current_strategy": h.get("strategy_name", ""),
                        "new_strategy": best_alt["name"],
                        "reason": f"原策略寿命仅剩 {h.get('lifespan_months', 0):.1f} 个月",
                        "alternatives": alt_strategies,
                        "weight": h.get("weight", 0),
                    })

    # 处理偏离度过大的持仓
    for trigger in triggers:
        if trigger["type"] == "deviation_based":
            for dev in trigger.get("deviations", []):
                symbol = dev.get("symbol", "")
                deviation = dev.get("deviation", 0)

                action = "减仓" if deviation > 0 else "加仓"
                adjustments.append({
                    "symbol": symbol,
                    "name": dev.get("name", ""),
                    "action": action,
                    "current_weight": dev.get("current_weight", 0),
                    "target_weight": dev.get("target_weight", 0),
                    "deviation": deviation,
                    "reason": f"权重偏离目标 {deviation:.1%}",
                })

    # 处理周期切换
    for trigger in triggers:
        if trigger["type"] == "cycle_based":
            adjustments.append({
                "action": "周期调整",
                "old_cycle": trigger.get("old_cycle", ""),
                "new_cycle": trigger.get("new_cycle", ""),
                "reason": "市场周期切换",
                "suggested_changes": _generate_cycle_adjustments(
                    trigger.get("old_cycle", ""),
                    trigger.get("new_cycle", ""),
                    holdings,
                ),
            })

    return {
        "trigger_summary": f"检测到 {len(triggers)} 个再平衡触发条件",
        "adjustments": adjustments,
        "estimated_trades": len([a for a in adjustments if a.get("symbol")]),
        "expected_impact": _estimate_rebalance_impact(adjustments, portfolio),
    }


def _get_highest_priority(triggers: list[dict[str, Any]]) -> str:
    """获取最高优先级."""
    priorities = [t.get("priority", "normal") for t in triggers]
    if "high" in priorities:
        return "high"
    return "normal"


def _risk_match(strategy_risk: str, user_risk: str) -> bool:
    """检查策略风险等级是否匹配用户风险承受."""
    risk_levels = {
        "low": 1,
        "medium": 2,
        "high": 3,
        "very_high": 4,
    }
    user_levels = {
        "保守型": 1,
        "稳健型": 2,
        "积极型": 3,
        "激进型": 4,
    }

    s_level = risk_levels.get(strategy_risk, 2)
    u_level = user_levels.get(user_risk, 2)

    # 策略风险不应超过用户承受 + 1
    return s_level <= u_level + 1


def _calculate_strategy_match_score(
    strategy: dict[str, Any],
    target: dict[str, Any],
    profile: dict[str, Any],
    market_signal: dict[str, Any],
) -> float:
    """计算策略匹配分数."""
    score = 0.0

    # 夏普比率 (0-30分)
    sharpe = strategy.get("sharpe_ratio", 0)
    score += min(sharpe * 10, 30)

    # 健康度 (0-25分)
    health = strategy.get("health_score", 0)
    score += health * 0.25

    # 寿命 (0-20分)
    lifespan = strategy.get("lifespan_months", 0)
    score += min(lifespan * 2, 20)

    # 胜率 (0-15分)
    win_rate = strategy.get("win_rate", 0)
    score += win_rate * 15

    # 回撤控制 (0-10分)
    drawdown = strategy.get("max_drawdown", 0.3)
    score += max(0, 10 - drawdown * 20)

    return round(score, 2)


def _generate_advantages(
    new_strategy: dict[str, Any],
    old_strategy: dict[str, Any],
) -> list[str]:
    """生成新策略相对旧策略的优势."""
    advantages = []

    new_sharpe = new_strategy.get("sharpe_ratio", 0)
    old_sharpe = old_strategy.get("sharpe_ratio", 0)
    if new_sharpe > old_sharpe:
        advantages.append(f"夏普比率更高 ({new_sharpe:.2f} vs {old_sharpe:.2f})")

    new_lifespan = new_strategy.get("lifespan_months", 0)
    old_lifespan = old_strategy.get("lifespan_months", 0)
    if new_lifespan > old_lifespan:
        advantages.append(f"策略寿命更长 ({new_lifespan:.0f}月 vs {old_lifespan:.0f}月)")

    new_health = new_strategy.get("health_score", 0)
    old_health = old_strategy.get("health_score", 0)
    if new_health > old_health:
        advantages.append(f"健康度更好 ({new_health:.0f} vs {old_health:.0f})")

    if not advantages:
        advantages.append("策略风格更适合当前市场环境")

    return advantages


def _generate_cycle_adjustments(
    old_cycle: str,
    new_cycle: str,
    holdings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """生成周期切换的调整建议."""
    cycle_adjustments = {
        ("recovery", "expansion"): [
            {"action": "增配", "asset_class": "stock", "reason": "扩张期股票表现好"},
            {"action": "减配", "asset_class": "bond", "reason": "债券吸引力下降"},
        ],
        ("expansion", "peak"): [
            {"action": "减配", "asset_class": "stock", "reason": "顶部风险增加"},
            {"action": "增配", "asset_class": "commodity", "reason": "通胀受益"},
            {"action": "增配", "asset_class": "cash", "reason": "保留现金等待机会"},
        ],
        ("peak", "contraction"): [
            {"action": "大幅减配", "asset_class": "stock", "reason": "收缩期股票承压"},
            {"action": "增配", "asset_class": "bond", "reason": "债券避险"},
            {"action": "增配", "asset_class": "commodity", "reason": "黄金避险"},
        ],
        ("contraction", "recovery"): [
            {"action": "逐步增配", "asset_class": "stock", "reason": "复苏期布局股票"},
            {"action": "减配", "asset_class": "cash", "reason": "减少现金，增加风险资产"},
        ],
    }

    return cycle_adjustments.get(
        (old_cycle, new_cycle),
        [{"action": "关注", "reason": "市场周期变化，建议审视组合配置"}]
    )


def _estimate_rebalance_impact(
    adjustments: list[dict[str, Any]],
    portfolio: dict[str, Any],
) -> dict[str, Any]:
    """估算调仓影响."""
    total_value = portfolio.get("total_value", 0)
    trade_count = len([a for a in adjustments if a.get("symbol")])

    # 估算交易成本 (假设万3佣金)
    estimated_cost = total_value * 0.03 * trade_count / 100

    return {
        "estimated_trades": trade_count,
        "estimated_cost": round(estimated_cost, 2),
        "cost_rate": "0.03%",
        "note": "实际成本取决于券商佣金率",
    }
