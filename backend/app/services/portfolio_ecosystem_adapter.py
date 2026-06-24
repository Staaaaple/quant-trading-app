"""将组合中的策略自动接入生态系统（DNA + 系统发育）.

当组合生成时，组合里的策略可能还没有 DNA 记录（例如内置策略或动态生成的策略）。
这个模块负责从组合配置中提取策略元数据，创建/更新对应的 Strategy、StrategyDNA、
StrategyPhylogeny 记录，使生态系统页面能展示真实数据。
"""

import datetime
from collections import Counter
from typing import Any

from sqlalchemy.orm import Session

from app.models.portfolio import Portfolio
from app.models.strategy import Strategy
from app.models.strategy_dna import StrategyDNA, StrategyPhylogeny


# 基于策略家族预定义的基因标签（与 dna_sequencer 的检测逻辑尽量对应）
FAMILY_GENE_MAP: dict[str, dict[str, list[str]]] = {
    "trend": {
        "feature": ["trend_following", "moving_average", "price_momentum"],
        "signal": ["ema_cross", "trend_breakout", "ma_alignment"],
        "risk": ["stop_loss", "trailing_stop", "max_drawdown_control"],
        "execution": ["order_execution", "position_sizing"],
    },
    "momentum": {
        "feature": ["momentum", "rate_of_change", "relative_strength"],
        "signal": ["rsi_signal", "momentum_breakout", "overbought_oversold"],
        "risk": ["stop_loss", "volatility_filter", "time_stop"],
        "execution": ["order_execution", "position_sizing"],
    },
    "mean_reversion": {
        "feature": ["mean_reversion", "volatility", "bollinger_bands"],
        "signal": ["bbands_reversion", "zscore", "extreme_price"],
        "risk": ["stop_loss", "volatility_filter", "regime_filter"],
        "execution": ["order_execution", "position_sizing"],
    },
    "value": {
        "feature": ["valuation", "fundamental", "pe_pb_ratio"],
        "signal": ["undervalued_signal", "quality_score"],
        "risk": ["stop_loss", "concentration_limit", "time_stop"],
        "execution": ["order_execution", "position_sizing"],
    },
    "quality": {
        "feature": ["quality", "fundamental", "roe_roic"],
        "signal": ["quality_score", "earnings_stability"],
        "risk": ["stop_loss", "concentration_limit"],
        "execution": ["order_execution", "position_sizing"],
    },
    "multi_factor": {
        "feature": ["multi_factor", "factor_overlay", "value_growth"],
        "signal": ["composite_score", "factor_ranking"],
        "risk": ["stop_loss", "factor_risk_control", "max_drawdown_control"],
        "execution": ["order_execution", "position_sizing"],
    },
    "ml": {
        "feature": ["machine_learning", "feature_engineering", "ensemble"],
        "signal": ["ml_model", "prediction_signal", "probability_score"],
        "risk": ["stop_loss", "model_risk_control", "volatility_filter"],
        "execution": ["order_execution", "position_sizing"],
    },
}


def _genes_for_family(family: str) -> tuple[list[str], list[str], list[str], list[str]]:
    """根据策略家族返回基因标签."""
    genes = FAMILY_GENE_MAP.get(family.lower(), FAMILY_GENE_MAP["trend"])
    return (
        genes["feature"].copy(),
        genes["signal"].copy(),
        genes["risk"].copy(),
        genes["execution"].copy(),
    )


def _placeholder_code(strategy_id: str, family: str) -> str:
    """生成占位策略代码，仅用于满足 Strategy.code 非空约束."""
    return f"# Auto-generated placeholder for {strategy_id} ({family})\n"


def _diversity_score(feature: list, signal: list, risk: list, execution: list) -> float:
    """计算基因多样性得分（与 dna_sequencer 逻辑一致）."""
    total_unique = len(set(feature + signal + risk + execution))
    return round(min(total_unique / 16.0, 1.0), 2)


def _health_score(diversity: float, has_risk: bool) -> float:
    """计算出生健康度."""
    score = 50 + (diversity * 30)
    if has_risk:
        score += 10
    return round(min(score, 100), 1)


def _metabolic_for_family(family: str) -> float:
    """基于家族估算代谢率（高换手率策略代谢率更高）."""
    family = family.lower()
    if family in ("momentum", "mean_reversion"):
        return 0.25
    if family in ("ml", "multi_factor"):
        return 0.20
    if family == "trend":
        return 0.15
    return 0.10


def _niche_for_family(family: str) -> float:
    """基于家族估算生态位宽度."""
    family = family.lower()
    if family in ("multi_factor", "ml"):
        return 0.80
    if family in ("trend", "momentum", "mean_reversion"):
        return 0.60
    return 0.45


