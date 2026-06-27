"""
Stocks router.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.deps import get_db
from api.schemas import StockListOut, StockOut
from api.services import stock_service

router = APIRouter(prefix="/stocks", tags=["stocks"])


@router.get("", response_model=StockListOut)
def read_stocks(db: Session = Depends(get_db)):
    """List all supervised stocks."""
    stocks = stock_service.list_stocks(db)
    return {"stocks": stocks}


@router.get("/{ticker}", response_model=StockOut)
def read_stock(ticker: str, db: Session = Depends(get_db)):
    """Get a single stock by ticker."""
    return stock_service.get_stock_by_ticker(db, ticker)
