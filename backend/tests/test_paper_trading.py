import uuid
from unittest.mock import patch, MagicMock


def test_create_paper_trading_session(client):
    # 先创建策略
    strategy_payload = {
        "strategy_id": "s_pt_001",
        "name": "Paper Trading Strategy",
        "code": "from akquant import Strategy\nclass S(Strategy):\n    def on_bar(self, bar): pass",
    }
    client.post("/api/v1/strategies/", json=strategy_payload)

    payload = {
        "session_id": "pt001",
        "strategy_id": "s_pt_001",
        "symbols": ["000001"],
        "initial_cash": 100000.0,
        "start_date": "2024-01-01",
        "end_date": "2024-03-01",
    }
    resp = client.post("/api/v1/paper-trading/sessions", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["session_id"] == "pt001"
    assert data["strategy_id"] == "s_pt_001"
    assert data["symbols"] == ["000001"]
    assert data["status"] == "idle"


def test_list_paper_trading_sessions(client):
    resp = client.get("/api/v1/paper-trading/sessions")
    assert resp.status_code == 200
    assert resp.json() == []


def test_run_paper_trading_session_mocked(client):
    # 创建策略
    strategy_payload = {
        "strategy_id": "s_pt_002",
        "name": "Paper Trading Strategy 2",
        "code": "from akquant import Strategy\nclass S(Strategy):\n    def on_bar(self, bar): self.buy(symbol='000001', quantity=100)",
    }
    client.post("/api/v1/strategies/", json=strategy_payload)

    # 创建 session
    session_payload = {
        "session_id": "pt002",
        "strategy_id": "s_pt_002",
        "symbols": ["000001"],
        "initial_cash": 100000.0,
        "start_date": "2024-01-01",
        "end_date": "2024-01-10",
    }
    client.post("/api/v1/paper-trading/sessions", json=session_payload)

    # Mock 数据获取和 akquant
    mock_df = MagicMock()
    mock_order = MagicMock()
    mock_order.symbol = "000001"
    mock_order.side = "Buy"
    mock_order.quantity = 100.0
    mock_order.price = 10.2
    mock_order.status = "New"

    mock_result = MagicMock()
    mock_result.orders = [mock_order]
    mock_result.trades = []

    with patch("app.services.paper_trading_service.fetch_stock_data", return_value=mock_df):
        with patch("app.services.paper_trading_service.akquant.run_backtest", return_value=mock_result):
            resp = client.post("/api/v1/paper-trading/sessions/pt002/run")

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] == "success"

    # 验证信号已写入
    signals_resp = client.get(f"/api/v1/paper-trading/sessions/pt002")
    assert signals_resp.status_code == 200


def test_stop_paper_trading_session(client):
    strategy_payload = {
        "strategy_id": "s_pt_003",
        "name": "Paper Trading Strategy 3",
        "code": "from akquant import Strategy\nclass S(Strategy):\n    def on_bar(self, bar): pass",
    }
    client.post("/api/v1/strategies/", json=strategy_payload)

    session_payload = {
        "session_id": "pt003",
        "strategy_id": "s_pt_003",
        "symbols": ["000001"],
        "initial_cash": 100000.0,
    }
    client.post("/api/v1/paper-trading/sessions", json=session_payload)

    # 直接更新状态为 running 再 stop（使用测试数据库会话）
    from tests.conftest import TestingSessionLocal
    from app.services import paper_trading_service
    db = TestingSessionLocal()
    db_obj = paper_trading_service.get_session(db, "pt003")
    db_obj.status = "running"
    db.commit()
    db.close()

    resp = client.post("/api/v1/paper-trading/sessions/pt003/stop")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] == "stopped"
