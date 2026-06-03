"""操作日志与推送模型.

Phase D: 全链路服务 - 记录用户操作、推送历史、教学卡片.
"""

import datetime
from sqlalchemy import Column, Integer, String, JSON, Float, Boolean, DateTime, ForeignKey, Text
from app.db.base import Base


class OperationLog(Base):
    """用户操作日志."""
    __tablename__ = "operation_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=True, index=True)

    # 操作类型
    operation_type = Column(String(32), nullable=False)  # buy / sell / hold / rebalance / warning / info

    # 标的信息
    symbol = Column(String(16), nullable=True)
    symbol_name = Column(String(64), nullable=True)

    # 操作详情
    action = Column(String(16), nullable=True)  # 买入/卖出/持有
    amount = Column(Float, nullable=True)  # 金额
    quantity = Column(Float, nullable=True)  # 数量
    price = Column(Float, nullable=True)  # 价格

    # 原因说明
    reason = Column(Text, nullable=True)  # 操作原因
    strategy_id = Column(String(64), nullable=True)  # 触发策略
    strategy_name = Column(String(128), nullable=True)

    # 教学卡片
    has_teaching = Column(Boolean, default=False)  # 是否附带教学
    teaching_content = Column(Text, nullable=True)  # 教学内容
    teaching_title = Column(String(128), nullable=True)  # 教学标题

    # 状态
    status = Column(String(16), default="pending")  # pending / confirmed / ignored / executed
    confirmed_at = Column(DateTime, nullable=True)

    # 推送相关
    pushed_at = Column(DateTime, nullable=True)  # 推送时间
    read_at = Column(DateTime, nullable=True)  # 阅读时间
    push_channel = Column(String(16), default="in_app")  # in_app / email / sms

    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class WeeklyReport(Base):
    """周报记录."""
    __tablename__ = "weekly_reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=True)

    # 报告周期
    week_start = Column(String(10), nullable=False)  # YYYY-MM-DD
    week_end = Column(String(10), nullable=False)

    # 组合表现
    portfolio_return = Column(Float, nullable=True)  # 本周收益
    portfolio_cum_return = Column(Float, nullable=True)  # 累计收益
    benchmark_return = Column(Float, nullable=True)  # 基准收益
    max_drawdown = Column(Float, nullable=True)

    # 资产配置变化
    allocation_snapshot = Column(JSON, nullable=True)  # 配置快照
    allocation_changes = Column(JSON, nullable=True)  # 变化明细

    # 市场回顾
    market_summary = Column(Text, nullable=True)  # 市场回顾文本
    market_cycle = Column(String(16), nullable=True)  # 当前周期
    composite_score = Column(Float, nullable=True)  # 综合评分

    # 下周展望
    next_week_outlook = Column(Text, nullable=True)
    recommended_actions = Column(JSON, nullable=True)  # 建议操作列表

    # 寿命预警
    lifespan_alerts = Column(JSON, nullable=True)  # 寿命预警列表

    # 状态
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime, nullable=True)
    pushed_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class PushNotification(Base):
    """推送通知."""
    __tablename__ = "push_notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 通知类型
    notification_type = Column(String(32), nullable=False)  # daily_op / weekly_report / rebalance_alert / lifespan_alert / cycle_alert

    # 标题和内容
    title = Column(String(128), nullable=False)
    content = Column(Text, nullable=True)
    summary = Column(String(256), nullable=True)  # 摘要（用于列表展示）

    # 关联数据
    related_data = Column(JSON, nullable=True)  # 关联的操作日志ID、组合ID等

    # 优先级
    priority = Column(String(16), default="normal")  # high / normal / low

    # 状态
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime, nullable=True)
    is_pushed = Column(Boolean, default=False)
    pushed_at = Column(DateTime, nullable=True)

    # 过期时间
    expires_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class TeachingCard(Base):
    """教学卡片库."""
    __tablename__ = "teaching_cards"

    id = Column(Integer, primary_key=True, index=True)
    card_id = Column(String(64), unique=True, index=True, nullable=False)

    # 卡片分类
    category = Column(String(32), nullable=False)  # strategy / market / risk / operation / concept

    # 内容
    title = Column(String(128), nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(String(256), nullable=True)

    # 关联策略/概念
    related_strategy_id = Column(String(64), nullable=True)
    related_concept = Column(String(64), nullable=True)  # 金叉 / 死叉 / 动量 / 波动率 等

    # 难度等级
    difficulty = Column(String(16), default="beginner")  # beginner / intermediate / advanced

    # 使用统计
    view_count = Column(Integer, default=0)
    helpful_count = Column(Integer, default=0)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
