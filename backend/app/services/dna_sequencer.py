import ast
import re
from typing import Any
from sqlalchemy.orm import Session

from app.models.strategy_dna import StrategyDNA
from app.models.strategy import Strategy

# Gene detection patterns
FEATURE_PATTERNS = {
    "MA": ["MA", "SMA", "EMA", "WMA", "moving_average", "均线"],
    "MACD": ["MACD", "macd"],
    "RSI": ["RSI", "rsi"],
    "KDJ": ["KDJ", "kdj"],
    "BOLL": ["BOLL", "boll", "bollinger"],
    "volume": ["volume", "vol", "turnover", "成交量"],
    "ATR": ["ATR", "atr"],
    "close_price": ["close", "收盘价"],
    "open_price": ["open", "开盘价"],
    "high_price": ["high", "最高价"],
    "low_price": ["low", "最低价"],
    "PE": ["PE", "pe_ratio", "市盈率"],
    "PB": ["PB", "pb_ratio", "市净率"],
    "ROE": ["ROE", "roe", "净资产收益率"],
    "momentum": ["momentum", "动量"],
    "volatility": ["volatility", "std", "波动率"],
    "turnover_rate": ["turnover_rate", "换手率"],
}

SIGNAL_PATTERNS = {
    "rule_based": ["if", "cross", "above", "below", ">", "<", "金叉", "死叉"],
    "ml_model": ["sklearn", "RandomForest", "XGBoost", "LightGBM", "SVR", "神经网络", "LSTM", "GRU"],
    "trend_following": ["trend", "trending", "突破", "趋势"],
    "mean_reversion": ["reversion", "revert", "回归", "均值回归"],
    "momentum": ["momentum", "momentum_signal", "动量"],
    "crossover": ["cross", "crossover", "crossover_signal", "交叉"],
    "daily_freq": ["on_bar", "daily", "日频"],
    "intraday_freq": ["on_tick", "minute", "tick", "分钟", "高频"],
    "weekly_freq": ["weekly", "周频"],
}

RISK_PATTERNS = {
    "fixed_stop": ["stop_loss", "止损", "stoploss", "fixed_stop"],
    "atr_stop": ["atr_stop", "ATR_stop", "波动率止损"],
    "trailing_stop": ["trailing", "追踪止损", "移动止损"],
    "time_stop": ["time_stop", "时间止损"],
    "position_limit": ["position_limit", "max_position", "仓位限制"],
    "max_drawdown_limit": ["max_drawdown", "回撤限制", "drawdown_limit"],
    "circuit_breaker": ["circuit_breaker", "熔断", "暂停交易"],
}

EXECUTION_PATTERNS = {
    "market_order": ["market_order", "市价单", "self.buy", "self.sell"],
    "limit_order": ["limit_order", "限价单"],
    "twap_order": ["TWAP", "twap", "时间加权"],
    "slippage_control": ["slippage", "滑点", "slippage_control"],
    "delay_tolerant": ["delay", "延迟容忍"],
}


def _detect_genes(code: str, patterns: dict[str, list[str]]) -> list[str]:
    """Detect gene tags from code using keyword patterns."""
    detected = set()
    for gene_name, keywords in patterns.items():
        for kw in keywords:
            if kw.lower() in code.lower():
                detected.add(gene_name)
                break
    return sorted(list(detected))


def _extract_ast_features(code: str) -> dict[str, Any]:
    """Extract structural features from AST."""
    features = {
        "has_class": False,
        "has_ml_import": False,
        "has_indicator_func": False,
        "decision_logic_count": 0,
        "risk_func_count": 0,
    }
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                features["has_class"] = True
            elif isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if any(ml in alias.name for ml in ["sklearn", "torch", "tensorflow", "xgboost", "lightgbm"]):
                        features["has_ml_import"] = True
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    fname = node.func.id
                    if fname in ["MA", "SMA", "EMA", "MACD", "RSI", "BOLL", "ATR"]:
                        features["has_indicator_func"] = True
            elif isinstance(node, ast.If):
                features["decision_logic_count"] += 1
            elif isinstance(node, ast.FunctionDef):
                if any(r in node.name.lower() for r in ["risk", "stop", "drawdown", "position"]):
                    features["risk_func_count"] += 1
    except SyntaxError:
        pass
    return features


