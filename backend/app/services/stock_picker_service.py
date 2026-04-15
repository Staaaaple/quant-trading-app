import datetime
import uuid
import json
from typing import Any, List

from sqlalchemy.orm import Session, selectinload

from app.models.strategy import Strategy
from app.models.stock_picker import StockPool, StockPoolItem, PickerRun, NotificationSettings
from app.schemas.stock_picker import StockPoolCreate, NotificationSettingsUpdate

BUILTIN_PICKER_ID = "builtin_weekly_picker"

DEFAULT_BUILTIN_CODE = '''def pick_stocks():
    """
    复合选股策略：
    选股1 = 质量 + 动量 + 低波动（机构基本面选股），取前50
    选股2 = 量价结构 + 资金健康度（纯技术选股），取前50
    最终股票池 = 选股1 ∩ 选股2（交集），通常15~35只
    返回列表，每个元素为 dict，包含 symbol, name, score, reason
    """
    import akshare as ak
    import pandas as pd
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from datetime import datetime, timedelta

    # --------------- 数据准备 ---------------
    # 1. 当日全市场行情（新浪接口）
    spot = ak.stock_zh_a_spot()
    spot = spot[spot["代码"].str.startswith(("sh", "sz"))].copy()
    spot = spot[~spot["名称"].str.contains("ST|退", na=False)]
    spot = spot[~spot["名称"].str.contains("^N|^C", regex=True, na=False)]
    spot["成交额"] = pd.to_numeric(spot["成交额"], errors="coerce")
    spot = spot[spot["成交额"] >= 50_000_000]

    # 2. 最新业绩快报（批量基本面数据）
    today = datetime.now()
    year, month = today.year, today.month
    if month <= 4:
        report_date = f"{year-1}1231"
    elif month <= 7:
        report_date = f"{year}0331"
    elif month <= 10:
        report_date = f"{year}0630"
    else:
        report_date = f"{year}0930"

    yjbb = ak.stock_yjbb_em(date=report_date)
    if len(yjbb) < 3000 and report_date.endswith("1231"):
        yjbb = ak.stock_yjbb_em(date=f"{year-1}0930")

    spot["纯代码"] = spot["代码"].str.replace("sh", "", regex=False).str.replace("sz", "", regex=False)
    merged = pd.merge(spot, yjbb, left_on="纯代码", right_on="股票代码", how="inner")

    # --------------- 选股1：基本面 ---------------
    merged["净资产收益率"] = pd.to_numeric(merged["净资产收益率"], errors="coerce")
    merged["销售毛利率"] = pd.to_numeric(merged["销售毛利率"], errors="coerce")
    merged["净利润"] = pd.to_numeric(merged["净利润-净利润"], errors="coerce")
    merged["营收"] = pd.to_numeric(merged["营业总收入-营业总收入"], errors="coerce")
    merged["净利率"] = merged["净利润"] / merged["营收"] * 100

    merged = merged[
        (merged["净资产收益率"] >= 10.0) &
        (merged["销售毛利率"] >= 15.0) &
        (merged["净利率"] >= 8.0)
    ].copy()

    # 等权综合排名
    merged["roe_rank"] = merged["净资产收益率"].rank(ascending=False, pct=True)
    merged["gross_rank"] = merged["销售毛利率"].rank(ascending=False, pct=True)
    merged["net_rank"] = merged["净利率"].rank(ascending=False, pct=True)
    merged["amount_rank"] = merged["成交额"].rank(ascending=False, pct=True)
    merged["fundamental_score"] = (
        merged["roe_rank"] + merged["gross_rank"] + merged["net_rank"] + merged["amount_rank"]
    ) / 4

    pool1 = merged.sort_values("fundamental_score", ascending=False).head(50)

    # --------------- 选股2：技术面 ---------------
    start_date = (datetime.now() - timedelta(days=150)).strftime("%Y%m%d")
    end_date = datetime.now().strftime("%Y%m%d")

    def ema(series, span):
        return pd.Series(series).ewm(span=span, adjust=False).mean().values

    def fetch_tech(symbol):
        try:
            df = ak.stock_zh_a_daily(symbol=symbol, start_date=start_date, end_date=end_date, adjust="qfq")
            if len(df) < 60:
                return None
            df = df.sort_values("date").reset_index(drop=True)
            close = df["close"].values
            volume = df["volume"].values

            ema20 = ema(close, 20)[-1]
            ema60 = ema(close, 60)[-1]
            ema120 = ema(close, 120)[-1] if len(close) >= 120 else ema60

            ret20 = (close[-1] / close[-21] - 1) if len(close) >= 21 else 0
            ret120 = (close[-1] / close[-121] - 1) if len(close) >= 121 else (close[-1] / close[0] - 1)

            daily_ret = pd.Series(close[-120:]).pct_change().dropna()
            vol120 = daily_ret.std() * (252 ** 0.5) if len(daily_ret) > 1 else 999

            vol5 = volume[-5:].mean()
            vol20 = volume[-20:].mean()
            vol_ratio = vol5 / vol20 if vol20 > 0 else 0

            latest_change = (close[-1] / close[-2] - 1) * 100 if len(close) >= 2 else 0
            # 连续3日累计涨幅（排除连续涨停）
            surge_3d = (close[-1] / close[-4] - 1) * 100 if len(close) >= 4 else 0

            return {
                "symbol": symbol,
                "ema20": ema20, "ema60": ema60, "ema120": ema120,
                "ret20": ret20, "ret120": ret120, "vol120": vol120,
                "vol_ratio": vol_ratio, "latest_change": latest_change,
                "surge_3d": surge_3d, "latest_close": close[-1],
            }
        except Exception:
            return None

    tech_results = {}
    symbols = pool1["代码"].tolist()
    for s in symbols:
        res = fetch_tech(s)
        if res:
            tech_results[res["symbol"]] = res

    if not tech_results:
        return []

    tech_df = pd.DataFrame.from_dict(tech_results, orient="index")
    # 方案2：放宽技术面阈值，确保震荡市也能稳定产出 15~35 只标的
    tech_df = tech_df[
        (tech_df["ema20"] >= tech_df["ema60"] * 0.95) &
        (tech_df["ema60"] >= tech_df["ema120"] * 0.97) &
        (tech_df["vol_ratio"] >= 0.6) &
        (tech_df["latest_close"] >= tech_df["ema20"] * 0.95) &
        (tech_df["latest_change"] < 9.5) &
        (tech_df["latest_change"] > -9.0) &
        (tech_df["ret120"] - tech_df["ret20"] >= -0.05) &
        ~((tech_df["vol_ratio"] > 2.5) & (tech_df["latest_change"] < -5.0)) &
        (tech_df["surge_3d"] < 35.0)
    ].copy()

    # 120日波动率最低60%
    tech_df["vol_rank"] = tech_df["vol120"].rank(ascending=True, pct=True)
    tech_df = tech_df[tech_df["vol_rank"] <= 0.60]

    # 趋势健康度打分
    tech_df["trend_score"] = (
        (tech_df["ema20"] / tech_df["ema60"] - 1).rank(pct=True) +
        (tech_df["ema60"] / tech_df["ema120"] - 1).rank(pct=True) +
        tech_df["vol_ratio"].rank(pct=True) +
        (tech_df["ret120"] - tech_df["ret20"]).rank(pct=True)
    ) / 4

    pool2 = tech_df.sort_values("trend_score", ascending=False).head(50)

    # --------------- 最终交集 ---------------
    final_symbols = set(pool1["代码"]) & set(pool2.index)
    final_df = pool1[pool1["代码"].isin(final_symbols)].copy()

    results = []
    for _, row in final_df.iterrows():
        symbol_clean = row["代码"].replace("sh", "").replace("sz", "")
        tech = tech_results.get(row["代码"], {})
        results.append({
            "symbol": symbol_clean,
            "name": str(row["名称"]),
            "score": round(float(row["fundamental_score"]), 3),
            "reason": (
                f"ROE {row['净资产收益率']:.1f}%, 毛利 {row['销售毛利率']:.1f}%, "
                f"净利率 {row['净利率']:.1f}%, 120日收益 {(tech.get('ret120',0)*100):.1f}%, "
                f"波动 {(tech.get('vol120',0)*100):.1f}%, EMA多头"
            ),
        })

    return results
'''


