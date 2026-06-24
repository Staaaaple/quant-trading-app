"""A/B 测试模型."""

from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Text
from datetime import datetime

from app.db.base import Base


class ABTest(Base):
    """A/B 测试定义."""

    __tablename__ = "ab_tests"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    hypothesis = Column(Text, nullable=True)
    target_metric = Column(String(50), default="return")
    variant_a_name = Column(String(100), default="变体A")
    variant_a_config = Column(JSON, nullable=True)
    variant_b_name = Column(String(100), default="变体B")
    variant_b_config = Column(JSON, nullable=True)
    status = Column(String(20), default="draft")  # draft / running / paused / completed
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    target_sample_size = Column(Integer, default=100)
    current_sample_a = Column(Integer, default=0)
    current_sample_b = Column(Integer, default=0)
    significance_level = Column(Float, default=0.05)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ABTestResult(Base):
    """A/B 测试结果（用户参与记录）."""

    __tablename__ = "ab_test_results"

    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    variant = Column(String(10), nullable=False)  # "A" or "B"
    metric_value = Column(Float, nullable=True)
    context = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ABTestStatistics(Base):
    """A/B 测试统计汇总."""

    __tablename__ = "ab_test_statistics"

    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, nullable=False, index=True)
    variant_a_stats = Column(JSON, nullable=True)
    variant_b_stats = Column(JSON, nullable=True)
    p_value = Column(Float, nullable=True)
    winner = Column(String(10), nullable=True)
    calculated_at = Column(DateTime, default=datetime.utcnow)
