"""演示模式预置数据.

所有数据均为静态模拟，不依赖外部 API 和本地大模型。
"""

from __future__ import annotations

import datetime
import random
from typing import Any

from sqlalchemy.orm import Session


# ── 演示用户名称 ──
DEMO_USER_NAME = "演示用户"


# ── 演示组合 ──
DEMO_PORTFOLIO: dict[str, Any] = {
    "portfolio_id": "pf_demo_001",
    "adopted": True,
    "name": "演示稳健平衡组合",
    "saa": {
        "risk_profile": {"name": "稳健型"},
        "weights": {
            "stock": 0.15,
            "etf": 0.25,
            "bond": 0.35,
            "cash": 0.15,
            "commodity": 0.10,
        },
        "rationale": "基于稳健型画像的防御性战略资产配置：债券与现金提供安全垫，ETF 分散权益风险，个股适度增强",
        "data_source": "saa_engine (demo)",
    },
    "taa": {
        "overweight": ["国债ETF", "银行ETF"],
        "underweight": ["科技ETF"],
        "rationale": "当前市场周期下偏防御的战术调整，控制个股与高波动权益暴露",
        "data_source": "taa_engine (demo)",
    },
    "bindings": [
        {"symbol": "159995", "name": "科技ETF", "asset_class": "ETF", "weight": 0.0700, "strategy_id": "demo_s1", "sector": "科技", "sector_name": "科技"},
        {"symbol": "159928", "name": "消费ETF", "asset_class": "ETF", "weight": 0.0600, "strategy_id": "demo_s2", "sector": "消费", "sector_name": "消费"},
        {"symbol": "512800", "name": "银行ETF", "asset_class": "ETF", "weight": 0.0500, "strategy_id": "demo_s3", "sector": "金融", "sector_name": "金融"},
        {"symbol": "512100", "name": "工业ETF", "asset_class": "ETF", "weight": 0.0300, "strategy_id": "demo_s4", "sector": "工业", "sector_name": "工业"},
        {"symbol": "512170", "name": "医疗ETF", "asset_class": "ETF", "weight": 0.0400, "strategy_id": "demo_s5", "sector": "医药", "sector_name": "医药"},
        {"symbol": "511010", "name": "国债ETF", "asset_class": "bond", "weight": 0.3500, "strategy_id": "demo_s6", "sector": "债券", "sector_name": "债券"},
        {"symbol": "511880", "name": "银华日利", "asset_class": "cash", "weight": 0.1500, "strategy_id": "demo_s7", "sector": "现金", "sector_name": "现金"},
        {"symbol": "518880", "name": "黄金ETF", "asset_class": "commodity", "weight": 0.1000, "strategy_id": "demo_s8", "sector": "商品", "sector_name": "商品"},
        {"symbol": "300394", "name": "天孚通信", "asset_class": "stock", "weight": 0.1500, "strategy_id": "demo_s9", "sector": "通信", "sector_name": "通信"},
    ],
    "risk_config": {
        "stop_loss": 0.06,
        "max_position": 0.12,
        "max_drawdown": 0.10,
        "rebalance_threshold": 0.03,
        "risk_level": "中低风险",
        "rationale": "演示风控配置：严格控制单一权益仓位与组合最大回撤",
        "data_source": "rule_engine (demo)",
    },
    "reliability": {
        "score": 84.0,
        "confidence": 0.84,
        "reliability_level": "高",
        "backtest_available": True,
        "stress_test_available": True,
        "monte_carlo_available": True,
        "adoption_status": {"adopted": True, "reason": "通过 RAG 质检"},
        "rationale": "历史回测与压力测试表现稳定，波动率低于基准",
        "data_source": "backtest_summary (demo)",
    },
    "portfolio_lifespan": 30,
    "portfolio_health": 86,
    "backtest_summary": {
        "annual_return": 0.058,
        "sharpe_ratio": 0.98,
        "max_drawdown": 0.06,
        "trade_count": 8,
        "win_rate": 0.62,
        "data_source": "backtest_adapter (demo)",
    },
    "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "status": "adopted",
    "data_sources": {
        "profile": "demo_profile",
        "market_signal": "demo_market_signal",
        "saa": "saa_engine (demo)",
        "taa": "taa_engine (demo)",
        "bindings": "hybrid_designer (demo)",
        "risk_config": "rule_engine (demo)",
        "reliability": "backtest_summary (demo)",
    },
    "dynamic_picking": None,
}


