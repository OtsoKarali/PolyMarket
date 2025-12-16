"""Trade/fill data schema."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Trade(BaseModel):
    """Normalized trade/fill model."""

    trade_id: str = Field(..., description="Unique trade identifier")
    source: str
    market_id: str
    outcome_id: str = Field(..., description="Outcome that was traded")
    price: float = Field(..., description="Trade price (0-1 for probability markets)")
    quantity: float = Field(..., description="Trade quantity/size")
    timestamp: datetime = Field(..., description="Trade execution timestamp")
    side: Optional[str] = Field(None, description="'buy' or 'sell'")
    taker_address: Optional[str] = Field(None, description="Taker wallet address")
    maker_address: Optional[str] = Field(None, description="Maker wallet address")
    transaction_hash: Optional[str] = Field(None, description="Blockchain transaction hash")
    raw_data: Optional[dict] = Field(None, description="Original raw JSON")

    class Config:
        """Pydantic config."""

        json_encoders = {datetime: lambda v: v.isoformat()}

