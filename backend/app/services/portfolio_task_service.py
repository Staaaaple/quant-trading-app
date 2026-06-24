import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models.portfolio import Portfolio
from app.models.portfolio_design_task import PortfolioDesignTask
from app.services.portfolio_ecosystem_adapter import ensure_portfolio_ecosystem_data


def create_task(db: Session, user_id: int, payload: dict[str, Any]) -> PortfolioDesignTask:
    """创建新的组合设计任务."""
    task = PortfolioDesignTask(
        user_id=user_id,
        status="pending",
        progress=0.0,
        payload_json=payload,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def get_task(db: Session, task_id: int) -> PortfolioDesignTask | None:
    """根据 ID 查询任务."""
    return db.query(PortfolioDesignTask).filter(PortfolioDesignTask.id == task_id).first()


def get_latest_task_for_user(db: Session, user_id: int) -> PortfolioDesignTask | None:
    """查询用户最新的一个任务（任意状态）."""
    return (
        db.query(PortfolioDesignTask)
        .filter(PortfolioDesignTask.user_id == user_id)
        .order_by(PortfolioDesignTask.created_at.desc())
        .first()
    )


def get_running_task_for_user(db: Session, user_id: int) -> PortfolioDesignTask | None:
    """查询用户当前进行中的任务（pending 或 running）."""
    return (
        db.query(PortfolioDesignTask)
        .filter(
            PortfolioDesignTask.user_id == user_id,
            PortfolioDesignTask.status.in_(["pending", "running"]),
        )
        .order_by(PortfolioDesignTask.created_at.desc())
        .first()
    )


def start_task(db: Session, task_id: int) -> PortfolioDesignTask | None:
    """将任务状态改为 running."""
    task = get_task(db, task_id)
    if task is None:
        return None
    task.status = "running"
    db.commit()
    db.refresh(task)
    return task


def update_progress(
    db: Session,
    task_id: int,
    step: str,
    progress: float,
) -> PortfolioDesignTask | None:
    """更新任务进度."""
    task = get_task(db, task_id)
    if task is None:
        return None
    task.status = "running"
    task.current_step = step
    task.progress = max(0.0, min(1.0, progress))
    db.commit()
    db.refresh(task)
    return task


def complete_task(db: Session, task_id: int, result: dict[str, Any]) -> PortfolioDesignTask | None:
    """标记任务完成，保存结果，并写入 Portfolio 表."""
    task = get_task(db, task_id)
    if task is None:
        return None

    now = datetime.datetime.utcnow()
    task.status = "completed"
    task.result_json = result
    task.progress = 1.0
    task.completed_at = now
    db.commit()
    db.refresh(task)

    _save_portfolio_from_result(db, task, result)
    return task


def fail_task(db: Session, task_id: int, error: str) -> PortfolioDesignTask | None:
    """标记任务失败."""
    task = get_task(db, task_id)
    if task is None:
        return None

    now = datetime.datetime.utcnow()
    task.status = "failed"
    task.error_message = error
    task.completed_at = now
    db.commit()
    db.refresh(task)
    return task


def _save_portfolio_from_result(
    db: Session,
    task: PortfolioDesignTask,
    result: dict[str, Any],
) -> Portfolio | None:
    """把任务结果持久化到 portfolios 表."""
    portfolio_data = result.get("portfolio") or {}
    if not portfolio_data:
        return None

    portfolio = Portfolio(
        user_id=task.user_id,
        name="AI 量化组合",
        config_json=portfolio_data,
        backtest_result_json=portfolio_data.get("reliability", {}).get("benchmark_comparison"),
        lifespan_months=portfolio_data.get("portfolio_lifespan"),
        health_score=portfolio_data.get("portfolio_health"),
        is_active=True,
    )
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)

    # 将组合中的策略自动接入生态系统（DNA + 系统发育）
    try:
        ensure_portfolio_ecosystem_data(db, portfolio)
    except Exception as e:
        print(f"[PortfolioTask] 组合生态系统数据接入失败: {e}")
        db.rollback()

    return portfolio


def task_to_dict(task: PortfolioDesignTask) -> dict[str, Any]:
    """将任务对象序列化为 API 响应字典."""
    return {
        "task_id": task.id,
        "user_id": task.user_id,
        "status": task.status,
        "current_step": task.current_step,
        "progress": task.progress,
        "result": task.result_json,
        "error_message": task.error_message,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "updated_at": task.updated_at.isoformat() if task.updated_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
    }
