"""
Update Stock Data - Daily Incremental Updates
Aggiorna i dati giornalieri per tutti i titoli nel database
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import yfinance as yf
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from database.models import Stock, Dividend, PriceData, DataCollectionLog


def create_database_session(db_path='data/dividend_recovery.db'):
    """Create database session"""
    engine = create_engine(f'sqlite:///{db_path}', echo=False)
    Session = sessionmaker(bind=engine)
    return Session()


def get_last_price_date(session, stock_id):
    """Get the date of the last price record for a stock"""
    last_price = session.query(PriceData).filter_by(
        stock_id=stock_id
    ).order_by(PriceData.date.desc()).first()
    
    if last_price:
        return last_price.date
    return None


def update_stock_prices(session, stock):
    """Update price data for a stock"""
    print(f"\n📊 Updating {stock.ticker}...")
    
    # Get last date in database
    last_date = get_last_price_date(session, stock.id)
    
    if not last_date:
        print(f"   ⚠️  No historical data found. Run download_stock_data.py first!")
        return {'prices': 0, 'dividends': 0}
    
    # Calculate date range for update
    start_date = (last_date + timedelta(days=1)).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    # Check if already up to date
    if last_date >= datetime.now().date():
        print(f"   ✅ Already up to date (last: {last_date})")
        return {'prices': 0, 'dividends': 0}
    
    print(f"   📅 Last data: {last_date}")
    print(f"   📅 Fetching: {start_date} to {end_date}")
    
    try:
        # Download new data - ⚠️ FORZA DATI NON ADJUSTED!
        ticker_obj = yf.Ticker(stock.ticker)
        hist = ticker_obj.history(start=start_date, end=end_date, auto_adjust=False, back_adjust=False)
        
        if hist.empty:
            print(f"   ℹ️  No new data available")
            return {'prices': 0, 'dividends': 0}
        
        # Save new price records
        prices_added = 0
        for date, row in hist.iterrows():
            # Check if already exists
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
                prices_added += 1
        
        # Check for new dividends
        dividends = ticker_obj.dividends
        dividends = dividends[dividends.index > last_date.strftime('%Y-%m-%d')]
        
        dividends_added = 0
        for date, amount in dividends.items():
            # Check if already exists
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
                dividends_added += 1
        
        session.commit()
        
        print(f"   ✅ Added {prices_added} price records, {dividends_added} dividends")
        
        # Log successful update
        log = DataCollectionLog(
            source='yahoo_finance',
            operation='update',
            stock_ticker=stock.ticker,
            status='success',
            records_processed=prices_added + dividends_added,
            message=f"Updated {prices_added} prices, {dividends_added} dividends"
        )
        session.add(log)
        session.commit()
        
        return {'prices': prices_added, 'dividends': dividends_added}
        
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        
        # Log error
        log = DataCollectionLog(
            source='yahoo_finance',
            operation='update',
            stock_ticker=stock.ticker,
            status='error',
            message=str(e)
        )
        session.add(log)
        session.commit()
        
        return {'prices': 0, 'dividends': 0}


def main():
    """Main function"""
    print("=" * 60)
    print("DIVIDEND RECOVERY SYSTEM - DATA UPDATE")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Create database session
    session = create_database_session()
    
    # Get all stocks
    stocks = session.query(Stock).all()
    
    if not stocks:
        print("⚠️  No stocks in database!")
        print("💡 Run download_stock_data.py first to add stocks")
        session.close()
        return
    
    print(f"📋 Found {len(stocks)} stock(s) to update\n")
    
    # Update each stock
    total_prices = 0
    total_dividends = 0
    
    for stock in stocks:
        result = update_stock_prices(session, stock)
        total_prices += result['prices']
        total_dividends += result['dividends']
    
    print("\n" + "=" * 60)
    print("📊 UPDATE SUMMARY")
    print("=" * 60)
    print(f"Total stocks updated: {len(stocks)}")
    print(f"Total new price records: {total_prices}")
    print(f"Total new dividend records: {total_dividends}")
    print("=" * 60)
    print()
    
    if total_prices + total_dividends > 0:
        print("✅ Update completed successfully!")
    else:
        print("ℹ️  No new data to update (already up to date)")
    
    session.close()


if __name__ == '__main__':
    main()
