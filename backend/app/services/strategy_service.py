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
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_strategy(db: Session, db_obj: Strategy, obj_in: StrategyUpdate):
    update_data = obj_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_strategy(db: Session, db_obj: Strategy):
    db.delete(db_obj)
    db.commit()
    return db_obj
