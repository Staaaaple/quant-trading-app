from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.paper_trading import (
    PaperTradingSessionCreate,
    PaperTradingSessionRead,
    PaperTradingSessionUpdate,
    PaperSignalRead,
)
from app.services import paper_trading_service
from app.models.paper_trading import PaperSignal

router = APIRouter()


@router.post("/sessions", response_model=PaperTradingSessionRead, status_code=status.HTTP_201_CREATED)
def create_session(
    *,
    db: Session = Depends(get_db),
    obj_in: PaperTradingSessionCreate,
):
    existing = paper_trading_service.get_session(db, session_id=obj_in.session_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Paper trading session with id '{obj_in.session_id}' already exists.",
        )
    return paper_trading_service.create_session(db, obj_in)


@router.get("/sessions", response_model=list[PaperTradingSessionRead])
def list_sessions(
    *,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
):
    return paper_trading_service.list_sessions(db, skip=skip, limit=limit)


@router.get("/sessions/{session_id}", response_model=PaperTradingSessionRead)
def get_session(
    *,
    db: Session = Depends(get_db),
    session_id: str,
):
    db_obj = paper_trading_service.get_session(db, session_id=session_id)
    if not db_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paper trading session '{session_id}' not found.",
        )
    return db_obj


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(
    *,
    db: Session = Depends(get_db),
    session_id: str,
):
    db_obj = paper_trading_service.get_session(db, session_id=session_id)
    if not db_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paper trading session '{session_id}' not found.",
        )
    paper_trading_service.delete_session(db, db_obj)
    return None


@router.post("/sessions/{session_id}/run", response_model=PaperTradingSessionRead)
def run_session(
    *,
    db: Session = Depends(get_db),
    session_id: str,
):
    db_obj = paper_trading_service.get_session(db, session_id=session_id)
    if not db_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paper trading session '{session_id}' not found.",
        )
    if db_obj.status == "running":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Paper trading session '{session_id}' is already running.",
        )
    try:
        return paper_trading_service.run_paper_trading_session(db, session_id=session_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run paper trading session: {e}",
        )


@router.post("/sessions/{session_id}/stop", response_model=PaperTradingSessionRead)
def stop_session(
    *,
    db: Session = Depends(get_db),
    session_id: str,
    obj_in: PaperTradingSessionUpdate | None = None,
):
    db_obj = paper_trading_service.get_session(db, session_id=session_id)
    if not db_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paper trading session '{session_id}' not found.",
        )
    if db_obj.status != "running":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Paper trading session '{session_id}' is not running.",
        )
    update = PaperTradingSessionUpdate(status="stopped")
    if obj_in and obj_in.stop_reason:
        update.stop_reason = obj_in.stop_reason
    return paper_trading_service.update_session(db, db_obj, update)


@router.get("/signals", response_model=list[PaperSignalRead])
def list_signals(
    *,
    db: Session = Depends(get_db),
    strategy_id: str | None = None,
    status: str | None = None,
    skip: int = 0,
    limit: int = 100,
):
    query = db.query(PaperSignal).order_by(PaperSignal.signal_at.desc())
    if strategy_id:
        query = query.filter(PaperSignal.strategy_id == strategy_id)
    if status:
        query = query.filter(PaperSignal.status == status)
    return query.offset(skip).limit(limit).all()
