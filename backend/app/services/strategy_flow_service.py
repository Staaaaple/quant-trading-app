from sqlalchemy.orm import Session
from app.models.strategy_flow import StrategyFlow
from app.schemas.strategy_flow import StrategyFlowCreate, StrategyFlowUpdate


def get_flow(db: Session, flow_id: str):
    return db.query(StrategyFlow).filter(StrategyFlow.flow_id == flow_id).first()


def list_flows(db: Session, skip: int = 0, limit: int = 100):
    return db.query(StrategyFlow).order_by(StrategyFlow.created_at.desc()).offset(skip).limit(limit).all()


def create_flow(db: Session, obj_in: StrategyFlowCreate):
    db_obj = StrategyFlow(
        flow_id=obj_in.flow_id,
        name=obj_in.name,
        picker_strategy_id=obj_in.picker_strategy_id,
        risk_strategy_id=obj_in.risk_strategy_id,
        trade_strategy_id=obj_in.trade_strategy_id,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_flow(db: Session, db_obj: StrategyFlow, obj_in: StrategyFlowUpdate):
    update_data = obj_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_flow(db: Session, db_obj: StrategyFlow):
    db.delete(db_obj)
    db.commit()


def get_flows_by_strategy_id(db: Session, strategy_id: str):
    return (
        db.query(StrategyFlow)
        .filter(
            (StrategyFlow.picker_strategy_id == strategy_id)
            | (StrategyFlow.risk_strategy_id == strategy_id)
            | (StrategyFlow.trade_strategy_id == strategy_id)
        )
        .all()
    )
