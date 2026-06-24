"""SAA引擎 — 战略资产配置.

基于用户画像风险等级 × 市场周期 → 资产类别权重.
"""

from typing import Any


# 风险等级映射
RISK_PROFILES = {
    "conservative": {
        "name": "保守型",
        "stock_max": 0.30,
        "bond_min": 0.50,
        "cash_min": 0.10,
    },
    "moderate": {
        "name": "稳健型",
        "stock_max": 0.50,
        "bond_min": 0.30,
        "cash_min": 0.05,
    },
    "aggressive": {
        "name": "积极型",
        "stock_max": 0.70,
        "bond_min": 0.15,
        "cash_min": 0.05,
    },
    "very_aggressive": {
        "name": "激进型",
        "stock_max": 0.90,
        "bond_min": 0.05,
        "cash_min": 0.02,
    },
}

# 市场周期 × 资产调整系数
MARKET_CYCLE_ADJUSTMENTS = {
    "expansion": {  # 扩张期
        "stock": 1.2,
        "bond": 0.8,
        "commodity": 1.1,
        "cash": 0.5,
    },
    "peak": {  # 顶部
        "stock": 0.9,
        "bond": 1.0,
        "commodity": 1.2,
        "cash": 1.3,
    },
    "contraction": {  # 收缩期
        "stock": 0.7,
        "bond": 1.2,
        "commodity": 0.8,
        "cash": 1.5,
    },
    "trough": {  # 底部
        "stock": 1.3,
        "bond": 0.9,
        "commodity": 0.9,
        "cash": 0.7,
    },
    "recovery": {  # 复苏期
        "stock": 1.15,
        "bond": 0.85,
        "commodity": 1.0,
        "cash": 0.6,
    },
}


def calculate_saa(
    risk_tolerance: str,
    market_cycle: str,
    macro_score: float = 0.5,
    geo_risk: float = 0.5,
) -> dict[str, Any]:
    """计算战略资产配置权重.

    Args:
        risk_tolerance: 风险承受等级 (conservative/moderate/aggressive/very_aggressive)
        market_cycle: 市场周期 (expansion/peak/contraction/trough/recovery)
        macro_score: 宏观评分 0-1
        geo_risk: 地缘政治风险 0-1

    Returns:
        {
            "weights": {"stock": 0.6, "bond": 0.25, "commodity": 0.1, "cash": 0.05},
            "rationale": "...",
            "risk_profile": {...},
            "cycle_adjustment": {...},
        }
    """
    # 获取基础配置
    profile = RISK_PROFILES.get(risk_tolerance, RISK_PROFILES["moderate"])
    adjustments = MARKET_CYCLE_ADJUSTMENTS.get(
        market_cycle, MARKET_CYCLE_ADJUSTMENTS["recovery"]
    )

    # 基础权重
    base_stock = profile["stock_max"]
    base_bond = profile["bond_min"]
    base_cash = profile["cash_min"]
    base_commodity = 1.0 - base_stock - base_bond - base_cash

    # 应用周期调整
    adjusted_stock = base_stock * adjustments["stock"]
    adjusted_bond = base_bond * adjustments["bond"]
    adjusted_commodity = base_commodity * adjustments["commodity"]
    adjusted_cash = base_cash * adjustments["cash"]

    # 地缘政治风险调整
    if geo_risk > 0.7:  # 高风险
        adjusted_stock *= 0.85
        adjusted_bond *= 1.1
        adjusted_cash *= 1.3
    elif geo_risk < 0.3:  # 低风险
        adjusted_stock *= 1.05
        adjusted_cash *= 0.9

    # 宏观评分微调
    if macro_score > 0.7:  # 宏观向好
        adjusted_stock *= 1.05
        adjusted_commodity *= 1.05
    elif macro_score < 0.3:  # 宏观向差
        adjusted_stock *= 0.95
        adjusted_bond *= 1.05

    # 归一化
    total = adjusted_stock + adjusted_bond + adjusted_commodity + adjusted_cash
    weights = {
        "stock": round(adjusted_stock / total, 4),
        "bond": round(adjusted_bond / total, 4),
        "commodity": round(adjusted_commodity / total, 4),
        "cash": round(adjusted_cash / total, 4),
    }

    # ── 强制满足风险画像硬约束 ──
    # 周期/宏观调整可能使股票超过上限或债券/现金低于下限，需二次修正
    stock_max = profile.get("stock_max", 0.90)
    bond_min = profile.get("bond_min", 0.05)
    cash_min = profile.get("cash_min", 0.03)

    # 股票上限截断
    if weights["stock"] > stock_max:
        excess = weights["stock"] - stock_max
        weights["stock"] = stock_max
        weights["bond"] += excess

    # 债券下限提升
    if weights["bond"] < bond_min:
        deficit = bond_min - weights["bond"]
        weights["bond"] = bond_min
        if weights["stock"] >= deficit:
            weights["stock"] -= deficit
        elif weights["commodity"] >= deficit:
            weights["commodity"] -= deficit
        else:
            weights["stock"] = 0
            weights["commodity"] = max(0, weights["commodity"] - (deficit - weights["stock"]))

    # 现金下限提升
    if weights["cash"] < cash_min:
        deficit = cash_min - weights["cash"]
        weights["cash"] = cash_min
        if weights["stock"] >= deficit:
            weights["stock"] -= deficit
        elif weights["commodity"] >= deficit:
            weights["commodity"] -= deficit
        else:
            weights["stock"] = 0
            weights["commodity"] = max(0, weights["commodity"] - (deficit - weights["stock"]))

    # 最终归一化（修正浮点误差）
    final_total = sum(weights.values())
    if final_total > 0 and abs(final_total - 1.0) > 0.001:
        for k in weights:
            weights[k] = round(weights[k] / final_total, 4)

    # 避免 cash 因浮点截断低于下限
    if weights["cash"] < cash_min:
        deficit = cash_min - weights["cash"]
        weights["cash"] = cash_min
        if weights["stock"] >= deficit:
            weights["stock"] -= deficit
        elif weights["commodity"] >= deficit:
            weights["commodity"] -= deficit

    # 生成理由
    rationale = _generate_rationale(
        risk_tolerance, market_cycle, weights, macro_score, geo_risk
    )

    return {
        "weights": weights,
        "rationale": rationale,
        "risk_profile": profile,
        "cycle_adjustment": adjustments,
        "macro_score": macro_score,
        "geo_risk": geo_risk,
    }


