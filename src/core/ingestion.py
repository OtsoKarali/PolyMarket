"""Core ingestion engine orchestrating data collection."""

from datetime import datetime
from typing import List, Optional

from src.core.interfaces import MarketAdapter, StorageBackend
from src.core.observability import log_duration, logger, metrics


class IngestionEngine:
    """Orchestrates data ingestion from market adapters to storage."""

    def __init__(
        self,
        adapter: MarketAdapter,
        storage: StorageBackend,
    ):
        """Initialize ingestion engine."""
        self.adapter = adapter
        self.storage = storage
        self.source = adapter.source_name

    def ingest_markets(
        self,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
        store_raw: bool = True,
    ) -> int:
        """
        Ingest market metadata.

        Returns:
            Number of markets ingested
        """
        with log_duration("ingestion.markets", source=self.source):
            try:
                # Fetch from adapter
                response = self.adapter.fetch_markets(limit=limit, cursor=cursor)
                raw_markets = response.get("data", [])
                next_cursor = response.get("nextCursor")

                if not raw_markets:
                    logger.info("ingestion.markets.empty", source=self.source)
                    return 0

                # Store raw responses if requested
                if store_raw:
                    request_id = self.storage.store_raw(
                        source=self.source,
                        endpoint="markets",
                        response_data={"data": raw_markets, "cursor": cursor},
                    )
                    logger.debug("ingestion.markets.raw_stored", request_id=request_id, count=len(raw_markets))

                # Normalize and store
                normalized = [self.adapter.normalize_market(m) for m in raw_markets]
                count = self.storage.store_markets(normalized)
                metrics.increment("ingestion.markets.stored", value=count, tags={"source": self.source})

                logger.info(
                    "ingestion.markets.complete",
                    source=self.source,
                    fetched=len(raw_markets),
                    stored=count,
                    next_cursor=next_cursor,
                )

                # Recursively fetch next page if cursor exists
                if next_cursor and (limit is None or len(raw_markets) == limit):
                    additional = self.ingest_markets(limit=limit, cursor=next_cursor, store_raw=store_raw)
                    count += additional

                return count

            except Exception as e:
                logger.error("ingestion.markets.error", error=str(e), error_type=type(e).__name__)
                metrics.increment("ingestion.markets.errors", tags={"source": self.source})
                raise

    def ingest_trades(
        self,
        market_id: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
        store_raw: bool = True,
    ) -> int:
        """
        Ingest trades.

        Args:
            market_id: Filter by market (None = all)
            since: Only fetch trades after this timestamp
            limit: Max trades per request
            cursor: Pagination cursor
            store_raw: Whether to store raw API responses

        Returns:
            Number of trades ingested
        """
        with log_duration("ingestion.trades", source=self.source, market_id=market_id):
            try:
                # Use checkpoint if since not provided
                if since is None:
                    checkpoint = self.storage.get_latest_checkpoint(self.source, "trades")
                    if checkpoint:
                        since = checkpoint
                        logger.info("ingestion.trades.using_checkpoint", checkpoint=checkpoint.isoformat())

                response = self.adapter.fetch_trades(
                    market_id=market_id,
                    since=since,
                    limit=limit,
                    cursor=cursor,
                )
                raw_trades = response.get("data", [])
                next_cursor = response.get("nextCursor")

                if not raw_trades:
                    logger.info("ingestion.trades.empty", source=self.source, market_id=market_id)
                    return 0

                if store_raw:
                    request_id = self.storage.store_raw(
                        source=self.source,
                        endpoint="trades",
                        response_data={"data": raw_trades, "cursor": cursor},
                    )
                    logger.debug("ingestion.trades.raw_stored", request_id=request_id, count=len(raw_trades))

                normalized = [self.adapter.normalize_trade(t) for t in raw_trades]
                count = self.storage.store_trades(normalized)

                # Update checkpoint to latest trade timestamp
                if normalized:
                    latest_timestamp = max(t["timestamp"] for t in normalized if t.get("timestamp"))
                    if latest_timestamp:
                        self.storage.update_checkpoint(self.source, "trades", latest_timestamp)

                metrics.increment("ingestion.trades.stored", value=count, tags={"source": self.source})

                logger.info(
                    "ingestion.trades.complete",
                    source=self.source,
                    fetched=len(raw_trades),
                    stored=count,
                    next_cursor=next_cursor,
                )

                # Fetch next page
                if next_cursor and (limit is None or len(raw_trades) == limit):
                    additional = self.ingest_trades(
                        market_id=market_id,
                        since=since,
                        limit=limit,
                        cursor=next_cursor,
                        store_raw=store_raw,
                    )
                    count += additional

                return count

            except Exception as e:
                logger.error("ingestion.trades.error", error=str(e), error_type=type(e).__name__)
                metrics.increment("ingestion.trades.errors", tags={"source": self.source})
                raise

    def ingest_price_snapshots(
        self,
        market_id: Optional[str] = None,
        since: Optional[datetime] = None,
        store_raw: bool = True,
    ) -> int:
        """Ingest price/probability snapshots."""
        with log_duration("ingestion.prices", source=self.source, market_id=market_id):
            try:
                response = self.adapter.fetch_price_snapshots(market_id=market_id, since=since)
                raw_snapshots = response.get("data", [])

                if not raw_snapshots:
                    logger.info("ingestion.prices.empty", source=self.source, market_id=market_id)
                    return 0

                if store_raw:
                    request_id = self.storage.store_raw(
                        source=self.source,
                        endpoint="price_snapshots",
                        response_data={"data": raw_snapshots},
                    )
                    logger.debug("ingestion.prices.raw_stored", request_id=request_id, count=len(raw_snapshots))

                normalized = [self.adapter.normalize_price_snapshot(s) for s in raw_snapshots]
                count = self.storage.store_price_snapshots(normalized)

                # Update checkpoint
                if normalized:
                    latest_timestamp = max(s["timestamp"] for s in normalized if s.get("timestamp"))
                    if latest_timestamp:
                        self.storage.update_checkpoint(self.source, "price_snapshots", latest_timestamp)

                metrics.increment("ingestion.prices.stored", value=count, tags={"source": self.source})

                logger.info(
                    "ingestion.prices.complete",
                    source=self.source,
                    fetched=len(raw_snapshots),
                    stored=count,
                )

                return count

            except Exception as e:
                logger.error("ingestion.prices.error", error=str(e), error_type=type(e).__name__)
                metrics.increment("ingestion.prices.errors", tags={"source": self.source})
                raise

