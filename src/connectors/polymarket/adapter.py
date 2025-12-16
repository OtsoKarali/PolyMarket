"""Polymarket adapter implementing MarketAdapter interface."""

from datetime import datetime
from typing import Any, Dict, Optional

from src.core.interfaces import MarketAdapter
from src.connectors.polymarket.client import PolymarketClient
from src.connectors.polymarket.schemas import (
    normalize_market_from_raw,
    normalize_trade_from_raw,
    normalize_price_snapshot_from_raw,
)


class PolymarketAdapter(MarketAdapter):
    """Polymarket implementation of MarketAdapter."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        rate_limit_per_second: float = 10.0,
    ):
        """Initialize Polymarket adapter."""
        self.client = PolymarketClient(
            api_key=api_key,
            rate_limit_per_second=rate_limit_per_second,
        )

    @property
    def source_name(self) -> str:
        """Return source identifier."""
        return "polymarket"

    def fetch_markets(
        self,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Fetch market metadata from Polymarket."""
        return self.client.get_markets(limit=limit, cursor=cursor)

    def fetch_trades(
        self,
        market_id: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Fetch trades from Polymarket."""
        since_str = since.isoformat() if since else None
        return self.client.get_trades(
            market_id=market_id,
            since=since_str,
            limit=limit,
            cursor=cursor,
        )

    def fetch_price_snapshots(
        self,
        market_id: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Fetch price snapshots from Polymarket."""
        since_str = since.isoformat() if since else None
        return self.client.get_price_snapshots(market_id=market_id, since=since_str)

    def normalize_market(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize raw Polymarket market data."""
        return normalize_market_from_raw(raw, source=self.source_name)

    def normalize_trade(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize raw Polymarket trade data."""
        return normalize_trade_from_raw(raw, source=self.source_name)

    def normalize_price_snapshot(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize raw Polymarket price snapshot data."""
        return normalize_price_snapshot_from_raw(raw, source=self.source_name)

    def close(self):
        """Close underlying client."""
        self.client.close()

