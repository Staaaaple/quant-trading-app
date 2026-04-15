from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey
from app.db.base import Base


class RiskStrategyConfig(Base):
    __tablename__ = "risk_strategy_configs"

    id = Column(Integer, primary_key=True)
    strategy_id = Column(String(64), ForeignKey("strategies.strategy_id"), nullable=False, unique=True)
    max_position_pct = Column(Float, default=0.2)
    max_daily_drawdown = Column(Float, default=0.05)
    blacklist = Column(Text, default="")
