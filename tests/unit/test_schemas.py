"""Unit tests for data normalization schemas."""

from datetime import datetime

import pytest

from src.connectors.polymarket.schemas import (
    normalize_market_from_raw,
    normalize_price_snapshot_from_raw,
    normalize_trade_from_raw,
)


def test_normalize_market():
    """Test market normalization."""
    raw = {
        "id": "market-123",
        "question": "Test question?",
        "description": "Test description",
        "endDate": "2024-12-31T00:00:00Z",
        "liquidity": "1000.5",
        "volume24h": "500.25",
        "category": "politics",
        "tags": ["test", "example"],
    }

    normalized = normalize_market_from_raw(raw, source="polymarket")

    assert normalized["market_id"] == "market-123"
    assert normalized["source"] == "polymarket"
    assert normalized["question"] == "Test question?"
    assert normalized["liquidity"] == 1000.5
    assert normalized["volume_24h"] == 500.25
    assert normalized["raw_data"] == raw


def test_normalize_trade():
    """Test trade normalization."""
    raw = {
        "id": "trade-456",
        "marketId": "market-123",
        "outcomeId": "YES",
        "price": "0.65",
        "quantity": "100.0",
        "timestamp": "2024-01-15T10:30:00Z",
        "side": "buy",
    }

    normalized = normalize_trade_from_raw(raw, source="polymarket")

    assert normalized["trade_id"] == "trade-456"
    assert normalized["source"] == "polymarket"
    assert normalized["market_id"] == "market-123"
    assert normalized["outcome_id"] == "YES"
    assert normalized["price"] == 0.65
    assert normalized["quantity"] == 100.0
    assert normalized["side"] == "buy"


def test_normalize_price_snapshot():
    """Test price snapshot normalization."""
    raw = {
        "marketId": "market-123",
        "outcomeId": "YES",
        "timestamp": "2024-01-15T10:30:00Z",
        "impliedProbability": "0.65",
        "bid": "0.64",
        "ask": "0.66",
    }

    normalized = normalize_price_snapshot_from_raw(raw, source="polymarket")

    assert normalized["market_id"] == "market-123"
    assert normalized["outcome_id"] == "YES"
    assert normalized["implied_probability"] == 0.65
    assert normalized["bid"] == 0.64
    assert normalized["ask"] == 0.66
    # Should calculate mid and spread
    assert normalized["mid"] == 0.65
    assert normalized["spread"] == 0.02

