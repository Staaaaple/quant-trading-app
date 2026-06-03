"""TAA引擎 — 战术资产配置.

基于行业景气度 × 社会趋势 → 细分权重调整.
"""

from typing import Any


# 行业配置基准（基于SAA的股票部分）
SECTOR_BASE_WEIGHTS = {
    "technology": 0.20,    # 科技
    "finance": 0.15,       # 金融
    "healthcare": 0.12,    # 医药
    "consumer": 0.15,      # 消费
    "energy": 0.08,        # 能源
    "materials": 0.08,     # 材料
    "industrials": 0.12,   # 工业
    "utilities": 0.05,     # 公用事业
    "real_estate": 0.05,   # 房地产
}

# 行业景气度调整系数
INDUSTRY_CYCLE_MULTIPLIERS = {
    "technology": {
        "expansion": 1.3, "peak": 1.1, "contraction": 0.7,
        "trough": 0.8, "recovery": 1.2,
    },
    "finance": {
        "expansion": 1.2, "peak": 1.0, "contraction": 0.8,
        "trough": 0.9, "recovery": 1.1,
    },
    "healthcare": {
        "expansion": 1.1, "peak": 1.0, "contraction": 1.0,
        "trough": 1.1, "recovery": 1.1,
    },
    "consumer": {
        "expansion": 1.2, "peak": 1.1, "contraction": 0.8,
        "trough": 0.9, "recovery": 1.15,
    },
    "energy": {
        "expansion": 1.0, "peak": 1.2, "contraction": 0.9,
        "trough": 1.0, "recovery": 1.0,
    },
    "materials": {
        "expansion": 1.1, "peak": 1.1, "contraction": 0.8,
        "trough": 0.9, "recovery": 1.1,
    },
    "industrials": {
        "expansion": 1.2, "peak": 1.0, "contraction": 0.7,
        "trough": 0.8, "recovery": 1.2,
    },
    "utilities": {
        "expansion": 0.9, "peak": 0.9, "contraction": 1.2,
        "trough": 1.1, "recovery": 1.0,
    },
    "real_estate": {
        "expansion": 1.1, "peak": 1.0, "contraction": 0.7,
        "trough": 0.8, "recovery": 1.1,
    },
}

# 社会趋势影响
SOCIAL_TREND_IMPACT = {
    "ai_revolution": {        # AI革命
        "technology": 1.3,
        "healthcare": 1.1,
        "finance": 1.05,
    },
    "aging_society": {        # 老龄化
        "healthcare": 1.25,
        "consumer": 0.95,
        "technology": 1.05,
    },
    "green_energy": {         # 新能源
        "energy": 1.2,
        "materials": 1.1,
        "industrials": 1.05,
    },
    "consumption_upgrade": {  # 消费升级
        "consumer": 1.2,
        "technology": 1.1,
        "healthcare": 1.05,
    },
    "digital_transformation": {  # 数字化转型
        "technology": 1.25,
        "finance": 1.15,
        "industrials": 1.1,
    },
}


