"""市场报告生成服务 — 每日市场报告 + 资产组合表现 + 每周市场综述.

完全替换原有 weekly_report.py 的功能.
"""

import datetime
import json
from typing import Any

import akshare as ak
import pandas as pd

from app.db.session import SessionLocal
from app.services import data_fetcher
from app.services.market_signal_service import collect_market_signal
from app.services.news_crawler import crawl_and_analyze
from app.services import demo_user_service
from app.services.demo_data import get_demo_daily_report, get_demo_weekly_report


# ── 主要指数配置 ──
MAIN_INDICES = {
    "000001": {"name": "上证指数", "category": "broad"},
    "399001": {"name": "深证成指", "category": "broad"},
    "000300": {"name": "沪深300", "category": "broad"},
    "000905": {"name": "中证500", "category": "broad"},
    "399006": {"name": "创业板指", "category": "growth"},
    "000688": {"name": "科创50", "category": "tech"},
}

# 关键时间点（用于分时描述）
INTRADAY_TIME_SEGMENTS = [
    ("09:30", "10:30", "早盘"),
    ("10:30", "11:30", "上午盘中"),
    ("13:00", "14:00", "午后开盘"),
    ("14:00", "15:00", "尾盘"),
]


def generate_daily_market_report(user_id: int, portfolio_id: int | None = None) -> dict[str, Any]:
    """生成完整的每日市场报告（分页1 + 分页2）."""
    if demo_user_service.is_demo_user(SessionLocal(), user_id):
        return get_demo_daily_report(user_id, portfolio_id)

    today = datetime.date.today()

    page1 = _generate_page1_daily_market()
    page2 = _generate_page2_portfolio_performance(user_id, portfolio_id)

    return {
        "user_id": user_id,
        "portfolio_id": portfolio_id,
        "report_type": "daily",
        "report_date": today.isoformat(),
        "page1_market_overview": page1,
        "page2_portfolio_performance": page2,
        "page3_weekly_market": None,
    }


def generate_weekly_market_report(user_id: int, portfolio_id: int | None = None) -> dict[str, Any]:
    """生成完整的每周市场报告（分页1 + 分页2 + 分页3）."""
    if demo_user_service.is_demo_user(SessionLocal(), user_id):
        return get_demo_weekly_report(user_id, portfolio_id)

    today = datetime.date.today()
    week_start = today - datetime.timedelta(days=today.weekday())
    week_end = week_start + datetime.timedelta(days=6)

    page1 = _generate_page1_daily_market()
    page2 = _generate_page2_portfolio_performance(user_id, portfolio_id)
    page3 = _generate_page3_weekly_market(week_start, week_end)

    return {
        "user_id": user_id,
        "portfolio_id": portfolio_id,
        "report_type": "weekly",
        "report_date": today.isoformat(),
        "page1_market_overview": page1,
        "page2_portfolio_performance": page2,
        "page3_weekly_market": page3,
    }


# ── 分页1：今日国内股票市场交易报告 ──

def _generate_page1_daily_market() -> dict[str, Any]:
    """生成分页1：今日国内股票市场交易报告."""
    signal = collect_market_signal()

    return {
        "market_summary": _generate_market_summary(signal),
        "index_performance": _fetch_index_performance_with_intraday(),
        "sector_performance": _fetch_sector_performance_with_intraday(),
        "policy_changes": _extract_policy_changes(),
        "risk_signals": _analyze_risk_signals(signal),
        "northbound_fund": _fetch_northbound_fund(),
        "outlook": _generate_daily_outlook(signal),
    }


