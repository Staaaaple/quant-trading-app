"""演示用户相关服务.

- 自动创建/识别演示用户
- 判断指定用户是否为演示用户
- 重置演示用户的全部业务数据（保留用户行）
- 从最新正式用户复制数据到演示用户
"""

import datetime
from copy import deepcopy

from sqlalchemy.orm import Session

DEMO_USER_NAME = "演示用户"


def ensure_demo_user(db: Session):
    """确保数据库中存在演示用户，不存在则创建."""
    from app.models.user import User

    user = db.query(User).filter(User.name == DEMO_USER_NAME).first()
    if user:
        if not user.is_demo:
            user.is_demo = True
            db.commit()
            db.refresh(user)
        return user

    user = User(name=DEMO_USER_NAME, is_active=True, is_demo=True)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def is_demo_user(db: Session, user_id: int) -> bool:
    """判断指定用户是否为演示用户."""
    from app.models.user import User

    user = db.query(User).filter(User.id == user_id).first()
    return bool(user and user.is_demo)


def _find_latest_real_user(db: Session) -> int | None:
    """找到最近更新的非演示、活跃用户 ID."""
    from app.models.user import User

    user = (
        db.query(User)
        .filter(User.is_active == True, User.is_demo == False)
        .order_by(User.updated_at.desc())
        .first()
    )
    return user.id if user else None


def _copy_portfolio(db: Session, source_user_id: int, demo_user_id: int) -> int | None:
    """复制源用户最新激活的 Portfolio 到演示用户，返回 portfolio_id."""
    from app.models.portfolio import Portfolio

    source = (
        db.query(Portfolio)
        .filter(Portfolio.user_id == source_user_id, Portfolio.is_active == True)
        .order_by(Portfolio.updated_at.desc())
        .first()
    )
    if not source:
        return None

    copy = Portfolio(
        user_id=demo_user_id,
        name=source.name,
        config_json=deepcopy(source.config_json),
        backtest_result_json=deepcopy(source.backtest_result_json),
        lifespan_months=source.lifespan_months,
        health_score=source.health_score,
        is_active=True,
    )
    db.add(copy)
    db.commit()
    db.refresh(copy)
    return copy.id


def _copy_paper_trading_records(
    db: Session, source_user_id: int, demo_user_id: int, portfolio_id: int, days: int = 3
) -> None:
    """复制源用户最近 N 条模拟盘日记录到演示用户."""
    from app.models.paper_trading import PaperTradingDailyRecord

    records = (
        db.query(PaperTradingDailyRecord)
        .filter(PaperTradingDailyRecord.user_id == source_user_id)
        .order_by(PaperTradingDailyRecord.record_date.desc())
        .limit(days)
        .all()
    )
    for r in reversed(records):
        copy = PaperTradingDailyRecord(
            user_id=demo_user_id,
            portfolio_id=portfolio_id,
            record_date=r.record_date,
            daily_return=r.daily_return,
            cumulative_return=r.cumulative_return,
            nav=r.nav,
            report_id=None,
            asset_snapshot=deepcopy(r.asset_snapshot) if r.asset_snapshot else None,
        )
        db.add(copy)
    db.commit()


def _copy_market_reports(db: Session, source_user_id: int, demo_user_id: int, portfolio_id: int | None) -> None:
    """复制源用户最新的日报和周报到演示用户."""
    from app.models.operation_log import MarketReport

    for report_type in ("daily", "weekly"):
        source = (
            db.query(MarketReport)
            .filter(MarketReport.user_id == source_user_id, MarketReport.report_type == report_type)
            .order_by(MarketReport.created_at.desc())
            .first()
        )
        if not source:
            continue
        copy = MarketReport(
            user_id=demo_user_id,
            portfolio_id=portfolio_id,
            report_type=report_type,
            report_date=source.report_date,
            page1_market_overview=deepcopy(source.page1_market_overview),
            page2_portfolio_performance=deepcopy(source.page2_portfolio_performance),
            page3_weekly_market=deepcopy(source.page3_weekly_market) if source.page3_weekly_market else None,
        )
        db.add(copy)
    db.commit()


def _copy_weekly_report(db: Session, source_user_id: int, demo_user_id: int, portfolio_id: int | None) -> None:
    """复制源用户最新的 WeeklyReport 到演示用户."""
    from app.models.operation_log import WeeklyReport

    source = (
        db.query(WeeklyReport)
        .filter(WeeklyReport.user_id == source_user_id)
        .order_by(WeeklyReport.created_at.desc())
        .first()
    )
    if not source:
        return

    copy = WeeklyReport(
        user_id=demo_user_id,
        portfolio_id=portfolio_id,
        week_start=source.week_start,
        week_end=source.week_end,
        portfolio_return=source.portfolio_return,
        portfolio_cum_return=source.portfolio_cum_return,
        benchmark_return=source.benchmark_return,
        max_drawdown=source.max_drawdown,
        allocation_snapshot=deepcopy(source.allocation_snapshot) if source.allocation_snapshot else None,
        allocation_changes=deepcopy(source.allocation_changes) if source.allocation_changes else None,
        market_summary=source.market_summary,
        market_cycle=source.market_cycle,
        composite_score=source.composite_score,
        next_week_outlook=source.next_week_outlook,
        recommended_actions=deepcopy(source.recommended_actions) if source.recommended_actions else None,
        lifespan_alerts=deepcopy(source.lifespan_alerts) if source.lifespan_alerts else None,
    )
    db.add(copy)
    db.commit()


