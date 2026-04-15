import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from app.db.base import Base


class StrategyFlow(Base):
    __tablename__ = "strategy_flows"

    id = Column(Integer, primary_key=True)
    flow_id = Column(String(64), unique=True, nullable=False)
    name = Column(String(128), nullable=False)
    picker_strategy_id = Column(String(64), ForeignKey("strategies.strategy_id"), nullable=True)
    risk_strategy_id = Column(String(64), ForeignKey("strategies.strategy_id"), nullable=True)
    trade_strategy_id = Column(String(64), ForeignKey("strategies.strategy_id"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )
