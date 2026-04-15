from sqlalchemy.orm import Session
from app.models.risk_strategy import RiskStrategyConfig
from app.schemas.risk_strategy import RiskStrategyConfigCreate, RiskStrategyConfigUpdate


def get_config(db: Session, strategy_id: str):
    return db.query(RiskStrategyConfig).filter(RiskStrategyConfig.strategy_id == strategy_id).first()


def create_config(db: Session, obj_in: RiskStrategyConfigCreate):
    db_obj = RiskStrategyConfig(
        strategy_id=obj_in.strategy_id,
        max_position_pct=obj_in.max_position_pct,
        max_daily_drawdown=obj_in.max_daily_drawdown,
        blacklist=obj_in.blacklist,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_config(db: Session, db_obj: RiskStrategyConfig, obj_in: RiskStrategyConfigUpdate):
    db_obj.max_position_pct = obj_in.max_position_pct
    db_obj.max_daily_drawdown = obj_in.max_daily_drawdown
    db_obj.blacklist = obj_in.blacklist
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj
