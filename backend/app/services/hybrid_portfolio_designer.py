"""Hybrid Portfolio Designer — 组合设计总控.

6步编排:
1. SAA: 战略资产配置
2. TAA: 战术资产配置
3. 策略-标的绑定
4. 风控配置
5. 可靠性评估
6. 组合寿命计算
"""

import datetime
from typing import Any

from app.services.saa_engine import calculate_saa, get_risk_level_from_profile, get_market_cycle_from_signal
from app.services.taa_engine import calculate_taa, get_top_sectors


def _load_strategy_templates() -> list[dict[str, Any]]:
    """从数据库加载策略模板池."""
    try:
        from sqlalchemy.orm import Session
        from app.db.base import SessionLocal
        from app.models.strategy_template import StrategyTemplate

        db: Session = SessionLocal()
        try:
            templates = db.query(StrategyTemplate).filter(
                StrategyTemplate.is_active == True
            ).all()
            return [
                {
                    "id": t.template_id,
                    "name": t.name,
                    "family": t.family,
                    "risk_level": t.risk_level,
                    "suitable_cycles": t.suitable_cycles or [],
                    "health_score": t.health_score,
                    "lifespan_months": t.lifespan_months,
                }
                for t in templates
            ]
        finally:
            db.close()
    except Exception as e:
        print(f"[PortfolioDesigner] Failed to load templates from DB: {e}")
        return []


# 回退策略模板池（当数据库不可用时）
DEFAULT_STRATEGY_TEMPLATES = [
    {"id": "tmpl_001", "name": "双均线趋势跟踪", "family": "趋势跟踪", "risk_level": "medium", "suitable_cycles": ["复苏", "扩张"]},
    {"id": "tmpl_002", "name": "EMA动量趋势", "family": "趋势跟踪", "risk_level": "medium", "suitable_cycles": ["复苏", "扩张", "过热"]},
    {"id": "tmpl_003", "name": "RSI均值回归", "family": "均值回归", "risk_level": "low", "suitable_cycles": ["衰退", "复苏"]},
    {"id": "tmpl_004", "name": "MACD趋势确认", "family": "趋势跟踪", "risk_level": "medium", "suitable_cycles": ["复苏", "扩张"]},
    {"id": "tmpl_005", "name": "布林带回归", "family": "均值回归", "risk_level": "low", "suitable_cycles": ["衰退", "复苏", "过热"]},
    {"id": "tmpl_006", "name": "价格动量突破", "family": "动量策略", "risk_level": "high", "suitable_cycles": ["扩张", "过热"]},
    {"id": "tmpl_007", "name": "箱体突破", "family": "突破策略", "risk_level": "high", "suitable_cycles": ["复苏", "扩张"]},
    {"id": "tmpl_008", "name": "价值因子", "family": "量化多因子", "risk_level": "low", "suitable_cycles": ["衰退", "复苏"]},
    {"id": "tmpl_009", "name": "低波动因子", "family": "量化多因子", "risk_level": "low", "suitable_cycles": ["衰退", "复苏"]},
    {"id": "tmpl_010", "name": "期现套利", "family": "套利策略", "risk_level": "low", "suitable_cycles": ["衰退", "复苏", "扩张", "过热"]},
]


