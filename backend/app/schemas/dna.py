from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional


class GeneProfile(BaseModel):
    feature_genes: List[str]
    signal_genes: List[str]
    risk_genes: List[str]
    execution_genes: List[str]


class StrategyDNAResponse(BaseModel):
    strategy_id: str
    feature_genes: List[str]
    signal_genes: List[str]
    risk_genes: List[str]
    execution_genes: List[str]
    gene_diversity_score: float
    health_birth_score: float
    inbreeding_coefficient: float
    family_id: Optional[str]
    family_name: Optional[str]
    sequence_version: str
    sequenced_at: datetime
    status: str
    error_message: Optional[str]

    # Metabolic profiling (Phase 2)
    metabolic_rate: float = 0.0
    niche_width: float = 0.0
    metabolic_syndrome: bool = False
    metabolic_markers: List[str] = []

    # Lifespan prediction (Phase 3)
    lifespan_months: int = 0
    lifespan_phase: str = "mature"
    lifespan_phase_label: str = "成熟"
    aging_velocity: float = 0.0
    lifespan_recommendations: List[str] = []

    class Config:
        from_attributes = True


class StrategyDNASummary(BaseModel):
    strategy_id: str
    name: str
    gene_diversity_score: float
    health_birth_score: float
    feature_genes: List[str]
    signal_genes: List[str]
    status: str
    family_id: Optional[str] = None
    family_name: Optional[str] = None

    # Integration fields for eco-pre-check (方案一)
    metabolic_rate: float = 0.0
    niche_width: float = 0.0
    inbreeding_warning: bool = False
    homogeneity_risk: float = 0.0
    lifespan_months: int = 0


class GeneSequencingRequest(BaseModel):
    strategy_id: str


class DNAPreviewRequest(BaseModel):
    strategy_id: str
    code: str


class DNAPreviewResponse(BaseModel):
    strategy_id: str
    feature_genes: List[str]
    signal_genes: List[str]
    risk_genes: List[str]
    execution_genes: List[str]
    gene_diversity_score: float
    health_birth_score: float
    gene_vector: List[float]
    metabolic_rate: float
    niche_width: float
    metabolic_syndrome: bool
    metabolic_markers: List[str]
    ast_features: dict


class GeneMatch(BaseModel):
    strategy_id: str
    name: str
    similarity: float


class StrategyPhylogenyResponse(BaseModel):
    strategy_id: str
    family_id: Optional[str]
    family_name: Optional[str]
    relatives: List[GeneMatch]
    homogeneity_risk: float
    inbreeding_warning: bool

    class Config:
        from_attributes = True