ALLOWED_MODULES = {
    "akshare",
    "pandas",
    "numpy",
    "datetime",
    "json",
    "math",
    "random",
    "re",
    "collections",
    "itertools",
    "concurrent",
    "concurrent.futures",
    "time",
}


def ensure_builtin_picker(db: Session) -> Strategy:
    db_obj = db.query(Strategy).filter(Strategy.strategy_id == BUILTIN_PICKER_ID).first()
    if not db_obj:
        db_obj = Strategy(
            strategy_id=BUILTIN_PICKER_ID,
            name="本周选股（内置）",
            type="picker",
            description="系统内置的每周自动选股策略，基于当日活跃量价数据筛选。",
            code=DEFAULT_BUILTIN_CODE,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
    elif db_obj.code != DEFAULT_BUILTIN_CODE:
        db_obj.code = DEFAULT_BUILTIN_CODE
        db.commit()
        db.refresh(db_obj)
    return db_obj


def run_picker_code(code: str) -> List[dict]:
    """在受限环境中执行选股代码并返回结果。"""
    import importlib

    restricted_globals = {
        "__builtins__": {
            "True": True,
            "False": False,
            "None": None,
            "str": str,
            "int": int,
            "float": float,
            "list": list,
            "dict": dict,
            "tuple": tuple,
            "set": set,
            "type": type,
            "len": len,
            "range": range,
            "enumerate": enumerate,
            "zip": zip,
            "map": map,
            "filter": filter,
            "sum": sum,
            "min": min,
            "max": max,
            "abs": abs,
            "round": round,
            "print": print,
            "Exception": Exception,
            "ValueError": ValueError,
            "TypeError": TypeError,
            "KeyError": KeyError,
            "IndexError": IndexError,
            "isinstance": isinstance,
            "hasattr": hasattr,
            "getattr": getattr,
            "all": all,
            "any": any,
            "sorted": sorted,
            "reversed": reversed,
            "next": next,
            "iter": iter,
            "chr": chr,
            "ord": ord,
            "format": format,
            "repr": repr,
            "bool": bool,
            "object": object,
            "id": id,
            "hash": hash,
        }
    }

    def safe_import(name, *args, **kwargs):
        if name in ALLOWED_MODULES or any(name.startswith(m + ".") for m in ALLOWED_MODULES):
            return importlib.__import__(name, *args, **kwargs)
        raise ImportError(f"Module '{name}' is not allowed in picker environment.")

    restricted_globals["__builtins__"]["__import__"] = safe_import

    local_ns: dict[str, Any] = {}
    exec(code, restricted_globals, local_ns)

    if "pick_stocks" not in local_ns:
        raise ValueError("选股代码中必须定义 pick_stocks() 函数。")

    pick_fn = local_ns["pick_stocks"]
    results = pick_fn()
    if not isinstance(results, list):
        raise ValueError("pick_stocks() 必须返回一个列表。")
    return results


def create_picker_run(db: Session, picker_id: str) -> PickerRun:
    run = PickerRun(
        run_id=str(uuid.uuid4()),
        picker_id=picker_id,
        status="pending",
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def execute_picker(db: Session, picker_id: str) -> StockPool:
    picker = db.query(Strategy).filter(
        Strategy.strategy_id == picker_id, Strategy.type == "picker"
    ).first()
    if not picker:
        raise ValueError(f"选股策略 '{picker_id}' 不存在。")

    run = create_picker_run(db, picker_id)
    run.status = "running"
    db.add(run)
    db.commit()

    try:
        items = run_picker_code(picker.code)
        pool_id = str(uuid.uuid4())
        pool_name = f"{picker.name} - {datetime.datetime.now().strftime('%m-%d %H:%M')}"
        is_builtin = picker_id == BUILTIN_PICKER_ID

        # 如果是内置策略，将旧的 builtin 标记取消
        if is_builtin:
            db.query(StockPool).filter(StockPool.is_builtin_weekly == True).update(
                {StockPool.is_builtin_weekly: False}
            )
            pool_name = "本周选股"

        pool = StockPool(
            pool_id=pool_id,
            picker_id=picker_id,
            name=pool_name,
            is_builtin_weekly=is_builtin,
            expires_at=datetime.datetime.utcnow() + datetime.timedelta(days=7) if is_builtin else None,
        )
        db.add(pool)

        for item in items:
            db.add(
                StockPoolItem(
                    pool_id=pool_id,
                    symbol=item.get("symbol", ""),
                    name=item.get("name"),
                    score=item.get("score"),
                    reason=item.get("reason"),
                )
            )

        run.status = "success"
        run.result_count = len(items)
        run.logs = json.dumps({"message": "执行成功", "count": len(items)}, ensure_ascii=False)
        run.finished_at = datetime.datetime.utcnow()
        db.commit()
        db.refresh(pool)
        # 强制触发 items 懒加载，确保 FastAPI 序列化时数据已填充
        _ = pool.items
        return pool
    except Exception as e:
        run.status = "failed"
        run.logs = json.dumps({"error": str(e)}, ensure_ascii=False)
        run.finished_at = datetime.datetime.utcnow()
        db.commit()
        raise


def get_stock_pools(db: Session, picker_id: str | None = None, skip: int = 0, limit: int = 100):
    q = db.query(StockPool).options(selectinload(StockPool.items))
    if picker_id:
        q = q.filter(StockPool.picker_id == picker_id)
    return q.order_by(StockPool.generated_at.desc()).offset(skip).limit(limit).all()


def get_stock_pool(db: Session, pool_id: str) -> StockPool | None:
    return db.query(StockPool).options(selectinload(StockPool.items)).filter(StockPool.pool_id == pool_id).first()


def get_picker_runs(db: Session, picker_id: str | None = None, skip: int = 0, limit: int = 100):
    q = db.query(PickerRun)
    if picker_id:
        q = q.filter(PickerRun.picker_id == picker_id)
    return q.order_by(PickerRun.created_at.desc()).offset(skip).limit(limit).all()


def get_weekly_picker_summary(db: Session) -> dict:
    pool = db.query(StockPool).options(selectinload(StockPool.items)).filter(StockPool.is_builtin_weekly == True).first()
    if not pool:
        return {"has_new_weekly": False, "pool": None, "generated_at": None, "item_count": 0}
    return {
        "has_new_weekly": True,
        "pool": pool,
        "generated_at": pool.generated_at,
        "item_count": len(pool.items),
    }


def get_or_create_notification_settings(db: Session) -> NotificationSettings:
    ns = db.query(NotificationSettings).first()
    if not ns:
        ns = NotificationSettings(weekly_picker_push=True)
        db.add(ns)
        db.commit()
        db.refresh(ns)
    return ns


def update_notification_settings(db: Session, obj_in: NotificationSettingsUpdate) -> NotificationSettings:
    ns = get_or_create_notification_settings(db)
    ns.weekly_picker_push = obj_in.weekly_picker_push
    db.commit()
    db.refresh(ns)
    return ns


def run_builtin_weekly_if_enabled(db: Session):
    """由定时任务调用：如果推送开启，则运行内置策略。"""
    ns = get_or_create_notification_settings(db)
    if not ns.weekly_picker_push:
        return None
    ensure_builtin_picker(db)
    return execute_picker(db, BUILTIN_PICKER_ID)