def design_portfolio(
    profile_vector: dict[str, float],
    market_signal: dict[str, Any],
    strategy_pool: list[dict] | None = None,
    target_count: int = 5,
) -> dict[str, Any]:
    """设计完整的投资组合.

    Args:
        profile_vector: 用户画像15维向量
        market_signal: 市场五层信号
        strategy_pool: 策略池（可选，默认使用占位）
        target_count: 目标策略数量

    Returns:
        完整组合配置
    """
    # Step 1: SAA — 战略资产配置
    risk_level = get_risk_level_from_profile(profile_vector)
    market_cycle = get_market_cycle_from_signal(market_signal)
    macro_score = market_signal.get("macro_score", 0.5)
    geo_risk = market_signal.get("geo_risk", 0.5)

    saa_result = calculate_saa(
        risk_tolerance=risk_level,
        market_cycle=market_cycle,
        macro_score=macro_score,
        geo_risk=geo_risk,
    )

    # Step 2: TAA — 战术资产配置
    industry_scores = market_signal.get("industry_scores", {})
    social_trends = market_signal.get("social_trends", [])

    taa_result = calculate_taa(
        saa_weights=saa_result["weights"],
        market_cycle=market_cycle,
        industry_scores=industry_scores,
        social_trends=social_trends,
        market_signal=market_signal,
    )

    # Step 3: 策略-标的绑定（智能匹配版）
    strategies = strategy_pool or _load_strategy_templates() or DEFAULT_STRATEGY_TEMPLATES
    top_sectors = get_top_sectors(taa_result, n=5)

    # 智能匹配：根据市场周期、行业、风险等级匹配最佳策略
    cycle_map = {
        "expansion": "扩张", "peak": "过热", "contraction": "衰退",
        "trough": "萧条", "recovery": "复苏",
    }
    current_cycle = cycle_map.get(market_cycle, "复苏")

    # 风险等级映射
    risk_map = {
        "conservative": ["low"], "moderate": ["low", "medium"],
        "aggressive": ["medium", "high"], "very_aggressive": ["high"],
    }
    allowed_risk = risk_map.get(risk_level, ["low", "medium"])

    bindings = []
    used_strategies = set()

    for sector_info in top_sectors:
        sector = sector_info["sector"]
        # 筛选匹配当前周期和风险等级的策略
        candidates = [
            s for s in strategies
            if s["id"] not in used_strategies
            and (s.get("risk_level") in allowed_risk or s.get("risk_level") == "medium")
            and any(current_cycle in c or "复苏" in c for c in s.get("suitable_cycles", []))
        ]

        # 如果没有匹配，放宽条件
        if not candidates:
            candidates = [s for s in strategies if s["id"] not in used_strategies]

        if candidates:
            # 选择健康度最高的策略
            best = max(candidates, key=lambda s: s.get("health_score", 70))
            used_strategies.add(best["id"])

            # 获取该行业的真实ETF
            from app.services.assets import get_sector_etf
            etf = get_sector_etf(sector)

            bindings.append({
                "sector": sector,
                "sector_name": sector_info["name"],
                "weight": sector_info["weight"],
                "strategy_id": best["id"],
                "strategy_name": best["name"],
                "strategy_family": best["family"],
                "symbol": etf.get("symbol") if etf else None,
                "symbol_name": etf.get("name") if etf else sector_info["name"],
                "health_score": best.get("health_score", 75),
                "lifespan_months": best.get("lifespan_months", 12),
            })

    # Step 4: 风控配置
    risk_config = _generate_risk_config(profile_vector, saa_result)

    # Step 5: 可靠性评估
    reliability = _evaluate_reliability(
        bindings=bindings,
        risk_config=risk_config,
        market_cycle=market_cycle,
    )

    # Step 6: 组合寿命（基于绑定策略的加权平均）
    if bindings:
        portfolio_lifespan = round(
            sum(b.get("lifespan_months", 12) * b.get("weight", 0.1) for b in bindings) /
            sum(b.get("weight", 0.1) for b in bindings), 1
        )
        portfolio_health = round(
            sum(b.get("health_score", 75) * b.get("weight", 0.1) for b in bindings) /
            sum(b.get("weight", 0.1) for b in bindings), 1
        )
    else:
        portfolio_lifespan = 12
        portfolio_health = 75

    return {
        "portfolio_id": f"pf_{hash(str(profile_vector)) % 10000:04d}",
        "saa": saa_result,
        "taa": taa_result,
        "bindings": bindings,
        "risk_config": risk_config,
        "reliability": reliability,
        "portfolio_lifespan": portfolio_lifespan,
        "portfolio_health": portfolio_health,
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),  # 实时读取系统时钟
        "status": "draft",
    }


