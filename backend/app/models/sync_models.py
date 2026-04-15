import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime
from app.db.base import Base


class RealTrade(Base):
    __tablename__ = "real_trades"

    id = Column(Integer, primary_key=True, index=True)
    signal_id = Column(String(64), nullable=True, index=True)
    strategy_id = Column(String(64), nullable=False, index=True)
    symbol = Column(String(16), nullable=False)
    side = Column(String(8), nullable=False)  # Buy / Sell
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    commission = Column(Float, default=0.0)
    stamp_tax = Column(Float, default=0.0)
    transfer_fee = Column(Float, default=0.0)
    total_cost = Column(Float, nullable=False)
    sync_status = Column(String(16), default="synced")  # synced / partial / cancelled
    synced_at = Column(DateTime, default=datetime.datetime.utcnow)
    source = Column(String(16), default="manual")  # manual / csv_import / ocr / broker_auto
    remark = Column(Text, nullable=True)


class RealPosition(Base):
    __tablename__ = "real_positions"

    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(String(64), nullable=False, index=True)
    symbol = Column(String(16), nullable=False)
    quantity = Column(Float, default=0.0)
    available_qty = Column(Float, default=0.0)
    avg_cost = Column(Float, default=0.0)
    total_cost = Column(Float, default=0.0)
    market_value = Column(Float, default=0.0)
    floating_pnl = Column(Float, default=0.0)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )


class SyncLog(Base):
    __tablename__ = "sync_logs"

    id = Column(Integer, primary_key=True, index=True)
    signal_id = Column(String(64), nullable=True, index=True)
    strategy_id = Column(String(64), nullable=False, index=True)
    symbol = Column(String(16), nullable=False)
    signal_side = Column(String(8), nullable=True)
    signal_qty = Column(Float, nullable=True)
    signal_price = Column(Float, nullable=True)
    actual_qty = Column(Float, nullable=True)
    actual_price = Column(Float, nullable=True)
    diff_reason = Column(String(32), nullable=True)  # price_slippage / qty_partial / not_executed / extra_trade
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
