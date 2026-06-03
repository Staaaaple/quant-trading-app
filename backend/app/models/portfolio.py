import datetime
from sqlalchemy import Column, Integer, String, JSON, Float, Boolean, DateTime, ForeignKey
from app.db.base import Base


class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    profile_id = Column(Integer, ForeignKey("investor_profiles.id"), nullable=True, index=True)

    name = Column(String(128), nullable=False, default="我的默认组合")
    config_json = Column(JSON, nullable=True)          # Full portfolio config
    backtest_result_json = Column(JSON, nullable=True) # Backtest results
    lifespan_months = Column(Float, nullable=True)     # Portfolio lifespan
    health_score = Column(Float, nullable=True)        # Portfolio health

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )
