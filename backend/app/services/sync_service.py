import csv
import datetime
import io
from typing import Any

from sqlalchemy.orm import Session

from app.models.account_settings import AccountSettings
from app.models.paper_trading import PaperSignal
from app.models.sync_models import RealTrade, RealPosition, SyncLog
from app.schemas.sync import RealTradeCreate, SyncLogCreate


def list_trades(db: Session, skip: int = 0, limit: int = 100):
    return (
        db.query(RealTrade)
        .order_by(RealTrade.synced_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def calculate_fees(db: Session, side: str, quantity: float, price: float) -> dict[str, float]:
    """根据账户设置自动计算手续费."""
    settings = db.query(AccountSettings).first()
    if not settings:
        settings = AccountSettings()

    amount = quantity * price
    commission = max(amount * settings.commission_rate, settings.min_commission)
    transfer_fee = amount * settings.transfer_fee_rate if settings.is_sh_market else 0.0
    stamp_tax = amount * settings.stamp_tax_rate if side.lower() == "sell" else 0.0

    return {
        "commission": round(commission, 2),
        "stamp_tax": round(stamp_tax, 2),
        "transfer_fee": round(transfer_fee, 2),
    }


def create_trade(db: Session, obj_in: RealTradeCreate) -> RealTrade:
    # Auto-calculate fees if not provided (and not cancelled)
    commission = obj_in.commission
    stamp_tax = obj_in.stamp_tax
    transfer_fee = obj_in.transfer_fee
    if obj_in.sync_status != "cancelled" and (commission == 0 and stamp_tax == 0 and transfer_fee == 0):
        fees = calculate_fees(db, obj_in.side, obj_in.quantity, obj_in.price)
        commission = fees["commission"]
        stamp_tax = fees["stamp_tax"]
        transfer_fee = fees["transfer_fee"]

    total_cost = obj_in.total_cost
    if total_cost == 0 and obj_in.sync_status != "cancelled":
        total_cost = obj_in.quantity * obj_in.price + commission + stamp_tax + transfer_fee

    db_trade = RealTrade(
        signal_id=obj_in.signal_id,
        strategy_id=obj_in.strategy_id,
        symbol=obj_in.symbol,
        side=obj_in.side,
        quantity=obj_in.quantity,
        price=obj_in.price,
        commission=commission,
        stamp_tax=stamp_tax,
        transfer_fee=transfer_fee,
        total_cost=total_cost,
        sync_status=obj_in.sync_status,
        source=obj_in.source,
        remark=obj_in.remark,
        synced_at=datetime.datetime.utcnow(),
    )
    db.add(db_trade)

    # Update real position
    trade_for_position = RealTradeCreate(
        signal_id=obj_in.signal_id,
        strategy_id=obj_in.strategy_id,
        symbol=obj_in.symbol,
        side=obj_in.side,
        quantity=obj_in.quantity,
        price=obj_in.price,
        commission=commission,
        stamp_tax=stamp_tax,
        transfer_fee=transfer_fee,
        total_cost=total_cost,
        sync_status=obj_in.sync_status,
        source=obj_in.source,
        remark=obj_in.remark,
    )
    _update_position_on_trade(db, trade_for_position)

    # Create sync log if signal_id exists
    if obj_in.signal_id:
        signal = (
            db.query(PaperSignal)
            .filter(PaperSignal.signal_id == obj_in.signal_id)
            .first()
        )
        if signal:
            diff_reason = _compute_diff_reason(signal, obj_in)
            db_log = SyncLog(
                signal_id=obj_in.signal_id,
                strategy_id=obj_in.strategy_id,
                symbol=obj_in.symbol,
                signal_side=signal.side,
                signal_qty=signal.quantity,
                signal_price=signal.price,
                actual_qty=obj_in.quantity,
                actual_price=obj_in.price,
                diff_reason=diff_reason,
                created_at=datetime.datetime.utcnow(),
            )
            db.add(db_log)
            signal.status = "synced"
            db.add(signal)

    db.commit()
    db.refresh(db_trade)
    return db_trade


def _compute_diff_reason(signal: PaperSignal, trade: RealTradeCreate) -> str | None:
    if trade.sync_status == "cancelled":
        return "not_executed"
    if trade.sync_status == "partial":
        return "qty_partial"
    if trade.quantity != signal.quantity:
        return "qty_partial"
    if trade.price is not None and signal.price is not None:
        if abs(trade.price - signal.price) > 1e-6:
            return "price_slippage"
    return None


def _update_position_on_trade(db: Session, trade: RealTradeCreate) -> None:
    if trade.sync_status == "cancelled":
        return

    position = (
        db.query(RealPosition)
        .filter(
            RealPosition.strategy_id == trade.strategy_id,
            RealPosition.symbol == trade.symbol,
        )
        .first()
    )

    qty = trade.quantity if trade.sync_status != "partial" else trade.quantity
    if qty <= 0:
        return

    if trade.side.lower() == "buy":
        trade_total = trade.total_cost
        if not position:
            position = RealPosition(
                strategy_id=trade.strategy_id,
                symbol=trade.symbol,
                quantity=qty,
                available_qty=qty,
                avg_cost=trade.price,
                total_cost=trade_total,
                market_value=trade.price * qty,
                floating_pnl=0.0,
                updated_at=datetime.datetime.utcnow(),
            )
            db.add(position)
        else:
            new_qty = position.quantity + qty
            new_total_cost = position.total_cost + trade_total
            position.quantity = new_qty
            position.available_qty = position.available_qty + qty
            position.avg_cost = new_total_cost / new_qty if new_qty > 0 else 0.0
            position.total_cost = new_total_cost
            position.market_value = position.avg_cost * new_qty
            position.updated_at = datetime.datetime.utcnow()
            db.add(position)
    elif trade.side.lower() == "sell":
        if not position or position.quantity <= 0:
            return
        new_qty = max(0.0, position.quantity - qty)
        ratio = new_qty / position.quantity if position.quantity > 0 else 0.0
        position.total_cost = position.total_cost * ratio
        position.quantity = new_qty
        position.available_qty = max(0.0, position.available_qty - qty)
        if new_qty <= 0:
            position.avg_cost = 0.0
            position.total_cost = 0.0
        position.updated_at = datetime.datetime.utcnow()
        db.add(position)


def delete_trade(db: Session, trade_id: int) -> None:
    trade = db.query(RealTrade).filter(RealTrade.id == trade_id).first()
    if not trade:
        return
    db.delete(trade)
    db.commit()
    _rebuild_position(db, trade.strategy_id, trade.symbol)


def _rebuild_position(db: Session, strategy_id: str, symbol: str) -> None:
    trades = (
        db.query(RealTrade)
        .filter(
            RealTrade.strategy_id == strategy_id,
            RealTrade.symbol == symbol,
            RealTrade.sync_status != "cancelled",
        )
        .order_by(RealTrade.synced_at.asc())
        .all()
    )

    position = (
        db.query(RealPosition)
        .filter(
            RealPosition.strategy_id == strategy_id,
            RealPosition.symbol == symbol,
        )
        .first()
    )

    total_qty = 0.0
    total_cost = 0.0
    avg_cost = 0.0

    for t in trades:
        if t.side.lower() == "buy":
            total_qty += t.quantity
            total_cost += t.total_cost
            avg_cost = total_cost / total_qty if total_qty > 0 else 0.0
        elif t.side.lower() == "sell":
            new_qty = max(0.0, total_qty - t.quantity)
            ratio = new_qty / total_qty if total_qty > 0 else 0.0
            total_cost = total_cost * ratio
            total_qty = new_qty
            avg_cost = avg_cost if total_qty > 0 else 0.0

    if not position:
        if total_qty > 0:
            position = RealPosition(
                strategy_id=strategy_id,
                symbol=symbol,
                quantity=total_qty,
                available_qty=total_qty,
                avg_cost=avg_cost,
                total_cost=total_cost,
                market_value=avg_cost * total_qty,
                floating_pnl=0.0,
                updated_at=datetime.datetime.utcnow(),
            )
            db.add(position)
    else:
        position.quantity = total_qty
        position.available_qty = total_qty
        position.avg_cost = avg_cost
        position.total_cost = total_cost
        position.market_value = avg_cost * total_qty
        position.updated_at = datetime.datetime.utcnow()
        db.add(position)

    db.commit()


def list_positions(db: Session, strategy_id: str | None = None, skip: int = 0, limit: int = 100):
    query = db.query(RealPosition).order_by(RealPosition.updated_at.desc())
    if strategy_id:
        query = query.filter(RealPosition.strategy_id == strategy_id)
    return query.offset(skip).limit(limit).all()


def list_logs(db: Session, skip: int = 0, limit: int = 100):
    return (
        db.query(SyncLog)
        .order_by(SyncLog.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_diff(db: Session, strategy_id: str) -> dict[str, Any]:
    signals = (
        db.query(PaperSignal)
        .filter(
            PaperSignal.strategy_id == strategy_id,
            PaperSignal.status.in_(["pending", "synced"]),
        )
        .all()
    )
    positions = (
        db.query(RealPosition)
        .filter(RealPosition.strategy_id == strategy_id)
        .all()
    )

    signal_map = {}
    for s in signals:
        if s.symbol not in signal_map:
            signal_map[s.symbol] = {"qty": 0.0, "side": s.side, "price": s.price}
        signal_map[s.symbol]["qty"] += s.quantity

    position_map = {p.symbol: p for p in positions}
    all_symbols = set(signal_map.keys()) | set(position_map.keys())

    diffs = []
    for sym in all_symbols:
        sig = signal_map.get(sym)
        pos = position_map.get(sym)

        if sig and not pos:
            diffs.append(
                {
                    "symbol": sym,
                    "status": "missing_real",
                    "signal_qty": sig["qty"],
                    "signal_side": sig["side"],
                    "real_qty": 0.0,
                    "message": "模拟有信号，真实无持仓",
                }
            )
        elif pos and not sig:
            diffs.append(
                {
                    "symbol": sym,
                    "status": "extra_real",
                    "signal_qty": 0.0,
                    "signal_side": None,
                    "real_qty": pos.quantity,
                    "message": "真实有持仓，模拟无信号",
                }
            )
        else:
            # both exist
            if abs(sig["qty"] - pos.quantity) < 1e-6:
                diffs.append(
                    {
                        "symbol": sym,
                        "status": "match",
                        "signal_qty": sig["qty"],
                        "signal_side": sig["side"],
                        "real_qty": pos.quantity,
                        "message": "完全一致",
                    }
                )
            else:
                diffs.append(
                    {
                        "symbol": sym,
                        "status": "mismatch",
                        "signal_qty": sig["qty"],
                        "signal_side": sig["side"],
                        "real_qty": pos.quantity,
                        "message": "持仓数量不一致",
                    }
                )

    return {"strategy_id": strategy_id, "diffs": diffs}


def import_csv_trades(db: Session, file_content: str) -> dict[str, Any]:
    """从 CSV 内容批量导入交割单并写入 real_trades / real_positions."""
    reader = csv.DictReader(io.StringIO(file_content))
    created = 0
    errors: list[str] = []
    for row in reader:
        try:
            symbol = row.get("标的", row.get("symbol", "")).strip()
            side = row.get("方向", row.get("side", "")).strip()
            quantity = float(row.get("数量", row.get("quantity", 0)))
            price = float(row.get("价格", row.get("price", 0)))
            date_str = row.get("日期", row.get("date", "")).strip()
            strategy_id = row.get("策略ID", row.get("strategy_id", "")).strip() or "default"

            if not symbol or not side or quantity <= 0 or price <= 0:
                errors.append(f"跳过无效行: {row}")
                continue

            fees = calculate_fees(db, side, quantity, price)
            total_cost = quantity * price + fees["commission"] + fees["stamp_tax"] + fees["transfer_fee"]

            trade = RealTradeCreate(
                signal_id=None,
                strategy_id=strategy_id,
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=price,
                commission=fees["commission"],
                stamp_tax=fees["stamp_tax"],
                transfer_fee=fees["transfer_fee"],
                total_cost=total_cost,
                sync_status="synced",
                source="csv_import",
                remark=f"CSV导入 {date_str}",
            )
            create_trade(db, trade)
            created += 1
        except Exception as e:
            errors.append(str(e))

    return {"created": created, "errors": errors}


def batch_sync_signals(db: Session, items: list[dict[str, Any]]) -> dict[str, Any]:
    """批量补录：根据信号列表批量创建真实交易."""
    created = 0
    errors: list[str] = []
    for item in items:
        try:
            signal_id = item["signal_id"]
            actual_price = float(item["actual_price"])
            actual_qty = float(item.get("actual_qty", item.get("quantity", 0)))
            sync_status = item.get("sync_status", "synced")
            remark = item.get("remark", "")

            signal = db.query(PaperSignal).filter(PaperSignal.signal_id == signal_id).first()
            if not signal:
                errors.append(f"Signal {signal_id} not found")
                continue

            fees = calculate_fees(db, signal.side, actual_qty, actual_price)
            total_cost = actual_qty * actual_price + fees["commission"] + fees["stamp_tax"] + fees["transfer_fee"]

            trade = RealTradeCreate(
                signal_id=signal_id,
                strategy_id=signal.strategy_id,
                symbol=signal.symbol,
                side=signal.side,
                quantity=actual_qty,
                price=actual_price,
                commission=fees["commission"],
                stamp_tax=fees["stamp_tax"],
                transfer_fee=fees["transfer_fee"],
                total_cost=total_cost,
                sync_status=sync_status,
                source="manual",
                remark=remark,
            )
            create_trade(db, trade)
            created += 1
        except Exception as e:
            errors.append(str(e))

    return {"created": created, "errors": errors}


def generate_daily_report(db: Session, strategy_id: str, trade_date: str | None = None) -> dict[str, Any]:
    """生成当日对账单草稿."""
    if not trade_date:
        trade_date = datetime.date.today().isoformat()

    # 获取该策略下所有 pending / synced 信号（模拟持仓）
    signals = (
        db.query(PaperSignal)
        .filter(PaperSignal.strategy_id == strategy_id)
        .all()
    )
    pending_signals = [s for s in signals if s.status == "pending"]
    synced_signals = [s for s in signals if s.status == "synced"]

    # 真实持仓
    positions = (
        db.query(RealPosition)
        .filter(RealPosition.strategy_id == strategy_id)
        .all()
    )

    # 当日真实交易
    trades = (
        db.query(RealTrade)
        .filter(
            RealTrade.strategy_id == strategy_id,
            RealTrade.synced_at >= f"{trade_date} 00:00:00",
            RealTrade.synced_at < f"{trade_date} 23:59:59",
        )
        .all()
    )

    # 模拟盈亏（简化：按信号价格 vs 当日收盘价，实际应由 akquant 引擎提供）
    # 真实账本盈亏（简化：按真实成交均价计算）
    real_pnl = sum(t.total_cost * (1 if t.side.lower() == "sell" else -1) for t in trades)

    # 持仓差异
    diff = get_diff(db, strategy_id)
    diffs = diff.get("diffs", [])
    unsynced = [d for d in diffs if d["status"] != "match"]

    return {
        "trade_date": trade_date,
        "strategy_id": strategy_id,
        "simulated_signals_count": len(signals),
        "pending_signals_count": len(pending_signals),
        "synced_signals_count": len(synced_signals),
        "real_trades_count": len(trades),
        "real_pnl": round(real_pnl, 2),
        "positions": [{"symbol": p.symbol, "quantity": p.quantity, "avg_cost": p.avg_cost} for p in positions],
        "diffs": diffs,
        "unsynced_list": unsynced,
        "message": f"今日还有 {len(pending_signals)} 条信号未同步，{len(unsynced)} 只标的持仓不一致",
    }
