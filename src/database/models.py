"""
Database models for Dividend Recovery System
SQLAlchemy ORM models
"""

from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Stock(Base):
    """Stock table - Titoli supervisionati"""
    __tablename__ = 'stocks'
    
    id = Column(Integer, primary_key=True)
    ticker = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(200))
    market = Column(String(50))  # Italy, USA, etc.
    sector = Column(String(100))
    currency = Column(String(10), default='EUR')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    dividends = relationship('Dividend', back_populates='stock', cascade='all, delete-orphan')
    prices = relationship('PriceData', back_populates='stock', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Stock(ticker='{self.ticker}', name='{self.name}')>"


class Dividend(Base):
    """Dividend table - Dividendi storici e predetti"""
    __tablename__ = 'dividends'

    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False, index=True)
    ex_date = Column(Date, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    payment_date = Column(Date)
    record_date = Column(Date)
    currency = Column(String(10), default='EUR')
    dividend_type = Column(String(50))  # ordinary, extraordinary, special
    created_at = Column(DateTime, default=datetime.utcnow)

    # Prediction fields
    status = Column(String(20), default='CONFIRMED')  # CONFIRMED, PREDICTED, PAID
    confidence = Column(Float, default=1.0)  # 0.0 - 1.0
    prediction_source = Column(String(50))  # IBKR, HISTORICAL_PATTERN, MANUAL, HISTORICAL

    # Relationships
    stock = relationship('Stock', back_populates='dividends')

    def __repr__(self):
        return f"<Dividend(ticker='{self.stock.ticker}', ex_date='{self.ex_date}', amount={self.amount}, status='{self.status}')>"


class PriceData(Base):
    """Price data table - Dati prezzi OHLCV"""
    __tablename__ = 'price_data'
    
    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Integer)
    adjusted_close = Column(Float)
    
    # Relationships
    stock = relationship('Stock', back_populates='prices')
    
    def __repr__(self):
        return f"<PriceData(ticker='{self.stock.ticker}', date='{self.date}', close={self.close})>"


class DataCollectionLog(Base):
    """Log delle operazioni di raccolta dati"""
    __tablename__ = 'data_collection_logs'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    source = Column(String(100))  # yahoo_finance, borsa_italiana, etc.
    operation = Column(String(100))  # download, update, validate
    stock_ticker = Column(String(20))
    status = Column(String(50))  # success, error, warning
    records_processed = Column(Integer, default=0)
    message = Column(String(500))
    
    def __repr__(self):
        return f"<DataCollectionLog(timestamp='{self.timestamp}', source='{self.source}', status='{self.status}')>"
