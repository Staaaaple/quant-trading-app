"""Phylogeny engine: computes similarity, family clustering, and inbreeding risk."""

import math
from sqlalchemy.orm import Session

from app.models.strategy_dna import StrategyDNA, StrategyPhylogeny
from app.models.strategy import Strategy


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return round(dot / (norm_a * norm_b), 4)


# Family naming from seed strategies
_FAMILY_MAP = {
    "dual_ma": "趋势跟踪家族",
    "triple": "趋势跟踪家族",
    "macd": "趋势跟踪家族",
    "breakout": "趋势跟踪家族",
    "ema": "趋势跟踪家族",
    "rsi": "动量家族",
    "kdj": "动量家族",
    "volume": "动量家族",
    "momentum_20d": "动量家族",
    "boll": "均值回归家族",
    "volatility": "均值回归家族",
    "pe_pb": "多因子家族",
    "roe": "多因子家族",
    "small": "多因子家族",
    "momentum_value": "多因子家族",
    "atr": "风控增强家族",
    "position": "风控增强家族",
    "dynamic": "风控增强家族",
}


def _detect_family(strategy_id: str) -> tuple[str, str]:
    """Return (family_id, family_name) based on strategy_id patterns."""
    sid = strategy_id.lower()
    for key, family_name in _FAMILY_MAP.items():
        if key in sid:
            family_id = family_name.replace("家族", "")
            return family_id, family_name
    if sid == "builtin_weekly_picker":
        return "builtin", "系统内置"
    return "other", "其他"


def compute_all_phylogeny(db: Session) -> None:
    """Compute similarity matrix and update all phylogeny records."""
    dnas = db.query(StrategyDNA).filter(StrategyDNA.status == "success").all()
    if len(dnas) < 2:
        return

    # Build ID -> index map
    id_to_idx = {d.strategy_id: i for i, d in enumerate(dnas)}

    # Compute similarity matrix
    n = len(dnas)
    sim_matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        sim_matrix[i][i] = 1.0
        for j in range(i + 1, n):
            vec_i = dnas[i].gene_vector or []
            vec_j = dnas[j].gene_vector or []
            sim = _cosine_similarity(vec_i, vec_j)
            sim_matrix[i][j] = sim
            sim_matrix[j][i] = sim

    # For each strategy, compute relatives and family
    for i, dna in enumerate(dnas):
        # Get top 5 relatives (excluding self)
        relatives_idx = sorted(
            [j for j in range(n) if j != i],
            key=lambda j: sim_matrix[i][j],
            reverse=True,
        )[:5]

        relatives = []
        for j in relatives_idx:
            rel_strategy = db.query(Strategy).filter(Strategy.strategy_id == dnas[j].strategy_id).first()
            relatives.append({
                "strategy_id": dnas[j].strategy_id,
                "name": rel_strategy.name if rel_strategy else dnas[j].strategy_id,
                "similarity": sim_matrix[i][j],
            })

        # Compute average similarity with relatives = homogeneity risk
        if relatives:
            avg_sim = sum(r["similarity"] for r in relatives) / len(relatives)
        else:
            avg_sim = 0.0

        # Detect family
        family_id, family_name = _detect_family(dna.strategy_id)

        # Update DNA record with family info
        dna.family_id = family_id
        dna.family_name = family_name
        db.add(dna)

        # Upsert phylogeny record
        phylo = db.query(StrategyPhylogeny).filter(StrategyPhylogeny.strategy_id == dna.strategy_id).first()
        if phylo:
            phylo.family_id = family_id
            phylo.family_name = family_name
            phylo.relatives = relatives
            phylo.homogeneity_risk = round(avg_sim, 4)
            phylo.inbreeding_warning = avg_sim > 0.75
        else:
            phylo = StrategyPhylogeny(
                strategy_id=dna.strategy_id,
                family_id=family_id,
                family_name=family_name,
                relatives=relatives,
                homogeneity_risk=round(avg_sim, 4),
                inbreeding_warning=avg_sim > 0.75,
            )
            db.add(phylo)

    db.commit()


def get_phylogeny(db: Session, strategy_id: str) -> StrategyPhylogeny | None:
    return db.query(StrategyPhylogeny).filter(StrategyPhylogeny.strategy_id == strategy_id).first()


def get_family_members(db: Session, family_id: str) -> list[StrategyDNA]:
    return db.query(StrategyDNA).filter(
        StrategyDNA.family_id == family_id,
        StrategyDNA.status == "success",
    ).all()
