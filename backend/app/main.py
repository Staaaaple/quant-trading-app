import contextlib
import os
from datetime import datetime

# Fix OpenMP library conflict on macOS
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# Windows 上强制使用 spawn 启动子进程，避免 fork 损坏 CUDA 上下文
try:
    import torch.multiprocessing as mp
    mp.set_start_method("spawn", force=True)
    print("[Init] multiprocessing start method set to spawn")
except Exception:
    pass

# 可选：禁用后台调度器做 CUDA 问题对照实验
_DISABLE_SCHEDULER = os.getenv("DISABLE_SCHEDULER", "0") == "1"

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.api.v1.router import api_router
from app.core.config import settings
from app.db.base import Base, engine
from app.db.session import SessionLocal
import app.models  # noqa: F401 - 确保所有模型注册到 Base.metadata
from app.services import stock_picker_service, market_signal_service, seed_knowledge_base
from app.services.market_report_service import (
    generate_daily_market_report,
    generate_weekly_market_report,
)
from app.services import paper_trading_service
from app.services.lifespan_monitor_service import run_monthly_lifespan_check
from app.models.portfolio_design_task import PortfolioDesignTask

scheduler = BackgroundScheduler()

# 记录最后一次采集状态
_last_collection_status = {
    "last_run": None,
    "last_success": None,
    "last_error": None,
    "total_runs": 0,
    "total_success": 0,
}


def _run_builtin_weekly_job():
    db = SessionLocal()
    try:
        stock_picker_service.run_builtin_weekly_if_enabled(db)
    finally:
        db.close()


def _run_market_signal_collection(label: str = "Scheduled"):
    """执行市场信号采集并保存（覆盖当天数据）."""
    _last_collection_status["last_run"] = datetime.now().isoformat()
    _last_collection_status["total_runs"] += 1

    db = SessionLocal()
    try:
        signal_data = market_signal_service.collect_market_signal()
        market_signal_service.save_market_signal(db, signal_data)
        _last_collection_status["last_success"] = datetime.now().isoformat()
        _last_collection_status["total_success"] += 1
        _last_collection_status["last_error"] = None
        print(f"[{label}] Market signal collected: {signal_data['composite_score']} ({signal_data['market_mood']})")
    except Exception as e:
        _last_collection_status["last_error"] = str(e)
        print(f"[{label}] Market signal collection failed: {e}")
    finally:
        db.close()


def _run_daily_market_signal_job():
    """每日 09:00 自动采集市场信号（覆盖模式）."""
    _run_market_signal_collection(label="Daily09:00")


def _run_monthly_lifespan_job():
    """每月 1 日 03:00 自动执行策略寿命检查."""
    db = SessionLocal()
    try:
        result = run_monthly_lifespan_check(db)
        print(f"[MonthlyLifespan] 完成: {result['updated']}/{result['total_strategies']} 个策略, "
              f"黄灯{result['yellow_alerts']}个, 红灯{result['red_alerts']}个")
    except Exception as e:
        print(f"[MonthlyLifespan] 执行失败: {e}")
    finally:
        db.close()


def _run_daily_market_report_job():
    """每日 15:30 自动生成市场报告（分页1 + 分页2）."""
    from app.models.user import User
    from app.models.portfolio import Portfolio
    from app.models.operation_log import MarketReport

    db = SessionLocal()
    try:
        users = db.query(User).filter(User.is_active == True).all()
        today = datetime.now().date().isoformat()

        for user in users:
            try:
                portfolio = db.query(Portfolio).filter(
                    Portfolio.user_id == user.id,
                    Portfolio.is_active == True
                ).order_by(Portfolio.updated_at.desc()).first()

                portfolio_id = portfolio.id if portfolio else None
                report = generate_daily_market_report(user.id, portfolio_id)

                db_report = MarketReport(
                    user_id=user.id,
                    portfolio_id=portfolio_id,
                    report_type="daily",
                    report_date=today,
                    page1_market_overview=report["page1_market_overview"],
                    page2_portfolio_performance=report["page2_portfolio_performance"],
                    page3_weekly_market=None,
                )
                db.add(db_report)
                db.commit()

                # 同步模拟盘每日记录
                paper_trading_service.sync_daily_record_from_report(
                    db,
                    user_id=user.id,
                    portfolio_id=portfolio_id,
                    report_id=db_report.id,
                    report_date=today,
                    page2=report["page2_portfolio_performance"],
                )

                print(f"[DailyMarketReport] Generated for user {user.id}")

            except Exception as e:
                print(f"[DailyMarketReport] Failed for user {user.id}: {e}")
                db.rollback()

    finally:
        db.close()


