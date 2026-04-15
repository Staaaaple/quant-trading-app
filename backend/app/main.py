import contextlib

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.api.v1.router import api_router
from app.core.config import settings
from app.db.base import Base, engine
from app.db.session import SessionLocal
from app.services import stock_picker_service

scheduler = BackgroundScheduler()


def _run_builtin_weekly_job():
    db = SessionLocal()
    try:
        stock_picker_service.run_builtin_weekly_if_enabled(db)
    finally:
        db.close()


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create all database tables if they don't exist
    Base.metadata.create_all(bind=engine)

    # Ensure builtin picker exists
    db = SessionLocal()
    try:
        stock_picker_service.ensure_builtin_picker(db)
    finally:
        db.close()

    # Schedule weekly builtin picker: every Friday at 15:05
    if not scheduler.running:
        scheduler.add_job(
            _run_builtin_weekly_job,
            trigger=CronTrigger(day_of_week="fri", hour=15, minute=5),
            id="builtin_weekly_picker_job",
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
