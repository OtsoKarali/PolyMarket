"""Price/probability snapshot schema."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class PriceSnapshot(BaseModel):
    """Normalized price/probability snapshot model."""

    market_id: str
    source: str
    outcome_id: str
    timestamp: datetime = Field(..., description="Snapshot timestamp")
    implied_probability: float = Field(..., description="Current implied probability (0-1)")
    bid: Optional[float] = Field(None, description="Best bid price")
    ask: Optional[float] = Field(None, description="Best ask price")
    mid: Optional[float] = Field(None, description="Mid price (bid+ask)/2")
    spread: Optional[float] = Field(None, description="Spread (ask-bid)")
    volume_24h: Optional[float] = Field(None, description="24h volume for this outcome")
    liquidity: Optional[float] = Field(None, description="Available liquidity")
    raw_data: Optional[dict] = Field(None, description="Original raw JSON")

    class Config:
        """Pydantic config."""

        json_encoders = {datetime: lambda v: v.isoformat()}

