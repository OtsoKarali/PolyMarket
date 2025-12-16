"""Unit tests for Polymarket client."""

import json
from unittest.mock import MagicMock, patch

import httpx
import pytest

from src.connectors.polymarket.client import PolymarketClient


@pytest.fixture
def mock_response():
    """Mock API response."""
    return {
        "data": {
            "markets": {
                "data": [
                    {
                        "id": "test-market-1",
                        "question": "Will it rain tomorrow?",
                        "description": "Test market",
                        "endDate": "2024-12-31T00:00:00Z",
                        "liquidity": 1000.0,
                        "volume24h": 500.0,
                    }
                ],
                "nextCursor": None,
            }
        }
    }


@pytest.fixture
def client():
    """Create test client."""
    return PolymarketClient(rate_limit_per_second=100.0)


def test_get_markets(client, mock_response):
    """Test fetching markets."""
    with patch.object(client.client, "request") as mock_request:
        mock_request.return_value.status_code = 200
        mock_request.return_value.json.return_value = mock_response
        mock_request.return_value.raise_for_status = MagicMock()

        result = client.get_markets(limit=10)

        assert "data" in result
        assert len(result["data"]) == 1
        assert result["data"][0]["id"] == "test-market-1"


def test_rate_limiting(client):
    """Test rate limiting enforcement."""
    import time

    start = time.time()
    # Make two requests quickly
    with patch.object(client.client, "request") as mock_request:
        mock_request.return_value.status_code = 200
        mock_request.return_value.json.return_value = {"data": {"markets": {"data": []}}}
        mock_request.return_value.raise_for_status = MagicMock()

        client.get_markets()
        client.get_markets()

    # Should have taken at least min_request_interval
    elapsed = time.time() - start
    assert elapsed >= client._min_request_interval


def test_retry_on_network_error(client):
    """Test retry logic on network errors."""
    with patch.object(client.client, "request") as mock_request:
        # First two calls fail, third succeeds
        mock_request.side_effect = [
            httpx.NetworkError("Connection failed"),
            httpx.NetworkError("Connection failed"),
            MagicMock(
                status_code=200,
                json=lambda: {"data": {"markets": {"data": []}}},
                raise_for_status=MagicMock(),
            ),
        ]

        result = client.get_markets()
        assert mock_request.call_count == 3
        assert "data" in result

