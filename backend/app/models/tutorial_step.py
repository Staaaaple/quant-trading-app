"""购买教学/建仓截图教程模型."""

from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func

from app.db.base import Base


class TutorialStep(Base):
    """购买教学步骤."""

    __tablename__ = "tutorial_steps"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(50), nullable=False, default="building")
    # category: building(建仓), trading(交易), rebalance(再平衡)
    step_order = Column(Integer, nullable=False, default=0)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    tip = Column(Text, nullable=True)
    # tip: 注意事项/小贴士
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class TutorialProgress(Base):
    """用户教程学习进度."""

    __tablename__ = "tutorial_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    tutorial_category = Column(String(50), nullable=False, default="building")
    current_step = Column(Integer, nullable=False, default=0)
    total_steps = Column(Integer, nullable=False, default=0)
    completed = Column(Integer, nullable=False, default=0)
    # completed: 0=进行中, 1=已完成
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
