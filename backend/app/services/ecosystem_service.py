"""Ecosystem dashboard aggregation service."""

from sqlalchemy.orm import Session
from sqlalchemy import func, Integer

from app.models.strategy_dna import StrategyDNA, StrategyPhylogeny
from app.models.strategy import Strategy
from app.services.portfolio_ecosystem_adapter import (
    ensure_ecosystem_data_from_latest_portfolios,
    ensure_reference_strategies,
)


def get_ecosystem_overview(db: Session) -> dict:
    """Aggregate all ecosystem data for the dashboard."""
    # 如果没有任何 DNA 数据，尝试从已有组合中迁移
    dna_count = db.query(StrategyDNA).filter(StrategyDNA.status == "success").count()
    if dna_count == 0:
        try:
            ensure_ecosystem_data_from_latest_portfolios(db)
        except Exception as e:
            print(f"[EcosystemService] 自动接入组合数据失败: {e}")
            db.rollback()

    # 确保常见参考策略存在，用于丰富关系网络
    try:
        ensure_reference_strategies(db)
    except Exception as e:
        print(f"[EcosystemService] 确保参考策略失败: {e}")
        db.rollback()

    # Basic counts
    total = db.query(StrategyDNA).filter(StrategyDNA.status == "success").count()

    # Family distribution
    family_rows = (
        db.query(StrategyDNA.family_name, func.count(StrategyDNA.id))
        .filter(StrategyDNA.status == "success", StrategyDNA.family_name.isnot(None))
        .group_by(StrategyDNA.family_name)
        .all()
    )
    family_distribution = [
        {"name": r[0], "count": r[1]} for r in family_rows
    ]

    # Health stats
    health_rows = db.query(
        func.avg(StrategyDNA.health_birth_score),
        func.min(StrategyDNA.health_birth_score),
        func.max(StrategyDNA.health_birth_score),
    ).filter(StrategyDNA.status == "success").first()

    avg_health = round(health_rows[0] or 0, 1)
    min_health = round(health_rows[1] or 0, 1)
    max_health = round(health_rows[2] or 0, 1)

    # Health distribution buckets
    health_buckets = {"优秀(80+)": 0, "良好(60-80)": 0, "需关注(<60)": 0}
    all_health = (
        db.query(StrategyDNA.health_birth_score)
        .filter(StrategyDNA.status == "success")
        .all()
    )
    for h in all_health:
        score = h[0]
        if score >= 80:
            health_buckets["优秀(80+)"] += 1
        elif score >= 60:
            health_buckets["良好(60-80)"] += 1
        else:
            health_buckets["需关注(<60)"] += 1

    # Inbreeding risk count
    inbreeding_count = (
        db.query(StrategyPhylogeny)
        .filter(StrategyPhylogeny.inbreeding_warning == True)
        .count()
    )

    # Diversity stats
    diversity_rows = db.query(
        func.avg(StrategyDNA.gene_diversity_score),
    ).filter(StrategyDNA.status == "success").first()
    avg_diversity = round((diversity_rows[0] or 0) * 100, 1)

    # Metabolic stats
    metabolic_rows = db.query(
        func.avg(StrategyDNA.metabolic_rate),
        func.avg(StrategyDNA.niche_width),
        func.sum(StrategyDNA.metabolic_syndrome.cast(Integer)),
    ).filter(StrategyDNA.status == "success").first()
    avg_metabolic_rate = round(metabolic_rows[0] or 0, 3)
    avg_niche_width = round(metabolic_rows[1] or 0, 3)
    syndrome_count = int(metabolic_rows[2] or 0)

    # High metabolic rate strategies (need attention)
    high_metabolic = (
        db.query(StrategyDNA)
        .filter(StrategyDNA.status == "success", StrategyDNA.metabolic_rate > 0.2)
        .order_by(StrategyDNA.metabolic_rate.desc())
        .limit(5)
        .all()
    )
    high_metabolic_strategies = []
    for dna in high_metabolic:
        strategy = db.query(Strategy).filter(Strategy.strategy_id == dna.strategy_id).first()
        high_metabolic_strategies.append({
            "strategy_id": dna.strategy_id,
            "name": strategy.name if strategy else dna.strategy_id,
            "metabolic_rate": dna.metabolic_rate,
            "niche_width": dna.niche_width,
            "metabolic_syndrome": dna.metabolic_syndrome,
            "family_name": dna.family_name,
        })

    # Low health strategies (need attention)
    low_health = (
        db.query(StrategyDNA)
        .filter(StrategyDNA.status == "success", StrategyDNA.health_birth_score < 60)
        .order_by(StrategyDNA.health_birth_score.asc())
        .limit(5)
        .all()
    )
    low_health_strategies = []
    for dna in low_health:
        strategy = db.query(Strategy).filter(Strategy.strategy_id == dna.strategy_id).first()
        low_health_strategies.append({
            "strategy_id": dna.strategy_id,
            "name": strategy.name if strategy else dna.strategy_id,
            "health_birth_score": dna.health_birth_score,
            "gene_diversity_score": dna.gene_diversity_score,
            "family_name": dna.family_name,
        })

    # Recent strategies (by sequenced_at)
    recent = (
        db.query(StrategyDNA)
        .filter(StrategyDNA.status == "success")
        .order_by(StrategyDNA.sequenced_at.desc())
        .limit(5)
        .all()
    )
    recent_strategies = []
    for dna in recent:
        strategy = db.query(Strategy).filter(Strategy.strategy_id == dna.strategy_id).first()
        recent_strategies.append({
            "strategy_id": dna.strategy_id,
            "name": strategy.name if strategy else dna.strategy_id,
            "health_birth_score": dna.health_birth_score,
            "gene_diversity_score": dna.gene_diversity_score,
            "family_name": dna.family_name,
        })

    # Lifespan stats (Phase 3)
    lifespan_rows = db.query(
        func.avg(StrategyDNA.lifespan_months),
        func.min(StrategyDNA.lifespan_months),
        func.max(StrategyDNA.lifespan_months),
    ).filter(StrategyDNA.status == "success").first()
    avg_lifespan = round(lifespan_rows[0] or 0, 1)

    lifespan_distribution = {"年轻(36+)": 0, "成熟(12-36)": 0, "衰老(3-12)": 0, "濒危(<3)": 0}
    all_lifespan = (
        db.query(StrategyDNA.lifespan_months)
        .filter(StrategyDNA.status == "success")
        .all()
    )
    for ls in all_lifespan:
        m = ls[0] or 0
        if m > 36:
            lifespan_distribution["年轻(36+)"] += 1
        elif m >= 12:
            lifespan_distribution["成熟(12-36)"] += 1
        elif m >= 3:
            lifespan_distribution["衰老(3-12)"] += 1
        else:
            lifespan_distribution["濒危(<3)"] += 1

    endangered_count = (
        db.query(StrategyDNA)
        .filter(StrategyDNA.status == "success", StrategyDNA.lifespan_months < 3)
        .count()
    )

    # Short lifespan strategies (need attention)
    short_lifespan = (
        db.query(StrategyDNA)
        .filter(StrategyDNA.status == "success", StrategyDNA.lifespan_months < 12)
        .order_by(StrategyDNA.lifespan_months.asc())
        .limit(5)
        .all()
    )
    short_lifespan_strategies = []
    for dna in short_lifespan:
        strategy = db.query(Strategy).filter(Strategy.strategy_id == dna.strategy_id).first()
        short_lifespan_strategies.append({
            "strategy_id": dna.strategy_id,
            "name": strategy.name if strategy else dna.strategy_id,
            "lifespan_months": dna.lifespan_months,
            "lifespan_phase": dna.lifespan_phase,
            "aging_velocity": dna.aging_velocity,
            "family_name": dna.family_name,
        })

    # Metabolic ranking (all strategies sorted by metabolic rate)
    all_metabolic = (
        db.query(StrategyDNA)
        .filter(StrategyDNA.status == "success")
        .order_by(StrategyDNA.metabolic_rate.desc())
        .all()
    )
    metabolic_ranking = []
    for dna in all_metabolic:
        strategy = db.query(Strategy).filter(Strategy.strategy_id == dna.strategy_id).first()
        metabolic_ranking.append({
            "strategy_id": dna.strategy_id,
            "name": strategy.name if strategy else dna.strategy_id,
            "metabolic_rate": dna.metabolic_rate,
            "niche_width": dna.niche_width,
            "family_name": dna.family_name,
        })

    # Family radar data (competition dimensions per family)
    family_radar = []
    radar_indicators = [
        {"name": "健康度", "max": 100},
        {"name": "多样性", "max": 100},
        {"name": "代谢稳定性", "max": 1},
        {"name": "生态位宽度", "max": 1},
        {"name": "差异化", "max": 1},
    ]
    for family in family_distribution:
        family_name = family["name"]
        members = db.query(StrategyDNA).filter(
            StrategyDNA.status == "success",
            StrategyDNA.family_name == family_name,
        ).all()
        if not members:
            continue
        total_hr = 0
        valid_hr = 0
        for m in members:
            phylo = db.query(StrategyPhylogeny).filter(
                StrategyPhylogeny.strategy_id == m.strategy_id
            ).first()
            if phylo:
                total_hr += phylo.homogeneity_risk
                valid_hr += 1
        avg_homogeneity = total_hr / valid_hr if valid_hr > 0 else 0
        avg_health = sum(m.health_birth_score for m in members) / len(members)
        avg_diversity = sum(m.gene_diversity_score for m in members) / len(members)
        avg_metabolic = sum(m.metabolic_rate for m in members) / len(members)
        avg_niche = sum(m.niche_width for m in members) / len(members)
        family_radar.append({
            "name": family_name,
            "value": [
                round(avg_health, 1),
                round(avg_diversity * 100, 1),
                round(1 - avg_metabolic, 3),
                round(avg_niche, 3),
                round(1 - avg_homogeneity, 3),
            ],
        })

    # Family network (force-directed graph data)
    family_network = {"nodes": [], "links": []}
    all_dnas = db.query(StrategyDNA).filter(StrategyDNA.status == "success").all()
    all_phylos = db.query(StrategyPhylogeny).all()
    phylo_map = {p.strategy_id: p for p in all_phylos}

    for dna in all_dnas:
        strategy = db.query(Strategy).filter(Strategy.strategy_id == dna.strategy_id).first()
        family_network["nodes"].append({
            "id": dna.strategy_id,
            "name": strategy.name if strategy else dna.strategy_id,
            "family": dna.family_name or "其他",
            "family_id": dna.family_id or "other",
            "health": dna.health_birth_score,
            "lifespan": dna.lifespan_months,
            "metabolic_rate": dna.metabolic_rate,
            "value": dna.health_birth_score,
            "symbolSize": 12 + dna.health_birth_score / 8,
        })

    seen_links = set()
    for phylo in all_phylos:
        if phylo.relatives:
            for rel in phylo.relatives:
                if rel["similarity"] > 0.5:
                    # Undirected link, avoid duplicates
                    pair = tuple(sorted([phylo.strategy_id, rel["strategy_id"]]))
                    if pair not in seen_links:
                        seen_links.add(pair)
                        family_network["links"].append({
                            "source": phylo.strategy_id,
                            "target": rel["strategy_id"],
                            "value": rel["similarity"],
                        })

    return {
        "total_strategies": total,
        "family_count": len(family_distribution),
        "avg_health_score": avg_health,
        "min_health_score": min_health,
        "max_health_score": max_health,
        "avg_diversity": avg_diversity,
        "inbreeding_risk_count": inbreeding_count,
        "family_distribution": family_distribution,
        "health_distribution": health_buckets,
        "low_health_strategies": low_health_strategies,
        "recent_strategies": recent_strategies,
        "avg_metabolic_rate": avg_metabolic_rate,
        "avg_niche_width": avg_niche_width,
        "syndrome_count": syndrome_count,
        "high_metabolic_strategies": high_metabolic_strategies,
        "avg_lifespan": avg_lifespan,
        "lifespan_distribution": lifespan_distribution,
        "endangered_count": endangered_count,
        "short_lifespan_strategies": short_lifespan_strategies,
        "metabolic_ranking": metabolic_ranking,
        "family_radar": family_radar,
        "radar_indicators": radar_indicators,
        "family_network": family_network,
    }
