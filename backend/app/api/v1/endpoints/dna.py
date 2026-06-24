from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.dna import StrategyDNAResponse, StrategyDNASummary, StrategyPhylogenyResponse, GeneMatch, DNAPreviewRequest, DNAPreviewResponse
from app.services import dna_sequencer, phylogeny_service, ecosystem_service, lifespan_service

router = APIRouter()


@router.post("/dna/preview", response_model=DNAPreviewResponse)
def preview_dna(
    *,
    obj_in: DNAPreviewRequest,
):
    """Preview DNA sequencing result without saving to database."""
    result = dna_sequencer.preview_dna(obj_in.strategy_id, obj_in.code)
    return DNAPreviewResponse(**result)


@router.get("/strategies/{strategy_id}/dna", response_model=StrategyDNAResponse)
def get_strategy_dna(
    *,
    db: Session = Depends(get_db),
    strategy_id: str,
):
    """Get DNA sequencing result for a strategy."""
    dna = dna_sequencer.get_dna(db, strategy_id=strategy_id)
    if not dna:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"DNA not found for strategy '{strategy_id}'. Try saving the strategy first.",
        )
    return dna


@router.post("/strategies/{strategy_id}/dna/sequence", response_model=StrategyDNAResponse)
def run_dna_sequencing(
    *,
    db: Session = Depends(get_db),
    strategy_id: str,
):
    """Manually trigger DNA sequencing for a strategy."""
    from app.models.strategy import Strategy
    strategy = db.query(Strategy).filter(Strategy.strategy_id == strategy_id).first()
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Strategy '{strategy_id}' not found.",
        )
    dna = dna_sequencer.sequence_strategy(strategy_id, strategy.code, db)
    return dna


@router.get("/strategies/{strategy_id}/dna/summary", response_model=StrategyDNASummary)
def get_dna_summary(
    *,
    db: Session = Depends(get_db),
    strategy_id: str,
):
    """Get a lightweight DNA summary for the editor panel."""
    from app.models.strategy import Strategy
    from app.models.strategy_dna import StrategyPhylogeny
    strategy = db.query(Strategy).filter(Strategy.strategy_id == strategy_id).first()
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Strategy '{strategy_id}' not found.",
        )
    dna = dna_sequencer.get_dna(db, strategy_id=strategy_id)
    if not dna:
        # Auto-sequence if not exists
        dna = dna_sequencer.sequence_strategy(strategy_id, strategy.code, db)

    phylo = db.query(StrategyPhylogeny).filter(
        StrategyPhylogeny.strategy_id == strategy_id
    ).first()

    return StrategyDNASummary(
        strategy_id=strategy_id,
        name=strategy.name,
        gene_diversity_score=dna.gene_diversity_score,
        health_birth_score=dna.health_birth_score,
        feature_genes=dna.feature_genes,
        signal_genes=dna.signal_genes,
        status=dna.status,
        family_id=dna.family_id,
        family_name=dna.family_name,
        metabolic_rate=dna.metabolic_rate,
        niche_width=dna.niche_width,
        inbreeding_warning=phylo.inbreeding_warning if phylo else False,
        homogeneity_risk=phylo.homogeneity_risk if phylo else 0.0,
        lifespan_months=dna.lifespan_months,
    )


@router.get("/dna/ecosystem")
def get_ecosystem_overview(
    *,
    db: Session = Depends(get_db),
):
    """Get aggregated ecosystem dashboard data."""
    return ecosystem_service.get_ecosystem_overview(db)


