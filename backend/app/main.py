import contextlib

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


def _run_builtin_weekly_job():
    db = SessionLocal()
    try:
        stock_picker_service.run_builtin_weekly_if_enabled(db)
    finally:
        db.close()


def _run_daily_market_signal_job():
    """每日自动采集市场信号."""
    db = SessionLocal()
    try:
        signal_data = market_signal_service.collect_market_signal()
        market_signal_service.save_market_signal(db, signal_data)
        print(f"[Daily] Market signal collected: {signal_data['composite_score']} ({signal_data['market_mood']})")
    except Exception as e:
        print(f"[Daily] Market signal collection failed: {e}")
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

    # Schedule weekly builtin picker: every Friday at 15:05
    # Schedule daily market signal collection: every day at 09:00
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
            id="daily_market_signal_job",
            replace_existing=True,
        )
        scheduler.start()

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
