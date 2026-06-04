"""五层市场信号采集与计算服务.

Layer 1: 宏观基本面 (30%) — GDP/CPI/PMI/M2/利率/周期判断
Layer 2: 地缘政治 (20%) — 新闻爬虫 + 关键词分析
Layer 3: 行业景气度 (20%) — 新闻提及频率
Layer 4: 社会实事 (15%) — 主题趋势
Layer 5: 资产内部+股市走势 (15%) — 股债利差/成交量/北向资金

权重: 宏观30% + 地缘20% + 行业20% + 社会15% + 内部15% = 100%
"""

import datetime
from typing import Any

import akshare as ak
import pandas as pd
from sqlalchemy.orm import Session

from app.models.market_signal import MarketSignal
from app.services import news_crawler
from app.services.cycle_models import (
    merrill_lunch_clock,
    monetary_credit_cycle,
    inventory_cycle,
    fuse_cycle_phases,
)


# ── 权重配置 ──
LAYER_WEIGHTS = {
    "macro": 0.30,
    "geo": 0.20,
    "industry": 0.20,
    "social": 0.15,
    "internal": 0.15,
}


def _fetch_macro_data() -> dict[str, Any]:
    """获取宏观数据并计算评分（多模型融合版）."""
    result = {
        "gdp_trend": "企稳",
        "inflation_level": "温和",
        "liquidity": "中性",
        "interest_rate": "持平",
        "score": 50.0,
        "cycle_phase": "复苏",
    }

    try:
        # GDP
        gdp_df = ak.macro_china_gdp()
        if not gdp_df.empty:
            latest_gdp_yoy = float(gdp_df.iloc[0]["国内生产总值-同比增长"])
            prev_gdp_yoy = float(gdp_df.iloc[1]["国内生产总值-同比增长"]) if len(gdp_df) > 1 else latest_gdp_yoy
            if latest_gdp_yoy > prev_gdp_yoy + 0.5:
                result["gdp_trend"] = "加速"
            elif latest_gdp_yoy < prev_gdp_yoy - 0.5:
                result["gdp_trend"] = "放缓"
            else:
                result["gdp_trend"] = "企稳"
            result["gdp_yoy"] = round(latest_gdp_yoy, 2)
    except Exception as e:
        print(f"GDP fetch error: {e}")

    try:
        # CPI — 用同比增长率，不是指数值
        cpi_df = ak.macro_china_cpi()
        if not cpi_df.empty:
            # 优先取"全国-同比增长"，回退到第3列
            latest_cpi = float(cpi_df.iloc[0].get("全国-同比增长", cpi_df.iloc[0].get(cpi_df.columns[2], 0)))
            result["cpi_yoy"] = round(latest_cpi, 2)
            if latest_cpi < 0.5:
                result["inflation_level"] = "低"
            elif latest_cpi < 2.0:
                result["inflation_level"] = "温和"
            else:
                result["inflation_level"] = "高"
    except Exception as e:
        print(f"CPI fetch error: {e}")

    try:
        # PMI
        pmi_df = ak.macro_china_pmi()
        if not pmi_df.empty:
            latest_pmi = float(pmi_df.iloc[0].get("制造业-指数", pmi_df.iloc[0].get(pmi_df.columns[1], 50)))
            result["pmi"] = round(latest_pmi, 1)
    except Exception as e:
        print(f"PMI fetch error: {e}")

    try:
        # M2
        m2_df = ak.macro_china_money_supply()
        if not m2_df.empty:
            latest_m2_yoy = float(m2_df.iloc[0]["货币和准货币(M2)-同比增长"])
            result["m2_yoy"] = round(latest_m2_yoy, 2)
            if latest_m2_yoy > 12:
                result["liquidity"] = "宽松"
            elif latest_m2_yoy < 8:
                result["liquidity"] = "收紧"
            else:
                result["liquidity"] = "中性"
    except Exception as e:
        print(f"M2 fetch error: {e}")

    try:
        # LPR利率
        lpr_df = ak.macro_china_lpr()
        if not lpr_df.empty:
            latest_lpr = float(lpr_df.iloc[0].get("LPR_1Y", lpr_df.iloc[0].get(lpr_df.columns[1], 3.5)))
            prev_lpr = float(lpr_df.iloc[1].get("LPR_1Y", lpr_df.iloc[1].get(lpr_df.columns[1], 3.5)))
            result["lpr_1y"] = round(latest_lpr, 2)
            result["lpr_prev"] = round(prev_lpr, 2)
            if latest_lpr < prev_lpr - 0.05:
                result["interest_rate"] = "下行"
            elif latest_lpr > prev_lpr + 0.05:
                result["interest_rate"] = "上行"
            else:
                result["interest_rate"] = "持平"
    except Exception as e:
        print(f"LPR fetch error: {e}")

    try:
        # 社融增速 — 数据为绝对增量（亿元），需自行计算同比增速
        sf_df = ak.macro_china_shrzgm()
        if not sf_df.empty and len(sf_df) >= 13:
            # 取最近一个月和去年同期
            latest_sf = float(sf_df.iloc[0].get("社会融资规模增量", sf_df.iloc[0].get(sf_df.columns[1], 0)))
            yoy_sf = float(sf_df.iloc[12].get("社会融资规模增量", sf_df.iloc[12].get(sf_df.columns[1], 0)))
            if yoy_sf != 0:
                sf_yoy = (latest_sf / yoy_sf - 1) * 100
                result["social_financing_yoy"] = round(sf_yoy, 2)
    except Exception as e:
        print(f"Social financing fetch error: {e}")

    try:
        # 失业率
        unemployment_df = ak.macro_china_urban_unemployment()
        if not unemployment_df.empty:
            latest_unemployment = float(unemployment_df.iloc[0].get("全国城镇调查失业率", unemployment_df.iloc[0].get(unemployment_df.columns[1], 5.0)))
            result["unemployment_rate"] = round(latest_unemployment, 2)
    except Exception as e:
        print(f"Unemployment fetch error: {e}")

    try:
        # 工业企业利润
        profit_df = ak.macro_china_industrial_profit()
        if not profit_df.empty:
            latest_profit_yoy = float(profit_df.iloc[0].get("规模以上工业企业利润总额-同比增长", profit_df.iloc[0].get(profit_df.columns[1], 0)))
            result["industrial_profit_yoy"] = round(latest_profit_yoy, 2)
    except Exception as e:
        print(f"Industrial profit fetch error: {e}")

    try:
        # PPI（工业生产者出厂价格指数）— 用当月同比增长
        ppi_df = ak.macro_china_ppi()
        if not ppi_df.empty:
            latest_ppi = float(ppi_df.iloc[0].get("当月同比增长", ppi_df.iloc[0].get(ppi_df.columns[2], 0)))
            result["ppi_yoy"] = round(latest_ppi, 2)
    except Exception as e:
        print(f"PPI fetch error: {e}")

    try:
        # 房地产投资增速 — 返回的是指数值，取涨跌幅列
        re_df = ak.macro_china_real_estate()
        if not re_df.empty:
            # 取最新有数据的行（倒序找第一个非NaN涨跌幅）
            for i in range(min(12, len(re_df))):
                change = re_df.iloc[i].get("涨跌幅")
                if pd.notna(change):
                    result["real_estate_investment_yoy"] = round(float(change), 2)
                    break
    except Exception as e:
        print(f"Real estate investment fetch error: {e}")

    # 计算宏观评分 (0-100) 和周期判断（多模型融合）
    result["score"], result["cycle_phase"], result["cycle_analysis"] = _calculate_macro_score(result)
    return result


