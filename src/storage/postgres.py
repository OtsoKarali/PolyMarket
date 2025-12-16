"""PostgreSQL storage backend implementation."""

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from src.core.interfaces import StorageBackend
from src.core.observability import logger

Base = declarative_base()


# Table definitions
class RawApiResponse(Base):
    """Raw API response storage for auditability."""

    __tablename__ = "raw_api_responses"

    request_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source = Column(String(50), nullable=False, index=True)
    endpoint = Column(String(100), nullable=False)
    response_json = Column(JSON, nullable=False)
    status_code = Column(Integer)
    timestamp = Column(DateTime, default=func.now(), index=True)
    metadata = Column(JSON)

    __table_args__ = ({"schema": "prediction_markets"},)


class MarketTable(Base):
    """Normalized market metadata table."""

    __tablename__ = "markets"

    market_id = Column(String(255), nullable=False)
    source = Column(String(50), nullable=False)
    question = Column(Text, nullable=False)
    description = Column(Text)
    end_date = Column(DateTime)
    resolution_source = Column(String(255))
    category = Column(String(100))
    tags = Column(JSON)
    liquidity = Column(Float)
    volume_24h = Column(Float)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    raw_data = Column(JSON)

    __table_args__ = (
        UniqueConstraint("market_id", "source", name="uq_markets_id_source"),
        {"schema": "prediction_markets"},
    )


class MarketOutcomeTable(Base):
    """Market outcomes/tokens table."""

    __tablename__ = "market_outcomes"

    market_id = Column(String(255), nullable=False)
    source = Column(String(50), nullable=False)
    outcome_id = Column(String(255), nullable=False)
    outcome_name = Column(String(255), nullable=False)
    token_address = Column(String(255))
    created_at = Column(DateTime)

    __table_args__ = (
        UniqueConstraint("market_id", "outcome_id", "source", name="uq_outcomes"),
        {"schema": "prediction_markets"},
    )


class TradeTable(Base):
    """Normalized trades table."""

    __tablename__ = "trades"

    trade_id = Column(String(255), nullable=False)
    source = Column(String(50), nullable=False)
    market_id = Column(String(255), nullable=False, index=True)
    outcome_id = Column(String(255), nullable=False)
    price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    side = Column(String(10))
    taker_address = Column(String(255))
    maker_address = Column(String(255))
    transaction_hash = Column(String(255))
    raw_data = Column(JSON)

    __table_args__ = (
        UniqueConstraint("trade_id", "source", name="uq_trades_id_source"),
        {"schema": "prediction_markets"},
    )


class PriceSnapshotTable(Base):
    """Price/probability snapshot table."""

    __tablename__ = "price_snapshots"

    market_id = Column(String(255), nullable=False, index=True)
    source = Column(String(50), nullable=False)
    outcome_id = Column(String(255), nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    implied_probability = Column(Float, nullable=False)
    bid = Column(Float)
    ask = Column(Float)
    mid = Column(Float)
    spread = Column(Float)
    volume_24h = Column(Float)
    liquidity = Column(Float)
    raw_data = Column(JSON)

    __table_args__ = (
        UniqueConstraint("market_id", "outcome_id", "timestamp", "source", name="uq_price_snapshots"),
        {"schema": "prediction_markets"},
    )


class CheckpointTable(Base):
    """Ingestion checkpoint tracking."""

    __tablename__ = "ingestion_checkpoints"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(50), nullable=False)
    data_type = Column(String(50), nullable=False)  # 'markets', 'trades', 'prices'
    last_sync_timestamp = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, default=func.now())

    __table_args__ = (
        UniqueConstraint("source", "data_type", name="uq_checkpoints"),
        {"schema": "prediction_markets"},
    )


