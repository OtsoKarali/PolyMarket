# Polymarket Data Platform

Production-quality data ingestion and storage platform for prediction markets, designed for quantitative research.

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed design documentation.

## Quick Start

### Prerequisites

- Python 3.10+
- PostgreSQL (or use Docker: `docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres:15`)

### Installation

```bash
# Install dependencies
pip install -e .

# Or with dev dependencies
pip install -e ".[dev]"
```

### Configuration

Create a `.env` file:

```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/prediction_markets
POLYMARKET_API_KEY=your_api_key_here  # Optional, may not be needed for public data
POLYMARKET_RATE_LIMIT=10.0  # Requests per second
LOG_LEVEL=INFO
```

### Database Setup

```bash
python scripts/setup_db.py
```

### Usage

```bash
# Ingest market metadata
polymarket-ingest markets

# Ingest recent trades
polymarket-ingest trades --since 2024-01-01T00:00:00Z

# Ingest current price snapshots
polymarket-ingest prices

# Backfill historical trades
polymarket-ingest backfill --start 2024-01-01 --end 2024-01-31 --data-type trades
```

## Project Structure

```
src/
├── core/              # Market-agnostic core components
├── connectors/        # Market-specific adapters (polymarket, etc.)
├── models/           # Shared data models
└── storage/          # Storage backends (Postgres, Parquet, etc.)

cli/                  # CLI commands
config/               # Configuration management
tests/                # Test suite
scripts/              # Utility scripts
```

## Development

### Running Tests

```bash
pytest tests/
```

### Code Quality

```bash
black src/ cli/ tests/
ruff check src/ cli/ tests/
mypy src/ cli/
```

## Important Notes

⚠️ **API Assumptions**: This implementation makes assumptions about Polymarket's API structure (GraphQL endpoints, response formats). These are clearly marked with `ASSUMPTION:` comments in the code. Adjust based on the actual API documentation.

## Research Readiness

The normalized schema enables:

- **Time-series analysis**: Efficient queries by timestamp
- **Feature engineering**: Clean joins across markets, outcomes, trades
- **Cross-market analysis**: Unified schema across sources
- **Event labeling**: Link markets to external events (future)

## License

MIT