def _copy_backtest_results(db: Session, source_user_id: int, demo_user_id: int) -> None:
    """复制源用户最新的回测结果到演示用户."""
    from app.models.backtest import BacktestResult

    sources = (
        db.query(BacktestResult)
        .filter(BacktestResult.user_id == source_user_id)
        .order_by(BacktestResult.updated_at.desc())
        .limit(5)
        .all()
    )
    for source in sources:
        copy = BacktestResult(
            backtest_id=source.backtest_id,
            user_id=demo_user_id,
            strategy_id=source.strategy_id,
            status=source.status,
            start_date=source.start_date,
            end_date=source.end_date,
            initial_cash=source.initial_cash,
            metrics=deepcopy(source.metrics) if source.metrics else None,
            benchmark_metrics=deepcopy(source.benchmark_metrics) if source.benchmark_metrics else None,
            logs=source.logs,
            output_path=source.output_path,
        )
        db.add(copy)
    db.commit()


def seed_demo_data_from_real_user(db: Session, demo_user_id: int) -> dict:
    """从最新正式用户复制数据到演示用户.

    复制的数据包括：Portfolio、模拟盘日记录（最近 3 条）、
    MarketReport（daily/weekly）、WeeklyReport、BacktestResult。
    如果找不到正式用户或源数据，返回空统计。
    """
    source_user_id = _find_latest_real_user(db)
    if not source_user_id:
        return {"copied": False, "reason": "no real user found"}

    portfolio_id = _copy_portfolio(db, source_user_id, demo_user_id)
    if portfolio_id:
        _copy_paper_trading_records(db, source_user_id, demo_user_id, portfolio_id, days=3)
        _copy_market_reports(db, source_user_id, demo_user_id, portfolio_id)
        _copy_weekly_report(db, source_user_id, demo_user_id, portfolio_id)

    _copy_backtest_results(db, source_user_id, demo_user_id)

    return {
        "copied": True,
        "source_user_id": source_user_id,
        "portfolio_id": portfolio_id,
    }


def reset_demo_user_data(db: Session, user_id: int) -> dict:
    """清空演示用户的全部业务数据，保留用户行本身；然后从最新正式用户复制数据."""
    from app.models.user import User
    from app.models.investor_profile import InvestorProfile
    from app.models.portfolio import Portfolio
    from app.models.portfolio_design_task import PortfolioDesignTask
    from app.models.operation_log import MarketReport, WeeklyReport, OperationLog, PushNotification
    from app.models.paper_trading import PaperTradingDailyRecord, PaperTradingMonthlyStat
    from app.models.backtest import BacktestResult

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_demo:
        raise ValueError("Only demo user data can be reset")

    deleted_counts = {}

    def _delete(model, label: str):
        count = db.query(model).filter(model.user_id == user_id).delete(synchronize_session=False)
        deleted_counts[label] = count

    _delete(InvestorProfile, "investor_profiles")
    _delete(Portfolio, "portfolios")
    _delete(PortfolioDesignTask, "portfolio_design_tasks")
    _delete(MarketReport, "market_reports")
    _delete(WeeklyReport, "weekly_reports")
    _delete(OperationLog, "operation_logs")
    _delete(PushNotification, "push_notifications")
    _delete(PaperTradingDailyRecord, "paper_trading_daily_records")
    _delete(PaperTradingMonthlyStat, "paper_trading_monthly_stats")

    # BacktestResult 的 user_id 可能为 NULL（旧数据），只对非 NULL 行删除
    backtest_count = (
        db.query(BacktestResult)
        .filter(BacktestResult.user_id == user_id)
        .delete(synchronize_session=False)
    )
    deleted_counts["backtest_results"] = backtest_count

    db.commit()

    # 演示用户始终使用预置的演示组合与报告（避免复制正式用户可能过于激进或不真实的数据）
    from app.services.demo_data import ensure_demo_data

    portfolio_id = ensure_demo_data(db, user_id)

    # 可选：从最新正式用户复制回测结果，让演示用户有历史回测可看
    source_user_id = _find_latest_real_user(db)
    if source_user_id:
        _copy_backtest_results(db, source_user_id, user_id)

    copy_result = {
        "copied": True,
        "portfolio_id": portfolio_id,
        "source_user_id": source_user_id,
        "data_source": "synthetic demo data",
    }

    return {"ok": True, "deleted_counts": deleted_counts, "copy": copy_result}

    return {"ok": True, "deleted_counts": deleted_counts, "copy": copy_result}
