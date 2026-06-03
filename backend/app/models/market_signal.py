import datetime
from sqlalchemy import Column, Integer, String, JSON, Float, DateTime, Date
from app.db.base import Base


class MarketSignal(Base):
    __tablename__ = "market_signals"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True, default=datetime.date.today)

    # Layer 1: 宏观基本面 (30%)
    macro_cycle_phase = Column(String(16), nullable=True)  # 复苏/过热/滞胀/衰退
    macro_gdp_trend = Column(String(16), nullable=True)    # 加速/放缓/企稳
    macro_inflation_level = Column(String(16), nullable=True)  # 低/温和/高
    macro_liquidity = Column(String(16), nullable=True)   # 宽松/中性/收紧
    macro_interest_rate = Column(String(16), nullable=True)   # 下行/持平/上行
    macro_score = Column(Float, nullable=True)             # 0-100

    # Layer 2: 地缘政治 (20%)
    geo_overall_risk = Column(Float, nullable=True)        # 0-100
    geo_risk_level = Column(String(16), nullable=True)     # low/medium/high
    geo_safe_haven_demand = Column(String(16), nullable=True)
    geo_score = Column(Float, nullable=True)               # 0-100

    # Layer 3: 行业景气度 (20%)
    industry_heatmap = Column(JSON, nullable=True)         # {"科技": 85, ...}
    industry_recommended = Column(JSON, nullable=True)     # ["科技", "新能源"]
    industry_avoid = Column(JSON, nullable=True)           # ["房地产"]
    industry_score = Column(Float, nullable=True)          # 0-100

    # Layer 4: 社会实事 (15%)
    social_major_themes = Column(JSON, nullable=True)      # ["AI革命", ...]
    social_theme_strength = Column(JSON, nullable=True)    # {"AI革命": 90}
    social_consumer_confidence = Column(String(16), nullable=True)
    social_score = Column(Float, nullable=True)            # 0-100

    # Layer 5: 资产内部+股市走势 (15%)
    internal_equity_bond_spread = Column(Float, nullable=True)
    internal_sentiment = Column(String(16), nullable=True)   # 贪婪/中性/恐惧
    internal_style_rotation = Column(String(32), nullable=True)
    internal_volatility_regime = Column(String(16), nullable=True)
    internal_score = Column(Float, nullable=True)            # 0-100

    # 综合评分
    composite_score = Column(Float, nullable=True)           # 加权总分 -100~+100
    market_mood = Column(String(16), nullable=True)          # 中性偏乐观/...
    market_cycle = Column(String(16), nullable=True)         # 复苏期/...

    # 原始数据（用于调试和重新计算）
    raw_data = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
