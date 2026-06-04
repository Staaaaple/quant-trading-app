from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.market_signal import MarketSignal
from app.schemas.market_signal import MarketSignalRead, MarketSignalLatest
from app.services import market_signal_service

router = APIRouter()


@router.post("/collect", response_model=MarketSignalRead)
def collect_and_save(db: Session = Depends(get_db)):
    """手动触发市场信号采集（通常由定时任务自动执行）."""
    signal_data = market_signal_service.collect_market_signal()
    ms = market_signal_service.save_market_signal(db, signal_data)
    return ms


@router.get("/latest", response_model=MarketSignalLatest)
def get_latest(db: Session = Depends(get_db)):
    """获取最新市场信号（结构化展示）."""
    ms = market_signal_service.get_latest_signal(db)
    if not ms:
        raise HTTPException(status_code=404, detail="No market signal found")

    from app.schemas.market_signal import MacroLayer, GeoLayer, IndustryLayer, SocialLayer, InternalLayer

    # 构建 cycle_analysis（从数据库读取）
    cycle_analysis = None
    if ms.cycle_analysis:
        cycle_analysis = ms.cycle_analysis

    return MarketSignalLatest(
        date=ms.date,
        composite_score=ms.composite_score or 0,
        market_mood=ms.market_mood or "中性",
        market_cycle=ms.market_cycle or "复苏",
        cycle_analysis=cycle_analysis,
        macro=MacroLayer(
            cycle_phase=ms.macro_cycle_phase,
            gdp_trend=ms.macro_gdp_trend,
            inflation_level=ms.macro_inflation_level,
            liquidity=ms.macro_liquidity,
            interest_rate=ms.macro_interest_rate,
            score=ms.macro_score,
        ),
        geo=GeoLayer(
            overall_risk=ms.geo_overall_risk,
            risk_level=ms.geo_risk_level,
            safe_haven_demand=ms.geo_safe_haven_demand,
            score=ms.geo_score,
        ),
        industry=IndustryLayer(
            heatmap=ms.industry_heatmap,
            recommended=ms.industry_recommended,
            avoid=ms.industry_avoid,
            score=ms.industry_score,
        ),
        social=SocialLayer(
            major_themes=ms.social_major_themes,
            theme_strength=ms.social_theme_strength,
            consumer_confidence=ms.social_consumer_confidence,
            score=ms.social_score,
        ),
        internal=InternalLayer(
            equity_bond_spread=ms.internal_equity_bond_spread,
            sentiment=ms.internal_sentiment,
            style_rotation=ms.internal_style_rotation,
            volatility_regime=ms.internal_volatility_regime,
            score=ms.internal_score,
        ),
    )


@router.get("/history", response_model=list[MarketSignalRead])
def get_history(days: int = 30, db: Session = Depends(get_db)):
    """获取最近N天的信号历史."""
    return market_signal_service.get_signal_history(db, days)
