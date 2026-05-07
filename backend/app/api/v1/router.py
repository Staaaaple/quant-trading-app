from fastapi import APIRouter

from app.api.v1.endpoints import strategies, backtests, paper_trading, sync, account_settings, stock_picker, risk_strategies, strategy_flows, dna

api_router = APIRouter()
api_router.include_router(strategies.router, prefix="/strategies", tags=["strategies"])
api_router.include_router(backtests.router, prefix="/backtests", tags=["backtests"])
api_router.include_router(paper_trading.router, prefix="/paper-trading", tags=["paper-trading"])
api_router.include_router(sync.router, prefix="/sync", tags=["sync"])
api_router.include_router(account_settings.router, prefix="/account-settings", tags=["account-settings"])
api_router.include_router(stock_picker.router, prefix="/stock-picker", tags=["stock-picker"])
api_router.include_router(risk_strategies.router, prefix="/risk-strategies", tags=["risk-strategies"])
api_router.include_router(strategy_flows.router, prefix="/strategy-flows", tags=["strategy-flows"])
api_router.include_router(dna.router, tags=["dna"])
