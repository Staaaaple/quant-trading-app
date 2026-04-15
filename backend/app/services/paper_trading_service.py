import datetime
import json
import os
import tempfile
import traceback
import uuid

import akquant
from sqlalchemy.orm import Session

from app.models.paper_trading import PaperSignal, PaperTradingSession
from app.models.strategy import Strategy
from app.schemas.paper_trading import PaperTradingSessionCreate, PaperTradingSessionUpdate
from app.services.backtest_service import fetch_stock_data


def get_session(db: Session, session_id: str):
    return db.query(PaperTradingSession).filter(PaperTradingSession.session_id == session_id).first()


def list_sessions(db: Session, skip: int = 0, limit: int = 100):
    return (
        db.query(PaperTradingSession)
        .order_by(PaperTradingSession.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_session(db: Session, obj_in: PaperTradingSessionCreate):
    db_obj = PaperTradingSession(
        session_id=obj_in.session_id,
        strategy_id=obj_in.strategy_id,
        symbols=json.dumps(obj_in.symbols),
        initial_cash=obj_in.initial_cash,
        start_date=obj_in.start_date,
        end_date=obj_in.end_date,
        status="idle",
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_session(db: Session, db_obj: PaperTradingSession, obj_in: PaperTradingSessionUpdate):
    update_data = obj_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_session(db: Session, db_obj: PaperTradingSession):
    db.delete(db_obj)
    db.commit()


def _write_strategy_to_temp_file(code: str) -> str:
    """将策略源码写入临时文件并返回路径."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        return f.name


def run_paper_trading_session(db: Session, session_id: str) -> PaperTradingSession:
    """执行模拟盘回测并提取交易信号写入 PaperSignal."""
    db_session = get_session(db, session_id)
    if not db_session:
        raise ValueError(f"Paper trading session {session_id} not found")

    db_strategy = db.query(Strategy).filter(Strategy.strategy_id == db_session.strategy_id).first()
    if not db_strategy:
        raise ValueError(f"Strategy {db_session.strategy_id} not found")

    symbols = json.loads(db_session.symbols)
    start_date = db_session.start_date or (datetime.date.today() - datetime.timedelta(days=365)).isoformat()
    end_date = db_session.end_date or datetime.date.today().isoformat()

    db_session.status = "running"
    db_session.logs = ""
    db.commit()

    tmp_path = ""
    try:
        # 拉取数据（复用 backtest_service 的 AKShare 适配器）
        data_frames = {}
        for sym in symbols:
            df = fetch_stock_data(sym, start_date, end_date)
            data_frames[sym] = df

        if len(data_frames) == 1:
            data_input = list(data_frames.values())[0]
        else:
            data_input = data_frames

        # 写入策略临时文件
        tmp_path = _write_strategy_to_temp_file(db_strategy.code)

        # 运行回测引擎
        result = akquant.run_backtest(
            data=data_input,
            strategy_source=tmp_path,
            symbols=symbols,
            initial_cash=db_session.initial_cash,
            start_time=start_date,
            end_time=end_date,
            show_progress=False,
        )

        # 清理该策略下的旧信号（同一 strategy_id 的模拟信号会被覆盖）
        db.query(PaperSignal).filter(PaperSignal.strategy_id == db_session.strategy_id).delete()
        db.commit()

        # 提取订单为 PaperSignal
        signals_created = 0
        for order in result.orders:
            if order.status in ("New", "Filled", "PartiallyFilled"):
                side_str = order.side.value if hasattr(order.side, "value") else str(order.side)
                signal = PaperSignal(
                    signal_id=str(uuid.uuid4()),
                    strategy_id=db_session.strategy_id,
                    symbol=order.symbol,
                    side=side_str,
                    quantity=float(order.quantity) if order.quantity else 0.0,
                    price=order.price,
                    status="pending",
                    signal_at=datetime.datetime.utcnow(),
                )
                db.add(signal)
                signals_created += 1

        db_session.status = "success"
        db_session.logs = json.dumps(
            {
                "signals_created": signals_created,
                "total_trades": len(result.trades),
                "total_orders": len(result.orders),
                "engine_summary": str(result),
            },
            ensure_ascii=False,
            default=str,
        )
        db.commit()
    except Exception as e:
        db_session.status = "error"
        db_session.logs = f"Error: {e}\n{traceback.format_exc()}"
        db.commit()
        raise
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

    db.refresh(db_session)
    return db_session
