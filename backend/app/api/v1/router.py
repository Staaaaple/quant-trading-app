from fastapi import APIRouter

from app.api.v1.endpoints import strategies, backtests, paper_trading, sync

api_router = APIRouter()
api_router.include_router(strategies.router, prefix="/strategies", tags=["strategies"])
api_router.include_router(backtests.router, prefix="/backtests", tags=["backtests"])
api_router.include_router(paper_trading.router, prefix="/paper-trading", tags=["paper-trading"])
api_router.include_router(sync.router, prefix="/sync", tags=["sync"])
