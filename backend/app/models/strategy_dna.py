import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


class StrategyDNA(Base):
    __tablename__ = "strategy_dna"

    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(String(64), unique=True, index=True, nullable=False)

    # Gene vector (simplified 32-dim: 8 per layer)
    gene_vector = Column(JSON, nullable=True)

    # Four-layer gene tags (human-readable)
    feature_genes = Column(JSON, default=list)
    signal_genes = Column(JSON, default=list)
    risk_genes = Column(JSON, default=list)
    execution_genes = Column(JSON, default=list)

    # Summary scores
    gene_diversity_score = Column(Float, default=0.0)
    health_birth_score = Column(Float, default=0.0)
    inbreeding_coefficient = Column(Float, default=0.0)

    # Family info (populated by phylogeny engine later)
    family_id = Column(String(64), nullable=True)
    family_name = Column(String(128), nullable=True)

    # Sequencing metadata
    sequence_version = Column(String(16), default="1.0")
    sequenced_at = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String(16), default="success")  # success / failed / pending
    error_message = Column(String(256), nullable=True)

    # Raw gene profile for display
    gene_profile = Column(JSON, nullable=True)

    # Metabolic profiling (Phase 2)
    metabolic_rate = Column(Float, default=0.0)  # 信息代谢率 (0-1)
    niche_width = Column(Float, default=0.0)  # 生态位宽度 (0-1)
    metabolic_syndrome = Column(Boolean, default=False)  # 代谢综合征标记
    metabolic_markers = Column(JSON, default=list)  # 代谢异常标记列表

    # Lifespan prediction (Phase 3)
    lifespan_months = Column(Integer, default=0)  # 预计剩余寿命（月）
    lifespan_phase = Column(String(16), default="mature")  # young/mature/aging/endangered
    aging_velocity = Column(Float, default=0.0)  # 老化速度（edge 衰减率 / 月）
    lifespan_recommendations = Column(JSON, default=list)  # 寿命优化建议


class StrategyPhylogeny(Base):
    __tablename__ = "strategy_phylogeny"

    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(String(64), index=True, nullable=False)

    family_id = Column(String(64), index=True, nullable=True)
    family_name = Column(String(128), nullable=True)

    # Top relatives (list of {strategy_id, name, similarity})
    relatives = Column(JSON, nullable=True)

    # Risk markers
    homogeneity_risk = Column(Float, default=0.0)
    inbreeding_warning = Column(Boolean, default=False)

    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
