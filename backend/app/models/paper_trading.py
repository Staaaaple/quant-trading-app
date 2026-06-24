import datetime
import json
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, UniqueConstraint
from app.db.base import Base


class PaperSignal(Base):
    """模拟交易信号（保留给 sync_service 使用）."""

    __tablename__ = "paper_signals"

    id = Column(Integer, primary_key=True, index=True)
    signal_id = Column(String(64), unique=True, index=True, nullable=False)
    strategy_id = Column(String(64), index=True, nullable=False)
    symbol = Column(String(16), nullable=False)
    side = Column(String(8), nullable=False)  # Buy / Sell
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=True)
    signal_at = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String(16), default="pending")  # pending / synced / ignored
    remark = Column(Text, nullable=True)


class PaperTradingDailyRecord(Base):
    """模拟盘每日记录：基于市场报告日复利累计收益."""

    __tablename__ = "paper_trading_daily_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=True, index=True)

    # 报告日期 YYYY-MM-DD
    record_date = Column(String(10), nullable=False, index=True)

    # 当日组合收益率（来自 market_report.page2.portfolio_return）
    daily_return = Column(Float, nullable=False, default=0.0)

    # 累计收益率 = nav - 1
    cumulative_return = Column(Float, nullable=False, default=0.0)

    # 净值，初始为 1.0
    nav = Column(Float, nullable=False, default=1.0)

    # 关联的市场报告 ID 与资产快照
    report_id = Column(Integer, ForeignKey("market_reports.id"), nullable=True, index=True)
    asset_snapshot = Column(Text, nullable=True)  # JSON: page2.asset_performances

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )

    __table_args__ = (
        UniqueConstraint("user_id", "portfolio_id", "record_date", name="uq_paper_trading_daily_record"),
    )


class PaperTradingMonthlyStat(Base):
    """模拟盘月度统计."""

    __tablename__ = "paper_trading_monthly_stats"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=True, index=True)

    # 月份 YYYY-MM
    year_month = Column(String(7), nullable=False, index=True)

    # 月度收益率
    monthly_return = Column(Float, nullable=False, default=0.0)

    # 该月末累计收益率
    cumulative_return_at_month_end = Column(Float, nullable=False, default=0.0)

    # 该月有效记录数
    record_count = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )

    __table_args__ = (
        UniqueConstraint("user_id", "portfolio_id", "year_month", name="uq_paper_trading_monthly_stat"),
    )