@router.get("/dna/list", response_model=list[StrategyDNASummary])
def list_all_dna(
    *,
    db: Session = Depends(get_db),
):
    """List all DNA summaries for the ecosystem dashboard."""
    from app.services.portfolio_ecosystem_adapter import ensure_ecosystem_data_from_latest_portfolios
    from app.models.strategy_dna import StrategyDNA

    # 如果没有 DNA 数据，尝试从已有组合中自动迁移
    if db.query(StrategyDNA).filter(StrategyDNA.status == "success").count() == 0:
        try:
            ensure_ecosystem_data_from_latest_portfolios(db)
        except Exception as e:
            print(f"[DNA API] 自动接入组合数据失败: {e}")
            db.rollback()

    from app.models.strategy import Strategy
    from app.models.strategy_dna import StrategyPhylogeny
    dnas = dna_sequencer.get_all_dnas(db)
    result = []
    for dna in dnas:
        strategy = db.query(Strategy).filter(Strategy.strategy_id == dna.strategy_id).first()
        phylo = db.query(StrategyPhylogeny).filter(
            StrategyPhylogeny.strategy_id == dna.strategy_id
        ).first()
        result.append(StrategyDNASummary(
            strategy_id=dna.strategy_id,
            name=strategy.name if strategy else dna.strategy_id,
            gene_diversity_score=dna.gene_diversity_score,
            health_birth_score=dna.health_birth_score,
            feature_genes=dna.feature_genes,
            signal_genes=dna.signal_genes,
            status=dna.status,
            family_id=dna.family_id,
            family_name=dna.family_name,
            metabolic_rate=dna.metabolic_rate,
            niche_width=dna.niche_width,
            inbreeding_warning=phylo.inbreeding_warning if phylo else False,
            homogeneity_risk=phylo.homogeneity_risk if phylo else 0.0,
            lifespan_months=dna.lifespan_months,
        ))
    return result


@router.get("/strategies/{strategy_id}/phylogeny", response_model=StrategyPhylogenyResponse)
def get_strategy_phylogeny(
    *,
    db: Session = Depends(get_db),
    strategy_id: str,
):
    """Get phylogeny (relatives, family, inbreeding risk) for a strategy."""
    phylo = phylogeny_service.get_phylogeny(db, strategy_id)
    if not phylo:
        # Auto-compute if missing
        phylogeny_service.compute_all_phylogeny(db)
        phylo = phylogeny_service.get_phylogeny(db, strategy_id)
    if not phylo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Phylogeny not found for strategy '{strategy_id}'.",
        )
    return StrategyPhylogenyResponse(
        strategy_id=phylo.strategy_id,
        family_id=phylo.family_id,
        family_name=phylo.family_name,
        relatives=[GeneMatch(**r) for r in (phylo.relatives or [])],
        homogeneity_risk=phylo.homogeneity_risk,
        inbreeding_warning=phylo.inbreeding_warning,
    )


@router.post("/dna/phylogeny/compute")
def compute_all_phylogeny(
    *,
    db: Session = Depends(get_db),
):
    """Manually trigger full phylogeny recomputation for all strategies."""
    phylogeny_service.compute_all_phylogeny(db)
    return {"status": "ok", "message": "Phylogeny recomputed for all strategies"}


@router.get("/strategies/{strategy_id}/lifespan")
def get_strategy_lifespan(
    *,
    db: Session = Depends(get_db),
    strategy_id: str,
):
    """Get lifespan prediction for a strategy."""
    dna = dna_sequencer.get_dna(db, strategy_id=strategy_id)
    if not dna:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"DNA not found for strategy '{strategy_id}'.",
        )
    # Ensure lifespan is computed
    if not dna.lifespan_months:
        lifespan_service.compute_strategy_lifespan(db, strategy_id)
        db.refresh(dna)

    return {
        "strategy_id": strategy_id,
        "lifespan_months": dna.lifespan_months,
        "lifespan_phase": dna.lifespan_phase,
        "lifespan_phase_label": {
            "young": "年轻",
            "mature": "成熟",
            "aging": "衰老",
            "endangered": "濒危",
        }.get(dna.lifespan_phase, "成熟"),
        "aging_velocity": dna.aging_velocity,
        "lifespan_recommendations": dna.lifespan_recommendations or [],
    }


@router.post("/dna/lifespan/compute")
def compute_all_lifespans(
    *,
    db: Session = Depends(get_db),
):
    """Manually trigger lifespan recomputation for all strategies."""
    count = lifespan_service.compute_all_lifespans(db)
    return {"status": "ok", "message": f"Lifespan recomputed for {count} strategies"}


@router.get("/dna/families", response_model=list[dict])
def list_families(
    *,
    db: Session = Depends(get_db),
):
    """List all strategy families with member counts."""
    from sqlalchemy import func
    rows = (
        db.query(StrategyDNA.family_id, StrategyDNA.family_name, func.count(StrategyDNA.id))
        .filter(StrategyDNA.status == "success")
        .group_by(StrategyDNA.family_id, StrategyDNA.family_name)
        .all()
    )
    return [
        {
            "family_id": r[0] or "other",
            "family_name": r[1] or "其他",
            "count": r[2],
        }
        for r in rows
    ]