def _calculate_macro_score(data: dict[str, Any]) -> tuple[float, str, dict[str, Any]]:
    """根据宏观数据计算评分和周期阶段（多模型融合版）.

    融合三大模型（中国特供版）：
      1. 美林时钟修正版（GDP + CPI + PPI）
      2. 货币信用周期（M2 + 社融 + 利率 + 房地产）
      3. 库存周期（PMI + 工业企业利润 + PPI）
    """
    gdp_yoy = data.get("gdp_yoy", 5.0)
    cpi_yoy = data.get("cpi_yoy", 2.0)
    ppi_yoy = data.get("ppi_yoy")
    pmi = data.get("pmi", 50.0)
    m2_yoy = data.get("m2_yoy", 10.0)
    lpr_1y = data.get("lpr_1y")
    lpr_prev = data.get("lpr_prev")
    social_financing_yoy = data.get("social_financing_yoy")
    industrial_profit_yoy = data.get("industrial_profit_yoy")
    real_estate_investment_yoy = data.get("real_estate_investment_yoy")

    # 运行三大模型（新版）
    merrill = merrill_lunch_clock(gdp_yoy, cpi_yoy, ppi_yoy)
    monetary = monetary_credit_cycle(m2_yoy, social_financing_yoy, lpr_1y, lpr_prev, real_estate_investment_yoy)
    inventory = inventory_cycle(pmi, industrial_profit_yoy, ppi_yoy)

    # 融合
    fused = fuse_cycle_phases([merrill, monetary, inventory])

    # 综合评分（基于融合结果 + 传统因子）
    score = 50.0

    # GDP 贡献 -10 ~ +20
    if gdp_yoy > 6:
        score += 15
    elif gdp_yoy > 5:
        score += 10
    elif gdp_yoy > 4:
        score += 5
    elif gdp_yoy < 3:
        score -= 10

    # CPI 贡献 -10 ~ +10
    if 1.0 <= cpi_yoy <= 3.0:
        score += 10
    elif cpi_yoy > 4.0:
        score -= 10
    elif cpi_yoy < 0.5:
        score -= 5

    # PMI 贡献 -10 ~ +15
    if pmi > 52:
        score += 15
    elif pmi > 50:
        score += 5
    elif pmi > 48:
        score -= 5
    else:
        score -= 10

    # M2 贡献 -5 ~ +5
    if 9 <= m2_yoy <= 12:
        score += 5
    elif m2_yoy < 7:
        score -= 5

    # 融合结果微调（置信度高时加强信号）
    confidence = fused.get("confidence", 50)
    if confidence > 70:
        if fused["final_phase"] in ["复苏", "复苏早期", "主动补库", "宽货币宽信用"]:
            score += 5
        elif fused["final_phase"] in ["滞胀", "衰退", "主动去库", "紧货币紧信用"]:
            score -= 5

    score = max(0, min(100, round(score, 1)))

    return score, fused["final_phase"], fused


