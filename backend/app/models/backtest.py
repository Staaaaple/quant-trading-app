import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, JSON, ForeignKey
from app.db.base import Base


class BacktestResult(Base):
    __tablename__ = "backtest_results"

    id = Column(Integer, primary_key=True, index=True)
    backtest_id = Column(String(64), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    strategy_id = Column(String(64), index=True, nullable=False)
    status = Column(String(16), default="pending")  # pending / running / success / failed
    start_date = Column(String(16), nullable=True)
    end_date = Column(String(16), nullable=True)
    initial_cash = Column(Float, default=100000.0)
    metrics = Column(JSON, nullable=True)  # 收益指标等
    benchmark_metrics = Column(JSON, nullable=True)  # 对照组（买入并持有）收益指标
    logs = Column(Text, nullable=True)
    output_path = Column(String(256), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )
