"""
Tests for the stocks endpoints against the real SQLite database.
"""
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_list_stocks():
    response = client.get("/api/v1/stocks")
    assert response.status_code == 200
    data = response.json()
    assert "stocks" in data
    assert isinstance(data["stocks"], list)


def test_get_stock_detail():
    # Use the first stock returned by the list endpoint to test the detail endpoint.
    list_response = client.get("/api/v1/stocks")
    assert list_response.status_code == 200
    stocks = list_response.json()["stocks"]

    if not stocks:
        # Empty database: skip the detail test.
        return

    ticker = stocks[0]["ticker"]
    detail_response = client.get(f"/api/v1/stocks/{ticker}")
    assert detail_response.status_code == 200

    data = detail_response.json()
    assert data["ticker"] == ticker
    assert "price_count" in data
    assert "dividend_count" in data


def test_get_stock_not_found():
    response = client.get("/api/v1/stocks/XXX")
    assert response.status_code == 404
