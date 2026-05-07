import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime
from app.db.base import Base


class PaperTradingSession(Base):
    __tablename__ = "paper_trading_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(64), unique=True, index=True, nullable=False)
    strategy_id = Column(String(64), nullable=False, index=True)
    symbols = Column(Text, nullable=False)  # JSON list of strings
    initial_cash = Column(Float, default=100000.0)
    start_date = Column(String(10), nullable=True)
    end_date = Column(String(10), nullable=True)
    status = Column(String(16), default="idle")  # idle / running / paused / stopped / error
    stop_reason = Column(String(64), nullable=True)  # death cause when stopped
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )
    logs = Column(Text, nullable=True)


class PaperSignal(Base):
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
