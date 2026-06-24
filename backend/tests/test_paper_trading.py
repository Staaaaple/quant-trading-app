from datetime import date

from tests.conftest import TestingSessionLocal
from app.models.user import User
from app.models.portfolio import Portfolio
from app.models.operation_log import MarketReport
from app.services import paper_trading_service


def _setup_user_and_portfolio(db):
    user = User(name="测试用户", is_active=True)
    db.add(user)
    db.commit()
    db.refresh(user)
    portfolio = Portfolio(user_id=user.id, name="测试组合", is_active=True)
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)
    return user, portfolio


def test_sync_daily_record_from_report(client):
    db = TestingSessionLocal()
    user, portfolio = _setup_user_and_portfolio(db)

    report = MarketReport(
        user_id=user.id,
        portfolio_id=portfolio.id,
        report_type="daily",
        report_date="2024-01-02",
        page2_portfolio_performance={
            "portfolio_return": 0.01,
            "asset_performances": [
                {"symbol": "000001", "daily_return": 0.01, "contribution": 0.01}
            ],
        },
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    record = paper_trading_service.sync_daily_record_from_report(
        db,
        user_id=user.id,
        portfolio_id=portfolio.id,
        report_id=report.id,
        report_date="2024-01-02",
        page2=report.page2_portfolio_performance,
    )

    assert record.daily_return == 0.01
    assert abs(record.nav - 1.01) < 1e-9
    assert abs(record.cumulative_return - 0.01) < 1e-9


def test_cumulative_return_compounding(client):
    db = TestingSessionLocal()
    user, portfolio = _setup_user_and_portfolio(db)

    for i, (d, ret) in enumerate([
        ("2024-01-02", 0.01),
        ("2024-01-03", 0.02),
        ("2024-01-04", -0.005),
    ]):
        report = MarketReport(
            user_id=user.id,
            portfolio_id=portfolio.id,
            report_type="daily",
            report_date=d,
            page2_portfolio_performance={"portfolio_return": ret},
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        paper_trading_service.sync_daily_record_from_report(
            db,
            user_id=user.id,
            portfolio_id=portfolio.id,
            report_id=report.id,
            report_date=d,
            page2=report.page2_portfolio_performance,
        )

    latest = paper_trading_service.get_latest_daily_record(db, user.id, portfolio.id)
    expected_nav = 1.01 * 1.02 * 0.995
    assert abs(latest.nav - expected_nav) < 1e-9
    assert abs(latest.cumulative_return - (expected_nav - 1)) < 1e-9


def test_generate_monthly_stat(client):
    db = TestingSessionLocal()
    user, portfolio = _setup_user_and_portfolio(db)

    for d, ret in [
        ("2024-01-02", 0.01),
        ("2024-01-03", 0.02),
        ("2024-01-31", -0.005),
    ]:
        report = MarketReport(
            user_id=user.id,
            portfolio_id=portfolio.id,
            report_type="daily",
            report_date=d,
            page2_portfolio_performance={"portfolio_return": ret},
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        paper_trading_service.sync_daily_record_from_report(
            db,
            user_id=user.id,
            portfolio_id=portfolio.id,
            report_id=report.id,
            report_date=d,
            page2=report.page2_portfolio_performance,
        )

    stat = paper_trading_service.generate_monthly_stat(db, user.id, portfolio.id, "2024-01")
    start_nav = 1.01
    end_nav = 1.01 * 1.02 * 0.995
    assert abs(stat.monthly_return - (end_nav / start_nav - 1)) < 1e-9
    assert stat.record_count == 3


def test_api_daily_records(client):
    db = TestingSessionLocal()
    user, portfolio = _setup_user_and_portfolio(db)

    report = MarketReport(
        user_id=user.id,
        portfolio_id=portfolio.id,
        report_type="daily",
        report_date="2024-01-02",
        page2_portfolio_performance={"portfolio_return": 0.005},
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    paper_trading_service.sync_daily_record_from_report(
        db,
        user_id=user.id,
        portfolio_id=portfolio.id,
        report_id=report.id,
        report_date="2024-01-02",
        page2=report.page2_portfolio_performance,
    )

    resp = client.get("/api/v1/paper-trading/daily-records", headers={"X-User-Id": str(user.id)})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["daily_return"] == 0.005


def test_api_monthly_stats(client):
    db = TestingSessionLocal()
    user, portfolio = _setup_user_and_portfolio(db)

    report = MarketReport(
        user_id=user.id,
        portfolio_id=portfolio.id,
        report_type="daily",
        report_date="2024-01-02",
        page2_portfolio_performance={"portfolio_return": 0.01},
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    paper_trading_service.sync_daily_record_from_report(
        db,
        user_id=user.id,
        portfolio_id=portfolio.id,
        report_id=report.id,
        report_date="2024-01-02",
        page2=report.page2_portfolio_performance,
    )
    paper_trading_service.generate_monthly_stat(db, user.id, portfolio.id, "2024-01")

    resp = client.get("/api/v1/paper-trading/monthly-stats", headers={"X-User-Id": str(user.id)})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["year_month"] == "2024-01"