def _run_paper_trading_monthly_job():
    """每月 1 日自动生成模拟盘上月月度收益率统计."""
    db = SessionLocal()
    try:
        result = paper_trading_service.generate_all_users_monthly_stats(db)
        print(
            f"[PaperTradingMonthly] 完成: {result['created']} 个用户月度统计生成, "
            f"错误 {len(result['errors'])} 个"
        )
        if result["errors"]:
            for err in result["errors"]:
                print(f"[PaperTradingMonthly] Error user {err['user_id']}: {err['error']}")
    except Exception as e:
        print(f"[PaperTradingMonthly] 执行失败: {e}")
    finally:
        db.close()


def _run_weekly_market_report_job():
    """每周五 16:00 自动生成完整市场报告（分页1 + 分页2 + 分页3）."""
    from app.models.user import User
    from app.models.portfolio import Portfolio
    from app.models.operation_log import MarketReport

    db = SessionLocal()
    try:
        users = db.query(User).filter(User.is_active == True).all()
        today = datetime.now().date().isoformat()

        for user in users:
            try:
                portfolio = db.query(Portfolio).filter(
                    Portfolio.user_id == user.id,
                    Portfolio.is_active == True
                ).order_by(Portfolio.updated_at.desc()).first()

                portfolio_id = portfolio.id if portfolio else None
                report = generate_weekly_market_report(user.id, portfolio_id)

                db_report = MarketReport(
                    user_id=user.id,
                    portfolio_id=portfolio_id,
                    report_type="weekly",
                    report_date=today,
                    page1_market_overview=report["page1_market_overview"],
                    page2_portfolio_performance=report["page2_portfolio_performance"],
                    page3_weekly_market=report["page3_weekly_market"],
                )
                db.add(db_report)
                db.commit()
                print(f"[WeeklyMarketReport] Generated for user {user.id}")

            except Exception as e:
                print(f"[WeeklyMarketReport] Failed for user {user.id}: {e}")
                db.rollback()

    finally:
        db.close()


def _ensure_db_columns():
    """确保数据库表包含所有必需的列（兼容已有数据库）."""
    from sqlalchemy import inspect, text
    inspector = inspect(engine)
    columns = [c["name"] for c in inspector.get_columns("strategies")]
    if "pipeline_config" not in columns:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE strategies ADD COLUMN pipeline_config JSON"))
            conn.commit()


def _initial_market_signal_collection():
    """启动时立即执行一次市场信号采集（覆盖模式）."""
    print("[Init] Running initial market signal collection...")
    _run_market_signal_collection(label="Init")


