"""
Download Stock Data - Scarica dati storici completi
Popola il database SQLite con dati da Yahoo Finance
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import yfinance as yf
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from database.models import Base, Stock, Dividend, PriceData, DataCollectionLog


def create_database(db_path='data/dividend_recovery.db'):
    """Crea database e tabelle se non esistono"""
    # Create data directory if not exists
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    engine = create_engine(f'sqlite:///{db_path}', echo=False)
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    return Session()


def download_stock_data(ticker, start_date='2020-01-01', end_date=None):
    """Scarica dati storici da Yahoo Finance"""
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    print(f"\n📊 Downloading {ticker}...")
    print(f"   Period: {start_date} to {end_date}")
    
    try:
        stock = yf.Ticker(ticker)
        
        # ⚠️ FORZA I DATI NON ADJUSTED!
        hist = stock.history(start=start_date, end=end_date, auto_adjust=False, back_adjust=False)
        
        if hist.empty:
            print(f"   ❌ No price data found for {ticker}")
            return None, None
        
        # Download dividends
        dividends = stock.dividends
        dividends = dividends[dividends.index >= start_date]
        
        info = stock.info
        stock_name = info.get('longName', ticker)
        
        print(f"   ✅ Downloaded {len(hist)} price records")
        print(f"   ✅ Downloaded {len(dividends)} dividend records")
        
        return {
            'name': stock_name,
            'prices': hist,
            'dividends': dividends,
            'info': info
        }, None
        
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return None, str(e)



def save_to_database(session, ticker, data):
    """Salva dati nel database"""
    # Aggiungi questo debug prima di save_to_database
    print("\n📈 PRIME RIGHE DEI PREZZI:")
    print(data['prices'][['Open', 'High', 'Low', 'Close']].head())
    print(f"\n💾 Saving {ticker} to database...")
    
    # Check if stock exists
    stock = session.query(Stock).filter_by(ticker=ticker).first()
    
    if stock:
        print(f"   ℹ️  Stock {ticker} already exists, updating...")
    else:
        # Create new stock
        market = 'Italy' if ticker.endswith('.MI') else 'USA'
        stock = Stock(
            ticker=ticker,
            name=data['name'],
            market=market,
            sector=data['info'].get('sector', 'Unknown')
        )
        session.add(stock)
        session.flush()
        print(f"   ✅ Created stock record")
    
    # Save price data
    prices_saved = 0
    for date, row in data['prices'].iterrows():
        # Check if price already exists
        existing = session.query(PriceData).filter_by(
            stock_id=stock.id,
            date=date.date()
        ).first()
        
        if not existing:
            price = PriceData(
                stock_id=stock.id,
                date=date.date(),
                open=float(row['Open']),
                high=float(row['High']),
                low=float(row['Low']),
                close=float(row['Close']),
                volume=int(row['Volume']) if row['Volume'] else 0,
                adjusted_close=float(row['Close'])
            )
            session.add(price)
            prices_saved += 1
    
    print(f"   ✅ Saved {prices_saved} new price records")
    
    # Save dividends
    dividends_saved = 0
    for date, amount in data['dividends'].items():
        # Check if dividend already exists
        existing = session.query(Dividend).filter_by(
            stock_id=stock.id,
            ex_date=date.date()
        ).first()
        
        if not existing:
            dividend = Dividend(
                stock_id=stock.id,
                ex_date=date.date(),
                amount=float(amount),
                dividend_type='ordinary'
            )
            session.add(dividend)
            dividends_saved += 1
    
    print(f"   ✅ Saved {dividends_saved} new dividend records")
    
    # Log operation
    log = DataCollectionLog(
        source='yahoo_finance',
        operation='download',
        stock_ticker=ticker,
        status='success',
        records_processed=prices_saved + dividends_saved,
        message=f"Downloaded {prices_saved} prices, {dividends_saved} dividends"
    )
    session.add(log)
    
    session.commit()
    print(f"   ✅ All data committed to database")


def main():
    """Main function"""
    print("=" * 60)
    print("DIVIDEND RECOVERY SYSTEM - DATA DOWNLOAD")
    print("=" * 60)
    
    # Create database
    session = create_database()
    
    # Stocks to download
    tickers = [
        'ENEL.MI',      # Enel (Italy)
        # Add more tickers here as needed
    ]
    
    for ticker in tickers:
        data, error = download_stock_data(ticker)
        
        if data:
            save_to_database(session, ticker, data)
        else:
            print(f"\n❌ Failed to download {ticker}: {error}")
            
            # Log error
            log = DataCollectionLog(
                source='yahoo_finance',
                operation='download',
                stock_ticker=ticker,
                status='error',
                message=error
            )
            session.add(log)
            session.commit()
    
    print("\n" + "=" * 60)
    print("✅ DOWNLOAD COMPLETED")
    print("=" * 60)
    
    # Summary
    n_stocks = session.query(Stock).count()
    n_prices = session.query(PriceData).count()
    n_dividends = session.query(Dividend).count()
    
    print(f"\n📊 DATABASE SUMMARY:")
    print(f"   Stocks: {n_stocks}")
    print(f"   Price records: {n_prices}")
    print(f"   Dividend records: {n_dividends}")
    
    session.close()


if __name__ == '__main__':
    main()
