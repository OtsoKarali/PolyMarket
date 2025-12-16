"""Polymarket-specific data normalization functions."""

from datetime import datetime
from typing import Any, Dict

from dateutil.parser import parse as parse_date


def normalize_market_from_raw(raw: Dict[str, Any], source: str) -> Dict[str, Any]:
    """
    Normalize raw Polymarket market data to standard schema.

    ASSUMPTION: Raw data structure. Adjust based on actual API response.
    """
    # Extract fields with safe defaults
    market_id = str(raw.get("id", ""))
    question = raw.get("question", "")
    description = raw.get("description")
    end_date = _parse_datetime(raw.get("endDate"))
    resolution_source = raw.get("resolutionSource")
    category = raw.get("category")
    tags = raw.get("tags", [])

    # Financial metrics
    liquidity = _parse_float(raw.get("liquidity"))
    volume_24h = _parse_float(raw.get("volume24h"))

    # Timestamps
    created_at = _parse_datetime(raw.get("createdAt"))
    updated_at = _parse_datetime(raw.get("updatedAt"))

    return {
        "market_id": market_id,
        "source": source,
        "question": question,
        "description": description,
        "end_date": end_date,
        "resolution_source": resolution_source,
        "category": category,
        "tags": tags,
        "liquidity": liquidity,
        "volume_24h": volume_24h,
        "created_at": created_at,
        "updated_at": updated_at,
        "raw_data": raw,  # Preserve original for audit
    }


def normalize_trade_from_raw(raw: Dict[str, Any], source: str) -> Dict[str, Any]:
    """Normalize raw Polymarket trade data to standard schema."""
    trade_id = str(raw.get("id", ""))
    market_id = str(raw.get("marketId", ""))
    outcome_id = str(raw.get("outcomeId", ""))
    price = _parse_float(raw.get("price"), 0.0)
    quantity = _parse_float(raw.get("quantity"), 0.0)
    timestamp = _parse_datetime(raw.get("timestamp"))
    side = raw.get("side")  # 'buy' or 'sell'
    taker_address = raw.get("takerAddress")
    maker_address = raw.get("makerAddress")
    transaction_hash = raw.get("transactionHash")

    return {
        "trade_id": trade_id,
        "source": source,
        "market_id": market_id,
        "outcome_id": outcome_id,
        "price": price,
        "quantity": quantity,
        "timestamp": timestamp,
        "side": side,
        "taker_address": taker_address,
        "maker_address": maker_address,
        "transaction_hash": transaction_hash,
        "raw_data": raw,
    }


def normalize_price_snapshot_from_raw(raw: Dict[str, Any], source: str) -> Dict[str, Any]:
    """Normalize raw Polymarket price snapshot data to standard schema."""
    market_id = str(raw.get("marketId", ""))
    outcome_id = str(raw.get("outcomeId", ""))
    timestamp = _parse_datetime(raw.get("timestamp")) or datetime.utcnow()
    implied_probability = _parse_float(raw.get("impliedProbability"), 0.0)
    bid = _parse_float(raw.get("bid"))
    ask = _parse_float(raw.get("ask"))
    mid = _parse_float(raw.get("mid"))
    spread = _parse_float(raw.get("spread"))
    volume_24h = _parse_float(raw.get("volume24h"))
    liquidity = _parse_float(raw.get("liquidity"))

    # Calculate mid and spread if not provided
    if mid is None and bid is not None and ask is not None:
        mid = (bid + ask) / 2.0
    if spread is None and bid is not None and ask is not None:
        spread = ask - bid

    return {
        "market_id": market_id,
        "source": source,
        "outcome_id": outcome_id,
        "timestamp": timestamp,
        "implied_probability": implied_probability,
        "bid": bid,
        "ask": ask,
        "mid": mid,
        "spread": spread,
        "volume_24h": volume_24h,
        "liquidity": liquidity,
        "raw_data": raw,
    }


def _parse_datetime(value: Any) -> Optional[datetime]:
    """Safely parse datetime from various formats."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return parse_date(value)
        except (ValueError, TypeError):
            return None
    return None


def _parse_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    """Safely parse float."""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

