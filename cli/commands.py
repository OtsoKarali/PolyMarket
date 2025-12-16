"""CLI commands for ingestion and backfilling."""

import sys
from datetime import datetime, timedelta
from typing import Optional

import click
from dateutil.parser import parse as parse_date

from config.settings import settings
from src.connectors.polymarket.adapter import PolymarketAdapter
from src.core.ingestion import IngestionEngine
from src.storage.postgres import PostgresStorage


def get_storage() -> PostgresStorage:
    """Get configured storage backend."""
    return PostgresStorage(connection_string=settings.database_url, create_tables=True)


def get_adapter() -> PolymarketAdapter:
    """Get configured Polymarket adapter."""
    return PolymarketAdapter(
        api_key=settings.polymarket_api_key,
        rate_limit_per_second=settings.polymarket_rate_limit,
    )


@click.group()
def main():
    """Polymarket data ingestion CLI."""
    pass


@main.command()
@click.option("--limit", type=int, help="Maximum number of markets to fetch")
@click.option("--no-raw", is_flag=True, help="Skip storing raw API responses")
def markets(limit: Optional[int], no_raw: bool):
    """Ingest market metadata."""
    storage = get_storage()
    adapter = get_adapter()
    engine = IngestionEngine(adapter=adapter, storage=storage)

    try:
        count = engine.ingest_markets(limit=limit, store_raw=not no_raw)
        click.echo(f"✓ Ingested {count} markets")
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)
    finally:
        adapter.close()


@main.command()
@click.option("--market-id", help="Filter by specific market ID")
@click.option("--since", help="Only fetch trades after this timestamp (ISO format)")
@click.option("--limit", type=int, help="Maximum number of trades per request")
@click.option("--no-raw", is_flag=True, help="Skip storing raw API responses")
def trades(market_id: Optional[str], since: Optional[str], limit: Optional[int], no_raw: bool):
    """Ingest trades/fills."""
    storage = get_storage()
    adapter = get_adapter()
    engine = IngestionEngine(adapter=adapter, storage=storage)

    since_dt = None
    if since:
        try:
            since_dt = parse_date(since)
        except ValueError:
            click.echo(f"✗ Invalid date format: {since}", err=True)
            sys.exit(1)

    try:
        count = engine.ingest_trades(
            market_id=market_id,
            since=since_dt,
            limit=limit,
            store_raw=not no_raw,
        )
        click.echo(f"✓ Ingested {count} trades")
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)
    finally:
        adapter.close()


@main.command()
@click.option("--market-id", help="Filter by specific market ID")
@click.option("--no-raw", is_flag=True, help="Skip storing raw API responses")
def prices(market_id: Optional[str], no_raw: bool):
    """Ingest current price/probability snapshots."""
    storage = get_storage()
    adapter = get_adapter()
    engine = IngestionEngine(adapter=adapter, storage=storage)

    try:
        count = engine.ingest_price_snapshots(market_id=market_id, store_raw=not no_raw)
        click.echo(f"✓ Ingested {count} price snapshots")
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)
    finally:
        adapter.close()


@main.command()
@click.option("--start", required=True, help="Start date (ISO format: YYYY-MM-DD)")
@click.option("--end", required=True, help="End date (ISO format: YYYY-MM-DD)")
@click.option("--data-type", type=click.Choice(["trades", "prices"]), default="trades")
@click.option("--market-id", help="Filter by specific market ID")
@click.option("--no-raw", is_flag=True, help="Skip storing raw API responses")
def backfill(start: str, end: str, data_type: str, market_id: Optional[str], no_raw: bool):
    """
    Backfill historical data.

    For trades: fetches all trades between start and end dates.
    For prices: fetches snapshots (may be limited by API availability).
    """
    storage = get_storage()
    adapter = get_adapter()
    engine = IngestionEngine(adapter=adapter, storage=storage)

    try:
        start_dt = parse_date(start)
        end_dt = parse_date(end)
    except ValueError as e:
        click.echo(f"✗ Invalid date format: {e}", err=True)
        sys.exit(1)

    if start_dt >= end_dt:
        click.echo("✗ Start date must be before end date", err=True)
        sys.exit(1)

    try:
        if data_type == "trades":
            # Backfill trades day by day
            current = start_dt
            total = 0
            while current < end_dt:
                next_day = current.replace(hour=23, minute=59, second=59)
                if next_day > end_dt:
                    next_day = end_dt

                click.echo(f"Backfilling trades from {current.date()} to {next_day.date()}...")
                count = engine.ingest_trades(
                    market_id=market_id,
                    since=current,
                    store_raw=not no_raw,
                )
                total += count
                click.echo(f"  ✓ Ingested {count} trades")

                current = next_day.replace(hour=0, minute=0, second=0) + timedelta(days=1)

            click.echo(f"\n✓ Backfill complete: {total} total trades")
        else:
            click.echo("Price snapshot backfilling not yet implemented (API limitations)")
            sys.exit(1)

    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)
    finally:
        adapter.close()


if __name__ == "__main__":
    main()

