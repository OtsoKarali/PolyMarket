"""Abstract interfaces for market adapters and data processing."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Iterator, List, Optional, Protocol

from pydantic import BaseModel


class MarketAdapter(ABC):
    """Abstract interface for market-specific data adapters."""

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Return the market source identifier (e.g., 'polymarket')."""
        pass

    @abstractmethod
    def fetch_markets(
        self,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Fetch market metadata.

        Args:
            limit: Maximum number of markets to return
            cursor: Pagination cursor for incremental fetching

        Returns:
            Dict with 'data' (list of markets) and 'next_cursor' (optional)
        """
        pass

    @abstractmethod
    def fetch_trades(
        self,
        market_id: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Fetch trade/fill data.

        Args:
            market_id: Filter by specific market (None = all)
            since: Only fetch trades after this timestamp
            limit: Maximum number of trades
            cursor: Pagination cursor

        Returns:
            Dict with 'data' (list of trades) and 'next_cursor' (optional)
        """
        pass

    @abstractmethod
    def fetch_price_snapshots(
        self,
        market_id: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Fetch current price/probability snapshots.

        Args:
            market_id: Filter by specific market
            since: Only fetch snapshots after this timestamp
            limit: Maximum number of snapshots

        Returns:
            Dict with 'data' (list of price snapshots)
        """
        pass

    @abstractmethod
    def normalize_market(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """Transform raw market data to normalized schema."""
        pass

    @abstractmethod
    def normalize_trade(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """Transform raw trade data to normalized schema."""
        pass

    @abstractmethod
    def normalize_price_snapshot(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """Transform raw price data to normalized schema."""
        pass


class DataFetcher(Protocol):
    """Protocol for fetching raw API data with rate limiting and retries."""

    def fetch(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Fetch data from API endpoint with automatic retries and rate limiting."""
        ...


class StorageBackend(ABC):
    """Abstract interface for storage backends."""

    @abstractmethod
    def store_raw(
        self,
        source: str,
        endpoint: str,
        response_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Store raw API response for auditability.

        Returns:
            Request ID for tracking
        """
        pass

    @abstractmethod
    def store_markets(self, markets: List[Dict[str, Any]]) -> int:
        """Store normalized market data. Returns number of rows inserted/updated."""
        pass

    @abstractmethod
    def store_trades(self, trades: List[Dict[str, Any]]) -> int:
        """Store normalized trade data. Returns number of rows inserted/updated."""
        pass

    @abstractmethod
    def store_price_snapshots(self, snapshots: List[Dict[str, Any]]) -> int:
        """Store normalized price snapshot data. Returns number of rows inserted/updated."""
        pass

    @abstractmethod
    def get_latest_checkpoint(
        self,
        source: str,
        data_type: str,
    ) -> Optional[datetime]:
        """Get the latest successful ingestion timestamp for incremental sync."""
        pass

    @abstractmethod
    def update_checkpoint(
        self,
        source: str,
        data_type: str,
        timestamp: datetime,
    ) -> None:
        """Update the checkpoint after successful ingestion."""
        pass


class CheckpointManager(ABC):
    """Manages incremental sync state."""

    @abstractmethod
    def get_checkpoint(
        self,
        source: str,
        data_type: str,
    ) -> Optional[datetime]:
        """Get the last successful sync timestamp."""
        pass

    @abstractmethod
    def save_checkpoint(
        self,
        source: str,
        data_type: str,
        timestamp: datetime,
    ) -> None:
        """Save checkpoint after successful sync."""
        pass

