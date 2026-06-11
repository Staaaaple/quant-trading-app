"""策略寿命监控服务 — 定时自动化监控 + 预警.

功能:
1. 每月1日凌晨3:00自动执行寿命更新
2. 遍历所有活跃策略，重新计算寿命
3. 检测寿命变化，触发预警
4. 写入寿命历史表
5. 组合层面寿命聚合
6. 替代策略推荐

预警规则:
- 黄色预警: 寿命减少 > 20% 或 寿命 < 6月
- 红色预警: 寿命减少 > 40% 或 寿命 < 3月
"""

import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.strategy_dna import StrategyDNA, StrategyPhylogeny
from app.models.lifespan_history import LifespanHistory, PortfolioLifespanHistory
from app.models.portfolio import Portfolio
from app.services.lifespan_service import calculate_lifespan

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# 1. 市场环境因子计算
# ═══════════════════════════════════════════════════════════════

def calculate_market_factors(db: Session) -> dict[str, float]:
    """计算当前市场环境因子.

    Returns:
        {
            "volatility_factor": 波动率加速因子 (高波1.3 / 低波0.85),
            "cycle_factor": 周期适配因子 (匹配1.0 / 相邻0.9 / 不适0.7),
            "crowding_factor": 拥挤度因子 (sigmoid映射),
        }
    """
    # 简化实现: 从最近的市场信号获取
    try:
        from app.models.market_signal import MarketSignal
        latest_signal = db.query(MarketSignal).order_by(
            MarketSignal.date.desc()
        ).first()

        if not latest_signal:
            return {"volatility_factor": 1.0, "cycle_factor": 1.0, "crowding_factor": 1.0}

        # 波动率因子: 基于市场情绪
        mood = getattr(latest_signal, "market_mood", "neutral")
        volatility_map = {
            "extreme_greed": 1.2,
            "greed": 1.1,
            "neutral": 1.0,
            "fear": 1.15,
            "extreme_fear": 1.3,
        }
        volatility_factor = volatility_map.get(mood, 1.0)

        # 周期因子: 基于复合评分
        composite = getattr(latest_signal, "composite_score", 50)
        if composite >= 70:
            cycle_factor = 1.0  # 扩张期匹配
        elif composite >= 50:
            cycle_factor = 0.95
        elif composite >= 30:
            cycle_factor = 0.9
        else:
            cycle_factor = 0.8  # 收缩期

        # 拥挤度因子: 简化计算
        crowding_factor = 1.0  # 默认无拥挤

        return {
            "volatility_factor": round(volatility_factor, 2),
            "cycle_factor": round(cycle_factor, 2),
            "crowding_factor": round(crowding_factor, 2),
        }
    except Exception as e:
        logger.warning(f"计算市场环境因子失败: {e}")
        return {"volatility_factor": 1.0, "cycle_factor": 1.0, "crowding_factor": 1.0}


# ═══════════════════════════════════════════════════════════════
# 2. 单策略寿命更新
# ═══════════════════════════════════════════════════════════════