def _lifespan_for_family(family: str) -> int:
    """基于家族估算寿命（月）."""
    family = family.lower()
    if family in ("value", "quality"):
        return 36
    if family in ("trend", "multi_factor"):
        return 24
    if family in ("momentum", "mean_reversion"):
        return 12
    if family == "ml":
        return 9
    return 18


def _lifespan_phase(months: int) -> str:
    """根据寿命月数推断生命周期阶段."""
    if months > 36:
        return "young"
    if months >= 12:
        return "mature"
    if months >= 3:
        return "aging"
    return "endangered"


def _aging_velocity(family: str) -> float:
    """估算老化速度."""
    family = family.lower()
    if family in ("momentum", "mean_reversion"):
        return 0.08
    if family == "ml":
        return 0.10
    if family == "trend":
        return 0.04
    return 0.03


def ensure_portfolio_ecosystem_data(db: Session, portfolio: Portfolio) -> None:
    """根据组合配置创建/更新生态系统所需数据.

    Args:
        db: 数据库 session
        portfolio: Portfolio 模型对象（需包含 config_json）
    """
    config = portfolio.config_json or {}
    bindings = config.get("bindings", [])
    if not bindings:
        return

    # 提取唯一策略
    strategies: dict[str, dict[str, Any]] = {}
    for b in bindings:
        sid = b.get("strategy_id")
        if not sid or sid in strategies:
            continue
        strategies[sid] = {
            "name": b.get("strategy_name") or sid,
            "family": b.get("strategy_family") or "trend",
        }

    if not strategies:
        return

    # 计算家族分布，用于后续系统发育
    family_counts = Counter(s["family"] for s in strategies.values())
    total = len(strategies)

    # 1. 确保 Strategy 记录存在
    for sid, meta in strategies.items():
        strategy = db.query(Strategy).filter(Strategy.strategy_id == sid).first()
        if not strategy:
            strategy = Strategy(
                strategy_id=sid,
                name=meta["name"],
                type="trade",
                code=_placeholder_code(sid, meta["family"]),
            )
            db.add(strategy)

    # 2. 确保 StrategyDNA 记录存在
    now = datetime.datetime.utcnow()
    for sid, meta in strategies.items():
        family = meta["family"]
        feature, signal, risk, execution = _genes_for_family(family)
        diversity = _diversity_score(feature, signal, risk, execution)
        health = _health_score(diversity, len(risk) > 0)
        metabolic = _metabolic_for_family(family)
        niche = _niche_for_family(family)
        lifespan = _lifespan_for_family(family)

        dna = db.query(StrategyDNA).filter(StrategyDNA.strategy_id == sid).first()
        if not dna:
            dna = StrategyDNA(strategy_id=sid)

        dna.gene_vector = []
        dna.feature_genes = feature
        dna.signal_genes = signal
        dna.risk_genes = risk
        dna.execution_genes = execution
        dna.gene_diversity_score = diversity
        dna.health_birth_score = health
        dna.family_id = family
        dna.family_name = family
        dna.sequence_version = "1.0"
        dna.sequenced_at = now
        dna.status = "success"
        dna.error_message = None
        dna.gene_profile = {
            "feature_layer": feature,
            "signal_layer": signal,
            "risk_layer": risk,
            "execution_layer": execution,
            "ast_features": {},
        }
        dna.metabolic_rate = metabolic
        dna.niche_width = niche
        dna.metabolic_syndrome = metabolic > 0.25
        dna.metabolic_markers = ["auto_generated"] if dna.metabolic_syndrome else []
        dna.lifespan_months = lifespan
        dna.lifespan_phase = _lifespan_phase(lifespan)
        dna.aging_velocity = _aging_velocity(family)
        dna.lifespan_recommendations = []
        db.add(dna)

    # 3. 确保 StrategyPhylogeny 记录存在
    for sid, meta in strategies.items():
        family = meta["family"]
        same_family_count = family_counts.get(family, 0)
        homogeneity = same_family_count / total if total > 0 else 0.0
        relatives = []
        for other_sid, other_meta in strategies.items():
            if other_sid == sid:
                continue
            similarity = 0.7 if other_meta["family"] == family else 0.2
            relatives.append({
                "strategy_id": other_sid,
                "name": other_meta["name"],
                "similarity": similarity,
            })
        # 按相似度取前 5 个亲属
        relatives.sort(key=lambda x: x["similarity"], reverse=True)
        relatives = relatives[:5]

        phylo = db.query(StrategyPhylogeny).filter(StrategyPhylogeny.strategy_id == sid).first()
        if not phylo:
            phylo = StrategyPhylogeny(strategy_id=sid)

        phylo.family_id = family
        phylo.family_name = family
        phylo.relatives = relatives
        phylo.homogeneity_risk = round(homogeneity, 3)
        phylo.inbreeding_warning = homogeneity > 0.5
        phylo.updated_at = now
        db.add(phylo)

    db.commit()