def calculate_taa(
    saa_weights: dict[str, float],
    market_cycle: str,
    industry_scores: dict[str, float],
    social_trends: list[str],
    market_signal: dict | None = None,
) -> dict[str, Any]:
    """计算战术资产配置权重.

    Args:
        saa_weights: SAA输出的资产类别权重
        market_cycle: 市场周期
        industry_scores: 各行业景气度评分 {sector: 0-1}
        social_trends: 活跃社会趋势列表
        market_signal: 完整市场信号（可选）

    Returns:
        {
            "sector_weights": {"technology": 0.25, "finance": 0.12, ...},
            "adjustments": {...},
            "rationale": "...",
        }
    """
    stock_weight = saa_weights.get("stock", 0.6)

    # 基础行业权重
    base_weights = {
        sector: weight * stock_weight
        for sector, weight in SECTOR_BASE_WEIGHTS.items()
    }

    # 应用周期调整
    adjusted_weights = {}
    for sector, weight in base_weights.items():
        cycle_mult = INDUSTRY_CYCLE_MULTIPLIERS.get(sector, {}).get(market_cycle, 1.0)
        adjusted_weights[sector] = weight * cycle_mult

    # 应用行业景气度
    for sector, score in industry_scores.items():
        if sector in adjusted_weights:
            # 景气度评分 0-1，0.5为中性
            adjustment = 1.0 + (score - 0.5) * 0.4
            adjusted_weights[sector] *= adjustment

    # 应用社会趋势
    for trend in social_trends:
        impact = SOCIAL_TREND_IMPACT.get(trend, {})
        for sector, mult in impact.items():
            if sector in adjusted_weights:
                adjusted_weights[sector] *= mult

    # 归一化（确保总和等于股票权重）
    total = sum(adjusted_weights.values())
    if total > 0:
        normalized = {
            sector: round(weight / total * stock_weight, 4)
            for sector, weight in adjusted_weights.items()
        }
    else:
        normalized = base_weights

    # 生成调整说明
    adjustments = _calculate_adjustments(base_weights, normalized)

    # 生成理由
    rationale = _generate_taa_rationale(
        market_cycle, industry_scores, social_trends, adjustments
    )

    return {
        "sector_weights": normalized,
        "adjustments": adjustments,
        "rationale": rationale,
        "stock_weight": stock_weight,
    }


def _calculate_adjustments(
    base: dict[str, float],
    adjusted: dict[str, float],
) -> dict[str, float]:
    """计算各行业的调整幅度."""
    adjustments = {}
    for sector in base:
        if base[sector] > 0:
            change = (adjusted.get(sector, 0) - base[sector]) / base[sector]
            adjustments[sector] = round(change, 4)
    return adjustments


def _generate_taa_rationale(
    market_cycle: str,
    industry_scores: dict[str, float],
    social_trends: list[str],
    adjustments: dict[str, float],
) -> str:
    """生成TAA调整理由."""
    cycle_names = {
        "expansion": "扩张期",
        "peak": "顶部",
        "contraction": "收缩期",
        "trough": "底部",
        "recovery": "复苏期",
    }

    parts = [f"当前处于{cycle_names.get(market_cycle, '复苏期')}，行业配置调整如下："]

    # 找出调整最大的3个行业
    sorted_adjustments = sorted(
        adjustments.items(),
        key=lambda x: abs(x[1]),
        reverse=True,
    )[:3]

    for sector, change in sorted_adjustments:
        sector_names = {
            "technology": "科技",
            "finance": "金融",
            "healthcare": "医药",
            "consumer": "消费",
            "energy": "能源",
            "materials": "材料",
            "industrials": "工业",
            "utilities": "公用事业",
            "real_estate": "房地产",
        }
        name = sector_names.get(sector, sector)
        if change > 0.1:
            parts.append(f"{name}超配{change:.0%}（景气度上行）")
        elif change < -0.1:
            parts.append(f"{name}低配{abs(change):.0%}（防御性调整）")

    # 社会趋势
    if social_trends:
        trend_names = {
            "ai_revolution": "AI革命",
            "aging_society": "老龄化",
            "green_energy": "新能源",
            "consumption_upgrade": "消费升级",
            "digital_transformation": "数字化",
        }
        trend_str = "、".join([trend_names.get(t, t) for t in social_trends[:2]])
        parts.append(f"考虑{trend_str}趋势影响。")

    return " ".join(parts)


def get_top_sectors(
    taa_result: dict,
    n: int = 3,
) -> list[dict]:
    """获取权重最高的N个行业.

    Returns:
        [{"sector": "technology", "weight": 0.25, "name": "科技"}, ...]
    """
    sector_names = {
        "technology": "科技",
        "finance": "金融",
        "healthcare": "医药",
        "consumer": "消费",
        "energy": "能源",
        "materials": "材料",
        "industrials": "工业",
        "utilities": "公用事业",
        "real_estate": "房地产",
    }

    weights = taa_result.get("sector_weights", {})
    sorted_sectors = sorted(
        weights.items(),
        key=lambda x: x[1],
        reverse=True,
    )[:n]

    return [
        {
            "sector": sector,
            "weight": weight,
            "name": sector_names.get(sector, sector),
        }
        for sector, weight in sorted_sectors
    ]