def update_strategy_lifespan(
    db: Session,
    strategy_id: str,
    market_factors: dict[str, float],
) -> dict[str, Any] | None:
    """更新单个策略的寿命（含市场环境调整）.

    Args:
        db: 数据库会话
        strategy_id: 策略ID
        market_factors: 市场环境因子

    Returns:
        更新后的寿命信息，或None如果策略不存在
    """
    # 获取策略DNA
    dna = db.query(StrategyDNA).filter(
        StrategyDNA.strategy_id == strategy_id,
        StrategyDNA.status == "success",
    ).first()

    if not dna:
        return None

    # 获取同质化风险
    phylo = db.query(StrategyPhylogeny).filter(
        StrategyPhylogeny.strategy_id == strategy_id
    ).first()
    homogeneity_risk = phylo.homogeneity_risk if phylo else 0.0

    # 基础寿命计算
    base_result = calculate_lifespan(
        metabolic_rate=dna.metabolic_rate or 0.0,
        niche_width=dna.niche_width or 0.0,
        metabolic_syndrome=dna.metabolic_syndrome or False,
        homogeneity_risk=homogeneity_risk,
    )

    # 应用市场环境因子
    adjusted_lifespan = base_result["lifespan_months"]
    adjusted_lifespan *= market_factors.get("volatility_factor", 1.0)
    adjusted_lifespan *= market_factors.get("cycle_factor", 1.0)
    adjusted_lifespan *= market_factors.get("crowding_factor", 1.0)
    adjusted_lifespan = max(1, round(adjusted_lifespan))

    # 更新阶段
    if adjusted_lifespan > 36:
        phase = "young"
    elif adjusted_lifespan >= 12:
        phase = "mature"
    elif adjusted_lifespan >= 3:
        phase = "aging"
    else:
        phase = "endangered"

    # 获取上月寿命（用于变化检测）
    prev_record = db.query(LifespanHistory).filter(
        LifespanHistory.strategy_id == strategy_id
    ).order_by(LifespanHistory.date.desc()).first()

    prev_lifespan = prev_record.lifespan_months if prev_record else base_result["lifespan_months"]
    lifespan_change_pct = None
    if prev_lifespan and prev_lifespan > 0:
        lifespan_change_pct = (adjusted_lifespan - prev_lifespan) / prev_lifespan * 100

    # 预警检测
    alert_level = "none"
    alert_reason = None

    if adjusted_lifespan < 3:
        alert_level = "red"
        alert_reason = f"寿命仅剩{adjusted_lifespan}个月，策略濒临失效"
    elif lifespan_change_pct is not None and lifespan_change_pct < -40:
        alert_level = "red"
        alert_reason = f"寿命较上月下降{abs(lifespan_change_pct):.0f}%，超过40%阈值"
    elif adjusted_lifespan < 6:
        alert_level = "yellow"
        alert_reason = f"寿命仅剩{adjusted_lifespan}个月，建议关注"
    elif lifespan_change_pct is not None and lifespan_change_pct < -20:
        alert_level = "yellow"
        alert_reason = f"寿命较上月下降{abs(lifespan_change_pct):.0f}%，超过20%阈值"

    # 健康度计算（基于寿命阶段 + 市场环境）
    health_score = min(100, max(0,
        adjusted_lifespan * 2 +  # 基础: 每月2分
        (50 if phase == "young" else 30 if phase == "mature" else 10 if phase == "aging" else 0) +
        (10 if market_factors.get("cycle_factor", 1.0) >= 0.95 else 0)
    ))

    # 写入历史表
    history = LifespanHistory(
        strategy_id=strategy_id,
        date=datetime.utcnow(),
        lifespan_months=adjusted_lifespan,
        lifespan_phase=phase,
        health_score=round(health_score, 1),
        aging_velocity=base_result["aging_velocity"],
        metabolic_rate=dna.metabolic_rate or 0.0,
        niche_width=dna.niche_width or 0.0,
        homogeneity_risk=homogeneity_risk,
        metabolic_syndrome=1 if dna.metabolic_syndrome else 0,
        volatility_factor=market_factors.get("volatility_factor", 1.0),
        cycle_factor=market_factors.get("cycle_factor", 1.0),
        crowding_factor=market_factors.get("crowding_factor", 1.0),
        alert_level=alert_level,
        alert_reason=alert_reason,
        lifespan_change_pct=round(lifespan_change_pct, 2) if lifespan_change_pct is not None else None,
        prev_lifespan_months=prev_lifespan,
    )
    db.add(history)

    # 更新DNA记录
    dna.lifespan_months = adjusted_lifespan
    dna.lifespan_phase = phase
    dna.aging_velocity = base_result["aging_velocity"]

    return {
        "strategy_id": strategy_id,
        "lifespan_months": adjusted_lifespan,
        "lifespan_phase": phase,
        "health_score": round(health_score, 1),
        "alert_level": alert_level,
        "alert_reason": alert_reason,
        "lifespan_change_pct": lifespan_change_pct,
        "market_factors": market_factors,
    }


# ═══════════════════════════════════════════════════════════════
# 3. 批量寿命更新（定时任务入口）
# ═══════════════════════════════════════════════════════════════

