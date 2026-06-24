"""Portfolio API端点.

提供组合设计、查询、应用等接口.
"""

import asyncio
import datetime
import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Any

from app.api.deps import require_user_id
from app.db.session import get_db
from app.services.hybrid_portfolio_designer import design_portfolio, validate_portfolio, get_portfolio_summary
from app.services.hybrid_portfolio_designer_v2 import design_portfolio_v2
from app.services import portfolio_task_service, demo_user_service
from app.services.demo_data import DEMO_PORTFOLIO, ensure_demo_data

router = APIRouter()


def _get_db_session() -> Session:
    """手动获取一个独立的数据库 session（用于后台任务/回调中）."""
    db = next(get_db())
    return db


def _build_demo_portfolio_result(db: Session, user_id: int) -> dict[str, Any]:
    """为演示用户构造组合设计结果.

    优先使用已从正式用户复制过来的 Portfolio；若不存在则回退到 DEMO_PORTFOLIO。
    """
    from app.models.portfolio import Portfolio

    ensure_demo_data(db, user_id)
    db_portfolio = (
        db.query(Portfolio)
        .filter(Portfolio.user_id == user_id, Portfolio.is_active == True)
        .order_by(Portfolio.updated_at.desc())
        .first()
    )
    portfolio = db_portfolio.config_json if db_portfolio else DEMO_PORTFOLIO
    return {
        "success": True,
        "adopted": portfolio.get("adopted", False),
        "portfolio": portfolio,
        "validation": validate_portfolio(portfolio),
        "summary": get_portfolio_summary(portfolio),
        "rag_reviews": portfolio.get("rag_reviews", []),
        "rag_adjusted": portfolio.get("rag_adjusted", False),
        "rag_adjustment_count": portfolio.get("rag_adjustment_count", 0),
    }


@router.post("/design", response_model=dict[str, Any])
def create_portfolio_design(
    payload: dict[str, Any],
    db: Session = Depends(get_db),
    user_id: int = Depends(require_user_id),
):
    """设计新的投资组合.

    Payload:
    {
        "profile_vector": {...},
        "market_signal": {...},
        "strategy_pool": [...],  // 可选
    }
    """
    # 演示用户直接返回预置组合
    if demo_user_service.is_demo_user(db, user_id):
        return _build_demo_portfolio_result(db, user_id)

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


