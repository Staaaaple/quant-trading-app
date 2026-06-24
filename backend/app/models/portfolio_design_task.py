import datetime
from sqlalchemy import Column, Integer, String, JSON, Float, Text, DateTime, ForeignKey
from app.db.base import Base


class PortfolioDesignTask(Base):
    """资产组合设计任务表.

    用于持久化组合构建流程的状态，支持前端刷新/断线后恢复。
    """

    __tablename__ = "portfolio_design_tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 任务状态: pending / running / completed / failed
    status = Column(String(20), nullable=False, default="pending", index=True)

    current_step = Column(String(50), nullable=True)   # 当前步骤，如 saa / binding / reliability
    progress = Column(Float, nullable=True, default=0.0)  # 0.0 ~ 1.0

    payload_json = Column(JSON, nullable=True)         # 构建请求参数（画像向量、市场信号等）
    result_json = Column(JSON, nullable=True)          # 最终结果（PortfolioDesignResult）
    error_message = Column(Text, nullable=True)        # 失败时的错误信息

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )
    completed_at = Column(DateTime, nullable=True)
