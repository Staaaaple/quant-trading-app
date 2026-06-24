import datetime
import json
import os
import re
import tempfile
import traceback
import uuid
from typing import Any

import akquant
import akshare as ak
import numpy as np
import pandas as pd
import requests
from sqlalchemy.orm import Session

from app.models.backtest import BacktestResult
from app.models.strategy import Strategy
from app.models.strategy_flow import StrategyFlow
from app.schemas.backtest import BacktestCreate, BacktestUpdate
from app.services import stock_picker_service, strategy_flow_service, risk_strategy_service
from app.core.config import settings



class AkshareProxyError(Exception):
    """由于代理或网络问题导致无法连接任何数据源."""

    pass


class AkshareDataError(Exception):
    """所有数据源均不可用或返回空数据."""

    pass


def get_backtest(db: Session, backtest_id: str):
    return db.query(BacktestResult).filter(BacktestResult.backtest_id == backtest_id).first()


def get_backtests(db: Session, skip: int = 0, limit: int = 100):
    return db.query(BacktestResult).order_by(BacktestResult.created_at.desc()).offset(skip).limit(limit).all()


def create_backtest_record(db: Session, obj_in: BacktestCreate):
    db_obj = BacktestResult(
        backtest_id=obj_in.backtest_id,
        user_id=obj_in.user_id,
        strategy_id=obj_in.strategy_id,
        status=obj_in.status,
        start_date=obj_in.start_date,
        end_date=obj_in.end_date,
        initial_cash=obj_in.initial_cash,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_backtest_record(db: Session, db_obj: BacktestResult, obj_in: BacktestUpdate):
    update_data = obj_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_backtest(db: Session, db_obj: BacktestResult) -> None:
    db.delete(db_obj)
    db.commit()


def _add_exchange_prefix(symbol: str) -> str:
    """为新浪财经接口补充 sh/sz 前缀."""
    if symbol.startswith(("sh", "sz")):
        return symbol
    # 简单判断：6 开头为沪市(sh)，其余为深市(sz)
    if symbol.startswith("6"):
        return f"sh{symbol}"
    return f"sz{symbol}"


def _normalize_akquant_df(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """标准化 DataFrame 为 akquant 可用格式，保留扩展字段供策略使用.

    akquant 的 Bar.extra 会自动接收未被识别的数值列，因此保留更多字段
    可直接在策略中通过 bar.extra['amount'] 等方式访问。
    """
    # 列名映射字典：支持中文、英文、简写等多种原始列名
    column_mapping = {
        # 时间列
        "timestamp": ["date", "datetime", "time", "timestamp", "日期", "时间"],
        # OHLCV
        "open": ["open", "开盘", "OPEN"],
        "high": ["high", "最高", "HIGH"],
        "low": ["low", "最低", "LOW"],
        "close": ["close", "收盘", "CLOSE"],
        "volume": ["volume", "vol", "成交量", "VOLUME", "VOL"],
        # 扩展字段：资金/波动
        "amount": ["amount", "amt", "成交额", "AMOUNT"],
        "turnover": ["turnover", "换手率", "TURNOVER"],
        "turnover_rate": ["turnover_rate", "turnoverrate", "换手率", "turnover"],
        "turnover_rate_f": ["turnover_rate_f", "turnoverratef", "自由流通股换手率"],
        "change_pct": ["change_pct", "pct_change", "涨跌幅", "PCT_CHANGE"],
        "change": ["change", "change_amount", "涨跌额", "CHANGE"],
        "amplitude": ["amplitude", "振幅", "AMPLITUDE"],
        "pre_close": ["pre_close", "preclose", "昨收", "PRE_CLOSE", "昨收价"],
        # 扩展字段：股本/市值/估值（为后续多源数据预留）
        "outstanding_share": ["outstanding_share", "outstandingshare", "流通股本", "流通股"],
        "circulating_share": ["circulating_share", "circulatingshare", "circulating_mkv"],
        "market_cap": ["market_cap", "marketcap", "总市值", "流通市值", "circulating_market_cap"],
        "pe": ["pe", "市盈率", "price_earnings"],
        "pe_ttm": ["pe_ttm", "pe_ttm_ratio", "市盈率TTM"],
        "pb": ["pb", "市净率", "price_book"],
        "ps": ["ps", "市销率", "price_sales"],
        # 扩展字段：技术指标（部分数据源可能直接提供）
        "vwap": ["vwap", "volume_weighted_avg_price", "均价"],
        "ma5": ["ma5", "ma_5", "5日均线"],
        "ma10": ["ma10", "ma_10", "10日均线"],
        "ma20": ["ma20", "ma_20", "20日均线"],
        "ma60": ["ma60", "ma_60", "60日均线"],
    }

    # 建立原始列名 -> 标准列名的反向映射
    rename_map: dict[str, str] = {}
    used_targets: set[str] = set()
    for target, candidates in column_mapping.items():
        for col in df.columns:
            if col in candidates and target not in used_targets:
                rename_map[col] = target
                used_targets.add(target)
                break
        # 如果没有精确匹配，尝试大小写不敏感匹配
        if target not in used_targets:
            col_lower_map = {str(c).lower(): c for c in df.columns}
            for cand in candidates:
                if cand.lower() in col_lower_map:
                    rename_map[col_lower_map[cand.lower()]] = target
                    used_targets.add(target)
                    break

    df = df.rename(columns=rename_map)

    # 确保时间列存在（如果原始列名为索引）
    if "timestamp" not in df.columns and isinstance(df.index, pd.DatetimeIndex):
        df = df.reset_index().rename(columns={df.index.name or "index": "timestamp"})

    # 确保 timestamp 为 datetime 类型
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    else:
        raise ValueError("无法从 DataFrame 中解析出时间列")

    df["symbol"] = symbol

    # 定义需要保留的列顺序：核心字段在前，扩展字段在后
    core_cols = ["timestamp", "open", "high", "low", "close", "volume", "symbol"]
    extra_cols = [
        "amount", "turnover", "turnover_rate", "turnover_rate_f",
        "change_pct", "change", "amplitude", "pre_close",
        "outstanding_share", "circulating_share", "market_cap",
        "pe", "pe_ttm", "pb", "ps",
        "vwap", "ma5", "ma10", "ma20", "ma60",
    ]

    # 保留所有存在的字段（包括未被列名映射到的原始数值字段，akquant 会在 extra 中接收）
    keep_cols = core_cols + extra_cols
    # 同时保留原始 DataFrame 中其他数值列（供 extra 使用）
    numeric_cols = [c for c in df.columns if c not in keep_cols and pd.api.types.is_numeric_dtype(df[c])]
    final_cols = [c for c in (keep_cols + numeric_cols) if c in df.columns]

    df = df[final_cols].set_index("timestamp")

    # 确保核心字段为 float / int 类型
    for col in ["open", "high", "low", "close", "volume"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # 确保扩展字段为数值类型
    for col in extra_cols + numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def _fetch_from_eastmoney(symbol: str, start_date: str, end_date: str, period: str = "daily") -> pd.DataFrame:
    """从东方财富获取数据."""
    start_fmt = start_date.replace("-", "")
    end_fmt = end_date.replace("-", "")
    # period 映射: ak.stock_zh_a_hist 支持 daily/weekly/monthly
    em_period = {"daily": "daily", "weekly": "weekly", "monthly": "monthly"}.get(period, "daily")
    df = ak.stock_zh_a_hist(symbol=symbol, period=em_period, start_date=start_fmt, end_date=end_fmt, adjust="qfq")
    if df.empty:
        raise ValueError(f"No data returned from eastmoney for {symbol}")
    return _normalize_akquant_df(df, symbol)


def _fetch_from_sina(symbol: str, start_date: str, end_date: str, period: str = "daily") -> pd.DataFrame:
    """从新浪财经获取数据.

    新浪财经目前主要支持日线，分钟级数据需通过其他接口获取。
    """
    sina_symbol = _add_exchange_prefix(symbol)
    if period == "daily":
        df = ak.stock_zh_a_daily(symbol=sina_symbol, start_date=start_date, end_date=end_date, adjust="qfq")
    else:
        raise ValueError(f"Sina data source does not support period={period} yet")
    if df.empty:
        raise ValueError(f"No data returned from sina for {symbol}")
    return _normalize_akquant_df(df, symbol)


def _fetch_mock_data(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """生成模拟 K 线数据作为开发/测试回退."""
    dates = pd.date_range(start=start_date, end=end_date, freq='B')
    if len(dates) == 0:
        dates = pd.DatetimeIndex([pd.Timestamp(start_date)])
    np.random.seed(hash(symbol) % 2**32)
    base_price = 100.0
    data = []
    for i, date in enumerate(dates):
        if i == 0:
            open_p = base_price
        else:
            open_p = data[-1]['close']
        change = np.random.normal(0, 0.015)
        close = open_p * (1 + change)
        high = max(open_p, close) * (1 + abs(np.random.normal(0, 0.008)))
        low = min(open_p, close) * (1 - abs(np.random.normal(0, 0.008)))
        volume = int(np.random.uniform(1_000_000, 10_000_000))
        data.append({
            'timestamp': date,
            'open': round(open_p, 2),
            'high': round(high, 2),
            'low': round(low, 2),
            'close': round(close, 2),
            'volume': volume,
        })
    df = pd.DataFrame(data)
    return _normalize_akquant_df(df, symbol)


def fetch_stock_data(symbol: str, start_date: str, end_date: str, period: str = "daily") -> pd.DataFrame:
    """通过 akshare 获取股票历史K线数据并标准化为 akquant 可用格式.

    优先使用东方财富接口，失败时自动回退到新浪财经接口。
    若所有数据源均失败，开发环境下使用模拟数据回退。

    :param period: 数据周期，目前支持 "daily"（日线），东财额外支持 "weekly"/"monthly"
    """
    last_error = None
    is_proxy_error = False

    try:
        return _fetch_from_eastmoney(symbol, start_date, end_date, period=period)
    except requests.exceptions.ConnectionError as e:
        last_error = e
        is_proxy_error = True
    except Exception as e:
        last_error = e

    try:
        return _fetch_from_sina(symbol, start_date, end_date, period=period)
    except requests.exceptions.ConnectionError as e:
        last_error = e
        is_proxy_error = True
    except Exception as e:
        last_error = e

    if settings.BACKTEST_DEMO_FALLBACK:
        import logging
        logging.warning(f"[MOCK] 数据源不可用，使用模拟数据回退: {symbol} ({start_date} ~ {end_date})")
        return _fetch_mock_data(symbol, start_date, end_date)

    if is_proxy_error:
        raise AkshareProxyError(
            f"无法连接到 AKShare 数据源（代理或网络问题）。"
            f"请检查系统代理设置，或尝试关闭代理后重试。"
        ) from last_error

    raise AkshareDataError(
        f"无法从任何数据源获取 {symbol} 的历史数据 ({start_date} ~ {end_date})。"
        f"最后错误: {last_error}"
    ) from last_error


def _write_strategy_to_temp_file(code: str) -> str:
    """将策略源码写入临时文件并返回路径."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        return f.name


def _extract_metrics(result) -> dict[str, Any]:
    """从 akquant BacktestResult 中提取关键指标."""
    m = result.metrics
    raw = m._raw
    metrics = {}
    for attr in [
        "total_return",
        "total_return_pct",
        "annualized_return",
        "sharpe_ratio",
        "sortino_ratio",
        "calmar_ratio",
        "max_drawdown",
        "max_drawdown_pct",
        "max_drawdown_value",
        "volatility",
        "win_rate",
        "exposure_time_pct",
        "total_bars",
        "duration",
        "initial_market_value",
        "end_market_value",
    ]:
        try:
            val = getattr(raw, attr)
            # 确保可 JSON 序列化
            if pd.isna(val):
                val = None
            elif isinstance(val, (pd.Timestamp, datetime.datetime)):
                val = val.isoformat()
            metrics[attr] = val
        except Exception:
            metrics[attr] = None

    # trade_count 在 result.trade_metrics 中
    try:
        metrics["trade_count"] = int(result.trade_metrics.total_closed_trades)
    except Exception:
        metrics["trade_count"] = None

    return metrics


def _extract_trades(result) -> list[dict]:
    """从 akquant BacktestResult 中提取交易记录."""
    try:
        df = result.trades_df
        if df.empty:
            return []
        records = []
        for _, row in df.iterrows():
            records.append({
                "symbol": row.get("symbol"),
                "entry_time": row.get("entry_time").isoformat() if pd.notna(row.get("entry_time")) else None,
                "exit_time": row.get("exit_time").isoformat() if pd.notna(row.get("exit_time")) else None,
                "entry_price": float(row.get("entry_price")) if pd.notna(row.get("entry_price")) else None,
                "exit_price": float(row.get("exit_price")) if pd.notna(row.get("exit_price")) else None,
                "quantity": float(row.get("quantity")) if pd.notna(row.get("quantity")) else None,
                "side": row.get("side"),
                "pnl": float(row.get("pnl")) if pd.notna(row.get("pnl")) else None,
                "return_pct": float(row.get("return_pct")) if pd.notna(row.get("return_pct")) else None,
                "entry_tag": row.get("entry_tag"),
                "exit_tag": row.get("exit_tag"),
            })
        return records
    except Exception:
        return []


def _extract_candles(data_input, symbols: list[str]) -> dict[str, list[dict]]:
    """从原始数据中提取 K 线数据."""
    candles: dict[str, list[dict]] = {}
    try:
        if isinstance(data_input, dict):
            for sym, df in data_input.items():
                candles[sym] = _df_to_candles(df)
        elif hasattr(data_input, "iterrows"):
            # 单一 DataFrame，使用第一个 symbol
            sym = symbols[0] if symbols else "unknown"
            candles[sym] = _df_to_candles(data_input)
    except Exception:
        pass
    return candles


def _df_to_candles(df) -> list[dict]:
    """将 DataFrame 转换为前端可用的 K 线列表."""
    records = []
    df = df.copy().reset_index()
    # 标准化列名
    col_map = {}
    for c in df.columns:
        lc = str(c).lower()
        if lc in ("date", "datetime", "timestamp", "time"):
            col_map["date"] = c
        elif lc == "open":
            col_map["open"] = c
        elif lc == "high":
            col_map["high"] = c
        elif lc == "low":
            col_map["low"] = c
        elif lc == "close":
            col_map["close"] = c
        elif lc in ("volume", "vol"):
            col_map["volume"] = c

    for _, row in df.iterrows():
        dt = row.get(col_map.get("date", "date"))
        if dt is None or pd.isna(dt):
            continue
        if hasattr(dt, "strftime"):
            dt_str = dt.strftime("%Y-%m-%d")
        else:
            dt_str = str(dt)[:10]
        records.append({
            "date": dt_str,
            "open": float(row.get(col_map.get("open", "open"), 0)) if pd.notna(row.get(col_map.get("open", "open"))) else 0,
            "high": float(row.get(col_map.get("high", "high"), 0)) if pd.notna(row.get(col_map.get("high", "high"))) else 0,
            "low": float(row.get(col_map.get("low", "low"), 0)) if pd.notna(row.get(col_map.get("low", "low"))) else 0,
            "close": float(row.get(col_map.get("close", "close"), 0)) if pd.notna(row.get(col_map.get("close", "close"))) else 0,
            "volume": float(row.get(col_map.get("volume", "volume"), 0)) if pd.notna(row.get(col_map.get("volume", "volume"))) else 0,
        })
    return records


BUY_HOLD_BENCHMARK_CODE = '''from akquant import Strategy

class BuyHoldBenchmark(Strategy):
    def __init__(self):
        super().__init__()
        self._bought = False

    def on_bar(self, bar):
        if not self._bought:
            symbols = {symbols!r}
            weight = 0.95 / len(symbols) if symbols else 0.95
            for sym in symbols:
                self.order_target_percent(weight, sym)
            self._bought = True
'''

DEFAULT_DEMO_STRATEGY_CODE = '''from akquant import Strategy

class DemoStrategy(Strategy):
    def __init__(self):
        super().__init__()
        self._bought = False

    def on_bar(self, bar):
        if not self._bought:
            symbols = {symbols!r}
            weight = 0.95 / len(symbols) if symbols else 0.95
            for sym in symbols:
                self.order_target_percent(weight, sym)
            self._bought = True
'''


def _get_demo_strategy_code(symbols: list[str]) -> str:
    """生成使用指定标的的 Demo 策略代码."""
    return DEFAULT_DEMO_STRATEGY_CODE.format(symbols=symbols)


def _strategy_code_is_placeholder(code: str | None) -> bool:
    """判断策略代码是否为占位符或无法运行."""
    if not code or not code.strip():
        return True
    stripped = code.strip()
    if stripped.startswith('# Auto-generated placeholder'):
        return True
    if 'class' not in stripped and 'def on_bar' not in stripped:
        return True
    return False


def _extract_strategy_class_name(code: str) -> str:
    """从策略源码中提取继承自 Strategy 的类名，用于 akquant loader."""
    match = re.search(r"class\s+(\w+)\s*\(\s*Strategy\s*\)", code)
    return match.group(1) if match else "DemoStrategy"


def _run_benchmark(data_input, symbols: list[str], initial_cash: float, start_date: str, end_date: str) -> dict[str, Any]:
    """运行买入并持有基准回测."""
    code = BUY_HOLD_BENCHMARK_CODE.format(symbols=symbols)
    tmp_path = _write_strategy_to_temp_file(code)
    try:
        result = akquant.run_backtest(
            data=data_input,
            strategy_source=tmp_path,
            strategy_attr=_extract_strategy_class_name(code),
            symbols=symbols,
            initial_cash=initial_cash,
            start_time=start_date,
            end_time=end_date,
            show_progress=False,
        )
        return _extract_metrics(result)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


def _resolve_flow(
    db: Session,
    strategy_id: str,
    requested_symbols: list[str],
) -> tuple[Strategy, list[str], dict]:
    """解析策略流，返回实际交易策略、标的列表、风控配置."""
    flow = strategy_flow_service.get_flow(db, strategy_id)
    if not flow:
        raise ValueError(f"Strategy flow {strategy_id} not found")

    # 校验子策略存在性
    if flow.picker_strategy_id:
        picker = db.query(Strategy).filter(Strategy.strategy_id == flow.picker_strategy_id).first()
        if not picker:
            raise ValueError(f"Picker strategy {flow.picker_strategy_id} not found")
    if flow.risk_strategy_id:
        risk = db.query(Strategy).filter(Strategy.strategy_id == flow.risk_strategy_id).first()
        if not risk:
            raise ValueError(f"Risk strategy {flow.risk_strategy_id} not found")
    trade = db.query(Strategy).filter(Strategy.strategy_id == flow.trade_strategy_id).first()
    if not trade:
        raise ValueError(f"Trade strategy {flow.trade_strategy_id} not found")

    # 选股
    symbols = requested_symbols
    if flow.picker_strategy_id:
        pool = stock_picker_service.execute_picker(db, flow.picker_strategy_id)
        symbols = [item.symbol for item in pool.items]
        if not symbols:
            raise ValueError("选股结果为空，策略流终止")

    # 风控配置
    risk_config = {}
    if flow.risk_strategy_id:
        cfg = risk_strategy_service.get_config(db, flow.risk_strategy_id)
        if cfg:
            risk_config = {
                "max_position_pct": cfg.max_position_pct,
                "max_daily_drawdown": cfg.max_daily_drawdown,
                "blacklist": cfg.blacklist,
            }

    return trade, symbols, risk_config


def run_backtest_for_strategy(
    db: Session,
    backtest_id: str,
    strategy_id: str,
    symbols: list[str],
    start_date: str,
    end_date: str,
    initial_cash: float,
) -> BacktestResult:
    """执行完整回测流程：获取策略 -> 拉取数据 -> 运行回测 -> 保存结果."""
    db_backtest = get_backtest(db, backtest_id)
    if not db_backtest:
        raise ValueError(f"Backtest record {backtest_id} not found")

    db_strategy = db.query(Strategy).filter(Strategy.strategy_id == strategy_id).first()
    is_flow = False
    if not db_strategy:
        flow = strategy_flow_service.get_flow(db, strategy_id)
        if not flow:
            raise ValueError(f"Strategy {strategy_id} not found")
        is_flow = True

    # 更新状态为运行中
    db_backtest.status = "running"
    db.commit()

    tmp_path = ""
    try:
        risk_config = {}
        if is_flow:
            db_strategy, symbols, risk_config = _resolve_flow(db, strategy_id, symbols)

        # 拉取数据
        data_frames = {}
        for sym in symbols:
            df = fetch_stock_data(sym, start_date, end_date)
            data_frames[sym] = df

        if len(data_frames) == 1:
            data_input = list(data_frames.values())[0]
        else:
            data_input = data_frames

        # 写入策略临时文件
        strategy_code = db_strategy.code if db_strategy else ""
        is_placeholder = _strategy_code_is_placeholder(strategy_code)
        if settings.BACKTEST_DEMO_FALLBACK and is_placeholder:
            import logging
            logging.warning(f"[MOCK] 策略 {strategy_id} 代码为占位符，使用 Demo 策略回退")
            strategy_code = _get_demo_strategy_code(symbols)
        tmp_path = _write_strategy_to_temp_file(strategy_code)

        # 运行回测
        result = akquant.run_backtest(
            data=data_input,
            strategy_source=tmp_path,
            strategy_attr=_extract_strategy_class_name(strategy_code),
            symbols=symbols,
            initial_cash=initial_cash,
            start_time=start_date,
            end_time=end_date,
            show_progress=False,
        )

        metrics = _extract_metrics(result)
        db_backtest.metrics = metrics

        # 运行买入并持有基准对照组
        benchmark_metrics = _run_benchmark(
            data_input=data_input,
            symbols=symbols,
            initial_cash=initial_cash,
            start_date=start_date,
            end_date=end_date,
        )
        db_backtest.benchmark_metrics = benchmark_metrics

        db_backtest.status = "success"

        # Extract risk blocks from pipeline-generated strategies
        risk_blocks = []
        try:
            strategy_instance = getattr(result, "strategy", None)
            if strategy_instance and hasattr(strategy_instance, "_risk_blocks"):
                raw_blocks = strategy_instance._risk_blocks
                if raw_blocks:
                    # Deduplicate by (type, date) keeping the first occurrence
                    seen = set()
                    for block in raw_blocks:
                        key = (block.get("type"), block.get("date"), block.get("symbol"))
                        if key not in seen:
                            seen.add(key)
                            risk_blocks.append(block)
        except Exception:
            pass

        logs_data = {
            "engine_summary": str(result),
            "risk_config": risk_config,
            "trades": _extract_trades(result),
            "candles": _extract_candles(data_input, symbols),
            "risk_blocks": risk_blocks,
        }
        db_backtest.logs = json.dumps(
            logs_data,
            ensure_ascii=False,
            default=str,
        )
    except AkshareProxyError as e:
        db_backtest.status = "failed"
        db_backtest.logs = f"AkshareProxyError: {e}\n{traceback.format_exc()}"
        db_backtest.metrics = {
            "error_code": "akshare_proxy_error",
            "error": str(e),
        }
    except AkshareDataError as e:
        db_backtest.status = "failed"
        db_backtest.logs = f"AkshareDataError: {e}\n{traceback.format_exc()}"
        db_backtest.metrics = {
            "error_code": "akshare_data_error",
            "error": str(e),
        }
    except Exception as e:
        db_backtest.status = "failed"
        db_backtest.logs = f"Error: {e}\n{traceback.format_exc()}"
        db_backtest.metrics = {"error": str(e)}
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        db.commit()
        db.refresh(db_backtest)

    return db_backtest
