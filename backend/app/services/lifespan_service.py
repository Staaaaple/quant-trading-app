"""Lifespan predictor: estimates strategy edge remaining lifetime."""

from typing import Any
from sqlalchemy.orm import Session

from app.models.strategy_dna import StrategyDNA, StrategyPhylogeny


def calculate_lifespan(
    metabolic_rate: float,
    niche_width: float,
    metabolic_syndrome: bool,
    homogeneity_risk: float,
) -> dict[str, Any]:
    """
    Predict strategy edge remaining lifespan in months.

    Factors:
    - Metabolic rate: higher = ages faster (needs fresher data)
    - Niche width: wider = more adaptable = longer life
    - Homogeneity risk: higher = crowded trade = shorter life
    - Metabolic syndrome: structural fragility = severe penalty
    """
    # Base lifespan from metabolic rate (higher rate = shorter life)
    base_lifespan = max(6, 60 - metabolic_rate * 120)

    # Niche width bonus (wider = up to +24 months)
    niche_bonus = niche_width * 24

    # Homogeneity penalty (crowded trade = up to -20 months)
    homogeneity_penalty = homogeneity_risk * 20

    raw_lifespan = base_lifespan + niche_bonus - homogeneity_penalty

    # Metabolic syndrome: severe structural fragility
    if metabolic_syndrome:
        raw_lifespan *= 0.6

    lifespan_months = max(1, round(raw_lifespan))

    # Lifespan phase
    if lifespan_months > 36:
        phase = "young"
        phase_label = "年轻"
    elif lifespan_months >= 12:
        phase = "mature"
        phase_label = "成熟"
    elif lifespan_months >= 3:
        phase = "aging"
        phase_label = "衰老"
    else:
        phase = "endangered"
        phase_label = "濒危"

    # Aging velocity: % of edge decay per month
    aging_velocity = round(metabolic_rate * 0.5 + homogeneity_risk * 0.3 + (0.1 if metabolic_syndrome else 0), 3)

    # Generate recommendations
    recommendations = _generate_recommendations(
        metabolic_rate, niche_width, metabolic_syndrome, homogeneity_risk, phase
    )

    return {
        "lifespan_months": lifespan_months,
        "lifespan_phase": phase,
        "lifespan_phase_label": phase_label,
        "aging_velocity": aging_velocity,
        "lifespan_recommendations": recommendations,
    }


def _generate_recommendations(
    metabolic_rate: float,
    niche_width: float,
    metabolic_syndrome: bool,
    homogeneity_risk: float,
    phase: str,
) -> list[str]:
    """Generate personalized lifespan recommendations."""
    recs = []

    if phase == "endangered":
        recs.append("策略处于濒危状态，建议立即审查核心逻辑")
    elif phase == "aging":
        recs.append("策略进入衰老期，考虑引入新的信号源或风控机制")

    if metabolic_rate > 0.2:
        recs.append("高频代谢策略需要更频繁的数据更新与参数调优")
    elif metabolic_rate < 0.05:
        recs.append("低频策略逻辑稳定，适合长期持有")

    if niche_width < 0.3:
        recs.append("生态位狭窄，建议扩展特征层以覆盖更多市场状态")

    if metabolic_syndrome:
        recs.append("存在代谢综合征：增加指标多样性、完善风控层")

    if homogeneity_risk > 0.6:
        recs.append("同质化压力高，策略 edge 容易被市场套利侵蚀")
    elif homogeneity_risk > 0.4:
        recs.append("注意同类策略竞争，考虑差异化改进")

    if not recs:
        recs.append("策略健康状况良好，继续保持")

    return recs


def compute_strategy_lifespan(db: Session, strategy_id: str) -> dict[str, Any] | None:
    """Compute lifespan for a single strategy and update DB record."""
    dna = db.query(StrategyDNA).filter(
        StrategyDNA.strategy_id == strategy_id,
        StrategyDNA.status == "success",
    ).first()
    if not dna:
        return None

    # Get homogeneity risk from phylogeny
    phylo = db.query(StrategyPhylogeny).filter(
        StrategyPhylogeny.strategy_id == strategy_id
    ).first()
    homogeneity_risk = phylo.homogeneity_risk if phylo else 0.0

    result = calculate_lifespan(
        metabolic_rate=dna.metabolic_rate or 0.0,
        niche_width=dna.niche_width or 0.0,
        metabolic_syndrome=dna.metabolic_syndrome or False,
        homogeneity_risk=homogeneity_risk,
    )

    # Update DNA record
    dna.lifespan_months = result["lifespan_months"]
    dna.lifespan_phase = result["lifespan_phase"]
    dna.aging_velocity = result["aging_velocity"]
    dna.lifespan_recommendations = result["lifespan_recommendations"]
    db.add(dna)
    db.commit()

    return result


def compute_all_lifespans(db: Session) -> int:
    """Compute lifespan for all strategies. Returns count updated."""
    dnas = db.query(StrategyDNA).filter(StrategyDNA.status == "success").all()
    count = 0
    for dna in dnas:
        phylo = db.query(StrategyPhylogeny).filter(
            StrategyPhylogeny.strategy_id == dna.strategy_id
        ).first()
        homogeneity_risk = phylo.homogeneity_risk if phylo else 0.0

        result = calculate_lifespan(
            metabolic_rate=dna.metabolic_rate or 0.0,
            niche_width=dna.niche_width or 0.0,
            metabolic_syndrome=dna.metabolic_syndrome or False,
            homogeneity_risk=homogeneity_risk,
        )

        dna.lifespan_months = result["lifespan_months"]
        dna.lifespan_phase = result["lifespan_phase"]
        dna.aging_velocity = result["aging_velocity"]
        dna.lifespan_recommendations = result["lifespan_recommendations"]
        db.add(dna)
        count += 1

    db.commit()
    return count
