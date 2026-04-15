from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.risk_strategy import RiskStrategyConfigCreate, RiskStrategyConfigRead, RiskStrategyConfigUpdate
from app.services import risk_strategy_service

router = APIRouter()


@router.get("/{strategy_id}", response_model=RiskStrategyConfigRead)
def get_risk_config(
    *,
    db: Session = Depends(get_db),
    strategy_id: str,
):
    db_obj = risk_strategy_service.get_config(db, strategy_id=strategy_id)
    if not db_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Risk config for strategy '{strategy_id}' not found.",
        )
    return db_obj


@router.post("", response_model=RiskStrategyConfigRead, status_code=status.HTTP_201_CREATED)
def create_risk_config(
    *,
    db: Session = Depends(get_db),
    obj_in: RiskStrategyConfigCreate,
):
    db_obj = risk_strategy_service.get_config(db, strategy_id=obj_in.strategy_id)
    if db_obj:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Risk config for strategy '{obj_in.strategy_id}' already exists.",
        )
    return risk_strategy_service.create_config(db, obj_in)


@router.put("/{strategy_id}", response_model=RiskStrategyConfigRead)
def update_risk_config(
    *,
    db: Session = Depends(get_db),
    strategy_id: str,
    obj_in: RiskStrategyConfigUpdate,
):
    db_obj = risk_strategy_service.get_config(db, strategy_id=strategy_id)
    if not db_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Risk config for strategy '{strategy_id}' not found.",
        )
    return risk_strategy_service.update_config(db, db_obj, obj_in)
