import datetime
import json
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.paper_trading import PaperTradingDailyRecord, PaperTradingMonthlyStat


def _today_str() -> str:
    return datetime.date.today().isoformat()


def get_daily_record(db: Session, user_id: int, portfolio_id: int | None, record_date: str):
    """获取指定日期的模拟盘记录."""
    return (
        db.query(PaperTradingDailyRecord)
        .filter(
            PaperTradingDailyRecord.user_id == user_id,
            PaperTradingDailyRecord.portfolio_id == portfolio_id,
            PaperTradingDailyRecord.record_date == record_date,
        )
        .first()
    )


def get_previous_record(
    db: Session,
    user_id: int,
    portfolio_id: int | None,
    before_date: str,
):
    """获取指定日期之前的最近一条记录，用于计算净值."""
    return (
        db.query(PaperTradingDailyRecord)
        .filter(
            PaperTradingDailyRecord.user_id == user_id,
            PaperTradingDailyRecord.portfolio_id == portfolio_id,
            PaperTradingDailyRecord.record_date < before_date,
        )
        .order_by(PaperTradingDailyRecord.record_date.desc())
        .first()
    )


def _extract_daily_return(page2: dict | None) -> float:
    """从市场报告 page2 中提取组合日收益率."""
    if not page2:
        return 0.0
    value = page2.get("portfolio_return")
    try:
        return float(value) if value is not None else 0.0
    except (TypeError, ValueError):
        return 0.0


def sync_daily_record_from_report(
    db: Session,
    *,
    user_id: int,
    portfolio_id: int | None,
    report_id: int,
    report_date: str,
    page2: dict | None,
):
    """根据每日市场报告同步模拟盘日记录（幂等）."""
    daily_return = _extract_daily_return(page2)

    prev = get_previous_record(db, user_id, portfolio_id, report_date)
    base_nav = prev.nav if prev else 1.0
    nav = base_nav * (1 + daily_return)
    cumulative_return = nav - 1.0

    asset_snapshot = None
    if page2 and page2.get("asset_performances"):
        asset_snapshot = json.dumps(page2["asset_performances"], ensure_ascii=False)

    record = get_daily_record(db, user_id, portfolio_id, report_date)
    if record:
        record.daily_return = daily_return
        record.nav = nav
        record.cumulative_return = cumulative_return
        record.report_id = report_id
        record.asset_snapshot = asset_snapshot
    else:
        record = PaperTradingDailyRecord(
            user_id=user_id,
            portfolio_id=portfolio_id,
            record_date=report_date,
            daily_return=daily_return,
            nav=nav,
            cumulative_return=cumulative_return,
            report_id=report_id,
            asset_snapshot=asset_snapshot,
        )
        db.add(record)

    db.commit()
    db.refresh(record)
    return record