def _generate_market_summary(signal: dict[str, Any]) -> str:
    """生成市场综述文字."""
    today_str = datetime.date.today().strftime("%Y年%m月%d日")
    mood = signal.get("market_mood", "中性")
    cycle = signal.get("market_cycle", "")
    composite = signal.get("composite_score", 0)

    index_perf = _fetch_index_performance_with_intraday()
    indices = index_perf.get("indices", [])

    if not indices:
        return f"{today_str}，A股市场行情数据获取失败，暂无法生成市场综述。"

    # 根据主要指数涨跌判断大势
    avg_change = sum(i.get("change_pct", 0) for i in indices) / len(indices)
    up_indices = [i for i in indices if i.get("change_pct", 0) > 0]
    down_indices = [i for i in indices if i.get("change_pct", 0) < 0]

    if avg_change > 1:
        trend_desc = "强势上涨"
    elif avg_change > 0.3:
        trend_desc = "震荡走强"
    elif avg_change > -0.3:
        trend_desc = "窄幅震荡"
    elif avg_change > -1:
        trend_desc = "震荡走弱"
    else:
        trend_desc = "明显调整"

    summary = f"{today_str}，A股三大指数呈现{trend_desc}走势。"

    if len(up_indices) >= len(indices) * 0.7:
        summary += "市场整体情绪积极，多数主要指数收涨。"
    elif len(down_indices) >= len(indices) * 0.7:
        summary += "市场整体情绪偏谨慎，多数主要指数收跌。"
    else:
        summary += "市场内部出现分化，大小盘、成长价值板块表现不一。"

    # 加入五层信号信息
    summary += f"当前市场处于{cycle}，综合情绪{mood}，五层信号综合评分{composite:.1f}。"

    return summary


def _fetch_index_performance_with_intraday() -> dict[str, Any]:
    """获取主要指数今日表现并生成分时概述."""
    indices = []

    # 先尝试实时行情
    spot_df = None
    try:
        spot_df = ak.stock_zh_index_spot_em()
    except Exception as e:
        print(f"[MarketReport] Index spot fetch error: {e}")

    if spot_df is not None and not spot_df.empty:
        for symbol, info in MAIN_INDICES.items():
            row = spot_df[spot_df.get("代码", "") == symbol]
            if not row.empty:
                r = row.iloc[0]
                indices.append({
                    "name": info["name"],
                    "symbol": symbol,
                    "change_pct": _safe_float(r.get("涨跌幅"), 0),
                    "open": _safe_float(r.get("今开"), 0),
                    "high": _safe_float(r.get("最高"), 0),
                    "low": _safe_float(r.get("最低"), 0),
                    "close": _safe_float(r.get("最新价"), 0),
                    "prev_close": _safe_float(r.get("昨收"), 0),
                    "volume": _safe_float(r.get("成交量"), 0),
                    "amount": _safe_float(r.get("成交额"), 0),
                })

    # 实时行情失败或为空时，用历史日线回退
    if not indices:
        print("[MarketReport] Falling back to index hist data")
        today = datetime.date.today()
        for symbol, info in MAIN_INDICES.items():
            try:
                # 优先使用中证指数历史接口获取指数日线
                df = ak.stock_zh_index_hist_csindex(symbol=symbol)
                if df is not None and not df.empty:
                    df = df.copy()
                    df["日期"] = pd.to_datetime(df["日期"])
                    today_df = df[df["日期"] == pd.Timestamp(today)]
                    if not today_df.empty:
                        row = today_df.iloc[0]
                    else:
                        row = df.iloc[-1]

                    close = _safe_float(row.get("收盘"), 0)
                    open_price = _safe_float(row.get("开盘"), close)
                    prev_close = _safe_float(row.get("昨收"), open_price)
                    change_pct = (close - prev_close) / prev_close * 100 if prev_close else 0
                    indices.append({
                        "name": info["name"],
                        "symbol": symbol,
                        "change_pct": change_pct,
                        "open": open_price,
                        "high": _safe_float(row.get("最高"), 0),
                        "low": _safe_float(row.get("最低"), 0),
                        "close": close,
                        "prev_close": prev_close,
                        "volume": _safe_float(row.get("成交量"), 0),
                        "amount": 0,
                    })
            except Exception as e:
                print(f"[MarketReport] Index hist fallback error for {symbol}: {e}")

    narrative = _generate_index_intraday_narrative(indices)
    return {"indices": indices, "intraday_narrative": narrative}


