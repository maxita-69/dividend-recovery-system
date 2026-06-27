"""
Business logic for stock endpoints.
"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from database.models import Dividend, PriceData, Stock


def list_stocks(db: Session):
    """Return all stocks with price and dividend counts."""
    stocks = db.query(Stock).order_by(Stock.ticker).all()
    result = []
    for stock in stocks:
        price_count = db.query(PriceData).filter_by(stock_id=stock.id).count()
        dividend_count = db.query(Dividend).filter_by(stock_id=stock.id).count()
        result.append(
            {
                "id": stock.id,
                "ticker": stock.ticker,
                "name": stock.name,
                "market": stock.market,
                "sector": stock.sector,
                "currency": stock.currency,
                "price_count": price_count,
                "dividend_count": dividend_count,
            }
        )
    return result


def get_stock_by_ticker(db: Session, ticker: str):
    """Return a single stock with price and dividend counts."""
    stock = db.query(Stock).filter_by(ticker=ticker).first()
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {ticker} not found")

    price_count = db.query(PriceData).filter_by(stock_id=stock.id).count()
    dividend_count = db.query(Dividend).filter_by(stock_id=stock.id).count()
    return {
        "id": stock.id,
        "ticker": stock.ticker,
        "name": stock.name,
        "market": stock.market,
        "sector": stock.sector,
        "currency": stock.currency,
        "price_count": price_count,
        "dividend_count": dividend_count,
    }