# ── 演示市场报告：分页1 ──
_DEMO_PAGE1: dict[str, Any] = {
    "market_summary": "今日市场窄幅震荡，主要指数小幅收涨，北向资金净流入约 25 亿元。当前市场处于复苏期，综合情绪中性偏乐观，五层信号综合评分 68.5。",
    "index_performance": {
        "indices": [
            {"name": "上证指数", "symbol": "000001", "change_pct": 0.34, "open": 3040.12, "high": 3055.67, "low": 3038.45, "close": 3050.21, "prev_close": 3039.88, "volume": 320000000, "amount": 42000000000},
            {"name": "深证成指", "symbol": "399001", "change_pct": 0.52, "open": 9769.33, "high": 9845.18, "low": 9741.26, "close": 9820.14, "prev_close": 9769.33, "volume": 410000000, "amount": 56000000000},
            {"name": "沪深300", "symbol": "000300", "change_pct": 0.41, "open": 3565.80, "high": 3592.15, "low": 3558.92, "close": 3580.66, "prev_close": 3565.80, "volume": 150000000, "amount": 28000000000},
            {"name": "中证500", "symbol": "000905", "change_pct": 0.63, "open": 5386.18, "high": 5442.07, "low": 5369.45, "close": 5420.33, "prev_close": 5386.18, "volume": 180000000, "amount": 24000000000},
            {"name": "创业板指", "symbol": "399006", "change_pct": 0.78, "open": 1865.42, "high": 1892.17, "low": 1858.03, "close": 1880.55, "prev_close": 1865.42, "volume": 220000000, "amount": 32000000000},
        ],
        "intraday_narrative": "早盘小幅高开后震荡整理，午后科技板块带动指数走强，尾盘维持红盘报收。",
    },
    "sector_performance": {
        "sectors": [
            {"name": "半导体", "change_pct": 2.17, "fund_flow": 1250000000, "main_force": 850000000, "rank": 1},
            {"name": "银行", "change_pct": 1.05, "fund_flow": 830000000, "main_force": 520000000, "rank": 2},
            {"name": "医药", "change_pct": 0.34, "fund_flow": 210000000, "main_force": 120000000, "rank": 4},
            {"name": "白酒", "change_pct": -0.52, "fund_flow": -420000000, "main_force": -280000000, "rank": 5},
        ],
        "fund_flow_summary": "主力资金净流入半导体、银行板块，白酒板块小幅流出。",
        "intraday_narrative": "上午资金偏向防守，午后科技成长板块获得资金回流。",
    },
    "policy_changes": {
        "has_policy": False,
        "summary": "今日无重大政策发布",
        "policies": [],
    },
    "risk_signals": {
        "volatility_regime": "低波动",
        "sentiment": "中性偏乐观",
        "alerts": ["注意科技股分化", "关注北向资金流向"],
    },
    "northbound_fund": {
        "net_inflow": 25.3,
        "cumulative_inflow": 1250.5,
        "leading_sectors": ["半导体", "银行"],
        "external_env": "美联储维持利率不变",
        "inference": "外资延续净流入，偏好成长与金融板块",
    },
    "outlook": {
        "short_term": "预计市场维持震荡，个股分化加剧",
        "medium_term": "关注业绩披露窗口与政策落地节奏",
        "risks": ["外部地缘风险", "汇率波动", "科技股估值承压"],
    },
}


