# Polymarket Data Platform Architecture

## Overview

A production-quality, modular data ingestion and storage platform for prediction markets, designed with quantitative research in mind. The system treats each market (Polymarket, Kalshi, etc.) as a pluggable adapter within a market-agnostic core framework.

## Design Principles

1. **Separation of Concerns**: Market-specific code isolated in adapters; core logic is market-agnostic
2. **Research-First**: Normalized schemas optimized for time-series analysis and feature engineering
3. **Production-Ready**: Rate limiting, retries, idempotency, observability
4. **Extensible**: Easy to add new markets without rewriting core components

## Repository Structure

```
PolyMarket/
├── src/
│   ├── core/                    # Market-agnostic core
│   │   ├── __init__.py
│   │   ├── interfaces.py        # Abstract base classes
│   │   ├── ingestion.py         # Core ingestion engine
│   │   ├── storage.py            # Storage abstractions
│   │   ├── checkpoint.py        # Incremental sync state
│   │   └── observability.py     # Logging & metrics
│   ├── connectors/              # Market-specific adapters
│   │   ├── __init__.py
│   │   └── polymarket/
│   │       ├── __init__.py
│   │       ├── client.py        # API client wrapper
│   │       ├── adapter.py       # Implements core interfaces
│   │       └── schemas.py       # Polymarket-specific data models
│   ├── storage/                 # Storage implementations
│   │   ├── __init__.py
│   │   ├── postgres.py          # Postgres storage
│   │   ├── parquet.py           # Parquet/Arrow for research
│   │   └── migrations/          # Database migrations
│   └── models/                  # Shared data models
│       ├── __init__.py
│       ├── market.py            # Market metadata schema
│       ├── trade.py             # Trade/fill schema
│       ├── price.py             # Price/probability snapshot
│       └── orderbook.py         # Order book snapshot
├── cli/
│   ├── __init__.py
│   └── commands.py              # CLI entry points
├── tests/
│   ├── unit/
│   │   ├── test_connectors.py
│   │   ├── test_ingestion.py
│   │   └── fixtures/
│   └── integration/
├── config/
│   └── settings.py              # Configuration management
├── scripts/
│   └── setup_db.py              # Database initialization
├── pyproject.toml               # Dependencies & project config
├── README.md
└── ARCHITECTURE.md
```

## Module Responsibilities

### `core/interfaces.py`
Abstract base classes defining the contract for market adapters:
- `MarketAdapter`: Interface for market-specific implementations
- `DataFetcher`: Interface for fetching raw data
- `DataNormalizer`: Interface for transforming raw → normalized

### `core/ingestion.py`
Orchestrates the ingestion pipeline:
- Coordinates adapters, storage, checkpointing
- Handles retries, rate limiting, error recovery
- Manages incremental vs full sync modes

### `core/storage.py`
Storage abstractions:
- `RawStorage`: Landing zone for raw JSON
- `CuratedStorage`: Normalized table storage
- Supports multiple backends (Postgres, Parquet, DuckDB)

### `connectors/polymarket/`
Polymarket-specific implementation:
- `client.py`: Wraps Polymarket GraphQL/REST API
- `adapter.py`: Implements `MarketAdapter` interface
- Handles auth, pagination, rate limits

### `storage/postgres.py`
Postgres implementation with:
- Connection pooling
- Transaction management
- Schema migrations

## Data Model

### Tables

1. **markets** (metadata)
   - Primary key: `(market_id, source)`
   - Fields: id, question, description, end_date, resolution_source, etc.
   - Partitioned by source (polymarket, kalshi, etc.)

2. **market_outcomes**
   - Primary key: `(market_id, outcome_id, source)`
   - Fields: outcome_id, outcome_name, token_address, etc.

3. **trades**
   - Primary key: `(trade_id, source)`
   - Fields: market_id, outcome_id, price, quantity, timestamp, etc.
   - Partitioned by timestamp (monthly)

4. **price_snapshots**
   - Primary key: `(market_id, outcome_id, timestamp, source)`
   - Fields: implied_probability, bid, ask, mid, volume_24h, etc.
   - Partitioned by timestamp (daily)

5. **orderbook_snapshots** (if available)
   - Primary key: `(market_id, outcome_id, timestamp, source)`
   - Fields: bids, asks (JSON arrays)

6. **raw_api_responses** (audit trail)
   - Primary key: `(request_id, source)`
   - Fields: endpoint, response_json, timestamp, status_code

## Ingestion Flow

```
CLI Command
    ↓
Ingestion Engine
    ↓
Market Adapter (Polymarket)
    ↓
API Client (rate-limited, retries)
    ↓
Raw Storage (JSON landing)
    ↓
Normalizer (raw → schema)
    ↓
Curated Storage (normalized tables)
    ↓
Checkpoint Update
```

## Research Readiness

The schema design enables:
- **Time-series queries**: Efficient filtering by timestamp
- **Feature engineering**: Clean joins across markets, outcomes, trades
- **Cross-market analysis**: Unified schema across sources
- **Event labeling**: Link markets to external events (future)

## Storage Strategy

- **Postgres**: Primary storage for normalized tables, ACID guarantees
- **Parquet/DuckDB**: Export for research notebooks, fast analytical queries
- **Raw JSON**: Preserved for auditability and schema evolution

