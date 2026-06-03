import datetime
from sqlalchemy import Column, Integer, String, JSON, Float, Boolean, DateTime, ForeignKey
from app.db.base import Base


class PortfolioHolding(Base):
    __tablename__ = "portfolio_holdings"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False, index=True)

    symbol = Column(String(16), nullable=False)          # 标的代码 e.g. 510300
    name = Column(String(64), nullable=True)             # 标的名称
    asset_class = Column(String(16), nullable=False)     # stock/bond/commodity/cash
    weight = Column(Float, nullable=False)               # 配置权重 0-1

    # 绑定的策略
    strategy_id = Column(String(64), nullable=True)      # 策略ID
    strategy_name = Column(String(128), nullable=True)   # 策略名称
    strategy_family = Column(String(32), nullable=True)  # 策略家族

    # 策略信号
    signal = Column(Integer, nullable=True, default=0)   # -1(卖) / 0(持有) / 1(买)
    signal_confidence = Column(Float, nullable=True)     # 置信度 0-1
    expected_return = Column(Float, nullable=True)       # 预期收益
    risk_estimate = Column(Float, nullable=True)         # 风险估计

    # 寿命监控
    lifespan_months = Column(Float, nullable=True)
    health_score = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