# ── 演示市场报告：分页2 ──
_DEMO_PAGE2: dict[str, Any] = {
    "portfolio_return": 0.0042,
    "portfolio_return_pct": "+0.42%",
    "benchmark_return": 0.0041,
    "excess_return": 0.00007,
    "summary": "今日组合小幅收涨，个股与科技板块贡献居前，黄金小幅回调。",
    "asset_performances": [
        {"symbol": "159995", "name": "科技ETF", "asset_class": "ETF", "weight": 0.0700, "price": 2.92, "change_pct": 1.85, "daily_return": 0.0185, "contribution": 0.00130},
        {"symbol": "159928", "name": "消费ETF", "asset_class": "ETF", "weight": 0.0600, "price": 0.627, "change_pct": 0.62, "daily_return": 0.0062, "contribution": 0.00037},
        {"symbol": "512800", "name": "银行ETF", "asset_class": "ETF", "weight": 0.0500, "price": 0.771, "change_pct": 0.98, "daily_return": 0.0098, "contribution": 0.00049},
        {"symbol": "512100", "name": "工业ETF", "asset_class": "ETF", "weight": 0.0300, "price": 3.58, "change_pct": -0.41, "daily_return": -0.0041, "contribution": -0.00012},
        {"symbol": "512170", "name": "医疗ETF", "asset_class": "ETF", "weight": 0.0400, "price": 0.297, "change_pct": 0.23, "daily_return": 0.0023, "contribution": 0.00009},
        {"symbol": "511010", "name": "国债ETF", "asset_class": "bond", "weight": 0.3500, "price": 141.463, "change_pct": 0.018, "daily_return": 0.00018, "contribution": 0.00006},
        {"symbol": "511880", "name": "银华日利", "asset_class": "cash", "weight": 0.1500, "price": 100.541, "change_pct": 0.003, "daily_return": 0.00003, "contribution": 0.00001},
        {"symbol": "518880", "name": "黄金ETF", "asset_class": "commodity", "weight": 0.1000, "price": 8.716, "change_pct": -0.28, "daily_return": -0.0028, "contribution": -0.00028},
        {"symbol": "300394", "name": "天孚通信", "asset_class": "stock", "weight": 0.1500, "price": 326.12, "change_pct": 1.50, "daily_return": 0.0150, "contribution": 0.00225},
    ],
    "best_contributor": {"symbol": "300394", "name": "天孚通信", "asset_class": "stock", "weight": 0.15, "price": 326.12, "change_pct": 1.50, "daily_return": 0.0150, "contribution": 0.00225},
    "worst_contributor": {"symbol": "518880", "name": "黄金ETF", "asset_class": "commodity", "weight": 0.10, "price": 8.716, "change_pct": -0.28, "daily_return": -0.0028, "contribution": -0.00028},
}


# ── 演示市场报告：分页3（每周） ──
_DEMO_PAGE3: dict[str, Any] = {
    "week_start": (datetime.date.today() - datetime.timedelta(days=datetime.date.today().weekday())).isoformat(),
    "week_end": (datetime.date.today() - datetime.timedelta(days=datetime.date.today().weekday()) + datetime.timedelta(days=6)).isoformat(),
    "market_summary": "本周市场先抑后扬，科技板块领涨，北向资金累计净流入约 80 亿元。",
    "index_performance": {
        "indices": [
            {"name": "上证指数", "symbol": "000001", "change_pct": 1.2, "open": 3015.33, "high": 3060.18, "low": 3008.92, "close": 3050.21, "prev_close": 3015.33, "volume": 1500000000, "amount": 200000000000},
            {"name": "深证成指", "symbol": "399001", "change_pct": 1.8, "open": 9648.56, "high": 9855.30, "low": 9612.18, "close": 9820.14, "prev_close": 9648.56, "volume": 1900000000, "amount": 260000000000},
            {"name": "沪深300", "symbol": "000300", "change_pct": 1.5, "open": 3528.24, "high": 3595.10, "low": 3512.67, "close": 3580.66, "prev_close": 3528.24, "volume": 700000000, "amount": 130000000000},
        ],
        "intraday_narrative": "周一至周三震荡整理，周四科技板块带动市场反弹，周五维持强势。",
    },
    "sector_performance": {
        "sectors": [
            {"name": "半导体", "change_pct": 4.5, "fund_flow": 5800000000, "main_force": 3900000000, "rank": 1},
            {"name": "银行", "change_pct": 2.2, "fund_flow": 3100000000, "main_force": 2100000000, "rank": 2},
            {"name": "医药", "change_pct": 0.8, "fund_flow": 800000000, "main_force": 520000000, "rank": 3},
        ],
        "fund_flow_summary": "本周主力资金持续流入半导体与银行板块，医药板块小幅流入。",
        "intraday_narrative": "资金从消费向科技成长切换，周期股表现分化。",
    },
    "policy_changes": {
        "has_policy": False,
        "summary": "本周无重大政策发布",
        "policies": [],
    },
    "risk_signals": {
        "volatility_regime": "中等波动",
        "sentiment": "中性偏乐观",
        "alerts": ["科技股短期涨幅较大", "关注周五美股走势"],
    },
    "northbound_fund": {
        "net_inflow": 80.6,
        "cumulative_inflow": 1305.2,
        "leading_sectors": ["半导体", "银行", "新能源"],
        "external_env": "美元指数走弱，人民币汇率企稳",
        "inference": "外资加仓成长与金融，风险偏好回升",
    },
    "outlook": {
        "short_term": "预计下周市场维持震荡，关注业绩披露",
        "medium_term": "经济复苏预期延续，结构性机会为主",
        "risks": ["外部地缘风险", "美联储政策预期变化"],
    },
}


