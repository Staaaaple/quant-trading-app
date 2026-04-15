def test_create_strategy(client):
    payload = {
        "strategy_id": "s001",
        "name": "Test Strategy",
        "description": "A test strategy",
        "code": "print('hello')",
    }
    resp = client.post("/api/v1/strategies/", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["strategy_id"] == "s001"
    assert data["name"] == "Test Strategy"


def test_create_strategy_conflict(client):
    payload = {
        "strategy_id": "s001",
        "name": "Test Strategy",
        "code": "print('hello')",
    }
    resp = client.post("/api/v1/strategies/", json=payload)
    assert resp.status_code == 201
    resp2 = client.post("/api/v1/strategies/", json=payload)
    assert resp2.status_code == 409


def test_list_strategies(client):
    resp = client.get("/api/v1/strategies/")
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_strategy(client):
    payload = {
        "strategy_id": "s002",
        "name": "Get Me",
        "code": "pass",
    }
    client.post("/api/v1/strategies/", json=payload)
    resp = client.get("/api/v1/strategies/s002")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Get Me"


def test_get_strategy_not_found(client):
    resp = client.get("/api/v1/strategies/no-such-id")
    assert resp.status_code == 404


def test_update_strategy(client):
    payload = {
        "strategy_id": "s003",
        "name": "Old Name",
        "code": "pass",
    }
    client.post("/api/v1/strategies/", json=payload)
    resp = client.put("/api/v1/strategies/s003", json={"name": "New Name"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "New Name"


def test_delete_strategy(client):
    payload = {
        "strategy_id": "s004",
        "name": "Delete Me",
        "code": "pass",
    }
    client.post("/api/v1/strategies/", json=payload)
    resp = client.delete("/api/v1/strategies/s004")
    assert resp.status_code == 204
    resp2 = client.get("/api/v1/strategies/s004")
    assert resp2.status_code == 404
