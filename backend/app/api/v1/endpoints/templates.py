from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Any

from app.db.session import get_db
from app.models.strategy_template import StrategyTemplate
from app.services import template_manager

router = APIRouter()


@router.get("", response_model=list[dict[str, Any]])
def list_templates(
    family: str | None = None,
    risk_level: str | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """获取策略模板列表."""
    items = template_manager.list_templates(db, family=family, risk_level=risk_level, skip=skip, limit=limit)
    return [
        {
            "id": t.id,
            "template_id": t.template_id,
            "name": t.name,
            "family": t.family,
            "risk_level": t.risk_level,
            "suitable_cycles": t.suitable_cycles,
            "asset_classes": t.asset_classes,
            "health_score": t.health_score,
            "lifespan_months": t.lifespan_months,
            "param_space": t.param_space,
        }
        for t in items
    ]


@router.get("/{template_id}", response_model=dict[str, Any])
def get_template(template_id: str, db: Session = Depends(get_db)):
    """获取单个模板详情."""
    t = template_manager.get_template(db, template_id)
    if not t:
        raise HTTPException(status_code=404, detail="Template not found")
    return {
        "id": t.id,
        "template_id": t.template_id,
        "name": t.name,
        "family": t.family,
        "description": t.description,
        "code": t.code,
        "param_space": t.param_space,
        "suitable_cycles": t.suitable_cycles,
        "risk_level": t.risk_level,
        "asset_classes": t.asset_classes,
        "health_score": t.health_score,
        "lifespan_months": t.lifespan_months,
        "backtest_summary": t.backtest_summary,
    }


@router.get("/stats/families")
def get_family_stats(db: Session = Depends(get_db)):
    """获取各家族统计."""
    return template_manager.get_family_stats(db)


@router.post("/{template_id}/backtest")
def run_template_backtest(
    template_id: str,
    payload: dict[str, Any],
    db: Session = Depends(get_db),
):
    """运行模板回测（简化版）."""
    from app.services import template_runner

    symbols = payload.get("symbols", ["000001", "000002", "600000"])
    start_date = payload.get("start_date", "20240101")
    end_date = payload.get("end_date", "20240601")
    params = payload.get("params", {})
    asset_class = payload.get("asset_class", "stock")

    result = template_runner.run_batch_backtest(
        template_id=template_id,
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        params=params,
        asset_class=asset_class,
    )

    # 更新模板回测结果
    template_manager.update_template_backtest(
        db, template_id,
        backtest_summary=result,
    )

    return result
