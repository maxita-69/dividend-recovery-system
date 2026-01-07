"""
Database utilities - session management and data retrieval.
"""
import pandas as pd
from pathlib import Path
from typing import Optional
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from config import get_config, DATABASE_PATH
from database.models import Stock, PriceData, Dividend


_engine = None
_SessionMaker = None


def get_engine():
    """Get or create SQLAlchemy engine (singleton)."""
    global _engine
    if _engine is None:
        cfg = get_config()
        _engine = create_engine(cfg.database_url, echo=cfg.database_echo)
    return _engine


def get_session_maker():
    """Get or create session maker (singleton)."""
    global _SessionMaker
    if _SessionMaker is None:
        _SessionMaker = sessionmaker(bind=get_engine())
    return _SessionMaker


def get_database_session() -> Session:
    """
    Create a new database session.

    Returns:
        SQLAlchemy Session object

    Example:
        >>> session = get_database_session()
        >>> stocks = session.query(Stock).all()
        >>> session.close()
    """
    SessionMaker = get_session_maker()
    return SessionMaker()


@contextmanager
def session_scope():
    """
    Provide a transactional scope around a series of operations.

    Automatically commits on success, rolls back on error, and closes session.

    Example:
        >>> with session_scope() as session:
        >>>     stock = Stock(ticker='TEST', name='Test Stock')
        >>>     session.add(stock)
        >>>     # Automatically commits here
    """
    session = get_database_session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise
    finally:
        session.close()


def get_price_dataframe(
    session: Session,
    stock_id: int,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Optional[pd.DataFrame]:
    """
    Get price data as a pandas DataFrame, sorted by date.

    Args:
        session: Database session
        stock_id: Stock ID
        start_date: Optional start date (YYYY-MM-DD)
        end_date: Optional end date (YYYY-MM-DD)

    Returns:
        DataFrame with columns: date (index), open, high, low, close, volume
        Returns None if no data found

    Example:
        >>> df = get_price_dataframe(session, stock.id)
        >>> df = get_price_dataframe(session, stock.id, start_date='2024-01-01')
    """
    try:
        query = session.query(PriceData).filter_by(stock_id=stock_id)

        if start_date:
            query = query.filter(PriceData.date >= start_date)
        if end_date:
            query = query.filter(PriceData.date <= end_date)

        prices = query.order_by(PriceData.date).all()

        if not prices:
            return None

        df = pd.DataFrame([{
            'date': p.date,
            'open': p.open,
            'high': p.high,
            'low': p.low,
            'close': p.close,
            'volume': p.volume
        } for p in prices])

        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')

        return df

    except SQLAlchemyError as e:
        raise DatabaseError(f"Failed to retrieve price data: {str(e)}")


def get_dividends_dataframe(
    session: Session,
    stock_id: int,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> pd.DataFrame:
    """
    Get dividend data as a pandas DataFrame.

    Args:
        session: Database session
        stock_id: Stock ID
        start_date: Optional start date filter
        end_date: Optional end date filter

    Returns:
        DataFrame with dividend information
    """
    try:
        query = session.query(Dividend).filter_by(stock_id=stock_id)

        if start_date:
            query = query.filter(Dividend.ex_date >= start_date)
        if end_date:
            query = query.filter(Dividend.ex_date <= end_date)

        dividends = query.order_by(Dividend.ex_date).all()

        if not dividends:
            return pd.DataFrame()

        df = pd.DataFrame([{
            'ex_date': d.ex_date,
            'amount': d.amount,
            'payment_date': d.payment_date,
            'record_date': d.record_date,
            'currency': d.currency,
            'dividend_type': d.dividend_type
        } for d in dividends])

        df['ex_date'] = pd.to_datetime(df['ex_date'])

        return df

    except SQLAlchemyError as e:
        raise DatabaseError(f"Failed to retrieve dividend data: {str(e)}")


def get_stock_by_ticker(session: Session, ticker: str) -> Optional[Stock]:
    """
    Get stock by ticker symbol.

    Args:
        session: Database session
        ticker: Stock ticker (e.g., 'ENEL.MI')

    Returns:
        Stock object or None if not found
    """
    try:
        return session.query(Stock).filter_by(ticker=ticker).first()
    except SQLAlchemyError as e:
        raise DatabaseError(f"Failed to retrieve stock: {str(e)}")


def get_all_stocks(session: Session, market: Optional[str] = None) -> list:
    """
    Get all stocks, optionally filtered by market.

    Args:
        session: Database session
        market: Optional market filter (e.g., 'XMIL')

    Returns:
        List of Stock objects
    """
    try:
        query = session.query(Stock)
        if market:
            query = query.filter_by(market=market)
        return query.order_by(Stock.ticker).all()
    except SQLAlchemyError as e:
        raise DatabaseError(f"Failed to retrieve stocks: {str(e)}")


def validate_database() -> dict:
    """
    Validate database integrity and return statistics.

    Returns:
        Dictionary with:
            - exists: bool
            - stocks_count: int
            - dividends_count: int
            - prices_count: int
            - errors: list of error messages
    """
    errors = []
    stats = {
        'exists': DATABASE_PATH.exists(),
        'stocks_count': 0,
        'dividends_count': 0,
        'prices_count': 0,
        'errors': errors
    }

    if not stats['exists']:
        errors.append(f"Database file not found: {DATABASE_PATH}")
        return stats

    try:
        with session_scope() as session:
            stats['stocks_count'] = session.query(Stock).count()
            stats['dividends_count'] = session.query(Dividend).count()
            stats['prices_count'] = session.query(PriceData).count()

    except Exception as e:
        errors.append(f"Database validation failed: {str(e)}")

    return stats


class DatabaseError(Exception):
    """Custom exception for database operations."""
    pass