def ensure_ecosystem_data_from_latest_portfolios(db: Session) -> None:
    """为数据库中所有已有组合补充生态系统数据.

    用于一次性迁移：当生态系统页面首次被访问且没有 DNA 数据时调用。
    """
    portfolios = db.query(Portfolio).all()
    for portfolio in portfolios:
        try:
            ensure_portfolio_ecosystem_data(db, portfolio)
        except Exception as e:
            # 单条失败不应影响其他组合
            print(f"[EcosystemAdapter] 组合 {portfolio.id} 数据接入失败: {e}")
            db.rollback()

    # 同时确保常见参考策略存在，用于丰富关系网络
    ensure_reference_strategies(db)


# 常见参考策略（未在组合中使用时作为关系网络中的候选节点）
REFERENCE_STRATEGIES: list[dict[str, Any]] = [
    {"strategy_id": "ref_trend_sma", "name": "SMA趋势跟踪", "family": "trend"},
    {"strategy_id": "ref_momentum_macd", "name": "MACD动量", "family": "momentum"},
    {"strategy_id": "ref_mean_reversion_rsi", "name": "RSI均值回归", "family": "mean_reversion"},
    {"strategy_id": "ref_breakout_channel", "name": "通道突破", "family": "breakout"},
    {"strategy_id": "ref_value_pe", "name": "低估值策略", "family": "value"},
    {"strategy_id": "ref_quality_roe", "name": "高质量ROE", "family": "quality"},
    {"strategy_id": "ref_multi_factor_vm", "name": "价值动量多因子", "family": "multi_factor"},
    {"strategy_id": "ref_ml_xgboost", "name": "XGBoost机器学习", "family": "ml"},
]


def ensure_reference_strategies(db: Session) -> None:
    """确保常见参考策略在生态系统中存在.

    这些策略可能没有被当前组合使用，但会出现在关系网络中，
    与组合中的真实策略建立联系，帮助用户理解策略生态。
    """
    now = datetime.datetime.utcnow()

    for ref in REFERENCE_STRATEGIES:
        sid = ref["strategy_id"]
        family = ref["family"]

        # 确保 Strategy 记录
        strategy = db.query(Strategy).filter(Strategy.strategy_id == sid).first()
        if not strategy:
            strategy = Strategy(
                strategy_id=sid,
                name=ref["name"],
                type="trade",
                code=_placeholder_code(sid, family),
            )
            db.add(strategy)

        # 如果该策略已在组合中使用，跳过 DNA 创建（避免覆盖真实数据）
        existing_dna = db.query(StrategyDNA).filter(StrategyDNA.strategy_id == sid).first()
        if existing_dna:
            continue

        feature, signal, risk, execution = _genes_for_family(family)
        diversity = _diversity_score(feature, signal, risk, execution)
        health = _health_score(diversity, len(risk) > 0)
        metabolic = _metabolic_for_family(family)
        niche = _niche_for_family(family)
        lifespan = _lifespan_for_family(family)

        dna = StrategyDNA(strategy_id=sid)
        dna.gene_vector = []
        dna.feature_genes = feature
        dna.signal_genes = signal
        dna.risk_genes = risk
        dna.execution_genes = execution
        dna.gene_diversity_score = diversity
        dna.health_birth_score = health
        dna.family_id = family
        dna.family_name = family
        dna.sequence_version = "1.0-ref"
        dna.sequenced_at = now
        dna.status = "success"
        dna.error_message = None
        dna.gene_profile = {
            "feature_layer": feature,
            "signal_layer": signal,
            "risk_layer": risk,
            "execution_layer": execution,
            "ast_features": {},
        }
        dna.metabolic_rate = metabolic
        dna.niche_width = niche
        dna.metabolic_syndrome = metabolic > 0.25
        dna.metabolic_markers = ["reference"] if dna.metabolic_syndrome else []
        dna.lifespan_months = lifespan
        dna.lifespan_phase = _lifespan_phase(lifespan)
        dna.aging_velocity = _aging_velocity(family)
        dna.lifespan_recommendations = []
        db.add(dna)

        # 创建与所有其他策略的亲属关系（后续由 phylogeny 服务重新计算也可）
        all_dnas = db.query(StrategyDNA).filter(StrategyDNA.strategy_id != sid).all()
        relatives = []
        for other in all_dnas:
            similarity = 0.7 if other.family_name == family else 0.2
            relatives.append({
                "strategy_id": other.strategy_id,
                "name": other.strategy_id,
                "similarity": similarity,
            })
        relatives.sort(key=lambda x: x["similarity"], reverse=True)
        relatives = relatives[:5]

        phylo = StrategyPhylogeny(strategy_id=sid)
        phylo.family_id = family
        phylo.family_name = family
        phylo.relatives = relatives
        # 参考策略同质性风险设为 0，避免影响统计
        phylo.homogeneity_risk = 0.0
        phylo.inbreeding_warning = False
        phylo.updated_at = now
        db.add(phylo)

    db.commit()