class PostgresStorage(StorageBackend):
    """PostgreSQL implementation of StorageBackend."""

    def __init__(self, connection_string: str, create_tables: bool = False):
        """
        Initialize Postgres storage.

        Args:
            connection_string: SQLAlchemy connection string
            create_tables: If True, create tables on init (use migrations in production)
        """
        self.engine = create_engine(connection_string, pool_pre_ping=True, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)

        if create_tables:
            # Create schema if it doesn't exist
            with self.engine.connect() as conn:
                conn.execute(func.text("CREATE SCHEMA IF NOT EXISTS prediction_markets"))
                conn.commit()
            Base.metadata.create_all(self.engine)
            logger.info("storage.postgres.tables_created")

    def store_raw(
        self,
        source: str,
        endpoint: str,
        response_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Store raw API response."""
        session = self.SessionLocal()
        try:
            request_id = uuid.uuid4()
            record = RawApiResponse(
                request_id=request_id,
                source=source,
                endpoint=endpoint,
                response_json=response_data,
                status_code=200,  # ASSUMPTION: Success if we got data
                metadata=metadata,
            )
            session.add(record)
            session.commit()
            return str(request_id)
        except Exception as e:
            session.rollback()
            logger.error("storage.postgres.store_raw.error", error=str(e))
            raise
        finally:
            session.close()

    def store_markets(self, markets: List[Dict[str, Any]]) -> int:
        """Store normalized market data (upsert)."""
        session = self.SessionLocal()
        count = 0
        try:
            for market_data in markets:
                # Upsert market
                existing = (
                    session.query(MarketTable)
                    .filter_by(market_id=market_data["market_id"], source=market_data["source"])
                    .first()
                )
                if existing:
                    # Update existing
                    for key, value in market_data.items():
                        if key not in ("market_id", "source"):
                            setattr(existing, key, value)
                else:
                    # Insert new
                    record = MarketTable(**market_data)
                    session.add(record)
                count += 1
            session.commit()
            return count
        except Exception as e:
            session.rollback()
            logger.error("storage.postgres.store_markets.error", error=str(e))
            raise
        finally:
            session.close()

    def store_trades(self, trades: List[Dict[str, Any]]) -> int:
        """Store normalized trade data (upsert)."""
        session = self.SessionLocal()
        count = 0
        try:
            for trade_data in trades:
                existing = (
                    session.query(TradeTable)
                    .filter_by(trade_id=trade_data["trade_id"], source=trade_data["source"])
                    .first()
                )
                if existing:
                    for key, value in trade_data.items():
                        if key not in ("trade_id", "source"):
                            setattr(existing, key, value)
                else:
                    record = TradeTable(**trade_data)
                    session.add(record)
                count += 1
            session.commit()
            return count
        except Exception as e:
            session.rollback()
            logger.error("storage.postgres.store_trades.error", error=str(e))
            raise
        finally:
            session.close()

    def store_price_snapshots(self, snapshots: List[Dict[str, Any]]) -> int:
        """Store normalized price snapshot data (upsert)."""
        session = self.SessionLocal()
        count = 0
        try:
            for snapshot_data in snapshots:
                existing = (
                    session.query(PriceSnapshotTable)
                    .filter_by(
                        market_id=snapshot_data["market_id"],
                        outcome_id=snapshot_data["outcome_id"],
                        timestamp=snapshot_data["timestamp"],
                        source=snapshot_data["source"],
                    )
                    .first()
                )
                if existing:
                    for key, value in snapshot_data.items():
                        if key not in ("market_id", "outcome_id", "timestamp", "source"):
                            setattr(existing, key, value)
                else:
                    record = PriceSnapshotTable(**snapshot_data)
                    session.add(record)
                count += 1
            session.commit()
            return count
        except Exception as e:
            session.rollback()
            logger.error("storage.postgres.store_price_snapshots.error", error=str(e))
            raise
        finally:
            session.close()

    def get_latest_checkpoint(
        self,
        source: str,
        data_type: str,
    ) -> Optional[datetime]:
        """Get latest checkpoint timestamp."""
        session = self.SessionLocal()
        try:
            checkpoint = (
                session.query(CheckpointTable)
                .filter_by(source=source, data_type=data_type)
                .first()
            )
            return checkpoint.last_sync_timestamp if checkpoint else None
        finally:
            session.close()

    def update_checkpoint(
        self,
        source: str,
        data_type: str,
        timestamp: datetime,
    ) -> None:
        """Update checkpoint timestamp."""
        session = self.SessionLocal()
        try:
            checkpoint = (
                session.query(CheckpointTable)
                .filter_by(source=source, data_type=data_type)
                .first()
            )
            if checkpoint:
                checkpoint.last_sync_timestamp = timestamp
                checkpoint.updated_at = datetime.utcnow()
            else:
                checkpoint = CheckpointTable(
                    source=source,
                    data_type=data_type,
                    last_sync_timestamp=timestamp,
                )
                session.add(checkpoint)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error("storage.postgres.update_checkpoint.error", error=str(e))
            raise
        finally:
            session.close()