def _fetch_internal_data() -> dict[str, Any]:
    """获取资产内部信号（股债利差、成交量、北向资金）."""
    result = {
        "equity_bond_spread": 3.0,
        "sentiment": "中性",
        "style_rotation": "大盘成长",
        "volatility_regime": "正常",
        "score": 50.0,
    }

    try:
        # 沪深300指数获取最新数据
        index_df = ak.index_zh_a_hist(symbol="000300", period="daily", start_date="20260101", end_date="20260630")
        if not index_df.empty:
            latest_close = float(index_df.iloc[-1]["收盘"])
            # 简化：用近20日涨跌幅判断情绪
            if len(index_df) >= 20:
                ret_20d = (latest_close / float(index_df.iloc[-20]["收盘"]) - 1) * 100
                result["ret_20d"] = round(ret_20d, 2)
                if ret_20d > 5:
                    result["sentiment"] = "贪婪"
                elif ret_20d < -5:
                    result["sentiment"] = "恐惧"
                else:
                    result["sentiment"] = "中性"

                # 成交量趋势
                vol_recent = float(index_df.iloc[-5:]["成交量"].mean())
                vol_prev = float(index_df.iloc[-10:-5]["成交量"].mean())
                if vol_recent > vol_prev * 1.2:
                    result["volume_trend"] = "放量"
                elif vol_recent < vol_prev * 0.8:
                    result["volume_trend"] = "缩量"
                else:
                    result["volume_trend"] = "持平"
    except Exception as e:
        print(f"Internal data fetch error: {e}")

    try:
        # 股债利差（简化：沪深300盈利收益率 - 10年期国债收益率）
        bond_df = ak.bond_zh_us_rate()
        if not bond_df.empty:
            china_10y = float(bond_df.iloc[-1]["中国国债收益率10年"])
            result["china_10y_yield"] = round(china_10y, 2)
            # 假设沪深300 PE约12，盈利收益率约8.3%
            equity_yield = 8.3
            spread = equity_yield - china_10y
            result["equity_bond_spread"] = round(spread, 2)
    except Exception as e:
        print(f"Bond yield fetch error: {e}")

    # 计算内部评分
    score = 50.0
    if result.get("ret_20d", 0) > 3:
        score += 15
    elif result.get("ret_20d", 0) < -3:
        score -= 15

    spread = result.get("equity_bond_spread", 3.0)
    if spread > 4:
        score += 10  # 股债利差高，股票性价比高
    elif spread < 2:
        score -= 10

    result["score"] = max(0, min(100, round(score, 1)))
    return result


