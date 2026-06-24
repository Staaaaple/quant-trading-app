from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import require_user_id
from app.db.session import get_db
from app.models.portfolio import Portfolio
from app.schemas.paper_trading import (
    PaperTradingDailyRecordRead,
    PaperTradingMonthlyStatRead,
)
from app.services import paper_trading_service

router = APIRouter()


def _resolve_active_portfolio_id(db: Session, user_id: int, portfolio_id: int | None) -> int | None:
    """未指定组合时，返回用户当前激活组合 ID."""
    if portfolio_id is not None:
        return portfolio_id
    portfolio = (
        db.query(Portfolio)
        .filter(
            Portfolio.user_id == user_id,
            Portfolio.is_active == True,
        )
        .order_by(Portfolio.updated_at.desc())
        .first()
    )
    return portfolio.id if portfolio else None


@router.get("/daily-records", response_model=list[PaperTradingDailyRecordRead])
def list_daily_records(
    *,
    db: Session = Depends(get_db),
    user_id: int = Depends(require_user_id),
    portfolio_id: int | None = Query(None, description="指定组合 ID，默认当前激活组合"),
    start_date: str | None = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: str | None = Query(None, description="结束日期 YYYY-MM-DD"),
    limit: int = Query(365, ge=1, le=1000),
):
    """查询模拟盘每日累计收益记录."""
    resolved_portfolio_id = _resolve_active_portfolio_id(db, user_id, portfolio_id)
    return paper_trading_service.list_daily_records(
        db,
        user_id=user_id,
        portfolio_id=resolved_portfolio_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )


@router.get("/monthly-stats", response_model=list[PaperTradingMonthlyStatRead])
def list_monthly_stats(
    *,
    db: Session = Depends(get_db),
    user_id: int = Depends(require_user_id),
    portfolio_id: int | None = Query(None, description="指定组合 ID，默认当前激活组合"),
    limit: int = Query(120, ge=1, le=240),
):
    """查询模拟盘月度收益率统计."""
    resolved_portfolio_id = _resolve_active_portfolio_id(db, user_id, portfolio_id)
    return paper_trading_service.list_monthly_stats(
        db,
        user_id=user_id,
        portfolio_id=resolved_portfolio_id,
        limit=limit,
    )


@router.post("/sync-daily", status_code=status.HTTP_200_OK)
def sync_daily_records(
    *,
    db: Session = Depends(get_db),
    user_id: int = Depends(require_user_id),
    report_date: str | None = Query(None, description="报告日期 YYYY-MM-DD，默认今天"),
):
    """手动触发从市场报告同步模拟盘日记录（用于补录或测试）."""
    try:
        result = paper_trading_service.sync_all_users_daily_records(
            db, report_date=report_date
        )
        return {"detail": "sync completed", "result": result}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync daily records: {e}",
        )


@router.post("/calc-monthly", status_code=status.HTTP_200_OK)
def calc_monthly_stats(
    *,
    db: Session = Depends(get_db),
    user_id: int = Depends(require_user_id),
    year_month: str | None = Query(None, description="月份 YYYY-MM，默认上一个月"),
):
    """手动触发月度统计（用于补录或测试）."""
    try:
        result = paper_trading_service.generate_all_users_monthly_stats(
            db, year_month=year_month
        )
        return {"detail": "monthly stats generated", "result": result}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate monthly stats: {e}",
        )


@router.get("/latest", response_model=PaperTradingDailyRecordRead | None)
def get_latest_record(
    *,
    db: Session = Depends(get_db),
    user_id: int = Depends(require_user_id),
    portfolio_id: int | None = Query(None, description="指定组合 ID，默认当前激活组合"),
):
    """获取最新一日的模拟盘记录."""
    resolved_portfolio_id = _resolve_active_portfolio_id(db, user_id, portfolio_id)
    return paper_trading_service.get_latest_daily_record(
        db, user_id=user_id, portfolio_id=resolved_portfolio_id
    )
