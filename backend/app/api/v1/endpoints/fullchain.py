"""全链路服务 API 端点.

Phase D: 画像→组合→教学→建仓→推送→调仓→周报，完整闭环.

提供以下接口:
- POST /onboarding/generate: 生成教学引导内容
- POST /building/plan: 生成建仓计划
- POST /building/batch: 获取单批建仓详情
- POST /push/daily: 生成今日操作推送
- POST /push/lifespan-alert: 生成寿命预警
- POST /rebalance/check: 检查再平衡触发条件
- POST /rebalance/alternatives: 获取替代策略推荐
- POST /weekly-report/generate: 生成周报
- GET /weekly-report/latest: 获取最新周报
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Any

from app.db.session import get_db
from app.api.deps import get_current_user_id
from app.services.onboarding_service import generate_full_onboarding
from app.services.building_service import calculate_building_plan, calculate_single_batch
from app.services.push_service import (
    generate_daily_operation_push,
    generate_lifespan_alert,
    generate_cycle_alert,
    generate_rebalance_alert,
)
from app.services.rebalance_service import (
    check_rebalance_triggers,
    generate_alternative_strategies,
    generate_rebalance_plan,
)
from app.services.weekly_report import generate_weekly_report

router = APIRouter()


# ── 教学引导 ──

@router.post("/onboarding/generate", response_model=dict[str, Any])
def generate_onboarding_content(
    payload: dict[str, Any],
    db: Session = Depends(get_db),
):
    """生成4步教学引导内容.

    Payload:
    {
        "profile": {用户画像},
        "portfolio": {组合配置}
    }
    """
    try:
        profile = payload.get("profile", {})
        portfolio = payload.get("portfolio", {})

        result = generate_full_onboarding(profile, portfolio)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成教学引导失败: {e}")


# ── 建仓助手 ──

@router.post("/building/plan", response_model=dict[str, Any])
def create_building_plan(
    payload: dict[str, Any],
    db: Session = Depends(get_db),
):
    """生成建仓计划.

    Payload:
    {
        "total_capital": 100000,
        "portfolio_config": {组合配置},
        "risk_label": "稳健型",
        "market_cycle": "recovery"
    }
    """
    try:
        total_capital = payload.get("total_capital", 100000)
        portfolio_config = payload.get("portfolio_config", {})
        risk_label = payload.get("risk_label", "稳健型")
        market_cycle = payload.get("market_cycle", "recovery")

        plan = calculate_building_plan(
            total_capital=total_capital,
            portfolio_config=portfolio_config,
            risk_label=risk_label,
            market_cycle=market_cycle,
        )
        return {"success": True, "data": plan}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成建仓计划失败: {e}")


@router.post("/building/batch/{batch_no}", response_model=dict[str, Any])
def get_batch_detail(
    batch_no: int,
    payload: dict[str, Any],
    db: Session = Depends(get_db),
):
    """获取单批建仓详情.

    Payload:
    {
        "total_capital": 100000,
        "portfolio_config": {组合配置},
        "risk_label": "稳健型"
    }
    """
    try:
        total_capital = payload.get("total_capital", 100000)
        portfolio_config = payload.get("portfolio_config", {})
        risk_label = payload.get("risk_label", "稳健型")

        batch = calculate_single_batch(
            batch_no=batch_no,
            total_capital=total_capital,
            portfolio_config=portfolio_config,
            risk_label=risk_label,
        )
        return {"success": True, "data": batch}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取建仓批次失败: {e}")


# ── 推送系统 ──

@router.post("/push/daily", response_model=dict[str, Any])
def generate_daily_push(
    payload: dict[str, Any],
    db: Session = Depends(get_db),
    header_user_id: int | None = Depends(get_current_user_id),
):
    """生成今日操作推送.

    Payload:
    {
        "user_id": 1,
        "portfolio": {组合配置},
        "market_signal": {市场信号},
        "strategy_signals": [{策略信号列表}]
    }
    """
    try:
        user_id = header_user_id or payload.get("user_id", 0)
        portfolio = payload.get("portfolio", {})
        market_signal = payload.get("market_signal", {})
        strategy_signals = payload.get("strategy_signals", [])

        push = generate_daily_operation_push(
            user_id=user_id,
            portfolio=portfolio,
            market_signal=market_signal,
            strategy_signals=strategy_signals,
        )
        return {"success": True, "data": push}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成每日推送失败: {e}")


@router.post("/push/lifespan-alert", response_model=dict[str, Any])
def generate_lifespan_push(
    payload: dict[str, Any],
    db: Session = Depends(get_db),
):
    """生成寿命预警推送.

    Payload:
    {
        "portfolio": {组合配置},
        "lifespan_data": {寿命数据}
    }
    """
    try:
        portfolio = payload.get("portfolio", {})
        lifespan_data = payload.get("lifespan_data", {})

        alert = generate_lifespan_alert(portfolio, lifespan_data)
        if alert is None:
            return {"success": True, "data": None, "message": "无寿命预警"}
        return {"success": True, "data": alert}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成寿命预警失败: {e}")


@router.post("/push/cycle-alert", response_model=dict[str, Any])
def generate_cycle_push(
    payload: dict[str, Any],
    db: Session = Depends(get_db),
):
    """生成周期切换提醒.

    Payload:
    {
        "old_cycle": "recovery",
        "new_cycle": "expansion",
        "market_signal": {市场信号}
    }
    """
    try:
        old_cycle = payload.get("old_cycle", "")
        new_cycle = payload.get("new_cycle", "")
        market_signal = payload.get("market_signal", {})

        alert = generate_cycle_alert(old_cycle, new_cycle, market_signal)
        if alert is None:
            return {"success": True, "data": None, "message": "无周期切换"}
        return {"success": True, "data": alert}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成周期提醒失败: {e}")


# ── 调仓提醒 ──

@router.post("/rebalance/check", response_model=dict[str, Any])
def check_rebalance(
    payload: dict[str, Any],
    db: Session = Depends(get_db),
):
    """检查再平衡触发条件.

    Payload:
    {
        "portfolio": {组合配置},
        "market_signal": {市场信号},
        "lifespan_data": {寿命数据},
        "last_rebalance_date": "2026-05-01"
    }
    """
    try:
        portfolio = payload.get("portfolio", {})
        market_signal = payload.get("market_signal", {})
        lifespan_data = payload.get("lifespan_data", {})
        last_rebalance_date = payload.get("last_rebalance_date")

        result = check_rebalance_triggers(
            portfolio=portfolio,
            market_signal=market_signal,
            lifespan_data=lifespan_data,
            last_rebalance_date=last_rebalance_date,
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"检查再平衡失败: {e}")


@router.post("/rebalance/alternatives", response_model=dict[str, Any])
def get_alternative_strategies(
    payload: dict[str, Any],
    db: Session = Depends(get_db),
):
    """获取替代策略推荐.

    Payload:
    {
        "target_holding": {需要替换的持仓},
        "strategy_pool": [{策略池}],
        "profile": {用户画像},
        "market_signal": {市场信号},
        "top_n": 3
    }
    """
    try:
        target_holding = payload.get("target_holding", {})
        strategy_pool = payload.get("strategy_pool", [])
        profile = payload.get("profile", {})
        market_signal = payload.get("market_signal", {})
        top_n = payload.get("top_n", 3)

        alternatives = generate_alternative_strategies(
            target_holding=target_holding,
            strategy_pool=strategy_pool,
            profile=profile,
            market_signal=market_signal,
            top_n=top_n,
        )
        return {"success": True, "data": alternatives}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取替代策略失败: {e}")


@router.post("/rebalance/plan", response_model=dict[str, Any])
def create_rebalance_plan(
    payload: dict[str, Any],
    db: Session = Depends(get_db),
):
    """生成调仓方案.

    Payload:
    {
        "portfolio": {组合配置},
        "triggers": [{触发条件}],
        "alternatives": {替代策略}
    }
    """
    try:
        portfolio = payload.get("portfolio", {})
        triggers = payload.get("triggers", [])
        alternatives = payload.get("alternatives", {})

        plan = generate_rebalance_plan(portfolio, triggers, alternatives)
        return {"success": True, "data": plan}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成调仓方案失败: {e}")


# ── 周报 ──

@router.post("/weekly-report/generate", response_model=dict[str, Any])
def create_weekly_report(
    payload: dict[str, Any],
    db: Session = Depends(get_db),
    header_user_id: int | None = Depends(get_current_user_id),
):
    """生成周报.

    Payload:
    {
        "user_id": 1,
        "portfolio": {组合配置},
        "market_signal": {市场信号},
        "performance_data": {表现数据},
        "lifespan_data": {寿命数据}
    }
    """
    try:
        user_id = header_user_id or payload.get("user_id", 0)
        portfolio = payload.get("portfolio", {})
        market_signal = payload.get("market_signal", {})
        performance_data = payload.get("performance_data", {})
        lifespan_data = payload.get("lifespan_data", {})

        report = generate_weekly_report(
            user_id=user_id,
            portfolio=portfolio,
            market_signal=market_signal,
            performance_data=performance_data,
            lifespan_data=lifespan_data,
        )
        return {"success": True, "data": report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成周报失败: {e}")


@router.get("/weekly-report/latest/{user_id}", response_model=dict[str, Any])
def get_latest_weekly_report(
    user_id: int,
    db: Session = Depends(get_db),
    header_user_id: int | None = Depends(get_current_user_id),
):
    """获取用户最新周报."""
    # 验证只能访问自己的周报
    if header_user_id and user_id != header_user_id:
        raise HTTPException(status_code=403, detail="Can only access your own report")
    # TODO: 从数据库查询最新周报
    return {
        "success": True,
        "data": None,
        "message": "功能开发中，请使用 POST /weekly-report/generate 生成周报",
    }