def list_daily_records(
    db: Session,
    user_id: int,
    portfolio_id: int | None,
    start_date: str | None = None,
    end_date: str | None = None,
    skip: int = 0,
    limit: int = 365,
):
    """查询每日累计收益记录."""
    query = (
        db.query(PaperTradingDailyRecord)
        .filter(
            PaperTradingDailyRecord.user_id == user_id,
            PaperTradingDailyRecord.portfolio_id == portfolio_id,
        )
    )
    if start_date:
        query = query.filter(PaperTradingDailyRecord.record_date >= start_date)
    if end_date:
        query = query.filter(PaperTradingDailyRecord.record_date <= end_date)
    return (
        query.order_by(PaperTradingDailyRecord.record_date.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_latest_daily_record(db: Session, user_id: int, portfolio_id: int | None):
    """获取最新一日的模拟盘记录."""
    return (
        db.query(PaperTradingDailyRecord)
        .filter(
            PaperTradingDailyRecord.user_id == user_id,
            PaperTradingDailyRecord.portfolio_id == portfolio_id,
        )
        .order_by(PaperTradingDailyRecord.record_date.desc())
        .first()
    )


def get_monthly_stat(db: Session, user_id: int, portfolio_id: int | None, year_month: str):
    return (
        db.query(PaperTradingMonthlyStat)
        .filter(
            PaperTradingMonthlyStat.user_id == user_id,
            PaperTradingMonthlyStat.portfolio_id == portfolio_id,
            PaperTradingMonthlyStat.year_month == year_month,
        )
        .first()
    )


def generate_monthly_stat(
    db: Session,
    user_id: int,
    portfolio_id: int | None,
    year_month: str,
):
    """统计指定自然月的月度收益率."""
    records = (
        db.query(PaperTradingDailyRecord)
        .filter(
            PaperTradingDailyRecord.user_id == user_id,
            PaperTradingDailyRecord.portfolio_id == portfolio_id,
            PaperTradingDailyRecord.record_date.like(f"{year_month}%"),
        )
        .order_by(PaperTradingDailyRecord.record_date.asc())
        .all()
    )

    if not records:
        return None

    start_nav = records[0].nav
    end_record = records[-1]
    end_nav = end_record.nav

    monthly_return = (end_nav / start_nav) - 1.0 if start_nav else 0.0

    stat = get_monthly_stat(db, user_id, portfolio_id, year_month)
    if stat:
        stat.monthly_return = monthly_return
        stat.cumulative_return_at_month_end = end_record.cumulative_return
        stat.record_count = len(records)
    else:
        stat = PaperTradingMonthlyStat(
            user_id=user_id,
            portfolio_id=portfolio_id,
            year_month=year_month,
            monthly_return=monthly_return,
            cumulative_return_at_month_end=end_record.cumulative_return,
            record_count=len(records),
        )
        db.add(stat)

    db.commit()
    db.refresh(stat)
    return stat


def list_monthly_stats(
    db: Session,
    user_id: int,
    portfolio_id: int | None,
    skip: int = 0,
    limit: int = 120,
):
    """查询月度统计."""
    return (
        db.query(PaperTradingMonthlyStat)
        .filter(
            PaperTradingMonthlyStat.user_id == user_id,
            PaperTradingMonthlyStat.portfolio_id == portfolio_id,
        )
        .order_by(PaperTradingMonthlyStat.year_month.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def sync_all_users_daily_records(db: Session, report_date: str | None = None):
    """遍历所有活跃用户与其当前激活组合，从最新日报同步模拟盘记录."""
    from app.models.user import User
    from app.models.portfolio import Portfolio
    from app.models.operation_log import MarketReport

    if report_date is None:
        report_date = _today_str()

    users = db.query(User).filter(User.is_active == True).all()
    results = {"created": 0, "errors": []}

    for user in users:
        try:
            portfolio = (
                db.query(Portfolio)
                .filter(
                    Portfolio.user_id == user.id,
                    Portfolio.is_active == True,
                )
                .order_by(Portfolio.updated_at.desc())
                .first()
            )
            portfolio_id = portfolio.id if portfolio else None

            report = (
                db.query(MarketReport)
                .filter(
                    MarketReport.user_id == user.id,
                    MarketReport.portfolio_id == portfolio_id,
                    MarketReport.report_type == "daily",
                    MarketReport.report_date == report_date,
                )
                .order_by(MarketReport.created_at.desc())
                .first()
            )

            if not report:
                continue

            sync_daily_record_from_report(
                db,
                user_id=user.id,
                portfolio_id=portfolio_id,
                report_id=report.id,
                report_date=report_date,
                page2=report.page2_portfolio_performance,
            )
            results["created"] += 1
        except Exception as e:
            results["errors"].append({"user_id": user.id, "error": str(e)})
            db.rollback()

    return results


def generate_all_users_monthly_stats(db: Session, year_month: str | None = None):
    """为所有活跃用户生成指定月份的月度统计；默认上一个月."""
    from app.models.user import User
    from app.models.portfolio import Portfolio

    if year_month is None:
        today = datetime.date.today()
        first_day = today.replace(day=1)
        prev_month = first_day - datetime.timedelta(days=1)
        year_month = prev_month.strftime("%Y-%m")

    users = db.query(User).filter(User.is_active == True).all()
    results = {"created": 0, "errors": []}

    for user in users:
        try:
            portfolio = (
                db.query(Portfolio)
                .filter(
                    Portfolio.user_id == user.id,
                    Portfolio.is_active == True,
                )
                .order_by(Portfolio.updated_at.desc())
                .first()
            )
            portfolio_id = portfolio.id if portfolio else None

            stat = generate_monthly_stat(db, user.id, portfolio_id, year_month)
            if stat:
                results["created"] += 1
        except Exception as e:
            results["errors"].append({"user_id": user.id, "error": str(e)})
            db.rollback()

    return results
