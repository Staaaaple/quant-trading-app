"""策略寿命历史记录表 — 用于追踪寿命变化趋势和预警.

记录每个策略每月的寿命状态，支持:
- 寿命变化趋势分析
- 预警触发（减少>20%黄灯/<3月红灯）
- 组合层面寿命聚合
"""

import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Index
from app.db.base import Base


class LifespanHistory(Base):
    """策略寿命历史记录."""

    __tablename__ = "lifespan_history"

    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(String(64), index=True, nullable=False)
    date = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    # 寿命指标
    lifespan_months = Column(Integer, default=0)  # 预计剩余寿命（月）
    lifespan_phase = Column(String(16), default="mature")  # young/mature/aging/endangered
    health_score = Column(Float, default=0.0)  # 健康度评分 (0-100)
    aging_velocity = Column(Float, default=0.0)  # 老化速度

    # 影响因素
    metabolic_rate = Column(Float, default=0.0)
    niche_width = Column(Float, default=0.0)
    homogeneity_risk = Column(Float, default=0.0)
    metabolic_syndrome = Column(Integer, default=0)  # 0/1

    # 市场环境因子
    volatility_factor = Column(Float, default=1.0)  # 波动率加速因子
    cycle_factor = Column(Float, default=1.0)  # 周期适配因子
    crowding_factor = Column(Float, default=1.0)  # 拥挤度因子

    # 预警级别
    alert_level = Column(String(16), default="none")  # none/yellow/red
    alert_reason = Column(String(256), nullable=True)

    # 变化检测
    lifespan_change_pct = Column(Float, nullable=True)  # 相较上月变化百分比
    prev_lifespan_months = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # 复合索引：按策略+日期查询
    __table_args__ = (
        Index("ix_lifespan_history_strategy_date", "strategy_id", "date"),
    )


class PortfolioLifespanHistory(Base):
    """组合寿命历史记录."""

    __tablename__ = "portfolio_lifespan_history"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(String(64), index=True, nullable=False)
    date = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    # 组合层面指标
    portfolio_lifespan_months = Column(Integer, default=0)  # min(各组件寿命)
    portfolio_health_score = Column(Float, default=0.0)  # 加权平均健康度
    component_count = Column(Integer, default=0)  # 组件数量
    endangered_count = Column(Integer, default=0)  # 濒危组件数量

    # 预警
    alert_level = Column(String(16), default="none")  # none/yellow/red
    alert_reason = Column(String(256), nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        Index("ix_portfolio_lifespan_history_portfolio_date", "portfolio_id", "date"),
    )