def _generate_index_intraday_narrative(indices: list[dict]) -> str:
    """根据指数数据生成分时概述文字（含关键时间点）."""
    if not indices:
        return "今日指数数据获取失败，无法生成分时概述。"

    # 用上证指数为代表生成描述
    sh_index = next((i for i in indices if i["symbol"] == "000001"), None)
    if not sh_index:
        sh_index = indices[0]

    change_pct = sh_index.get("change_pct", 0)
    high = sh_index.get("high", 0)
    low = sh_index.get("low", 0)
    prev_close = sh_index.get("prev_close", 0)

    # 基于涨跌幅判断开盘情绪
    if change_pct > 1:
        open_mood = "高开"
    elif change_pct > 0.3:
        open_mood = "小幅高开"
    elif change_pct > -0.3:
        open_mood = "平开"
    elif change_pct > -1:
        open_mood = "小幅低开"
    else:
        open_mood = "低开"

    narrative = f"{sh_index['name']}今日{open_mood}"

    if prev_close > 0:
        high_pct = (high - prev_close) / prev_close * 100
        low_pct = (low - prev_close) / prev_close * 100

        if abs(high_pct - low_pct) > 1.5:
            narrative += f"，盘中波动剧烈，最高触及{high:.2f}点（{high_pct:+.2f}%），最低下探{low:.2f}点（{low_pct:+.2f}%）"
        else:
            narrative += f"，盘中围绕{prev_close:.2f}点窄幅波动"

    # 尝试获取分钟数据关键时间点
    minute_summary = _fetch_index_minute_summary(sh_index["symbol"], sh_index["name"])
    if minute_summary:
        narrative += f"。{minute_summary}"

    narrative += f"，最终收涨{change_pct:+.2f}%。"

    # 描述其他指数相对强弱
    others = [i for i in indices if i["symbol"] != sh_index["symbol"]]
    if others:
        best = max(others, key=lambda x: x["change_pct"])
        worst = min(others, key=lambda x: x["change_pct"])
        narrative += f"{best['name']}表现最强（{best['change_pct']:+.2f}%），{worst['name']}表现最弱（{worst['change_pct']:+.2f}%）。"

    return narrative


def _fetch_index_minute_summary(symbol: str, name: str) -> str:
    """获取指数分时数据并提取关键时间点描述."""
    try:
        # 优先尝试东方财富分钟数据
        today = datetime.date.today()
        start_str = today.strftime("%Y%m%d")
        end_str = start_str
        df = ak.stock_zh_a_hist_min_em(symbol=symbol, period="1", start_date=start_str, end_date=end_str)
        if df is None or df.empty:
            return ""

        df = df.copy()
        df["时间"] = pd.to_datetime(df["时间"])
        df["涨跌幅"] = df["涨跌幅"].astype(float)

        # 关键时间点
        open_time = df[df["时间"].dt.strftime("%H:%M") == "09:30"]
        morning_low = df[df["时间"] <= "11:30"]["涨跌幅"].min() if not df[df["时间"] <= "11:30"].empty else None
        afternoon_high = df[df["时间"] >= "13:00"]["涨跌幅"].max() if not df[df["时间"] >= "13:00"].empty else None
        close_time = df[df["时间"].dt.strftime("%H:%M") == "15:00"]

        parts = []

        # 早盘低点时间
        if morning_low is not None:
            low_row = df[df["时间"] <= "11:30"][df["涨跌幅"] == morning_low]
            if not low_row.empty:
                low_time = low_row.iloc[0]["时间"].strftime("%H:%M")
                parts.append(f"早盘{low_time}左右触及日内低点（{morning_low:+.2f}%）")

        # 午后高点时间
        if afternoon_high is not None:
            high_row = df[df["时间"] >= "13:00"][df["涨跌幅"] == afternoon_high]
            if not high_row.empty:
                high_time = high_row.iloc[0]["时间"].strftime("%H:%M")
                parts.append(f"午后{high_time}左右创日内高点（{afternoon_high:+.2f}%）")

        # 尾盘走势
        if not close_time.empty:
            close_change = float(close_time.iloc[0]["涨跌幅"])
            parts.append(f"收盘前维持{close_change:+.2f}%附近")

        if parts:
            return "；".join(parts)
    except Exception as e:
        print(f"[MarketReport] Minute data fetch error for {symbol}: {e}")

    return ""


