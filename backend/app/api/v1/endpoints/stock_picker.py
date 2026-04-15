from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.stock_picker import (
    StockPoolRead,
    PickerRunRead,
    NotificationSettingsRead,
    NotificationSettingsUpdate,
    RunPickerRequest,
    WeeklyPickerSummary,
)
from app.services import stock_picker_service

router = APIRouter()


@router.post("/run", response_model=StockPoolRead)
def run_picker(
    *,
    db: Session = Depends(get_db),
    req: RunPickerRequest,
):
    try:
        pool = stock_picker_service.execute_picker(db, req.picker_id)
        return pool
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/pools", response_model=list[StockPoolRead])
def list_pools(
    *,
    db: Session = Depends(get_db),
    picker_id: str | None = None,
    skip: int = 0,
    limit: int = 100,
):
    return stock_picker_service.get_stock_pools(db, picker_id=picker_id, skip=skip, limit=limit)


@router.get("/pools/{pool_id}", response_model=StockPoolRead)
def get_pool(
    *,
    db: Session = Depends(get_db),
    pool_id: str,
):
    pool = stock_picker_service.get_stock_pool(db, pool_id)
    if not pool:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pool not found.")
    return pool


@router.get("/runs", response_model=list[PickerRunRead])
def list_runs(
    *,
    db: Session = Depends(get_db),
    picker_id: str | None = None,
    skip: int = 0,
    limit: int = 100,
):
    return stock_picker_service.get_picker_runs(db, picker_id=picker_id, skip=skip, limit=limit)


@router.get("/weekly-summary", response_model=WeeklyPickerSummary)
def weekly_summary(
    *,
    db: Session = Depends(get_db),
):
    return stock_picker_service.get_weekly_picker_summary(db)


@router.get("/notification-settings", response_model=NotificationSettingsRead)
def get_notification_settings(
    *,
    db: Session = Depends(get_db),
):
    return stock_picker_service.get_or_create_notification_settings(db)


@router.put("/notification-settings", response_model=NotificationSettingsRead)
def update_notification_settings(
    *,
    db: Session = Depends(get_db),
    obj_in: NotificationSettingsUpdate,
):
    return stock_picker_service.update_notification_settings(db, obj_in)