def _generate_rationale(
    risk_tolerance: str,
    market_cycle: str,
    weights: dict,
    macro_score: float,
    geo_risk: float,
) -> str:
    """生成配置理由."""
    risk_names = {
        "conservative": "保守型",
        "moderate": "稳健型",
        "aggressive": "积极型",
        "very_aggressive": "激进型",
    }
    cycle_names = {
        "expansion": "经济扩张期",
        "peak": "周期顶部",
        "contraction": "经济收缩期",
        "trough": "周期底部",
        "recovery": "复苏期",
    }

    parts = [
        f"基于您的{risk_names.get(risk_tolerance, '稳健型')}风险偏好，"
        f"结合当前{cycle_names.get(market_cycle, '复苏期')}市场环境："
    ]

    if weights["stock"] > 0.5:
        parts.append(f"股票配置{weights['stock']:.0%}，充分利用权益资产的增长潜力。")
    else:
        parts.append(f"股票配置{weights['stock']:.0%}，控制权益风险敞口。")

    if weights["bond"] > 0.3:
        parts.append(f"债券配置{weights['bond']:.0%}，提供稳定收益和下行保护。")

    if weights["cash"] > 0.1:
        parts.append(f"现金配置{weights['cash']:.0%}，保持流动性应对不确定性。")

    if geo_risk > 0.7:
        parts.append("地缘政治风险较高，适当提高防御性资产配置。")

    return " ".join(parts)


def get_risk_level_from_profile(profile_vector: dict) -> str:
    """从画像向量推断风险等级.

    Args:
        profile_vector: {
            "risk_tolerance": 0-1,
            "loss_aversion": 0-1,
            "time_horizon": 0-1,
            ...
        }

    Returns:
        risk_level: conservative/moderate/aggressive/very_aggressive
    """
    risk_tolerance = profile_vector.get("risk_tolerance", 0.5)
    loss_aversion = profile_vector.get("loss_aversion", 0.5)
    time_horizon = profile_vector.get("time_horizon", 0.5)

    # 综合评分
    # time_horizon可能是字符串，需要转换
    if isinstance(time_horizon, str):
        th_map = {"short": 0.2, "medium": 0.5, "long": 0.8}
        time_horizon = th_map.get(time_horizon, 0.5)
    score = risk_tolerance * 0.4 + (1 - loss_aversion) * 0.3 + time_horizon * 0.3

    if score < 0.25:
        return "conservative"
    elif score < 0.5:
        return "moderate"
    elif score < 0.75:
        return "aggressive"
    else:
        return "very_aggressive"


def get_market_cycle_from_signal(market_signal: dict) -> str:
    """从市场信号推断周期阶段.

    Args:
        market_signal: {
            "macro_score": 0-1,
            "industry_score": 0-1,
            "sentiment_score": 0-1,
            ...
        }

    Returns:
        cycle: expansion/peak/contraction/trough/recovery
    """
    macro = market_signal.get("macro_score", 0.5)
    industry = market_signal.get("industry_score", 0.5)
    sentiment = market_signal.get("sentiment_score", 0.5)

    # 综合评分
    composite = macro * 0.4 + industry * 0.3 + sentiment * 0.3

    # 判断周期
    if composite > 0.7 and sentiment > 0.6:
        return "expansion"
    elif composite > 0.7 and sentiment <= 0.6:
        return "peak"
    elif composite < 0.3 and sentiment < 0.4:
        return "contraction"
    elif composite < 0.3 and sentiment >= 0.4:
        return "trough"
    else:
        return "recovery"