DEMO_DAILY_REPORT: dict[str, Any] = {
    "user_id": None,  # 调用时填充
    "portfolio_id": None,
    "report_type": "daily",
    "report_date": None,  # 调用时填充
    "page1_market_overview": _DEMO_PAGE1,
    "page2_portfolio_performance": _DEMO_PAGE2,
    "page3_weekly_market": None,
}


DEMO_WEEKLY_REPORT: dict[str, Any] = {
    "user_id": None,
    "portfolio_id": None,
    "report_type": "weekly",
    "report_date": None,
    "page1_market_overview": _DEMO_PAGE1,
    "page2_portfolio_performance": _DEMO_PAGE2,
    "page3_weekly_market": _DEMO_PAGE3,
}


def _seed_float(seed: str, low: float, high: float) -> float:
    """基于字符串 seed 生成 [low, high] 内的确定性浮点数."""
    h = hash(seed)
    if h < 0:
        h = -h
    return low + (h % 10000) / 10000 * (high - low)


def get_demo_backtest_metrics(seed: str = "demo_default") -> dict[str, Any]:
    """为不同策略/标的生成差异化的演示回测指标.

    同一 seed 永远返回同一组指标，保证演示数据可复现；
    不同 seed 之间收益、波动、回撤会有明显差异，避免每项资产回测都相同。
    """
    asset_profile = seed.lower()

    # 根据标的类型设定基础区间
    if "bond" in asset_profile or "511010" in asset_profile or "国债" in asset_profile:
        base_return = _seed_float(seed + "_ret", 0.020, 0.045)
        volatility = _seed_float(seed + "_vol", 0.020, 0.040)
        max_dd = _seed_float(seed + "_dd", 0.010, 0.030)
    elif "cash" in asset_profile or "511880" in asset_profile or "银华" in asset_profile:
        base_return = _seed_float(seed + "_ret", 0.005, 0.020)
        volatility = _seed_float(seed + "_vol", 0.001, 0.005)
        max_dd = 0.0
    elif "commodity" in asset_profile or "518880" in asset_profile or "黄金" in asset_profile:
        base_return = _seed_float(seed + "_ret", 0.030, 0.080)
        volatility = _seed_float(seed + "_vol", 0.100, 0.160)
        max_dd = _seed_float(seed + "_dd", 0.050, 0.120)
    elif "stock" in asset_profile or "300394" in asset_profile or "天孚" in asset_profile:
        base_return = _seed_float(seed + "_ret", -0.050, 0.150)
        volatility = _seed_float(seed + "_vol", 0.220, 0.380)
        max_dd = _seed_float(seed + "_dd", 0.100, 0.250)
    else:  # ETF 等权益类
        base_return = _seed_float(seed + "_ret", 0.020, 0.100)
        volatility = _seed_float(seed + "_vol", 0.120, 0.220)
        max_dd = _seed_float(seed + "_dd", 0.060, 0.150)

    sharpe = base_return / volatility if volatility > 0 else 0.0
    win_rate = _seed_float(seed + "_wr", 0.45, 0.70)
    trade_count = int(_seed_float(seed + "_tc", 5, 25))
    total_return = base_return * _seed_float(seed + "_tr", 1.5, 2.5)

    return {
        "total_return": round(total_return, 4),
        "annual_return": round(base_return, 4),
        "annualized_return": round(base_return, 4),
        "sharpe_ratio": round(sharpe, 2),
        "max_drawdown": round(max_dd, 4),
        "volatility": round(volatility, 4),
        "trade_count": trade_count,
        "win_rate": round(win_rate, 2),
        "avg_return_per_trade": round(base_return / trade_count if trade_count else 0, 4),
    }