def _fetch_sector_performance_with_intraday() -> dict[str, Any]:
    """获取板块表现与资金流向."""
    sectors = []
    fund_df = None

    try:
        fund_df = ak.stock_fund_flow_industry(symbol="即时")
    except Exception as e:
        print(f"[MarketReport] Sector fund flow fetch error: {e}")

    if fund_df is not None and not fund_df.empty:
        for _, row in fund_df.head(20).iterrows():
            sectors.append({
                "name": str(row.get("行业", "")),
                "change_pct": _safe_float(row.get("行业-涨跌幅"), 0),
                "fund_flow": _safe_float(row.get("净额", 0), 0) * 10000,  # 亿元转万元
                "main_force": _safe_float(row.get("超大单净流入", 0), 0) * 10000,
                "rank": len(sectors) + 1,
            })

    narrative = _generate_sector_intraday_narrative(sectors)
    fund_summary = _generate_fund_flow_summary(sectors)

    return {
        "sectors": sectors,
        "fund_flow_summary": fund_summary,
        "intraday_narrative": narrative,
    }


def _generate_sector_intraday_narrative(sectors: list[dict]) -> str:
    """生成板块分时概述（含关键时间点以资金流向为核心）."""
    if not sectors:
        return "板块数据获取失败，无法生成分时概述。"

    inflow_sectors = sorted([s for s in sectors if s.get("fund_flow", 0) > 0], key=lambda x: x["fund_flow"], reverse=True)
    outflow_sectors = sorted([s for s in sectors if s.get("fund_flow", 0) < 0], key=lambda x: x["fund_flow"])

    parts = []

    if inflow_sectors:
        top3 = inflow_sectors[:3]
        names = ", ".join([s["name"] for s in top3])
        total_in = sum(s["fund_flow"] for s in top3) / 10000
        parts.append(f"早盘至收盘，{names}持续获得资金净流入，合计净流入约{total_in:.1f}亿元")

    if outflow_sectors:
        bottom3 = outflow_sectors[:3]
        names = ", ".join([s["name"] for s in bottom3])
        total_out = abs(sum(s["fund_flow"] for s in bottom3)) / 10000
        parts.append(f"{names}资金净流出居前，合计净流出约{total_out:.1f}亿元")

    # 领涨/领跌
    up_sorted = sorted(sectors, key=lambda x: x["change_pct"], reverse=True)
    if up_sorted:
        leader = up_sorted[0]
        laggard = up_sorted[-1]
        parts.append(f"收盘时{leader['name']}领涨（{leader['change_pct']:+.2f}%），{laggard['name']}领跌（{laggard['change_pct']:+.2f}%）")

    if parts:
        return "。".join(parts) + "。"
    return "板块表现相对平稳，资金分歧不大。"


def _generate_fund_flow_summary(sectors: list[dict]) -> str:
    """生成资金流向总结与核心矛盾."""
    if not sectors:
        return "资金流向数据获取失败。"

    total_in = sum(s["fund_flow"] for s in sectors if s["fund_flow"] > 0) / 10000
    total_out = abs(sum(s["fund_flow"] for s in sectors if s["fund_flow"] < 0)) / 10000
    net = total_in - total_out

    inflow_sectors = sorted([s for s in sectors if s["fund_flow"] > 0], key=lambda x: x["fund_flow"], reverse=True)
    outflow_sectors = sorted([s for s in sectors if s["fund_flow"] < 0], key=lambda x: x["fund_flow"])

    summary = f"主力资金净流入{total_in:.1f}亿元，净流出{total_out:.1f}亿元，合计净{'流入' if net > 0 else '流出'}{abs(net):.1f}亿元。"

    if inflow_sectors and outflow_sectors:
        top_in = inflow_sectors[0]
        top_out = outflow_sectors[0]
        summary += f"资金呈现明显的\"从{top_out['name']}向{top_in['name']}切换\"特征。"

    return summary


