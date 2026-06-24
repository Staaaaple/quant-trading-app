"""用户反馈收集模型."""

from sqlalchemy import Column, Integer, String, Float, Text, DateTime, JSON
from sqlalchemy.sql import func

from app.db.base import Base


class UserFeedback(Base):
    """用户对策略/组合的反馈."""

    __tablename__ = "user_feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    portfolio_id = Column(Integer, nullable=True, index=True)
    strategy_id = Column(String(100), nullable=True, index=True)

    # 反馈类型
    feedback_type = Column(String(50), nullable=False, default="general")
    # general(总体), strategy(策略), portfolio(组合), service(服务)

    # 评分维度 (1-5星)
    overall_rating = Column(Integer, nullable=True)
    return_rating = Column(Integer, nullable=True)
    risk_rating = Column(Integer, nullable=True)
    usability_rating = Column(Integer, nullable=True)

    # 实际收益数据 (用户填写)
    actual_return_pct = Column(Float, nullable=True)
    period_days = Column(Integer, nullable=True)

    # 文字反馈
    pros = Column(Text, nullable=True)
    cons = Column(Text, nullable=True)
    suggestion = Column(Text, nullable=True)

    # 是否愿意参与后续优化访谈
    willing_to_interview = Column(Integer, nullable=False, default=0)

    # 是否用于推荐优化
    used_for_optimization = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FeedbackSummary(Base):
    """反馈汇总统计 (定时任务更新)."""

    __tablename__ = "feedback_summaries"

    id = Column(Integer, primary_key=True, index=True)
    target_type = Column(String(50), nullable=False)
    # strategy / portfolio / overall
    target_id = Column(String(100), nullable=True)

    avg_overall_rating = Column(Float, nullable=True)
    avg_return_rating = Column(Float, nullable=True)
    avg_risk_rating = Column(Float, nullable=True)
    avg_usability_rating = Column(Float, nullable=True)

    feedback_count = Column(Integer, nullable=False, default=0)
    avg_actual_return = Column(Float, nullable=True)

    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