def run_monthly_lifespan_check(db: Session) -> dict[str, Any]:
    """每月寿命检查定时任务入口.

    Args:
        db: 数据库会话

    Returns:
        执行结果统计
    """
    logger.info("[LifespanMonitor] 开始月度寿命检查...")
    start_time = datetime.utcnow()

    # 1. 计算市场环境因子
    market_factors = calculate_market_factors(db)
    logger.info(f"[LifespanMonitor] 市场环境因子: {market_factors}")

    # 2. 获取所有活跃策略
    active_dnas = db.query(StrategyDNA).filter(
        StrategyDNA.status == "success"
    ).all()

    logger.info(f"[LifespanMonitor] 发现 {len(active_dnas)} 个活跃策略")

    # 3. 逐个更新寿命
    updated = []
    alerts = {"yellow": [], "red": []}
    errors = []

    for dna in active_dnas:
        try:
            result = update_strategy_lifespan(db, dna.strategy_id, market_factors)
            if result:
                updated.append(result)
                if result["alert_level"] == "yellow":
                    alerts["yellow"].append(result)
                elif result["alert_level"] == "red":
                    alerts["red"].append(result)
        except Exception as e:
            logger.error(f"[LifespanMonitor] 更新 {dna.strategy_id} 失败: {e}")
            errors.append({"strategy_id": dna.strategy_id, "error": str(e)})

    # 4. 提交数据库
    db.commit()

    # 5. 更新组合层面寿命
    portfolio_results = update_portfolio_lifespans(db)

    # 6. 汇总
    elapsed = (datetime.utcnow() - start_time).total_seconds()

    summary = {
        "run_at": start_time.isoformat(),
        "elapsed_seconds": round(elapsed, 2),
        "total_strategies": len(active_dnas),
        "updated": len(updated),
        "yellow_alerts": len(alerts["yellow"]),
        "red_alerts": len(alerts["red"]),
        "errors": len(errors),
        "market_factors": market_factors,
        "alert_details": {
            "yellow": [{"id": r["strategy_id"], "reason": r["alert_reason"]} for r in alerts["yellow"]],
            "red": [{"id": r["strategy_id"], "reason": r["alert_reason"]} for r in alerts["red"]],
        },
        "portfolio_updates": portfolio_results,
        "error_details": errors,
    }

    logger.info(
        f"[LifespanMonitor] 完成: {summary['updated']}/{summary['total_strategies']} 个策略更新, "
        f"黄灯{summary['yellow_alerts']}个, 红灯{summary['red_alerts']}个, "
        f"耗时{elapsed:.1f}秒"
    )

    return summary


# ═══════════════════════════════════════════════════════════════
# 4. 组合层面寿命聚合
# ═══════════════════════════════════════════════════════════════

def update_portfolio_lifespans(db: Session) -> list[dict[str, Any]]:
    """更新所有活跃组合的寿命.

    组合寿命 = min(各组件寿命)
    组合健康度 = 加权平均(各组件健康度)

    Returns:
        更新结果列表
    """
    from app.models.portfolio_holding import PortfolioHolding

    results = []

    # 获取所有活跃组合
    portfolios = db.query(Portfolio).filter(
        Portfolio.status == "active"
    ).all()

    for portfolio in portfolios:
        try:
            # 获取组合持仓
            holdings = db.query(PortfolioHolding).filter(
                PortfolioHolding.portfolio_id == portfolio.id
            ).all()

            if not holdings:
                continue

            # 获取各组件的寿命
            component_lifespans = []
            component_healths = []
            endangered_count = 0

            for holding in holdings:
                # 查找对应策略的DNA
                dna = db.query(StrategyDNA).filter(
                    StrategyDNA.strategy_id == holding.strategy_id,
                    StrategyDNA.status == "success",
                ).first()

                if dna and dna.lifespan_months:
                    component_lifespans.append(dna.lifespan_months)
                    # 健康度估算
                    health = min(100, dna.lifespan_months * 2)
                    component_healths.append(health)
                    if dna.lifespan_months < 3:
                        endangered_count += 1

            if not component_lifespans:
                continue

            # 组合层面指标
            portfolio_lifespan = min(component_lifespans)
            portfolio_health = sum(component_healths) / len(component_healths)

            # 预警
            alert_level = "none"
            alert_reason = None
            if portfolio_lifespan < 3 or endangered_count > 0:
                alert_level = "red"
                alert_reason = f"组合寿命仅剩{portfolio_lifespan}个月，含{endangered_count}个濒危组件"
            elif portfolio_lifespan < 6:
                alert_level = "yellow"
                alert_reason = f"组合寿命仅剩{portfolio_lifespan}个月"

            # 写入历史表
            history = PortfolioLifespanHistory(
                portfolio_id=str(portfolio.id),
                date=datetime.utcnow(),
                portfolio_lifespan_months=portfolio_lifespan,
                portfolio_health_score=round(portfolio_health, 1),
                component_count=len(component_lifespans),
                endangered_count=endangered_count,
                alert_level=alert_level,
                alert_reason=alert_reason,
            )
            db.add(history)

            results.append({
                "portfolio_id": str(portfolio.id),
                "lifespan_months": portfolio_lifespan,
                "health_score": round(portfolio_health, 1),
                "endangered_count": endangered_count,
                "alert_level": alert_level,
            })

        except Exception as e:
            logger.error(f"[LifespanMonitor] 更新组合 {portfolio.id} 失败: {e}")

    db.commit()
    return results


# ═══════════════════════════════════════════════════════════════
# 5. 替代策略推荐
# ═══════════════════════════════════════════════════════════════

