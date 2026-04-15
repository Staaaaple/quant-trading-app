from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.strategy_flow import StrategyFlowCreate, StrategyFlowRead, StrategyFlowUpdate
from app.services import strategy_flow_service, strategy_service
from app.models.strategy import Strategy

router = APIRouter()


def _validate_strategy_refs(db: Session, obj_in: StrategyFlowCreate | StrategyFlowUpdate):
    sids = []
    if obj_in.picker_strategy_id:
        sids.append(obj_in.picker_strategy_id)
    if obj_in.risk_strategy_id:
        sids.append(obj_in.risk_strategy_id)
    if obj_in.trade_strategy_id:
        sids.append(obj_in.trade_strategy_id)

    if getattr(obj_in, "trade_strategy_id", None) is None and getattr(obj_in, "flow_id", None) is None:
        # For updates, trade_strategy_id can be omitted; handled below
        pass

    for sid in sids:
        s = strategy_service.get_strategy(db, sid)
        if not s:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Strategy '{sid}' does not exist.",
            )
        if s.type == "flow":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot bind a strategy flow ('{sid}') inside another flow.",
            )


@router.post("", response_model=StrategyFlowRead, status_code=status.HTTP_201_CREATED)
def create_flow(
    *,
    db: Session = Depends(get_db),
    obj_in: StrategyFlowCreate,
):
    db_obj = strategy_flow_service.get_flow(db, flow_id=obj_in.flow_id)
    if db_obj:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Strategy flow with id '{obj_in.flow_id}' already exists.",
        )
    if not obj_in.trade_strategy_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Trade strategy is required.",
        )
    _validate_strategy_refs(db, obj_in)
    return strategy_flow_service.create_flow(db, obj_in)


@router.get("", response_model=list[StrategyFlowRead])
def list_flows(
    *,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
):
    return strategy_flow_service.list_flows(db, skip=skip, limit=limit)


@router.get("/{flow_id}", response_model=StrategyFlowRead)
def get_flow(
    *,
    db: Session = Depends(get_db),
    flow_id: str,
):
    db_obj = strategy_flow_service.get_flow(db, flow_id=flow_id)
    if not db_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Strategy flow '{flow_id}' not found.",
        )
    return db_obj


@router.put("/{flow_id}", response_model=StrategyFlowRead)
def update_flow(
    *,
    db: Session = Depends(get_db),
    flow_id: str,
    obj_in: StrategyFlowUpdate,
):
    db_obj = strategy_flow_service.get_flow(db, flow_id=flow_id)
    if not db_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Strategy flow '{flow_id}' not found.",
        )
    _validate_strategy_refs(db, obj_in)
    return strategy_flow_service.update_flow(db, db_obj, obj_in)


@router.delete("/{flow_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_flow(
    *,
    db: Session = Depends(get_db),
    flow_id: str,
):
    db_obj = strategy_flow_service.get_flow(db, flow_id=flow_id)
    if not db_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Strategy flow '{flow_id}' not found.",
        )
    strategy_flow_service.delete_flow(db, db_obj)
    return None
