import uuid
from unittest.mock import patch, MagicMock

import pandas as pd

from app.services.backtest_service import _normalize_akquant_df


def test_normalize_akquant_df_preserves_extra_columns():
    """验证 _normalize_akquant_df 能正确映射核心列并保留扩展字段."""
    raw = pd.DataFrame({
        "日期": ["2024-01-02", "2024-01-03"],
        "开盘": [10.0, 10.5],
        "收盘": [10.2, 10.3],
        "最高": [10.5, 10.6],
        "最低": [9.9, 10.2],
        "成交量": [10000, 15000],
        "成交额": [102000.0, 154500.0],
        "换手率": [0.5, 0.75],
        "市盈率": [12.5, 12.6],
        "MA5": [10.1, 10.15],
        "未知名": [99.0, 100.0],
    })
    df = _normalize_akquant_df(raw, symbol="000001")

    assert isinstance(df.index, pd.DatetimeIndex)
    assert "open" in df.columns
    assert "high" in df.columns
    assert "low" in df.columns
    assert "close" in df.columns
    assert "volume" in df.columns
    assert "symbol" in df.columns
    assert df["symbol"].iloc[0] == "000001"

    # 扩展列应被保留
    assert "amount" in df.columns
    assert "turnover_rate" in df.columns
    assert "pe" in df.columns
    assert "ma5" in df.columns

    # 未映射的数值列也应被保留（供 bar.extra 使用）
    assert "未知名" in df.columns

    # 核心和扩展字段应为数值类型
    for col in ["open", "high", "low", "close", "volume", "amount", "turnover_rate", "pe", "ma5", "未知名"]:
        assert pd.api.types.is_numeric_dtype(df[col]), f"{col} 不是数值类型"


def test_create_backtest(client):
    # 先创建策略
    strategy_payload = {
        "strategy_id": "s_bt_001",
        "name": "Backtest Strategy",
        "code": "from akquant import Strategy\nclass S(Strategy):\n    def on_bar(self, bar): pass",
    }
    client.post("/api/v1/strategies/", json=strategy_payload)

    payload = {
        "backtest_id": "bt001",
        "strategy_id": "s_bt_001",
        "start_date": "2024-01-01",
        "end_date": "2024-03-01",
        "initial_cash": 100000.0,
    }
    resp = client.post("/api/v1/backtests/", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["backtest_id"] == "bt001"
    assert data["status"] == "pending"


def test_list_backtests(client):
    resp = client.get("/api/v1/backtests/")
    assert resp.status_code == 200
    assert resp.json() == []


def test_run_backtest_mocked(client):
    # 创建策略
    strategy_payload = {
        "strategy_id": "s_bt_002",
        "name": "Backtest Strategy 2",
        "code": "from akquant import Strategy\nclass S(Strategy):\n    def on_bar(self, bar): pass",
    }
    client.post("/api/v1/strategies/", json=strategy_payload)

    # 创建回测记录
    backtest_payload = {
        "backtest_id": "bt002",
        "strategy_id": "s_bt_002",
        "start_date": "2024-01-01",
        "end_date": "2024-03-01",
        "initial_cash": 100000.0,
    }
    client.post("/api/v1/backtests/", json=backtest_payload)

    # Mock fetch_stock_data 和 akquant.run_backtest
    mock_df = MagicMock()
    mock_result = MagicMock()
    mock_metrics_raw = MagicMock()
    mock_metrics_raw.total_return = 0.05
    mock_metrics_raw.sharpe_ratio = 1.2
    mock_metrics_raw.max_drawdown = -0.02
    mock_metrics_raw.annualized_return = 0.15
    mock_metrics_raw.volatility = 0.1
    mock_metrics_raw.calmar_ratio = 7.5
    mock_metrics_raw.sortino_ratio = 1.5
    mock_metrics_raw.win_rate = 0.55
    mock_metrics_raw.total_return_pct = 5.0
    mock_metrics_raw.max_drawdown_pct = -2.0
    mock_metrics_raw.max_drawdown_value = -2000.0
    mock_metrics_raw.exposure_time_pct = 80.0
    mock_metrics_raw.total_bars = 60
    mock_metrics_raw.duration = 60
    mock_metrics_raw.initial_market_value = 100000.0
    mock_metrics_raw.end_market_value = 105000.0

    mock_metrics = MagicMock()
    mock_metrics._raw = mock_metrics_raw
    mock_result.metrics = mock_metrics

    with patch("app.services.backtest_service.fetch_stock_data", return_value=mock_df):
        with patch("app.services.backtest_service.akquant.run_backtest", return_value=mock_result):
            resp = client.post(
                "/api/v1/backtests/bt002/run",
                json={
                    "symbols": ["000001"],
                    "start_date": "2024-01-01",
                    "end_date": "2024-03-01",
                    "initial_cash": 100000.0,
                },
            )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] == "success"
    assert data["metrics"]["total_return"] == 0.05
    assert data["metrics"]["sharpe_ratio"] == 1.2
