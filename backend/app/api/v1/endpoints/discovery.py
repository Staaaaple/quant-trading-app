"""策略发现API端点.

提供策略发现、验证、注册的HTTP接口.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Any

from app.db.session import get_db
from app.services.strategy_discovery_service import (
    discover_and_validate,
    register_strategies_to_db,
    run_discovery_pipeline,
    get_strategy_pool,
    get_strategy_pool_size,
)

router = APIRouter()


@router.post("/run", response_model=dict[str, Any])
def run_discovery(
    background_tasks: BackgroundTasks,
    target_count: int = 35,
    auto_register: bool = True,
    db: Session = Depends(get_db),
):
    """运行策略发现流水线.

    - 从策略池加载策略
    - 验证策略质量
    - 注册通过的策略到数据库

    Args:
        target_count: 目标策略数量 (默认35)
        auto_register: 是否自动注册到数据库
    """
    try:
        result = run_discovery_pipeline(
            db=db,
            target_count=target_count,
            auto_register=auto_register,
            verbose=True,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Discovery failed: {e}")


@router.post("/validate", response_model=dict[str, Any])
def validate_strategies(
    target_count: int = 35,
):
    """仅验证策略，不注册到数据库.

    返回通过验证的策略列表和统计信息.
    """
    try:
        passed = discover_and_validate(target_count=target_count, verbose=False)
        return {
            "validated": len(passed),
            "target": target_count,
            "strategies": [
                {
                    "id": s["id"],
                    "name": s["name"],
                    "family": s.get("family", "Unknown"),
                    "paper": s.get("paper", "Unknown"),
                    "validation": s.get("validation", {}),
                }
                for s in passed
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {e}")


@router.get("/pool", response_model=dict[str, Any])
def get_pool_info():
    """获取策略池信息.

    返回当前策略池的大小和策略列表.
    """
    pool = get_strategy_pool()
    return {
        "total": len(pool),
        "strategies": [
            {
                "id": s["id"],
                "name": s["name"],
                "family": s.get("family", "Unknown"),
                "paper": s.get("paper", "Unknown"),
                "params": s["params"],
            }
            for s in pool
        ],
    }


@router.post("/register", response_model=dict[str, Any])
def register_validated(
    strategy_ids: list[str],
    db: Session = Depends(get_db),
):
    """将已验证的策略注册到数据库.

    Args:
        strategy_ids: 要注册的策略ID列表
    """
    try:
        pool = get_strategy_pool()
        strategies_to_register = [s for s in pool if s["id"] in strategy_ids]

        if not strategies_to_register:
            raise HTTPException(status_code=404, detail="No matching strategies found")

        registered = register_strategies_to_db(db, strategies_to_register)
        return {
            "requested": len(strategy_ids),
            "found": len(strategies_to_register),
            "registered": len(registered),
            "ids": registered,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {e}")


@router.get("/status", response_model=dict[str, Any])
def get_discovery_status(
    db: Session = Depends(get_db),
):
    """获取策略发现状态.

    返回策略池大小、已注册策略数量等信息.
    """
    from app.models.strategy_template import StrategyTemplate

    pool_size = get_strategy_pool_size()
    registered_count = db.query(StrategyTemplate).filter(
        StrategyTemplate.template_id.like("discovered_%")
    ).count()

    return {
        "pool_size": pool_size,
        "registered": registered_count,
        "pending": pool_size - registered_count,
        "status": "ready" if pool_size > 0 else "empty",
    }
