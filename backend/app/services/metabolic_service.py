"""Metabolic profiler: computes metabolic rate, niche width, and syndrome markers."""

from typing import Any


def calculate_metabolic_profile(code: str, feature_genes: list, signal_genes: list, risk_genes: list) -> dict[str, Any]:
    """Calculate metabolic profile based on code features and gene composition."""
    code_lower = code.lower()

    # 1. Information Metabolic Rate
    metabolic_rate = _calculate_metabolic_rate(code_lower, signal_genes)

    # 2. Niche Width
    niche_width = _calculate_niche_width(feature_genes, risk_genes)

    # 3. Metabolic Syndrome
    syndrome = _detect_metabolic_syndrome(feature_genes, signal_genes, risk_genes)

    return {
        "metabolic_rate": metabolic_rate,
        "niche_width": niche_width,
        "metabolic_syndrome": syndrome["has_syndrome"],
        "metabolic_markers": syndrome["markers"],
    }


def _calculate_metabolic_rate(code_lower: str, signal_genes: list) -> float:
    """
    Information Metabolic Rate: how quickly a strategy needs fresh data.
    Higher = more dependent on recent data (ages faster).
    """
    # Frequency detection
    if any(kw in code_lower for kw in ['tick', 'minute', 'intraday', '分钟', '高频', 'on_tick']):
        base_rate = 0.3
    elif any(kw in code_lower for kw in ['daily', '日频', 'on_bar']):
        base_rate = 0.1
    elif any(kw in code_lower for kw in ['weekly', '周频']):
        base_rate = 0.05
    elif any(kw in code_lower for kw in ['monthly', '月频']):
        base_rate = 0.02
    else:
        base_rate = 0.08  # default: moderate

    # Complexity factor: more signal genes = more complex processing
    complexity_factor = 1.0 + len(signal_genes) * 0.05

    # ML models have higher metabolic rate (need retraining)
    if any(kw in code_lower for kw in ['sklearn', 'torch', 'tensorflow', 'xgboost', 'lstm', 'gru']):
        complexity_factor += 0.3

    return round(min(base_rate * complexity_factor, 1.0), 3)


def _calculate_niche_width(feature_genes: list, risk_genes: list) -> float:
    """
    Niche Width: how many market regimes the strategy can survive in.
    Wider = more adaptable.
    """
    # Base width from feature gene count (more features = more adaptable)
    base_width = min(len(feature_genes) / 8.0, 0.5)

    # Market regime coverage bonus
    has_trend = any(g in feature_genes for g in ['MA', 'MACD', 'EMA', 'momentum'])
    has_reversion = any(g in feature_genes for g in ['RSI', 'BOLL', 'volatility'])
    has_value = any(g in feature_genes for g in ['PE', 'PB', 'ROE'])
    has_volume = 'volume' in feature_genes

    regime_count = sum([has_trend, has_reversion, has_value, has_volume])
    regime_bonus = (regime_count / 4.0) * 0.3

    # Risk adaptation bonus
    risk_bonus = min(len(risk_genes) / 3.0, 0.2)

    return round(min(base_width + regime_bonus + risk_bonus, 1.0), 3)


def _detect_metabolic_syndrome(feature_genes: list, signal_genes: list, risk_genes: list) -> dict:
    """
    Metabolic Syndrome: markers of structural fragility.
    """
    markers = []

    # Single indicator dependency
    if len(feature_genes) < 2:
        markers.append("单一指标依赖")

    # Oversimplified signal logic
    if len(signal_genes) < 2:
        markers.append("信号逻辑过于简单")

    # No risk management
    if len(risk_genes) == 0:
        markers.append("无风控机制")

    # Feature concentration (all in one layer type)
    if len(feature_genes) > 0 and len(signal_genes) == 1 and 'rule_based' in signal_genes:
        markers.append("纯规则驱动，缺乏自适应能力")

    return {
        "has_syndrome": len(markers) > 0,
        "markers": markers,
    }
