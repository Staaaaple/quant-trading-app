import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.db.base import Base


class StockPool(Base):
    __tablename__ = "stock_pools"

    id = Column(Integer, primary_key=True, index=True)
    pool_id = Column(String(64), unique=True, index=True, nullable=False)
    picker_id = Column(String(64), nullable=False, index=True)  # 关联的策略ID
    name = Column(String(128), nullable=False)
    generated_at = Column(DateTime, default=datetime.datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    is_builtin_weekly = Column(Boolean, default=False)  # 是否为本周选股池

    items = relationship("StockPoolItem", back_populates="pool", cascade="all, delete-orphan")


class StockPoolItem(Base):
    __tablename__ = "stock_pool_items"

    id = Column(Integer, primary_key=True, index=True)
    pool_id = Column(String(64), ForeignKey("stock_pools.pool_id"), nullable=False, index=True)
    symbol = Column(String(16), nullable=False)
    name = Column(String(64), nullable=True)  # 股票名称
    score = Column(Float, nullable=True)
    reason = Column(String(256), nullable=True)

    pool = relationship("StockPool", back_populates="items")


class PickerRun(Base):
    __tablename__ = "picker_runs"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String(64), unique=True, index=True, nullable=False)
    picker_id = Column(String(64), nullable=False, index=True)
    status = Column(String(16), default="pending")  # pending / running / success / failed
    result_count = Column(Integer, nullable=True)
    logs = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)


class NotificationSettings(Base):
    __tablename__ = "notification_settings"

    id = Column(Integer, primary_key=True, index=True)
    weekly_picker_push = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
