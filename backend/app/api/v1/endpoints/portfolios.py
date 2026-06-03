"""Portfolio API端点.

提供组合设计、查询、应用等接口.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Any

from app.db.session import get_db
from app.services.hybrid_portfolio_designer import design_portfolio, validate_portfolio, get_portfolio_summary

router = APIRouter()


@router.post("/design", response_model=dict[str, Any])
def create_portfolio_design(
    payload: dict[str, Any],
    db: Session = Depends(get_db),
):
    """设计新的投资组合.

    Payload:
    {
        "profile_vector": {...},
        "market_signal": {...},
        "strategy_pool": [...],  // 可选
    }
    """
    try:
        profile_vector = payload.get("profile_vector", {})
        market_signal = payload.get("market_signal", {})
        strategy_pool = payload.get("strategy_pool")

        portfolio = design_portfolio(
            profile_vector=profile_vector,
            market_signal=market_signal,
            strategy_pool=strategy_pool,
        )

        # 验证
        validation = validate_portfolio(portfolio)

        return {
            "success": True,
            "portfolio": portfolio,
            "validation": validation,
            "summary": get_portfolio_summary(portfolio),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Portfolio design failed: {e}")


@router.post("/{portfolio_id}/validate", response_model=dict[str, Any])
def validate_portfolio_endpoint(
    portfolio_id: str,
    payload: dict[str, Any],
):
    """验证组合配置."""
    portfolio = payload.get("portfolio", {})
    result = validate_portfolio(portfolio)
    return {
        "portfolio_id": portfolio_id,
        **result,
    }


@router.get("/{portfolio_id}/summary", response_model=dict[str, Any])
def get_portfolio_summary_endpoint(
    portfolio_id: str,
    payload: dict[str, Any],
):
    """获取组合摘要."""
    portfolio = payload.get("portfolio", {})
    return get_portfolio_summary(portfolio)