def recommend_replacement_strategies(
    db: Session,
    strategy_id: str,
    top_k: int = 3,
) -> list[dict[str, Any]]:
    """为寿命到期的策略推荐替代策略.

    推荐逻辑:
    1. 同家族内选择寿命最长的
    2. 相似策略（同质化检测）中排除
    3. 按健康度排序

    Args:
        db: 数据库会话
        strategy_id: 原策略ID
        top_k: 推荐数量

    Returns:
        推荐策略列表
    """
    # 获取原策略信息
    original = db.query(StrategyDNA).filter(
        StrategyDNA.strategy_id == strategy_id
    ).first()

    if not original:
        return []

    # 获取同家族的其他策略
    candidates = db.query(StrategyDNA).filter(
        StrategyDNA.status == "success",
        StrategyDNA.strategy_id != strategy_id,
    ).all()

    # 排除同质化高的策略
    phylo = db.query(StrategyPhylogeny).filter(
        StrategyPhylogeny.strategy_id == strategy_id
    ).first()

    excluded_ids = set()
    if phylo and phylo.relatives:
        for rel in phylo.relatives:
            if rel.get("similarity", 0) > 0.8:  # 相似度>80%排除
                excluded_ids.add(rel.get("strategy_id"))

    # 评分排序
    scored = []
    for cand in candidates:
        if cand.strategy_id in excluded_ids:
            continue

        score = 0
        # 寿命越长越好
        score += (cand.lifespan_months or 0) * 3
        # 健康度
        health = min(100, (cand.lifespan_months or 0) * 2)
        score += health
        # 同家族加分
        if original.family_id and cand.family_id == original.family_id:
            score += 20
        # 代谢率低加分（更稳定）
        score += (1 - (cand.metabolic_rate or 0)) * 10

        scored.append({
            "strategy_id": cand.strategy_id,
            "family_id": cand.family_id,
            "lifespan_months": cand.lifespan_months,
            "lifespan_phase": cand.lifespan_phase,
            "health_score": health,
            "score": score,
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]


# ═══════════════════════════════════════════════════════════════
# 6. 查询接口
# ═══════════════════════════════════════════════════════════════

def get_lifespan_trend(
    db: Session,
    strategy_id: str,
    months: int = 6,
) -> list[dict[str, Any]]:
    """获取策略寿命趋势.

    Args:
        db: 数据库会话
        strategy_id: 策略ID
        months: 查询月数

    Returns:
        寿命历史列表
    """
    since = datetime.utcnow() - timedelta(days=months * 30)

    records = db.query(LifespanHistory).filter(
        LifespanHistory.strategy_id == strategy_id,
        LifespanHistory.date >= since,
    ).order_by(LifespanHistory.date.asc()).all()

    return [
        {
            "date": r.date.isoformat(),
            "lifespan_months": r.lifespan_months,
            "lifespan_phase": r.lifespan_phase,
            "health_score": r.health_score,
            "alert_level": r.alert_level,
            "lifespan_change_pct": r.lifespan_change_pct,
        }
        for r in records
    ]


def get_active_alerts(db: Session) -> dict[str, list[dict[str, Any]]]:
    """获取当前活跃预警.

    Returns:
        {"yellow": [...], "red": [...]}
    """
    # 获取最新的记录
    latest_date = db.query(func.max(LifespanHistory.date)).scalar()

    if not latest_date:
        return {"yellow": [], "red": []}

    alerts = db.query(LifespanHistory).filter(
        LifespanHistory.date >= latest_date - timedelta(hours=1),
        LifespanHistory.alert_level.in_(["yellow", "red"]),
    ).all()

    result = {"yellow": [], "red": []}
    for alert in alerts:
        item = {
            "strategy_id": alert.strategy_id,
            "lifespan_months": alert.lifespan_months,
            "lifespan_phase": alert.lifespan_phase,
            "health_score": alert.health_score,
            "alert_reason": alert.alert_reason,
            "date": alert.date.isoformat(),
        }
        result[alert.alert_level].append(item)

    return result


def get_portfolio_lifespan_status(db: Session, portfolio_id: str) -> dict[str, Any] | None:
    """获取组合寿命状态.

    Args:
        db: 数据库会话
        portfolio_id: 组合ID

    Returns:
        组合寿命状态
    """
    latest = db.query(PortfolioLifespanHistory).filter(
        PortfolioLifespanHistory.portfolio_id == portfolio_id,
    ).order_by(PortfolioLifespanHistory.date.desc()).first()

    if not latest:
        return None

    return {
        "portfolio_id": portfolio_id,
        "lifespan_months": latest.portfolio_lifespan_months,
        "health_score": latest.portfolio_health_score,
        "component_count": latest.component_count,
        "endangered_count": latest.endangered_count,
        "alert_level": latest.alert_level,
        "alert_reason": latest.alert_reason,
        "updated_at": latest.date.isoformat(),
    }