def _extract_policy_changes() -> dict[str, Any]:
    """从新闻中提取政策变动."""
    result = {
        "has_policy": False,
        "summary": "无",
        "policies": [],
    }

    try:
        news_analysis = crawl_and_analyze()
    except Exception as e:
        print(f"[MarketReport] Policy extraction crawl error: {e}")
        return result

    policy_keywords = [
        "央行", "证监会", "金融监管总局", "国务院", "发改委", "财政部", "商务部",
        "降准", "降息", "LPR", "货币政策", "财政政策", "监管", "新规", "政策",
        "指导意见", "通知", "方案", "举措",
    ]

    policy_news = []
    for title in news_analysis.get("raw_titles", []):
        if any(kw in title for kw in policy_keywords):
            policy_news.append(title)

    if not policy_news:
        return result

    result["has_policy"] = True
    result["summary"] = "；".join(policy_news[:3])
    result["policies"] = [
        {
            "publish_time": "今日",
            "publisher": "相关部门",
            "title": title,
            "core_items": [],
            "market_reaction": "",
            "significance": "",
        }
        for title in policy_news[:3]
    ]

    return result


def _analyze_risk_signals(signal: dict[str, Any]) -> dict[str, Any]:
    """分析市场特征与风险信号."""
    internal = signal.get("internal", {})
    macro = signal.get("macro", {})
    geo = signal.get("geo", {})

    alerts = []

    # 波动率判断
    volatility = internal.get("volatility_regime", "正常")
    sentiment = internal.get("sentiment", "中性")

    # 指数失真风险
    alerts.append("指数由权重股主导，需关注个股中位数表现以判断真实赚钱效应。")

    # 资金面风险
    if sentiment in ["贪婪"]:
        alerts.append("市场情绪偏热，短期存在过热回调风险。")
    elif sentiment in ["恐惧"]:
        alerts.append("市场情绪偏冷，需警惕恐慌性抛售。")

    # 地缘风险
    geo_risk = geo.get("overall_risk", 0)
    if geo_risk > 60:
        alerts.append("地缘政治风险较高，避险情绪可能升温。")

    # 风格切换
    alerts.append("关注大盘蓝筹与科技成长股之间的资金轮动。")

    return {
        "volatility_regime": volatility,
        "sentiment": sentiment,
        "alerts": alerts,
    }


def _fetch_northbound_fund() -> dict[str, Any]:
    """获取北向资金数据与外部环境."""
    result = {
        "net_inflow": 0.0,
        "cumulative_inflow": 0.0,
        "leading_sectors": [],
        "external_env": "",
        "inference": "",
    }

    try:
        summary_df = ak.stock_hsgt_fund_flow_summary_em()
        if summary_df is not None and not summary_df.empty:
            result["net_inflow"] = _safe_float(summary_df.iloc[0].get("当日成交净买额", 0), 0)
    except Exception as e:
        print(f"[MarketReport] Northbound summary fetch error: {e}")

    try:
        hist_df = ak.stock_hsgt_hist_em(symbol="北向资金")
        if hist_df is not None and not hist_df.empty:
            result["cumulative_inflow"] = _safe_float(hist_df.iloc[0].get("历史累计净买额", 0), 0)
    except Exception as e:
        print(f"[MarketReport] Northbound hist fetch error: {e}")

    # 推断北向偏好板块
    sector_perf = _fetch_sector_performance_with_intraday()
    financial_sectors = ["银行", "证券", "保险", "多元金融"]
    leading = []
    for s in sector_perf.get("sectors", []):
        if any(fs in s["name"] for fs in financial_sectors) and s["fund_flow"] > 0:
            leading.append(s["name"])
    result["leading_sectors"] = leading[:5]

    # 外部环境概述
    result["external_env"] = "中美科技博弈持续，美联储利率政策、全球地缘冲突仍是主要外部变量。"

    # 净流入推断说明
    if result["net_inflow"] > 0:
        result["inference"] = f"今日北向资金净流入约{result['net_inflow']:.2f}亿元，显示外资对A股态度偏积极。"
    elif result["net_inflow"] < 0:
        result["inference"] = f"今日北向资金净流出约{abs(result['net_inflow']):.2f}亿元，外资短期偏谨慎。"
    else:
        result["inference"] = "今日北向资金精确数据未获取，但从金融板块及大盘蓝筹走势推断，外资流向相对平稳。"

    return result