def _generate_risk_config(
    profile_vector: dict,
    saa_result: dict,
) -> dict[str, Any]:
    """生成风控配置.

    基于画像特征自动生成止损线、仓位上限等.
    """
    loss_aversion = profile_vector.get("loss_aversion", 0.5)
    risk_tolerance = profile_vector.get("risk_tolerance", 0.5)

    # 止损线：损失厌恶越高，止损越紧
    if loss_aversion > 0.7:
        stop_loss = 0.05  # 5%
    elif loss_aversion > 0.4:
        stop_loss = 0.08  # 8%
    else:
        stop_loss = 0.12  # 12%

    # 仓位上限：风险承受越高，仓位越高
    if risk_tolerance > 0.7:
        max_position = 0.30  # 单票30%
    elif risk_tolerance > 0.4:
        max_position = 0.20  # 单票20%
    else:
        max_position = 0.15  # 单票15%

    # 最大回撤硬止损
    if loss_aversion > 0.7:
        max_drawdown = 0.10  # 10%
    elif loss_aversion > 0.4:
        max_drawdown = 0.15  # 15%
    else:
        max_drawdown = 0.25  # 25%

    # 再平衡触发阈值
    if risk_tolerance > 0.7:
        rebalance_threshold = 0.10  # 10%
    else:
        rebalance_threshold = 0.05  # 5%

    return {
        "stop_loss": stop_loss,
        "max_position": max_position,
        "max_drawdown": max_drawdown,
        "rebalance_threshold": rebalance_threshold,
        "rationale": f"基于您的损失厌恶({loss_aversion:.0%})和风险承受({risk_tolerance:.0%})设定",
    }


def validate_portfolio(portfolio: dict) -> dict[str, Any]:
    """验证组合配置的合理性.

    Returns:
        {"valid": bool, "issues": list[str], "warnings": list[str]}
    """
    issues = []
    warnings = []

    # 检查权重总和
    saa_weights = portfolio.get("saa", {}).get("weights", {})
    total_weight = sum(saa_weights.values())
    if abs(total_weight - 1.0) > 0.01:
        issues.append(f"SAA权重总和不等于100%: {total_weight:.1%}")

    # 检查绑定数量
    bindings = portfolio.get("bindings", [])
    if len(bindings) < 3:
        warnings.append(f"策略绑定数量较少({len(bindings)}个)，建议至少3个")

    # 检查风控配置
    risk_config = portfolio.get("risk_config", {})
    if not risk_config.get("stop_loss"):
        issues.append("缺少止损线配置")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
    }


def _evaluate_reliability(
    bindings: list[dict],
    risk_config: dict,
    market_cycle: str,
) -> dict[str, Any]:
    """评估组合可靠性.

    基于策略绑定、风控配置、市场环境综合评估.
    """
    # 基础置信度
    base_confidence = 0.6

    # 策略数量调整
    n_strategies = len(bindings)
    if n_strategies >= 5:
        base_confidence += 0.1
    elif n_strategies < 3:
        base_confidence -= 0.1

    # 风控配置调整
    stop_loss = risk_config.get("stop_loss", 0.08)
    max_drawdown = risk_config.get("max_drawdown", 0.15)
    if stop_loss <= 0.05:
        base_confidence += 0.05
    if max_drawdown <= 0.1:
        base_confidence += 0.05

    # 市场环境调整
    if market_cycle in ["expansion", "recovery"]:
        base_confidence += 0.05
    elif market_cycle in ["contraction", "peak"]:
        base_confidence -= 0.05

    # 置信度范围限制
    confidence = max(0.3, min(0.95, base_confidence))

    return {
        "backtest_available": True,
        "stress_test_available": True,
        "monte_carlo_available": True,
        "confidence": round(confidence, 2),
        "reliability_level": _get_reliability_level(confidence),
    }


def _get_reliability_level(confidence: float) -> str:
    """根据置信度获取可靠性等级."""
    if confidence >= 0.8:
        return "高"
    elif confidence >= 0.6:
        return "中"
    else:
        return "低"


def get_portfolio_summary(portfolio: dict) -> dict[str, Any]:
    """获取组合摘要（用于前端展示）.

    Returns:
        {
            "total_strategies": 5,
            "stock_ratio": "60%",
            "top_sector": "科技",
            "risk_level": "稳健型",
            "expected_lifespan": "12个月",
        }
    """
    saa = portfolio.get("saa", {})
    taa = portfolio.get("taa", {})
    bindings = portfolio.get("bindings", [])

    weights = saa.get("weights", {})
    stock_ratio = weights.get("stock", 0)

    top_sector = "未知"
    if bindings:
        top_sector = bindings[0].get("sector_name", "未知")

    risk_profile = saa.get("risk_profile", {})
    risk_name = risk_profile.get("name", "未知")

    return {
        "total_strategies": len(bindings),
        "stock_ratio": f"{stock_ratio:.0%}",
        "top_sector": top_sector,
        "risk_level": risk_name,
        "expected_lifespan": f"{portfolio.get('portfolio_lifespan', 12)}个月",
        "health_score": portfolio.get("portfolio_health", 75),
    }
