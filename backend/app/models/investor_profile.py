import datetime
from sqlalchemy import Column, Integer, String, JSON, Float, Boolean, DateTime, ForeignKey
from app.db.base import Base


class InvestorProfile(Base):
    __tablename__ = "investor_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Raw answers (18 questions)
    answers_json = Column(JSON, nullable=False)

    # Computed profile vector (18 dimensions, 1-10 scale)
    risk_tolerance = Column(Float, nullable=False)           # 综合风险承受
    loss_aversion = Column(Float, nullable=False)            # 损失厌恶
    herding_tendency = Column(Float, nullable=False)         # 从众倾向
    overconfidence = Column(Float, nullable=False)           # 过度自信
    delayed_gratification = Column(Float, nullable=False)    # 延迟满足
    security_need = Column(Float, nullable=False)            # 资金安全感
    time_horizon_score = Column(Float, nullable=False)       # 时间感知
    experience_level = Column(Float, nullable=False)         # 投资经验
    capital_tier = Column(Float, nullable=False)             # 资金规模
    income_stability = Column(Float, nullable=False)         # 收入稳定性
    debt_pressure = Column(Float, nullable=False)            # 负债压力
    information_processing = Column(Float, nullable=False)   # 信息处理方式
    social_pressure = Column(Float, nullable=False)          # 社会压力承受
    emergency_response = Column(Float, nullable=False)       # 突发亏损应对
    anchoring_effect = Column(Float, nullable=False)         # 锚定效应
    # NEW v2
    diversification_preference = Column(Float, nullable=False)  # 分散化偏好
    stop_loss_discipline = Column(Float, nullable=False)        # 止损纪律
    emotional_stability = Column(Float, nullable=False)         # 情绪稳定性

    # Derived labels
    risk_label = Column(String(16), nullable=True)           # 保守/稳健/积极/激进
    time_horizon_label = Column(String(16), nullable=True)   # 短期/中期/长期
    experience_label = Column(String(16), nullable=True)     # 小白/新手/熟手/高手

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )
