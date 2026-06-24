from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_user_id
from app.db.session import get_db
from app.schemas.backtest import BacktestCreate, BacktestRead, BacktestRunPayload, BacktestUpdate
from app.services import backtest_service, demo_user_service
from app.services.demo_data import (
    DEMO_BACKTEST_BENCHMARK_METRICS,
    DEMO_BACKTEST_METRICS,
    get_demo_backtest_metrics,
)

router = APIRouter()


def _fill_demo_backtest(db_obj, symbols: list[str] | None = None) -> None:
    """用预置指标填充演示用户回测结果；不同策略/标的返回差异化指标."""
    import json

    seed_parts = [db_obj.strategy_id or "demo_default"]
    if symbols:
        seed_parts.extend(symbols)
    seed = "_".join(seed_parts)
    db_obj.status = "success"
    db_obj.metrics = get_demo_backtest_metrics(seed)
    db_obj.benchmark_metrics = DEMO_BACKTEST_BENCHMARK_METRICS
    db_obj.logs = json.dumps({
        "engine_summary": "演示回测：使用内部模拟数据",
        "trades": [],
        "candles": {},
    }, ensure_ascii=False)


@router.post("", response_model=BacktestRead, status_code=status.HTTP_201_CREATED)
def create_backtest(
    *,
    db: Session = Depends(get_db),
    obj_in: BacktestCreate,
    user_id: int = Depends(require_user_id),
):
    existing = backtest_service.get_backtest(db, backtest_id=obj_in.backtest_id)
    if existing:
        # 演示用户：同名回测直接覆盖，避免前端重复提交导致失败
        if existing.user_id is not None and demo_user_service.is_demo_user(db, existing.user_id):
            backtest_service.delete_backtest(db, existing)
        else:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Backtest with id '{obj_in.backtest_id}' already exists.",
            )
    obj_in.user_id = user_id
    return backtest_service.create_backtest_record(db, obj_in)


@router.get("", response_model=list[BacktestRead])
def list_backtests(
    *,
    db: Session = Depends(get_db),
    user_id: int = Depends(require_user_id),
    skip: int = 0,
    limit: int = 100,
):
    return (
        db.query(backtest_service.BacktestResult)
        .filter(backtest_service.BacktestResult.user_id == user_id)
        .order_by(backtest_service.BacktestResult.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/{backtest_id}", response_model=BacktestRead)
def get_backtest(
    *,
    db: Session = Depends(get_db),
    backtest_id: str,
    user_id: int = Depends(require_user_id),
):
    db_obj = backtest_service.get_backtest(db, backtest_id=backtest_id)
    if not db_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Backtest '{backtest_id}' not found.",
        )
    if db_obj.user_id is not None and db_obj.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    return db_obj


@router.delete("/{backtest_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_backtest(
    *,
    db: Session = Depends(get_db),
    backtest_id: str,
    user_id: int = Depends(require_user_id),
):
    db_obj = backtest_service.get_backtest(db, backtest_id=backtest_id)
    if not db_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Backtest '{backtest_id}' not found.",
        )
    if db_obj.user_id is not None and db_obj.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    backtest_service.delete_backtest(db, db_obj)
    return None


@router.post("/{backtest_id}/run", response_model=BacktestRead)
def run_backtest(
    *,
    db: Session = Depends(get_db),
    backtest_id: str,
    payload: BacktestRunPayload,
    user_id: int = Depends(require_user_id),
):
    db_obj = backtest_service.get_backtest(db, backtest_id=backtest_id)
    if not db_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Backtest '{backtest_id}' not found.",
        )
    if db_obj.user_id is not None and db_obj.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    if db_obj.status in ("running", "success"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Backtest '{backtest_id}' is already {db_obj.status}.",
        )
    if db_obj.user_id is not None and demo_user_service.is_demo_user(db, db_obj.user_id):
        _fill_demo_backtest(db_obj, payload.symbols)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    return backtest_service.run_backtest_for_strategy(
        db=db,
        backtest_id=backtest_id,
        strategy_id=db_obj.strategy_id,
        symbols=payload.symbols,
        start_date=payload.start_date,
        end_date=payload.end_date,
        initial_cash=payload.initial_cash,
    )
