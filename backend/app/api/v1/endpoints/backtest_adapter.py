"""回测适配器API端点.

支持多资产类型回测、Walk-Forward验证、蒙特卡洛模拟、压力测试.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Any

from app.db.session import get_db
from app.services.backtest_adapter import (
    run_backtest_multi_asset,
    walk_forward_validation,
    monte_carlo_simulation,
    stress_test,
    run_all_stress_tests,
    STRESS_SCENARIOS,
    ASSET_TYPES,
)

router = APIRouter()


@router.post("/run", response_model=dict[str, Any])
def run_backtest(
    payload: dict[str, Any],
    db: Session = Depends(get_db),
):
    """运行多资产回测.

    Payload:
    {
        "symbols": ["000001", "510300"],
        "asset_types": ["stock", "etf"],
        "strategy_code": "...",
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "initial_cash": 100000,
    }
    """
    try:
        result = run_backtest_multi_asset(
            symbols=payload.get("symbols", []),
            asset_types=payload.get("asset_types", []),
            strategy_code=payload.get("strategy_code", ""),
            start_date=payload.get("start_date", "2024-01-01"),
            end_date=payload.get("end_date", "2024-12-31"),
            initial_cash=payload.get("initial_cash", 100000),
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backtest failed: {e}")


@router.post("/walk-forward", response_model=dict[str, Any])
def run_walk_forward(
    payload: dict[str, Any],
):
    """Walk-Forward验证.

    Payload:
    {
        "symbol": "000001",
        "asset_type": "stock",
        "strategy_code": "...",
        "start_date": "2020-01-01",
        "end_date": "2024-12-31",
        "train_ratio": 0.6,
        "val_ratio": 0.2,
    }
    """
    try:
        result = walk_forward_validation(
            symbol=payload.get("symbol", ""),
            asset_type=payload.get("asset_type", "stock"),
            strategy_code=payload.get("strategy_code", ""),
            start_date=payload.get("start_date", "2020-01-01"),
            end_date=payload.get("end_date", "2024-12-31"),
            train_ratio=payload.get("train_ratio", 0.6),
            val_ratio=payload.get("val_ratio", 0.2),
            initial_cash=payload.get("initial_cash", 100000),
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Walk-forward failed: {e}")


@router.post("/monte-carlo", response_model=dict[str, Any])
def run_monte_carlo(
    payload: dict[str, Any],
):
    """蒙特卡洛模拟.

    Payload:
    {
        "returns": [0.01, -0.02, 0.015, ...],
        "n_simulations": 1000,
        "n_days": 252,
        "initial_value": 100000,
    }
    """
    try:
        result = monte_carlo_simulation(
            returns=payload.get("returns", []),
            n_simulations=payload.get("n_simulations", 1000),
            n_days=payload.get("n_days", 252),
            initial_value=payload.get("initial_value", 100000),
            confidence=payload.get("confidence", 0.95),
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Monte Carlo failed: {e}")


@router.get("/stress-scenarios", response_model=dict[str, Any])
def list_stress_scenarios():
    """获取压力测试场景列表."""
    return {
        "scenarios": STRESS_SCENARIOS,
    }


@router.post("/stress-test", response_model=dict[str, Any])
def run_stress_test(
    payload: dict[str, Any],
):
    """压力测试.

    Payload:
    {
        "symbol": "000001",
        "asset_type": "stock",
        "strategy_code": "...",
        "scenario": "2022_bear",
    }
    """
    try:
        result = stress_test(
            symbol=payload.get("symbol", ""),
            asset_type=payload.get("asset_type", "stock"),
            strategy_code=payload.get("strategy_code", ""),
            scenario=payload.get("scenario", "2022_bear"),
            initial_cash=payload.get("initial_cash", 100000),
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stress test failed: {e}")


@router.post("/stress-test-all", response_model=dict[str, Any])
def run_all_stress(
    payload: dict[str, Any],
):
    """运行所有压力测试场景."""
    try:
        result = run_all_stress_tests(
            symbol=payload.get("symbol", ""),
            asset_type=payload.get("asset_type", "stock"),
            strategy_code=payload.get("strategy_code", ""),
            initial_cash=payload.get("initial_cash", 100000),
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stress tests failed: {e}")


@router.get("/asset-types", response_model=dict[str, Any])
def list_asset_types():
    """获取支持的资产类型列表."""
    return {
        "asset_types": ASSET_TYPES,
    }
