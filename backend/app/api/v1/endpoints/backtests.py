from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.backtest import BacktestCreate, BacktestRead, BacktestRunPayload, BacktestUpdate
from app.services import backtest_service

router = APIRouter()


@router.post("", response_model=BacktestRead, status_code=status.HTTP_201_CREATED)
def create_backtest(
    *,
    db: Session = Depends(get_db),
    obj_in: BacktestCreate,
):
    existing = backtest_service.get_backtest(db, backtest_id=obj_in.backtest_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Backtest with id '{obj_in.backtest_id}' already exists.",
        )
    return backtest_service.create_backtest_record(db, obj_in)


@router.get("", response_model=list[BacktestRead])
def list_backtests(
    *,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
):
    return backtest_service.get_backtests(db, skip=skip, limit=limit)


@router.get("/{backtest_id}", response_model=BacktestRead)
def get_backtest(
    *,
    db: Session = Depends(get_db),
    backtest_id: str,
):
    db_obj = backtest_service.get_backtest(db, backtest_id=backtest_id)
    if not db_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Backtest '{backtest_id}' not found.",
        )
    return db_obj


@router.delete("/{backtest_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_backtest(
    *,
    db: Session = Depends(get_db),
    backtest_id: str,
):
    db_obj = backtest_service.get_backtest(db, backtest_id=backtest_id)
    if not db_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Backtest '{backtest_id}' not found.",
        )
    backtest_service.delete_backtest(db, db_obj)
    return None


@router.post("/{backtest_id}/run", response_model=BacktestRead)
def run_backtest(
    *,
    db: Session = Depends(get_db),
    backtest_id: str,
    payload: BacktestRunPayload,
):
    db_obj = backtest_service.get_backtest(db, backtest_id=backtest_id)
    if not db_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Backtest '{backtest_id}' not found.",
        )
    if db_obj.status in ("running", "success"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Backtest '{backtest_id}' is already {db_obj.status}.",
        )
    return backtest_service.run_backtest_for_strategy(
        db=db,
        backtest_id=backtest_id,
        strategy_id=db_obj.strategy_id,
        symbols=payload.symbols,
        start_date=payload.start_date,
        end_date=payload.end_date,
        initial_cash=payload.initial_cash,
    )
