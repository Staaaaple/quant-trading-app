from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.sync import (
    RealTradeCreate,
    RealTradeRead,
    RealPositionRead,
    SyncLogRead,
)
from app.services import sync_service

router = APIRouter()


@router.get("/trades", response_model=list[RealTradeRead])
def list_trades(
    *,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
):
    return sync_service.list_trades(db, skip=skip, limit=limit)


@router.post("/trades", response_model=RealTradeRead, status_code=status.HTTP_201_CREATED)
def create_trade(
    *,
    db: Session = Depends(get_db),
    obj_in: RealTradeCreate,
):
    return sync_service.create_trade(db, obj_in)


@router.delete("/trades/{trade_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_trade(
    *,
    db: Session = Depends(get_db),
    trade_id: int,
):
    sync_service.delete_trade(db, trade_id)
    return None


@router.get("/positions", response_model=list[RealPositionRead])
def list_positions(
    *,
    db: Session = Depends(get_db),
    strategy_id: str | None = None,
    skip: int = 0,
    limit: int = 100,
):
    return sync_service.list_positions(db, strategy_id=strategy_id, skip=skip, limit=limit)


@router.get("/logs", response_model=list[SyncLogRead])
def list_logs(
    *,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
):
    return sync_service.list_logs(db, skip=skip, limit=limit)


@router.get("/diff/{strategy_id}")
def get_diff(
    *,
    db: Session = Depends(get_db),
    strategy_id: str,
):
    return sync_service.get_diff(db, strategy_id)


@router.post("/import-csv")
def import_csv(
    *,
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
):
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
    content = file.file.read().decode("utf-8-sig")
    result = sync_service.import_csv_trades(db, content)
    return result


@router.post("/batch-sync")
def batch_sync(
    *,
    db: Session = Depends(get_db),
    items: list[dict[str, Any]],
):
    result = sync_service.batch_sync_signals(db, items)
    return result


@router.get("/daily-report/{strategy_id}")
def daily_report(
    *,
    db: Session = Depends(get_db),
    strategy_id: str,
    trade_date: str | None = None,
):
    return sync_service.generate_daily_report(db, strategy_id, trade_date)


@router.get("/pending-summary")
def pending_summary(
    *,
    db: Session = Depends(get_db),
    threshold_minutes: int = 30,
):
    from app.models.paper_trading import PaperSignal

    now = __import__("datetime").datetime.utcnow()
    all_pending = db.query(PaperSignal).filter(PaperSignal.status == "pending").all()
    overdue = [
        s for s in all_pending
        if s.signal_at and (now - s.signal_at).total_seconds() > threshold_minutes * 60
    ]
    return {
        "pending_count": len(all_pending),
        "overdue_count": len(overdue),
        "threshold_minutes": threshold_minutes,
    }