# 保留常量名作为默认演示组合级指标（向后兼容）
DEMO_BACKTEST_METRICS: dict[str, Any] = get_demo_backtest_metrics("demo_portfolio")


DEMO_BACKTEST_BENCHMARK_METRICS: dict[str, Any] = {
    "total_return": 0.1021,
    "annual_return": 0.058,
    "annualized_return": 0.058,
    "sharpe_ratio": 0.78,
    "max_drawdown": 0.14,
    "volatility": 0.16,
}


def get_demo_daily_report(user_id: int, portfolio_id: int | None) -> dict[str, Any]:
    """返回填充了用户/组合/日期的每日演示报告."""
    report = DEMO_DAILY_REPORT.copy()
    report["user_id"] = user_id
    report["portfolio_id"] = portfolio_id
    report["report_date"] = datetime.date.today().isoformat()
    return report


def get_demo_weekly_report(user_id: int, portfolio_id: int | None) -> dict[str, Any]:
    """返回填充了用户/组合/日期的每周演示报告."""
    report = DEMO_WEEKLY_REPORT.copy()
    report["user_id"] = user_id
    report["portfolio_id"] = portfolio_id
    report["report_date"] = datetime.date.today().isoformat()
    return report


def ensure_demo_portfolio(db: Session, user_id: int) -> int:
    """确保演示用户存在一个且仅一个激活的 Portfolio，返回 portfolio_id."""
    from app.models.portfolio import Portfolio

    existing = (
        db.query(Portfolio)
        .filter(Portfolio.user_id == user_id)
        .order_by(Portfolio.updated_at.desc())
        .all()
    )
    if existing:
        # 保留最新一个并激活，其余停用
        portfolio = existing[0]
        portfolio.is_active = True
        for p in existing[1:]:
            p.is_active = False
        db.commit()
        db.refresh(portfolio)
        return portfolio.id

    portfolio = Portfolio(
        user_id=user_id,
        name=DEMO_PORTFOLIO.get("name", "演示组合"),
        config_json=DEMO_PORTFOLIO,
        backtest_result_json={"metrics": DEMO_BACKTEST_METRICS},
        lifespan_months=DEMO_PORTFOLIO.get("portfolio_lifespan"),
        health_score=DEMO_PORTFOLIO.get("portfolio_health"),
        is_active=True,
    )
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)
    return portfolio.id


def seed_demo_paper_trading_records(db: Session, user_id: int, portfolio_id: int, days: int = 3) -> None:
    """为演示用户生成过去 N 天的模拟盘日记录（确定性随机）."""
    from app.models.paper_trading import PaperTradingDailyRecord

    random.seed(user_id + portfolio_id + days)
    today = datetime.date.today()
    nav = 1.0
    for i in range(days, 0, -1):
        d = today - datetime.timedelta(days=i)
        # 每日收益率在 [-1.5%, +1.5%] 之间，产生缓慢向上的净值曲线
        daily_return = random.uniform(-0.015, 0.018)
        nav = nav * (1 + daily_return)
        record = PaperTradingDailyRecord(
            user_id=user_id,
            portfolio_id=portfolio_id,
            record_date=d.isoformat(),
            daily_return=daily_return,
            cumulative_return=nav - 1,
            nav=nav,
            report_id=None,
            asset_snapshot=None,
        )
        db.merge(record)
    db.commit()


