import datetime
from sqlalchemy import Column, Integer, String, JSON, Float, Boolean, DateTime, Text
from app.db.base import Base


class StrategyTemplate(Base):
    __tablename__ = "strategy_templates"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(String(64), unique=True, index=True, nullable=False)

    name = Column(String(128), nullable=False)
    family = Column(String(32), nullable=False, index=True)  # 经典技术指标/机器学习/因子挖掘/...
    description = Column(Text, nullable=True)

    # 策略代码（akquant框架适配）
    code = Column(Text, nullable=False)

    # 参数搜索空间（JSON）
    param_space = Column(JSON, nullable=False)

    # 适用条件
    suitable_cycles = Column(JSON, nullable=False, default=list)  # ["复苏", "过热"]
    risk_level = Column(String(16), nullable=False)  # 保守/稳健/积极/激进
    asset_classes = Column(JSON, nullable=False, default=list)  # ["stock", "etf"]

    # 健康度与寿命（简化版DNA）
    health_score = Column(Float, nullable=True)
    lifespan_months = Column(Float, nullable=True)

    # 回测摘要（10只股×6月×3段的结果汇总）
    backtest_summary = Column(JSON, nullable=True)

    # 状态
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
