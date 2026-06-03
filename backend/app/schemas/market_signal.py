from pydantic import BaseModel, ConfigDict
from datetime import date, datetime
from typing import Any


class MacroLayer(BaseModel):
    cycle_phase: str | None = None
    gdp_trend: str | None = None
    inflation_level: str | None = None
    liquidity: str | None = None
    interest_rate: str | None = None
    score: float | None = None


class GeoLayer(BaseModel):
    overall_risk: float | None = None
    risk_level: str | None = None
    safe_haven_demand: str | None = None
    score: float | None = None


class IndustryLayer(BaseModel):
    heatmap: dict[str, float] | None = None
    recommended: list[str] | None = None
    avoid: list[str] | None = None
    score: float | None = None


class SocialLayer(BaseModel):
    major_themes: list[str] | None = None
    theme_strength: dict[str, float] | None = None
    consumer_confidence: str | None = None
    score: float | None = None


class InternalLayer(BaseModel):
    equity_bond_spread: float | None = None
    sentiment: str | None = None
    style_rotation: str | None = None
    volatility_regime: str | None = None
    score: float | None = None


class MarketSignalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    date: date
    macro_cycle_phase: str | None
    macro_score: float | None
    geo_overall_risk: float | None
    geo_score: float | None
    industry_heatmap: dict[str, Any] | None
    industry_score: float | None
    social_major_themes: list[str] | None
    social_score: float | None
    internal_sentiment: str | None
    internal_score: float | None
    composite_score: float | None
    market_mood: str | None
    market_cycle: str | None
    created_at: datetime


class MarketSignalLatest(BaseModel):
    date: date
    composite_score: float
    market_mood: str
    market_cycle: str
    macro: MacroLayer
    geo: GeoLayer
    industry: IndustryLayer
    social: SocialLayer
    internal: InternalLayer
