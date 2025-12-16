"""Database setup script to create schema and tables."""

import sys

from sqlalchemy import create_engine, text

from config.settings import settings


def setup_database():
    """Create database schema and tables."""
    engine = create_engine(settings.database_url)

    with engine.connect() as conn:
        # Create schema
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS prediction_markets"))
        conn.commit()
        print("✓ Created schema 'prediction_markets'")

        # Import here to avoid circular imports
        from src.storage.postgres import Base

        # Create all tables
        Base.metadata.create_all(engine)
        print("✓ Created all tables")

    print("\n✓ Database setup complete!")
    print(f"  Connection: {settings.database_url}")


if __name__ == "__main__":
    try:
        setup_database()
    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        sys.exit(1)