def _vectorize_genes(feature_genes: list, signal_genes: list, risk_genes: list, execution_genes: list) -> list[float]:
    """Convert gene tags to a simplified 32-dim vector (8 per layer)."""
    all_feature = list(FEATURE_PATTERNS.keys())
    all_signal = list(SIGNAL_PATTERNS.keys())
    all_risk = list(RISK_PATTERNS.keys())
    all_exec = list(EXECUTION_PATTERNS.keys())

    vector = []
    # Feature layer (8 dims)
    for g in all_feature[:8]:
        vector.append(1.0 if g in feature_genes else 0.0)
    # Signal layer (8 dims)
    for g in all_signal[:8]:
        vector.append(1.0 if g in signal_genes else 0.0)
    # Risk layer (8 dims)
    for g in all_risk[:8]:
        vector.append(1.0 if g in risk_genes else 0.0)
    # Execution layer (8 dims)
    for g in all_exec[:8]:
        vector.append(1.0 if g in execution_genes else 0.0)
    return vector


def _calculate_diversity_score(feature_genes: list, signal_genes: list, risk_genes: list, execution_genes: list) -> float:
    """Calculate gene diversity score (0-1). More unique genes = higher diversity."""
    total_unique = len(set(feature_genes + signal_genes + risk_genes + execution_genes))
    # Max possible ~32 genes, normalize
    return round(min(total_unique / 16.0, 1.0), 2)


def _calculate_health_score(diversity: float, has_risk: bool, has_ml: bool) -> float:
    """Calculate birth health score (0-100)."""
    score = 50 + (diversity * 30)
    if has_risk:
        score += 10
    if has_ml:
        score += 5
    return round(min(score, 100), 1)


def sequence_strategy(strategy_id: str, code: str, db: Session) -> StrategyDNA:
    """Run DNA sequencing on a strategy's code. Create or update DNA record."""
    # Detect genes
    feature_genes = _detect_genes(code, FEATURE_PATTERNS)
    signal_genes = _detect_genes(code, SIGNAL_PATTERNS)
    risk_genes = _detect_genes(code, RISK_PATTERNS)
    execution_genes = _detect_genes(code, EXECUTION_PATTERNS)

    # AST analysis
    ast_features = _extract_ast_features(code)

    # Adjust signal genes based on AST
    if ast_features["has_ml_import"] and "ml_model" not in signal_genes:
        signal_genes.append("ml_model")
    if ast_features["has_class"] and "rule_based" not in signal_genes:
        signal_genes.append("rule_based")

    # Vectorize
    gene_vector = _vectorize_genes(feature_genes, signal_genes, risk_genes, execution_genes)

    # Calculate scores
    diversity = _calculate_diversity_score(feature_genes, signal_genes, risk_genes, execution_genes)
    health = _calculate_health_score(diversity, len(risk_genes) > 0, ast_features["has_ml_import"])

    # Build gene profile
    gene_profile = {
        "feature_layer": feature_genes,
        "signal_layer": signal_genes,
        "risk_layer": risk_genes,
        "execution_layer": execution_genes,
        "ast_features": ast_features,
    }

    # Metabolic profiling (Phase 2)
    from app.services.metabolic_service import calculate_metabolic_profile
    metabolic = calculate_metabolic_profile(code, feature_genes, signal_genes, risk_genes)

    # Upsert DNA record
    existing = db.query(StrategyDNA).filter(StrategyDNA.strategy_id == strategy_id).first()
    if existing:
        existing.gene_vector = gene_vector
        existing.feature_genes = feature_genes
        existing.signal_genes = signal_genes
        existing.risk_genes = risk_genes
        existing.execution_genes = execution_genes
        existing.gene_diversity_score = diversity
        existing.health_birth_score = health
        existing.gene_profile = gene_profile
        existing.metabolic_rate = metabolic["metabolic_rate"]
        existing.niche_width = metabolic["niche_width"]
        existing.metabolic_syndrome = metabolic["metabolic_syndrome"]
        existing.metabolic_markers = metabolic["metabolic_markers"]
        existing.status = "success"
        existing.error_message = None
        db.add(existing)
    else:
        existing = StrategyDNA(
            strategy_id=strategy_id,
            gene_vector=gene_vector,
            feature_genes=feature_genes,
            signal_genes=signal_genes,
            risk_genes=risk_genes,
            execution_genes=execution_genes,
            gene_diversity_score=diversity,
            health_birth_score=health,
            gene_profile=gene_profile,
            metabolic_rate=metabolic["metabolic_rate"],
            niche_width=metabolic["niche_width"],
            metabolic_syndrome=metabolic["metabolic_syndrome"],
            metabolic_markers=metabolic["metabolic_markers"],
            status="success",
        )
        db.add(existing)

    db.commit()
    db.refresh(existing)

    # Auto-trigger phylogeny recomputation after sequencing
    try:
        from app.services import phylogeny_service
        phylogeny_service.compute_all_phylogeny(db)
    except Exception:
        pass  # Don't fail sequencing if phylogeny fails

    # Auto-trigger lifespan prediction after phylogeny (Phase 3)
    try:
        from app.services import lifespan_service
        lifespan_service.compute_strategy_lifespan(db, strategy_id)
    except Exception:
        pass  # Don't fail sequencing if lifespan fails

    return existing


