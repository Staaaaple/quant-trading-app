"""建仓助手服务 — 分批建仓计划与金额计算.

Phase D: 全链路服务
根据组合配置 + 用户资金 → 生成可执行的分批建仓方案.
"""

import datetime
from typing import Any


def calculate_building_plan(
    total_capital: float,
    portfolio_config: dict[str, Any],
    risk_label: str = "稳健型",
    market_cycle: str = "recovery",
) -> dict[str, Any]:
    """计算分批建仓计划.

    Args:
        total_capital: 总资金（元）
        portfolio_config: 组合配置（含各标的权重）
        risk_label: 风险标签（保守/稳健/积极/激进）
        market_cycle: 市场周期

    Returns:
        完整的建仓计划
    """
    holdings = portfolio_config.get("holdings", [])
    if not holdings:
        return {"error": "组合配置为空"}

    # 根据风险等级和市场周期确定分批策略
    batch_strategy = _get_batch_strategy(risk_label, market_cycle)

    # 计算每批金额
    batches = []
    remaining_capital = total_capital

    for i, batch_pct in enumerate(batch_strategy["percentages"]):
        batch_amount = total_capital * batch_pct
        remaining_capital -= batch_amount

        # 计算该批每个标的的买入金额
        allocations = []
        for h in holdings:
            weight = h.get("weight", 0)
            symbol_amount = batch_amount * weight

            # 估算买入数量（简化，实际应根据实时价格）
            estimated_price = h.get("estimated_price", 1.0)
            estimated_quantity = int(symbol_amount / estimated_price) if estimated_price > 0 else 0

            allocations.append({
                "symbol": h.get("symbol", ""),
                "name": h.get("name", ""),
                "weight": weight,
                "amount": round(symbol_amount, 2),
                "estimated_price": estimated_price,
                "estimated_quantity": estimated_quantity,
                "asset_class": h.get("asset_class", "stock"),
            })

        # 按资产类别汇总
        class_summary = {}
        for a in allocations:
            ac = a["asset_class"]
            if ac not in class_summary:
                class_summary[ac] = {"amount": 0, "symbols": []}
            class_summary[ac]["amount"] += a["amount"]
            class_summary[ac]["symbols"].append(a["symbol"])

        batches.append({
            "batch_no": i + 1,
            "percentage": round(batch_pct * 100, 1),
            "amount": round(batch_amount, 2),
            "timing": _get_batch_timing(i, batch_strategy["interval_days"]),
            "allocations": allocations,
            "class_summary": class_summary,
            "focus": _get_batch_focus(i, holdings),
        })

    return {
        "total_capital": total_capital,
        "batch_count": len(batches),
        "interval_days": batch_strategy["interval_days"],
        "market_cycle": market_cycle,
        "risk_label": risk_label,
        "batches": batches,
        "summary": {
            "total_batches": len(batches),
            "first_batch_amount": batches[0]["amount"] if batches else 0,
            "first_batch_percentage": batches[0]["percentage"] if batches else 0,
            "estimated_completion_days": (len(batches) - 1) * batch_strategy["interval_days"],
        },
        "tips": _get_building_tips(risk_label, market_cycle),
    }


def calculate_single_batch(
    batch_no: int,
    total_capital: float,
    portfolio_config: dict[str, Any],
    risk_label: str = "稳健型",
) -> dict[str, Any]:
    """计算单批建仓的详细操作清单.

    返回每个标的的具体买入金额和预估数量.
    """
    plan = calculate_building_plan(total_capital, portfolio_config, risk_label)
    batches = plan.get("batches", [])

    if batch_no < 1 or batch_no > len(batches):
        return {"error": f"无效的批次号: {batch_no}"}

    batch = batches[batch_no - 1]

    # 生成操作清单
    operations = []
    for alloc in batch["allocations"]:
        operations.append({
            "symbol": alloc["symbol"],
            "name": alloc["name"],
            "action": "买入",
            "amount": alloc["amount"],
            "estimated_price": alloc["estimated_price"],
            "estimated_quantity": alloc["estimated_quantity"],
            "note": f"占该批资金的 {alloc['weight'] * 100:.1f}%",
        })

    return {
        "batch_no": batch_no,
        "total_amount": batch["amount"],
        "timing": batch["timing"],
        "operations": operations,
        "checklist": [
            "确认账户资金充足",
            "检查标的当前价格",
            "设置好买入价格（限价单）",
            "记录实际成交价格",
        ],
    }