def seed_demo_market_reports(db: Session, user_id: int, portfolio_id: int) -> None:
    """为演示用户生成今日日报和本周周报（MarketReport 表）."""
    from app.models.operation_log import MarketReport

    today = datetime.date.today()
    week_start = today - datetime.timedelta(days=today.weekday())
    week_end = week_start + datetime.timedelta(days=6)

    daily_report = get_demo_daily_report(user_id, portfolio_id)
    db.merge(
        MarketReport(
            user_id=user_id,
            portfolio_id=portfolio_id,
            report_type="daily",
            report_date=today.isoformat(),
            page1_market_overview=daily_report["page1_market_overview"],
            page2_portfolio_performance=daily_report["page2_portfolio_performance"],
            page3_weekly_market=None,
        )
    )

    weekly_report = get_demo_weekly_report(user_id, portfolio_id)
    db.merge(
        MarketReport(
            user_id=user_id,
            portfolio_id=portfolio_id,
            report_type="weekly",
            report_date=week_end.isoformat(),
            page1_market_overview=weekly_report["page1_market_overview"],
            page2_portfolio_performance=weekly_report["page2_portfolio_performance"],
            page3_weekly_market=weekly_report["page3_weekly_market"],
        )
    )
    db.commit()


def seed_demo_weekly_report(db: Session, user_id: int, portfolio_id: int) -> None:
    """为演示用户生成本周周报（WeeklyReport 表）."""
    from app.models.operation_log import WeeklyReport

    today = datetime.date.today()
    week_start = today - datetime.timedelta(days=today.weekday())
    week_end = week_start + datetime.timedelta(days=6)
    page3 = DEMO_WEEKLY_REPORT.get("page3_weekly_market") or {}

    db.merge(
        WeeklyReport(
            user_id=user_id,
            portfolio_id=portfolio_id,
            week_start=week_start.isoformat(),
            week_end=week_end.isoformat(),
            portfolio_return=DEMO_BACKTEST_METRICS.get("annual_return", 0.0),
            portfolio_cum_return=DEMO_BACKTEST_METRICS.get("total_return", 0.0),
            benchmark_return=DEMO_BACKTEST_BENCHMARK_METRICS.get("total_return", 0.0),
            max_drawdown=DEMO_BACKTEST_METRICS.get("max_drawdown", 0.0),
            allocation_snapshot=DEMO_PORTFOLIO.get("saa", {}),
            allocation_changes={},
            market_summary=page3.get("summary"),
            market_cycle=page3.get("market_cycle"),
            composite_score=page3.get("composite_score"),
            next_week_outlook=page3.get("next_week_outlook"),
            recommended_actions=page3.get("recommended_actions", []),
            lifespan_alerts=[],
        )
    )
    db.commit()


def ensure_demo_data(db: Session, user_id: int) -> int:
    """确保演示用户拥有 Portfolio、模拟盘记录、今日报告和本周周报；返回 portfolio_id."""
    portfolio_id = ensure_demo_portfolio(db, user_id)

    # 模拟盘日记录
    from app.models.paper_trading import PaperTradingDailyRecord

    existing_record = (
        db.query(PaperTradingDailyRecord)
        .filter(
            PaperTradingDailyRecord.user_id == user_id,
            PaperTradingDailyRecord.portfolio_id == portfolio_id,
        )
        .first()
    )
    if not existing_record:
        seed_demo_paper_trading_records(db, user_id, portfolio_id)

    # 今日报告（MarketReport daily）与本周周报（MarketReport weekly）
    from app.models.operation_log import MarketReport

    existing_daily = (
        db.query(MarketReport)
        .filter(
            MarketReport.user_id == user_id,
            MarketReport.report_type == "daily",
            MarketReport.report_date == datetime.date.today().isoformat(),
        )
        .first()
    )
    if not existing_daily:
        seed_demo_market_reports(db, user_id, portfolio_id)

    # 本周周报（WeeklyReport 表）
    from app.models.operation_log import WeeklyReport

    today = datetime.date.today()
    week_start = today - datetime.timedelta(days=today.weekday())
    existing_weekly = (
        db.query(WeeklyReport)
        .filter(
            WeeklyReport.user_id == user_id,
            WeeklyReport.week_start == week_start.isoformat(),
        )
        .first()
    )
    if not existing_weekly:
        seed_demo_weekly_report(db, user_id, portfolio_id)

    return portfolio_id
