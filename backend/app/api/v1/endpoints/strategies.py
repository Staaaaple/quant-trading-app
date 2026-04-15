from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.strategy import StrategyCreate, StrategyRead, StrategyUpdate
from app.services import strategy_service

router = APIRouter()


@router.post("", response_model=StrategyRead, status_code=status.HTTP_201_CREATED)
def create_strategy(
    *,
    db: Session = Depends(get_db),
    obj_in: StrategyCreate,
):
    db_obj = strategy_service.get_strategy(db, strategy_id=obj_in.strategy_id)
    if db_obj:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Strategy with id '{obj_in.strategy_id}' already exists.",
        )
    return strategy_service.create_strategy(db, obj_in)


@router.get("", response_model=list[StrategyRead])
def list_strategies(
    *,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    strategy_type: str | None = None,
):
    return strategy_service.get_strategies(db, skip=skip, limit=limit, strategy_type=strategy_type)


@router.get("/{strategy_id}", response_model=StrategyRead)
def get_strategy(
    *,
    db: Session = Depends(get_db),
    strategy_id: str,
):
    db_obj = strategy_service.get_strategy(db, strategy_id=strategy_id)
    if not db_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Strategy '{strategy_id}' not found.",
        )
    return db_obj


@router.put("/{strategy_id}", response_model=StrategyRead)
def update_strategy(
    *,
    db: Session = Depends(get_db),
    strategy_id: str,
    obj_in: StrategyUpdate,
):
    db_obj = strategy_service.get_strategy(db, strategy_id=strategy_id)
    if not db_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Strategy '{strategy_id}' not found.",
        )
    return strategy_service.update_strategy(db, db_obj, obj_in)


@router.delete("/{strategy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_strategy(
    *,
    db: Session = Depends(get_db),
    strategy_id: str,
):
    db_obj = strategy_service.get_strategy(db, strategy_id=strategy_id)
    if not db_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Strategy '{strategy_id}' not found.",
        )
    strategy_service.delete_strategy(db, db_obj)
    return None