def _cleanup_stuck_running_tasks():
    """启动时清理卡住的 running 任务.

    后端重启时，正在执行的异步后台任务会被强制中断，但数据库中状态仍可能
    保留为 running。启动后这些任务已成为"僵尸任务"，需要标记为失败，避免
    前端无限轮询。
    """
    db = SessionLocal()
    try:
        stuck = (
            db.query(PortfolioDesignTask)
            .filter(PortfolioDesignTask.status == "running")
            .all()
        )
        if stuck:
            now = datetime.utcnow()
            for task in stuck:
                task.status = "failed"
                task.error_message = "后端重启导致任务中断，请重新提交"
                task.completed_at = now
            db.commit()
            print(f"[Init] 清理 {len(stuck)} 个卡住的 running 任务")
    except Exception as e:
        print(f"[Init] 清理 running 任务失败: {e}")
        db.rollback()
    finally:
        db.close()


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create all database tables if they don't exist
    Base.metadata.create_all(bind=engine)

    # Ensure new columns exist for existing databases
    _ensure_db_columns()

    # 清理重启前卡住的 running 任务
    _cleanup_stuck_running_tasks()

    # Ensure builtin picker exists
    # Seed knowledge base (templates + papers)
    db = SessionLocal()
    try:
        stock_picker_service.ensure_builtin_picker(db)
        tmpl_count = seed_knowledge_base.seed_templates(db)
        paper_count = seed_knowledge_base.seed_papers(db)
        if tmpl_count > 0 or paper_count > 0:
            print(f"[Seed] Templates: +{tmpl_count}, Papers: +{paper_count}")
    finally:
        db.close()

    # 启动时立即采集一次市场信号（确保有数据）
    _initial_market_signal_collection()

    # 预加载 LLM 模型（避免 Windows WDDM 下的 CUDA 上下文问题）
    try:
        import traceback
        from app.services.rag.llm_service import get_llm_service
        llm = get_llm_service()
        print(f"[Init] LLM backend config={settings.LLM_BACKEND}, instance backend={llm.backend}")
        if llm.backend == "transformers":
            print("[Init] 预加载 Transformers 模型...", flush=True)
            available = llm.is_available()
            print(f"[Init] 模型预加载完成, available={available}", flush=True)
        else:
            print(f"[Init] 模型预加载跳过，backend={llm.backend}")
    except Exception as e:
        print(f"[Init] 模型预加载失败: {e}", flush=True)
        traceback.print_exc()

    # Schedule weekly builtin picker: every Friday at 15:05
    # Schedule market signal collection: 09:00 and 15:00 every day (overwrite mode)
    if _DISABLE_SCHEDULER:
        print("[Scheduler] DISABLE_SCHEDULER=1, 后台调度器已跳过")
    elif not scheduler.running:
        scheduler.add_job(
            _run_builtin_weekly_job,
            trigger=CronTrigger(day_of_week="fri", hour=15, minute=5),
            id="builtin_weekly_picker_job",
            replace_existing=True,
        )
        scheduler.add_job(
            _run_daily_market_signal_job,
            trigger=CronTrigger(hour=9, minute=0),
            id="daily_market_signal_job_0900",
            replace_existing=True,
        )
        scheduler.add_job(
            _run_market_signal_collection,
            trigger=CronTrigger(hour=15, minute=0),
            id="daily_market_signal_job_1500",
            replace_existing=True,
        )
        # 每月1日 03:00 策略寿命检查
        scheduler.add_job(
            _run_monthly_lifespan_job,
            trigger=CronTrigger(day=1, hour=3, minute=0),
            id="monthly_lifespan_check_job",
            replace_existing=True,
        )
        # 每日 15:30 自动生成市场报告
        scheduler.add_job(
            _run_daily_market_report_job,
            trigger=CronTrigger(hour=15, minute=30),
            id="daily_market_report_job",
            replace_existing=True,
        )
        # 每月 1 日 04:00 自动生成模拟盘月度统计
        scheduler.add_job(
            _run_paper_trading_monthly_job,
            trigger=CronTrigger(day=1, hour=4, minute=0),
            id="paper_trading_monthly_job",
            replace_existing=True,
        )
        # 每周五 16:00 自动生成完整市场报告
        scheduler.add_job(
            _run_weekly_market_report_job,
            trigger=CronTrigger(day_of_week="fri", hour=16, minute=0),
            id="weekly_market_report_job",
            replace_existing=True,
        )
        scheduler.start()
        print(f"[Scheduler] Started. Jobs: {[j.id for j in scheduler.get_jobs()]}")

    yield

    # Shutdown
    if scheduler.running:
        scheduler.shutdown()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/admin/collection-status")
def collection_status():
    """查看市场信号采集状态（调试用）."""
    return {
        **_last_collection_status,
        "scheduler_running": scheduler.running,
        "scheduled_jobs": [
            {
                "id": j.id,
                "next_run": j.next_run_time.isoformat() if j.next_run_time else None,
                "trigger": str(j.trigger),
            }
            for j in scheduler.get_jobs()
        ],
    }


# ── 远程部署：后端同时托管前端构建产物 ──
# 生产/远程环境会把 frontend/dist 复制到 backend/static，访问根域名即可打开页面。
_STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")

if os.path.isdir(_STATIC_DIR):
    app.mount("/", StaticFiles(directory=_STATIC_DIR, html=True), name="static")

    @app.get("/{catchall:path}", include_in_schema=False)
    async def serve_spa(catchall: str, request: Request):
        """SPA fallback：任意非 API 路由都返回 index.html."""
        # API/health/admin 已注册在前，未命中的未知路径才走到这里
        return FileResponse(os.path.join(_STATIC_DIR, "index.html"))