def preview_dna(strategy_id: str, code: str) -> dict:
    """Compute DNA preview without saving to database."""
    feature_genes = _detect_genes(code, FEATURE_PATTERNS)
    signal_genes = _detect_genes(code, SIGNAL_PATTERNS)
    risk_genes = _detect_genes(code, RISK_PATTERNS)
    execution_genes = _detect_genes(code, EXECUTION_PATTERNS)

    ast_features = _extract_ast_features(code)

    if ast_features["has_ml_import"] and "ml_model" not in signal_genes:
        signal_genes.append("ml_model")
    if ast_features["has_class"] and "rule_based" not in signal_genes:
        signal_genes.append("rule_based")

    gene_vector = _vectorize_genes(feature_genes, signal_genes, risk_genes, execution_genes)
    diversity = _calculate_diversity_score(feature_genes, signal_genes, risk_genes, execution_genes)
    health = _calculate_health_score(diversity, len(risk_genes) > 0, ast_features["has_ml_import"])

    from app.services.metabolic_service import calculate_metabolic_profile
    metabolic = calculate_metabolic_profile(code, feature_genes, signal_genes, risk_genes)

    return {
        "strategy_id": strategy_id,
        "feature_genes": feature_genes,
        "signal_genes": signal_genes,
        "risk_genes": risk_genes,
        "execution_genes": execution_genes,
        "gene_diversity_score": diversity,
        "health_birth_score": health,
        "gene_vector": gene_vector,
        "metabolic_rate": metabolic["metabolic_rate"],
        "niche_width": metabolic["niche_width"],
        "metabolic_syndrome": metabolic["metabolic_syndrome"],
        "metabolic_markers": metabolic["metabolic_markers"],
        "ast_features": ast_features,
    }


def get_dna(db: Session, strategy_id: str) -> StrategyDNA | None:
    return db.query(StrategyDNA).filter(StrategyDNA.strategy_id == strategy_id).first()


def get_all_dnas(db: Session) -> list[StrategyDNA]:
    return db.query(StrategyDNA).all()


def delete_dna(db: Session, strategy_id: str) -> None:
    dna = db.query(StrategyDNA).filter(StrategyDNA.strategy_id == strategy_id).first()
    if dna:
        db.delete(dna)
        db.commit()