def _generate_daily_outlook(signal: dict[str, Any]) -> dict[str, Any]:
    """生成后市展望."""
    composite = signal.get("composite_score", 0)
    mood = signal.get("market_mood", "中性")

    if composite > 20:
        short_term = "市场情绪偏暖，短期可继续关注金融、周期等顺周期板块的持续性，同时留意科技成长股的补涨机会。"
    elif composite > -10:
        short_term = "市场维持震荡格局，建议控制仓位，关注结构性机会，避免追高。"
    else:
        short_term = "市场情绪偏冷，短期以防御为主，关注高股息、低估值板块的避险价值。"

    medium_term = f"中期来看，当前处于{signal.get('market_cycle', '复苏')}阶段，结合{mood}情绪，建议根据市场周期调整股债配置比例。"

    risks = [
        "创业板指结构性风险：指数点位与个股中位数涨幅背离，存在权重股补跌风险。",
        "量能分歧：若指数上涨但主力资金净流出，需警惕诱多可能。",
        "政策脉冲风险：突发政策利好可能带来短期情绪波动，需关注后续落地情况。",
    ]

    return {
        "short_term": short_term,
        "medium_term": medium_term,
        "risks": risks,
    }


# ── 分页2：资产组合今日表现 ──

def _generate_page2_portfolio_performance(user_id: int, portfolio_id: int | None) -> dict[str, Any]:
    """生成分页2：资产组合今日表现."""
    db = SessionLocal()
    try:
        from app.models.portfolio import Portfolio
        from app.models.portfolio_holding import PortfolioHolding

        if portfolio_id:
            portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
        else:
            portfolio = db.query(Portfolio).filter(
                Portfolio.user_id == user_id,
                Portfolio.is_active == True
            ).order_by(Portfolio.updated_at.desc()).first()

        if not portfolio:
            return {
                "summary": "暂无组合数据",
                "portfolio_return": 0,
                "portfolio_return_pct": "0.00%",
                "benchmark_return": 0,
                "excess_return": 0,
                "asset_performances": [],
                "best_contributor": None,
                "worst_contributor": None,
            }

        holdings = db.query(PortfolioHolding).filter(
            PortfolioHolding.portfolio_id == portfolio.id
        ).all()

        # 如果 portfolio_holdings 表中没有数据，尝试从 config_json.bindings 解析
        if not holdings and portfolio.config_json:
            try:
                cfg = portfolio.config_json if isinstance(portfolio.config_json, dict) else json.loads(portfolio.config_json)
                bindings = cfg.get("bindings", []) or cfg.get("portfolio", {}).get("bindings", [])
                for b in bindings:
                    holdings.append({
                        "symbol": b.get("symbol", ""),
                        "name": b.get("name", b.get("symbol", "")),
                        "asset_class": b.get("asset_class", "ETF"),
                        "weight": b.get("weight", 0),
                    })
            except Exception as e:
                print(f"[MarketReport] Parse portfolio config_json error: {e}")

        asset_performances = []
        for h in holdings:
            symbol = h.symbol if hasattr(h, "symbol") else h.get("symbol", "")
            name = (h.name if hasattr(h, "name") else h.get("name", "")) or symbol
            asset_class = h.asset_class if hasattr(h, "asset_class") else h.get("asset_class", "ETF")
            weight = h.weight if hasattr(h, "weight") else h.get("weight", 0)
            perf = _fetch_single_asset_daily_performance(
                symbol, name, asset_class or "ETF", weight or 0
            )
            asset_performances.append(perf)

        portfolio_return = sum(p["contribution"] for p in asset_performances)
        benchmark_return = _fetch_benchmark_daily_return()

        asset_performances.sort(key=lambda x: x["contribution"], reverse=True)
        best = asset_performances[0] if asset_performances else None
        worst = asset_performances[-1] if asset_performances else None

        return {
            "portfolio_return": portfolio_return,
            "portfolio_return_pct": f"{portfolio_return:+.2%}",
            "benchmark_return": benchmark_return,
            "excess_return": portfolio_return - benchmark_return,
            "asset_performances": asset_performances,
            "best_contributor": best,
            "worst_contributor": worst,
            "summary": _generate_portfolio_summary(portfolio_return, best, worst),
        }
    finally:
        db.close()


