"""策略模板管理服务.

提供策略模板的CRUD、家族分类、回测验证入口.
"""

from typing import Any
from sqlalchemy.orm import Session

from app.models.strategy_template import StrategyTemplate


FAMILIES = [
    "经典技术指标",
    "机器学习",
    "因子挖掘",
    "统计套利",
    "波动率交易",
    "行为金融",
    "事件驱动",
]


def create_template(
    db: Session,
    template_id: str,
    name: str,
    family: str,
    code: str,
    param_space: dict[str, Any],
    suitable_cycles: list[str],
    risk_level: str,
    asset_classes: list[str] | None = None,
    description: str | None = None,
) -> StrategyTemplate:
    """创建策略模板."""
    if family not in FAMILIES:
        raise ValueError(f"Unknown family: {family}. Must be one of {FAMILIES}")

    tmpl = StrategyTemplate(
        template_id=template_id,
        name=name,
        family=family,
        description=description,
        code=code,
        param_space=param_space,
        suitable_cycles=suitable_cycles,
        risk_level=risk_level,
        asset_classes=asset_classes or ["stock", "etf"],
        health_score=60.0,  # 初始值，回测后更新
        lifespan_months=12.0,  # 初始值
    )
    db.add(tmpl)
    db.commit()
    db.refresh(tmpl)
    return tmpl


def get_template(db: Session, template_id: str) -> StrategyTemplate | None:
    """获取单个模板."""
    return (
        db.query(StrategyTemplate)
        .filter(StrategyTemplate.template_id == template_id, StrategyTemplate.is_active == True)
        .first()
    )


def list_templates(
    db: Session,
    family: str | None = None,
    risk_level: str | None = None,
    suitable_cycle: str | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[StrategyTemplate]:
    """列表查询，支持筛选."""
    q = db.query(StrategyTemplate).filter(StrategyTemplate.is_active == True)
    if family:
        q = q.filter(StrategyTemplate.family == family)
    if risk_level:
        q = q.filter(StrategyTemplate.risk_level == risk_level)
    if suitable_cycle:
        # suitable_cycles 是JSON列表，用contains
        q = q.filter(StrategyTemplate.suitable_cycles.contains([suitable_cycle]))
    return q.offset(skip).limit(limit).all()


def update_template_backtest(
    db: Session,
    template_id: str,
    backtest_summary: dict[str, Any],
    health_score: float | None = None,
    lifespan_months: float | None = None,
) -> StrategyTemplate | None:
    """更新模板回测结果."""
    tmpl = get_template(db, template_id)
    if not tmpl:
        return None
    tmpl.backtest_summary = backtest_summary
    if health_score is not None:
        tmpl.health_score = health_score
    if lifespan_months is not None:
        tmpl.lifespan_months = lifespan_months
    db.commit()
    db.refresh(tmpl)
    return tmpl


def delete_template(db: Session, template_id: str) -> bool:
    """软删除模板."""
    tmpl = get_template(db, template_id)
    if not tmpl:
        return False
    tmpl.is_active = False
    db.commit()
    return True


def get_family_stats(db: Session) -> list[dict[str, Any]]:
    """获取各家族的模板统计."""
    from sqlalchemy import func
    results = (
        db.query(
            StrategyTemplate.family,
            func.count(StrategyTemplate.id).label("count"),
            func.avg(StrategyTemplate.health_score).label("avg_health"),
        )
        .filter(StrategyTemplate.is_active == True)
        .group_by(StrategyTemplate.family)
        .all()
    )
    return [
        {
            "family": r.family,
            "count": r.count,
            "avg_health": round(r.avg_health or 0, 1),
        }
        for r in results
    ]