def collect_market_signal() -> dict[str, Any]:
    """采集完整的五层市场信号."""
    # Layer 1: 宏观
    macro = _fetch_macro_data()

    # Layer 2-4: 新闻爬虫（地缘+行业+社会）
    news_analysis = news_crawler.crawl_and_analyze()
    geo = news_analysis["geopolitical"]
    industry = news_analysis["industry"]
    social = news_analysis["social"]

    # Layer 5: 资产内部
    internal = _fetch_internal_data()

    # 综合评分
    composite = (
        macro["score"] * LAYER_WEIGHTS["macro"] +
        (100 - geo["overall_risk"]) * LAYER_WEIGHTS["geo"] +  # 风险越低分越高
        industry["score"] * LAYER_WEIGHTS["industry"] +
        social["score"] * LAYER_WEIGHTS["social"] +
        internal["score"] * LAYER_WEIGHTS["internal"]
    )
    composite = round(composite - 50, 1)  # 映射到 -50 ~ +50

    if composite > 20:
        mood = "乐观"
    elif composite > 5:
        mood = "中性偏乐观"
    elif composite > -5:
        mood = "中性"
    elif composite > -20:
        mood = "中性偏悲观"
    else:
        mood = "悲观"

    return {
        "macro": macro,
        "geo": geo,
        "industry": industry,
        "social": social,
        "internal": internal,
        "composite_score": composite,
        "market_mood": mood,
        "market_cycle": macro["cycle_phase"],
        "cycle_analysis": macro.get("cycle_analysis"),
        "raw_data": {
            "news_count": news_analysis["news_count"],
            "news_titles": news_analysis["raw_titles"],
        },
    }


def save_market_signal(db: Session, signal_data: dict[str, Any]) -> MarketSignal:
    """保存市场信号到数据库（覆盖当天已有记录）."""
    from sqlalchemy import delete

    today = datetime.date.today()
    # 覆盖模式：先删除当天已有记录
    db.execute(delete(MarketSignal).where(MarketSignal.date == today))
    db.commit()

    macro = signal_data["macro"]
    geo = signal_data["geo"]
    industry = signal_data["industry"]
    social = signal_data["social"]
    internal = signal_data["internal"]

    ms = MarketSignal(
        date=today,
        macro_cycle_phase=macro["cycle_phase"],
        macro_gdp_trend=macro["gdp_trend"],
        macro_inflation_level=macro["inflation_level"],
        macro_liquidity=macro["liquidity"],
        macro_interest_rate=macro["interest_rate"],
        macro_score=macro["score"],
        geo_overall_risk=geo["overall_risk"],
        geo_risk_level=geo["risk_level"],
        geo_safe_haven_demand=geo["safe_haven_demand"],
        geo_score=100 - geo["overall_risk"],
        industry_heatmap=industry["heatmap"],
        industry_recommended=industry["recommended"],
        industry_avoid=industry["avoid"],
        industry_score=industry["score"],
        social_major_themes=social["major_themes"],
        social_theme_strength=social["theme_strength"],
        social_consumer_confidence=social["consumer_confidence"],
        social_score=social["score"],
        internal_equity_bond_spread=internal.get("equity_bond_spread"),
        internal_sentiment=internal["sentiment"],
        internal_style_rotation=internal.get("style_rotation"),
        internal_volatility_regime=internal.get("volatility_regime"),
        internal_score=internal["score"],
        composite_score=signal_data["composite_score"],
        cycle_analysis=signal_data.get("cycle_analysis"),
        market_mood=signal_data["market_mood"],
        market_cycle=signal_data["market_cycle"],
        raw_data=signal_data["raw_data"],
    )
    db.add(ms)
    db.commit()
    db.refresh(ms)
    return ms


def get_latest_signal(db: Session) -> MarketSignal | None:
    """获取最新市场信号."""
    return (
        db.query(MarketSignal)
        .order_by(MarketSignal.date.desc())
        .first()
    )


def get_signal_history(db: Session, days: int = 30) -> list[MarketSignal]:
    """获取最近N天的信号历史."""
    from datetime import timedelta
    cutoff = datetime.date.today() - timedelta(days=days)
    return (
        db.query(MarketSignal)
        .filter(MarketSignal.date >= cutoff)
        .order_by(MarketSignal.date.desc())
        .all()
    )