def _fetch_single_asset_daily_performance(symbol: str, name: str, asset_class: str, weight: float) -> dict[str, Any]:
    """获取单个资产今日表现."""
    today = datetime.date.today()
    today_str = today.strftime("%Y%m%d")

    try:
        df = data_fetcher.fetch_stock_data(symbol, today_str, today_str)
        if df is not None and not df.empty:
            row = df.iloc[-1]
            close = _safe_float(row.get("close"), 0)
            open_price = _safe_float(row.get("open"), close)
            change_pct = (close - open_price) / open_price if open_price else 0

            return {
                "symbol": symbol,
                "name": name,
                "asset_class": asset_class,
                "weight": weight,
                "price": close,
                "change_pct": change_pct,
                "daily_return": change_pct,
                "contribution": change_pct * weight,
            }
    except Exception as e:
        print(f"[MarketReport] Asset performance fetch error for {symbol}: {e}")

    return {
        "symbol": symbol,
        "name": name,
        "asset_class": asset_class,
        "weight": weight,
        "price": 0,
        "change_pct": 0,
        "daily_return": 0,
        "contribution": 0,
    }


def _fetch_benchmark_daily_return() -> float:
    """获取沪深300今日涨跌幅作为基准."""
    try:
        spot_df = ak.stock_zh_index_spot_em()
        if spot_df is not None and not spot_df.empty:
            row = spot_df[spot_df.get("代码", "") == "000300"]
            if not row.empty:
                return _safe_float(row.iloc[0].get("涨跌幅"), 0) / 100
    except Exception as e:
        print(f"[MarketReport] Benchmark fetch error: {e}")
    return 0


def _generate_portfolio_summary(portfolio_return: float, best: dict | None, worst: dict | None) -> str:
    """生成组合表现总结."""
    if portfolio_return > 0.01:
        summary = "今日组合实现正收益，"
    elif portfolio_return > -0.01:
        summary = "今日组合基本持平，"
    else:
        summary = "今日组合小幅回撤，"

    if best:
        summary += f"{best['name']}贡献最大（{best['daily_return']:+.2%}）；"
    if worst:
        summary += f"{worst['name']}拖累最大（{worst['daily_return']:+.2%}）。"

    return summary


# ── 分页3：本周市场情况 ──