@router.post("/design-with-rag", response_model=dict[str, Any])
async def create_portfolio_design_with_rag(
    payload: dict[str, Any],
    db: Session = Depends(get_db),
    user_id: int = Depends(require_user_id),
):
    """设计投资组合（带RAG质检）.

    Payload:
    {
        "profile_vector": {...},
        "market_signal": {...},
        "strategy_pool": [...],  // 可选
        "use_rag_gate": true,     // 是否启用RAG质检，默认true
        "rag_strictness": "normal", // strict/normal/loose
    }

    Response:
    {
        "success": true,
        "adopted": true/false,
        "portfolio": {...},
        "rag_reviews": [...],
        "rag_adjusted": true/false,
        "rag_adjustment_count": 3,
        "summary": {...}
    }
    """
    # 演示用户直接返回预置组合
    if demo_user_service.is_demo_user(db, user_id):
        return _build_demo_portfolio_result(db, user_id)

    try:
        profile_vector = payload.get("profile_vector", {})
        market_signal = payload.get("market_signal", {})
        strategy_pool = payload.get("strategy_pool")
        use_rag_gate = payload.get("use_rag_gate", True)
        use_dynamic_picker = payload.get("use_dynamic_picker", True)

        portfolio = await design_portfolio_v2(
            profile_vector=profile_vector,
            market_signal=market_signal,
            strategy_pool=strategy_pool,
            use_rag_gate=use_rag_gate,
            use_dynamic_picker=use_dynamic_picker,
        )

        # 验证
        validation = validate_portfolio(portfolio)

        return {
            "success": True,
            "adopted": portfolio.get("adopted", False),
            "portfolio": portfolio,
            "validation": validation,
            "summary": get_portfolio_summary(portfolio),
            "rag_reviews": portfolio.get("rag_reviews", []),
            "rag_adjusted": portfolio.get("rag_adjusted", False),
            "rag_adjustment_count": portfolio.get("rag_adjustment_count", 0),
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Portfolio design with RAG failed: {e}")


@router.post("/design-async", response_model=dict[str, Any])
async def create_portfolio_design_async(
    payload: dict[str, Any],
    db: Session = Depends(get_db),
    user_id: int = Depends(require_user_id),
):
    """提交异步组合设计任务.

    立即返回 task_id，后端在后台持续运行，不受前端刷新影响。
    同一用户同时只能有一个 running 任务；若已有 running 任务，返回已有 task_id。
    """
    # 演示用户直接返回预置组合
    if demo_user_service.is_demo_user(db, user_id):
        result = _build_demo_portfolio_result(db, user_id)
        task = portfolio_task_service.create_task(db, user_id, payload)
        task.status = "completed"
        task.result_json = result
        task.progress = 1.0
        task.completed_at = datetime.datetime.utcnow()
        db.commit()
        db.refresh(task)
        return portfolio_task_service.task_to_dict(task)

    # 检查是否已有进行中的任务
    existing = portfolio_task_service.get_running_task_for_user(db, user_id)
    if existing:
        return {
            "task_id": existing.id,
            "status": existing.status,
            "current_step": existing.current_step,
            "progress": existing.progress,
        }

    # 创建新任务
    task = portfolio_task_service.create_task(db, user_id, payload)

    async def run_design() -> None:
        """后台执行组合设计."""
        _db = _get_db_session()
        try:
            portfolio_task_service.start_task(_db, task.id)

            async def progress_callback(event: dict[str, Any]) -> None:
                step = event.get("step", "")
                progress = event.get("progress", 0)
                if step and isinstance(progress, (int, float)):
                    progress_db = _get_db_session()
                    try:
                        portfolio_task_service.update_progress(progress_db, task.id, step, progress)
                    finally:
                        progress_db.close()

            portfolio = await design_portfolio_v2(
                profile_vector=payload.get("profile_vector", {}),
                market_signal=payload.get("market_signal", {}),
                strategy_pool=payload.get("strategy_pool"),
                use_rag_gate=payload.get("use_rag_gate", True),
                use_dynamic_picker=payload.get("use_dynamic_picker", True),
                progress_callback=progress_callback,
            )

            result_event = {
                "type": "result",
                "success": True,
                "adopted": portfolio.get("adopted", False),
                "portfolio": portfolio,
                "validation": validate_portfolio(portfolio),
                "summary": get_portfolio_summary(portfolio),
                "rag_reviews": portfolio.get("rag_reviews", []),
                "rag_adjusted": portfolio.get("rag_adjusted", False),
                "rag_adjustment_count": portfolio.get("rag_adjustment_count", 0),
            }
            portfolio_task_service.complete_task(_db, task.id, result_event)
        except Exception as e:
            import traceback
            traceback.print_exc()
            portfolio_task_service.fail_task(_db, task.id, str(e))
        finally:
            _db.close()

    # 启动后台任务并立即返回
    asyncio.create_task(run_design())

    return {
        "task_id": task.id,
        "status": "running",
        "current_step": task.current_step,
        "progress": task.progress,
    }


@router.get("/tasks/me", response_model=dict[str, Any])
def get_my_latest_task(
    db: Session = Depends(get_db),
    user_id: int = Depends(require_user_id),
):
    """获取当前用户最新的组合设计任务."""
    task = portfolio_task_service.get_latest_task_for_user(db, user_id)
    if not task:
        return {"task_id": None, "status": None}
    return portfolio_task_service.task_to_dict(task)


@router.get("/tasks/{task_id}", response_model=dict[str, Any])
def get_task_status(
    task_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(require_user_id),
):
    """查询指定任务的状态和结果."""
    task = portfolio_task_service.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this task")
    return portfolio_task_service.task_to_dict(task)


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


@router.post("/design-with-rag/stream")
async def create_portfolio_design_with_rag_stream(
    payload: dict[str, Any],
    db: Session = Depends(get_db),
    user_id: int = Depends(require_user_id),
):
    """设计投资组合（带RAG质检）SSE流式进度版.

    通过 Server-Sent Events 实时推送每步进度:
        data: {"type":"task","task_id":1}
        data: {"type":"progress","step":"saa","message":"...","progress":0.05}

    最终完成时推送结果:
        data: {"type":"result","portfolio":{...}}

    出错时推送:
        data: {"type":"error","message":"..."}
    """
    queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()

    # 检查是否已有进行中的任务
    existing_task = portfolio_task_service.get_running_task_for_user(db, user_id)

    async def progress_callback(event: dict[str, Any]) -> None:
        print(f"[SSE] 收到进度事件: {event.get('step')} - {event.get('message')}", flush=True)
        await queue.put(event)
        # 同步写入数据库任务状态
        step = event.get("step", "")
        progress = event.get("progress", 0)
        if step and isinstance(progress, (int, float)):
            progress_db = _get_db_session()
            try:
                portfolio_task_service.update_progress(progress_db, task.id, step, progress)
            finally:
                progress_db.close()

    async def event_generator():
        """SSE 事件生成器."""
        nonlocal task
        try:
            # 如果已有进行中的任务，直接返回 task_id，让前端去轮询
            if existing_task and existing_task.status in ("pending", "running"):
                task = existing_task
                yield f"data: {json.dumps({'type': 'task', 'task_id': task.id}, ensure_ascii=False)}\n\n"
                # 保持连接直到任务完成，每 2 秒推送一次当前状态
                while task.status in ("pending", "running"):
                    await asyncio.sleep(2.0)
                    status_db = _get_db_session()
                    try:
                        task = portfolio_task_service.get_task(status_db, task.id)
                    finally:
                        status_db.close()

                    if task.status == "running":
                        yield f"data: {json.dumps({'type': 'progress', 'step': task.current_step, 'message': task.current_step, 'progress': task.progress}, ensure_ascii=False)}\n\n"
                    elif task.status == "completed":
                        result = task.result_json or {}
                        yield f"data: {json.dumps(result, ensure_ascii=False)}\n\n"
                        return
                    elif task.status == "failed":
                        yield f"data: {json.dumps({'type': 'error', 'message': task.error_message or 'Task failed'}, ensure_ascii=False)}\n\n"
                        return
                    else:
                        yield ": heartbeat\n\n"
                return

            # 创建新任务（使用独立 session，避免 StreamingResponse 关闭后 session 失效）
            create_db = _get_db_session()
            try:
                task = portfolio_task_service.create_task(create_db, user_id, payload)
            finally:
                create_db.close()
            yield f"data: {json.dumps({'type': 'task', 'task_id': task.id}, ensure_ascii=False)}\n\n"

            start_db = _get_db_session()
            try:
                portfolio_task_service.start_task(start_db, task.id)
            finally:
                start_db.close()

            # 在后台任务中执行组合设计
            bg_task = asyncio.create_task(
                design_portfolio_v2(
                    profile_vector=payload.get("profile_vector", {}),
                    market_signal=payload.get("market_signal", {}),
                    strategy_pool=payload.get("strategy_pool"),
                    use_rag_gate=payload.get("use_rag_gate", True),
                    use_dynamic_picker=payload.get("use_dynamic_picker", True),
                    progress_callback=progress_callback,
                )
            )

            # 同时监听进度事件和任务完成
            while not bg_task.done():
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=1.0)
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                except asyncio.TimeoutError:
                    # 发送心跳保持连接
                    yield ": heartbeat\n\n"

            # 任务结束，获取结果
            portfolio = await bg_task
            result_event = {
                "type": "result",
                "success": True,
                "adopted": portfolio.get("adopted", False),
                "portfolio": portfolio,
                "validation": validate_portfolio(portfolio),
                "summary": get_portfolio_summary(portfolio),
                "rag_reviews": portfolio.get("rag_reviews", []),
                "rag_adjusted": portfolio.get("rag_adjusted", False),
                "rag_adjustment_count": portfolio.get("rag_adjustment_count", 0),
            }
            yield f"data: {json.dumps(result_event, ensure_ascii=False)}\n\n"

            # 持久化结果（使用独立 session）
            complete_db = _get_db_session()
            try:
                portfolio_task_service.complete_task(complete_db, task.id, result_event)
            finally:
                complete_db.close()

        except Exception as e:
            import traceback
            traceback.print_exc()
            error_event = {"type": "error", "message": str(e)}
            yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"
            if task:
                try:
                    fail_db = _get_db_session()
                    portfolio_task_service.fail_task(fail_db, task.id, str(e))
                    fail_db.close()
                except Exception:
                    pass

    # 用于 event_generator 内部引用的 task 变量
    task = None

    # 演示用户直接返回预置组合，不走 SSE 设计流程
    if demo_user_service.is_demo_user(db, user_id):
        async def _demo_event_generator():
            demo_db = _get_db_session()
            try:
                result = _build_demo_portfolio_result(demo_db, user_id)
                demo_task = portfolio_task_service.create_task(demo_db, user_id, payload)
                demo_task.status = "completed"
                demo_task.result_json = result
                demo_task.progress = 1.0
                demo_task.completed_at = datetime.datetime.utcnow()
                demo_db.commit()
                demo_db.refresh(demo_task)
                yield f"data: {json.dumps({'type': 'task', 'task_id': demo_task.id}, ensure_ascii=False)}\n\n"
                result_event = {**result, "type": "result"}
                yield f"data: {json.dumps(result_event, ensure_ascii=False)}\n\n"
            finally:
                demo_db.close()

        return StreamingResponse(
            _demo_event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用 Nginx 缓冲
        },
    )
