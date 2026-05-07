from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.strategy import Strategy
from app.schemas.strategy import StrategyCreate, StrategyUpdate


def get_strategy(db: Session, strategy_id: str):
    return db.query(Strategy).filter(Strategy.strategy_id == strategy_id).first()


def get_strategies(db: Session, skip: int = 0, limit: int = 100, strategy_type: str | None = None):
    q = db.query(Strategy)
    if strategy_type:
        q = q.filter(Strategy.type == strategy_type)
    return q.offset(skip).limit(limit).all()


def create_strategy(db: Session, obj_in: StrategyCreate):
    db_obj = Strategy(
        strategy_id=obj_in.strategy_id,
        name=obj_in.name,
        description=obj_in.description,
        code=obj_in.code,
        type=obj_in.type or "trade",
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    # Auto-trigger DNA sequencing after strategy creation
    from app.services import dna_sequencer
    dna_sequencer.sequence_strategy(db_obj.strategy_id, db_obj.code, db)
    return db_obj

def update_strategy(db: Session, db_obj: Strategy, obj_in: StrategyUpdate):
    from app.services import dna_sequencer
    update_data = obj_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    # Re-sequence if code was updated
    if "code" in update_data:
        dna_sequencer.sequence_strategy(db_obj.strategy_id, db_obj.code, db)
    return db_obj


def update_strategy(db: Session, db_obj: Strategy, obj_in: StrategyUpdate):
    from app.services import dna_sequencer, phylogeny_service
    update_data = obj_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    # Re-sequence if code was updated
    if "code" in update_data:
        dna_sequencer.sequence_strategy(db_obj.strategy_id, db_obj.code, db)
    # Recompute phylogeny
    try:
        phylogeny_service.compute_all_phylogeny(db)
    except Exception:
        pass
    return db_obj


def delete_strategy(db: Session, db_obj: Strategy):
    from app.services.strategy_flow_service import get_flows_by_strategy_id

    flows = get_flows_by_strategy_id(db, db_obj.strategy_id)
    if flows:
        names = ", ".join([f.name for f in flows])
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Strategy is referenced by strategy flow(s): {names}. Please remove the references first.",
        )
    db.delete(db_obj)
    db.commit()
    return db_obj
