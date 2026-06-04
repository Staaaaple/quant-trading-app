import contextlib
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.api.v1.router import api_router
from app.core.config import settings
from app.db.base import Base, engine
from app.db.session import SessionLocal
import app.models  # noqa: F401 - 确保所有模型注册到 Base.metadata
from app.services import stock_picker_service, market_signal_service, seed_knowledge_base

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


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create all database tables if they don't exist
    Base.metadata.create_all(bind=engine)

    # Ensure new columns exist for existing databases
    _ensure_db_columns()

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

    # Schedule weekly builtin picker: every Friday at 15:05
    # Schedule market signal collection: 09:00 and 15:00 every day (overwrite mode)
    if not scheduler.running:
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
