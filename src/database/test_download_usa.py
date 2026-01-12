"""
Test Download USA Stocks - Quick test con 3 stocks
"""

import sys
from pathlib import Path
from datetime import datetime
import yfinance as yf
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from database.models import Base, Stock, Dividend, PriceData, DataCollectionLog


def create_database(db_path='data/dividend_recovery.db'):
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f'sqlite:///{db_path}', echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


def download_stock_data(ticker, start_date='2019-01-01', end_date=None):
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')

    print(f"\n📊 Downloading {ticker}...")
    print(f"   Period: {start_date} to {end_date}")

    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(start=start_date, end=end_date, auto_adjust=False, back_adjust=False)

        if hist.empty:
            print(f"   ❌ No price data found for {ticker}")
            return None, None

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
    print(f"\n💾 Saving {ticker} to database...")

    stock = session.query(Stock).filter_by(ticker=ticker).first()

    if stock:
        print(f"   ℹ️  Stock {ticker} already exists, updating...")
    else:
        market = 'USA'
        stock = Stock(
            ticker=ticker,
            name=data['name'],
            market=market,
            sector=data['info'].get('sector', 'Unknown'),
            currency='USD'
        )
        session.add(stock)
        session.flush()
        print(f"   ✅ Created stock record")

    # Save price data
    prices_saved = 0
    for date, row in data['prices'].iterrows():
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
        existing = session.query(Dividend).filter_by(
            stock_id=stock.id,
            ex_date=date.date()
        ).first()

        if not existing:
            dividend = Dividend(
                stock_id=stock.id,
                ex_date=date.date(),
                amount=float(amount),
                dividend_type='ordinary',
                status='CONFIRMED',
                confidence=1.0,
                prediction_source='HISTORICAL',
                currency='USD'
            )
            session.add(dividend)
            dividends_saved += 1

    print(f"   ✅ Saved {dividends_saved} new dividend records")

    session.commit()
    print(f"   ✅ All data committed to database")


def main():
    print("=" * 60)
    print("TEST DOWNLOAD - USA STOCKS (3 samples)")
    print("=" * 60)

    session = create_database()

    # Test con 3 stock rappresentativi
    test_tickers = [
        'JNJ',   # Healthcare - Dividend Aristocrat
        'KO',    # Consumer - Dividend Aristocrat
        'T',     # Telecom - High yield
    ]

    print(f"\n🧪 Testing download with {len(test_tickers)} stocks:")
    for ticker in test_tickers:
        print(f"   - {ticker}")

    for ticker in test_tickers:
        data, error = download_stock_data(ticker, start_date='2019-01-01')

        if data:
            save_to_database(session, ticker, data)
        else:
            print(f"\n❌ Failed to download {ticker}: {error}")

    print("\n" + "=" * 60)
    print("✅ TEST COMPLETED")
    print("=" * 60)

    # Summary
    n_stocks = session.query(Stock).count()
    n_prices = session.query(PriceData).count()
    n_dividends = session.query(Dividend).count()

    print(f"\n📊 DATABASE SUMMARY:")
    print(f"   Stocks: {n_stocks}")
    print(f"   Price records: {n_prices:,}")
    print(f"   Dividend records: {n_dividends}")

    # Show USA stocks
    from sqlalchemy import text
    from sqlalchemy.orm import Session as SQLSession

    result = session.execute(text("""
        SELECT s.ticker, s.name, COUNT(d.id) as div_count
        FROM stocks s
        LEFT JOIN dividends d ON s.id = d.stock_id
        WHERE s.market = 'USA'
        GROUP BY s.id
        ORDER BY s.ticker
    """))

    print(f"\n🇺🇸 USA STOCKS IN DATABASE:")
    for ticker, name, div_count in result:
        print(f"   {ticker:6} - {div_count:2} dividends - {name[:40]}")

    session.close()


if __name__ == '__main__':
    main()