def _generate_page3_weekly_market(week_start: datetime.date, week_end: datetime.date) -> dict[str, Any]:
    """生成分页3：本周市场情况（更宏观）."""
    signal = collect_market_signal()
    start_str = week_start.strftime("%Y%m%d")
    end_str = week_end.strftime("%Y%m%d")

    weekly_indices = []
    for symbol, info in MAIN_INDICES.items():
        try:
            df = data_fetcher.fetch_stock_data(symbol, start_str, end_str)
            if df is not None and len(df) >= 1:
                week_open = _safe_float(df.iloc[0].get("open"), 0)
                week_close = _safe_float(df.iloc[-1].get("close"), 0)
                if week_open > 0:
                    week_change = (week_close - week_open) / week_open
                    weekly_indices.append({
                        "name": info["name"],
                        "symbol": symbol,
                        "week_change_pct": week_change,
                        "week_high": _safe_float(df["high"].max(), 0),
                        "week_low": _safe_float(df["low"].min(), 0),
                        "total_volume": _safe_float(df["volume"].sum(), 0),
                    })
        except Exception as e:
            print(f"[MarketReport] Weekly index fetch error for {symbol}: {e}")

    weekly_sectors = []
    try:
        fund_df = ak.stock_fund_flow_industry(symbol="5日排行")
        if fund_df is not None and not fund_df.empty:
            for _, row in fund_df.head(15).iterrows():
                weekly_sectors.append({
                    "name": str(row.get("名称", "")),
                    "week_change_pct": _safe_float(row.get("涨跌幅"), 0) / 100,
                    "week_fund_flow": _safe_float(row.get("净额", 0), 0) / 10000,  # 亿元
                })
    except Exception as e:
        print(f"[MarketReport] Weekly sector fetch error: {e}")

    weekly_northbound = {"total_net_inflow": 0.0}
    try:
        hist_df = ak.stock_hsgt_hist_em(symbol="北向资金")
        if hist_df is not None and not hist_df.empty and "日期" in hist_df.columns:
            hist_df["日期"] = pd.to_datetime(hist_df["日期"])
            mask = (hist_df["日期"] >= pd.Timestamp(week_start)) & (hist_df["日期"] <= pd.Timestamp(week_end))
            week_data = hist_df[mask]
            if not week_data.empty:
                weekly_northbound["total_net_inflow"] = _safe_float(week_data["当日成交净买额"].sum(), 0)
    except Exception as e:
        print(f"[MarketReport] Weekly northbound fetch error: {e}")

    market_summary = _generate_weekly_market_summary(weekly_indices, weekly_sectors)

    return {
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
        "market_summary": market_summary,
        "index_performance": {"indices": weekly_indices},
        "sector_performance": {"sectors": weekly_sectors},
        "policy_changes": _extract_policy_changes(),
        "risk_signals": _analyze_risk_signals(signal),
        "northbound_fund": weekly_northbound,
        "outlook": _generate_daily_outlook(signal),
    }


def _generate_weekly_market_summary(indices: list[dict], sectors: list[dict]) -> str:
    """生成本周市场宏观综述."""
    week_start_str = datetime.date.today().strftime("%Y年%m月%d日")

    if not indices:
        return f"{week_start_str}所在周，指数数据获取失败，暂无法生成本周综述。"

    avg_change = sum(i.get("week_change_pct", 0) for i in indices) / len(indices)

    if avg_change > 0.02:
        trend = "整体上行"
    elif avg_change > 0.005:
        trend = "小幅上涨"
    elif avg_change > -0.005:
        trend = "横盘震荡"
    elif avg_change > -0.02:
        trend = "小幅回调"
    else:
        trend = "明显调整"

    summary = f"本周（截至{week_start_str}）A股市场{trend}。"

    best = max(indices, key=lambda x: x["week_change_pct"])
    worst = min(indices, key=lambda x: x["week_change_pct"])
    summary += f"{best['name']}本周表现最强（{best['week_change_pct']:+.2%}），{worst['name']}表现最弱（{worst['week_change_pct']:+.2%}）。"

    if sectors:
        inflow = sorted([s for s in sectors if s.get("week_fund_flow", 0) > 0], key=lambda x: x["week_fund_flow"], reverse=True)
        if inflow:
            summary += f"资金周度主要流向{inflow[0]['name']}等板块。"

    summary += "宏观层面需关注国内政策落地节奏、海外流动性变化及地缘政治风险。"
    return summary


# ── 工具函数 ──

def _safe_float(value: Any, default: float = 0.0) -> float:
    """安全转换为 float."""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default
