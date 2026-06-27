"""
Pydantic schemas for the FastAPI backend.
"""
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class HealthOut(BaseModel):
    """Health check response."""
    status: str


class StockOut(BaseModel):
    """Stock detail response."""
    id: int
    ticker: str
    name: Optional[str] = None
    market: Optional[str] = None
    sector: Optional[str] = None
    currency: Optional[str] = None
    price_count: int
    dividend_count: int

    model_config = ConfigDict(from_attributes=True)


class StockListOut(BaseModel):
    """List of stocks response."""
    stocks: List[StockOut]