def adjust_plan_for_market_change(
    original_plan: dict[str, Any],
    market_change_pct: float,
) -> dict[str, Any]:
    """根据市场变化调整建仓计划.

    当市场出现大幅波动时，建议调整建仓节奏.

    Args:
        original_plan: 原始建仓计划
        market_change_pct: 市场变化百分比（正数=上涨，负数=下跌）

    Returns:
        调整建议
    """
    suggestions = []

    if market_change_pct < -5:
        suggestions.append({
            "type": "speed_up",
            "title": "市场大跌，可适当加快建仓",
            "content": f"市场已下跌 {abs(market_change_pct):.1f}%，是较好的买入时机。建议将下一批建仓提前。",
            "action": "将下一批建仓提前 3-5 天",
        })
    elif market_change_pct < -3:
        suggestions.append({
            "type": "normal",
            "title": "市场小幅回调",
            "content": f"市场下跌 {abs(market_change_pct):.1f}%，可按原计划执行。",
            "action": "按原计划执行",
        })
    elif market_change_pct > 5:
        suggestions.append({
            "type": "slow_down",
            "title": "市场大涨，建议放缓建仓",
            "content": f"市场已上涨 {market_change_pct:.1f}%，短期可能过热。建议暂缓下一批建仓。",
            "action": "将下一批建仓延后 5-7 天，或等回调后再买入",
        })
    elif market_change_pct > 3:
        suggestions.append({
            "type": "caution",
            "title": "市场涨幅较大",
            "content": f"市场上涨 {market_change_pct:.1f}%，注意控制节奏。",
            "action": "可按原计划执行，但建议分批买入时适当降低价格",
        })
    else:
        suggestions.append({
            "type": "normal",
            "title": "市场平稳",
            "content": "市场波动不大，按原计划执行即可。",
            "action": "按原计划执行",
        })

    return {
        "market_change_pct": market_change_pct,
        "suggestions": suggestions,
        "original_plan": original_plan,
    }


def _get_batch_strategy(risk_label: str, market_cycle: str) -> dict[str, Any]:
    """根据风险等级和市场周期确定分批策略."""
    # 基础策略
    base_strategies = {
        "保守型": {
            "percentages": [0.25, 0.25, 0.25, 0.25],
            "interval_days": 14,
        },
        "稳健型": {
            "percentages": [0.40, 0.35, 0.25],
            "interval_days": 14,
        },
        "积极型": {
            "percentages": [0.50, 0.30, 0.20],
            "interval_days": 10,
        },
        "激进型": {
            "percentages": [0.60, 0.40],
            "interval_days": 7,
        },
    }

    strategy = base_strategies.get(risk_label, base_strategies["稳健型"]).copy()

    # 根据市场周期调整
    cycle_adjustments = {
        "expansion": {"interval_multiplier": 0.8},  # 扩张期加快
        "peak": {"interval_multiplier": 1.5},  # 顶部放缓
        "contraction": {"interval_multiplier": 2.0},  # 收缩期大幅放缓
        "recovery": {"interval_multiplier": 1.0},  # 复苏期正常
    }

    adjustment = cycle_adjustments.get(market_cycle, cycle_adjustments["recovery"])
    strategy["interval_days"] = int(strategy["interval_days"] * adjustment["interval_multiplier"])

    return strategy


def _get_batch_timing(batch_index: int, interval_days: int) -> str:
    """生成批次时间描述."""
    if batch_index == 0:
        return "本周执行"

    days = batch_index * interval_days
    if days < 30:
        return f"{days}天后"
    elif days < 60:
        weeks = days // 7
        return f"约{weeks}周后"
    else:
        months = days // 30
        return f"约{months}个月后"


def _get_batch_focus(batch_index: int, holdings: list[dict]) -> str:
    """确定每批建仓的重点."""
    if not holdings:
        return "按目标配置买入"

    sorted_h = sorted(holdings, key=lambda x: x.get("weight", 0), reverse=True)

    if batch_index == 0:
        # 第一批：核心仓位
        core = sorted_h[:2]
        names = [h.get("name", h.get("symbol", "")) for h in core]
        return f"建立核心仓位: {', '.join(names)}"
    elif batch_index == 1:
        # 第二批：卫星仓位
        sat = sorted_h[2:4] if len(sorted_h) > 2 else sorted_h[1:3]
        names = [h.get("name", h.get("symbol", "")) for h in sat]
        return f"配置卫星仓位: {', '.join(names)}"
    else:
        return "补齐剩余仓位"


def _get_building_tips(risk_label: str, market_cycle: str) -> list[str]:
    """获取建仓提示."""
    tips = [
        "使用限价单而非市价单，避免滑点",
        "每笔交易记录实际成交价格",
        "不要在开盘前30分钟和收盘前15分钟大额交易",
    ]

    if risk_label in ["保守型", "稳健型"]:
        tips.append("保守型投资者建议更严格地执行分批计划，不要因市场波动而改变节奏")

    if market_cycle == "peak":
        tips.append("当前处于市场顶部区域，建议更谨慎，可适当降低首批建仓比例")
    elif market_cycle == "contraction":
        tips.append("当前处于收缩期，市场可能继续下跌，建议放缓建仓节奏")
    elif market_cycle == "recovery":
        tips.append("当前处于复苏期，是较好的建仓时机，可按计划执行")

    return tips


def generate_operation_plan_record(
    user_id: int,
    portfolio_id: int,
    building_plan: dict[str, Any],
) -> dict[str, Any]:
    """生成建仓计划的数据库记录格式.

    用于保存到 OperationPlan 表.
    """
    return {
        "user_id": user_id,
        "portfolio_id": portfolio_id,
        "plan_type": "building",
        "total_capital": building_plan["total_capital"],
        "batch_count": building_plan["batch_count"],
        "interval_days": building_plan["interval_days"],
        "status": "active",
        "plan_detail": building_plan,
        "created_at": datetime.datetime.utcnow().isoformat(),
    }
