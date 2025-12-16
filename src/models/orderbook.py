"""Order book snapshot schema."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class OrderBookLevel(BaseModel):
    """Single order book level (bid or ask)."""

    price: float
    quantity: float
    order_count: Optional[int] = None


class OrderBookSnapshot(BaseModel):
    """Normalized order book snapshot model."""

    market_id: str
    source: str
    outcome_id: str
    timestamp: datetime
    bids: list[OrderBookLevel] = Field(default_factory=list, description="Bid levels (descending price)")
    asks: list[OrderBookLevel] = Field(default_factory=list, description="Ask levels (ascending price)")
    raw_data: Optional[dict] = Field(None, description="Original raw JSON")

    class Config:
        """Pydantic config."""

        json_encoders = {datetime: lambda v: v.isoformat()}

