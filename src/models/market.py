"""Market metadata schema."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Market(BaseModel):
    """Normalized market metadata model."""

    market_id: str = Field(..., description="Unique market identifier")
    source: str = Field(..., description="Market source (e.g., 'polymarket')")
    question: str = Field(..., description="Market question/title")
    description: Optional[str] = Field(None, description="Detailed market description")
    end_date: Optional[datetime] = Field(None, description="Market resolution date")
    resolution_source: Optional[str] = Field(None, description="Source for resolution")
    category: Optional[str] = Field(None, description="Market category")
    tags: Optional[list[str]] = Field(None, description="Market tags")
    liquidity: Optional[float] = Field(None, description="Total liquidity")
    volume_24h: Optional[float] = Field(None, description="24h trading volume")
    created_at: Optional[datetime] = Field(None, description="Market creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    raw_data: Optional[dict] = Field(None, description="Original raw JSON for reference")

    class Config:
        """Pydantic config."""

        json_encoders = {datetime: lambda v: v.isoformat()}


class MarketOutcome(BaseModel):
    """Market outcome/token metadata."""

    market_id: str
    source: str
    outcome_id: str = Field(..., description="Outcome identifier (e.g., 'YES', 'NO', or token address)")
    outcome_name: str = Field(..., description="Human-readable outcome name")
    token_address: Optional[str] = Field(None, description="Token contract address (if applicable)")
    created_at: Optional[datetime] = None

