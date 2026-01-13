"""
Download Stock Data con FMP Provider
Scarica dati storici completi o incrementali dal Financial Modeling Prep
Popola il database SQLite
"""

import sys
import time
import random
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add paths
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.database.models import Base, Stock, Dividend, PriceData, DataCollectionLog
from providers import get_provider


# ---------------------------------------------------------
#  DATABASE SETUP
# ---------------------------------------------------------

def create_database(db_path='data/dividend_recovery.db'):
    """Crea database e tabelle se non esistono"""
    db_full_path = project_root / db_path
    db_full_path.parent.mkdir(parents=True, exist_ok=True)
    print("USING DB:", db_full_path.resolve())

    engine = create_engine(f'sqlite:///{db_full_path}', echo=False)
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    return Session()


def get_last_price_date(session, ticker):
    """Ritorna l'ultima data disponibile nel DB per un ticker, oppure None."""
    stock = session.query(Stock).filter_by(ticker=ticker).first()
    if not stock:
        return None

    last_price = (
        session.query(PriceData)
        .filter_by(stock_id=stock.id)
        .order_by(PriceData.date.desc())
        .first()
    )

    return last_price.date if last_price else None


# ---------------------------------------------------------
#  DOWNLOAD DATA CON FMP
# ---------------------------------------------------------

def download_stock_data_fmp(ticker, start_date='2020-01-01', end_date=None):
    """
    Scarica dati storici da FMP Provider

    Returns:
        tuple: (data_dict, error_message)
        data_dict contiene: {'name': str, 'prices': DataFrame, 'dividends': list, 'info': dict}
    """
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')

    print(f"\n📊 Downloading {ticker} from FMP...")
    print(f"   Period: {start_date} to {end_date}")

    try:
        # Ottieni provider FMP
        provider = get_provider("FMP")

        # 1. Scarica dati storici prezzi
        prices_data = provider.fetch_prices(ticker)

        if not prices_data:
            print(f"   ❌ No price data found for {ticker}")
            return None, "No price data available"

        # Converti in DataFrame pandas
        df = pd.DataFrame(prices_data)

        # FMP restituisce: date, open, high, low, close, volume
        # Convertiamo date da string a datetime e la settiamo come index
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')

        # Rinomina colonne per compatibilità con database
        df = df.rename(columns={
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume'
        })

        # Filtra per date range
        df = df[(df.index >= start_date) & (df.index <= end_date)]

        if df.empty:
            print(f"   ❌ No data in date range for {ticker}")
            return None, "No data in specified date range"

        # 2. Scarica profilo azienda
        profile = provider.get_profile(ticker)
        stock_name = profile.get('companyName', ticker) if profile else ticker
        sector = profile.get('sector', 'Unknown') if profile else 'Unknown'

        # 3. Scarica dividendi (potrebbe non essere disponibile in free plan)
        dividends_list = []
        try:
            dividends_data = provider.fetch_dividends(ticker)
            if dividends_data:
                # FMP dividends: [{date, dividend}, ...]
                for div in dividends_data:
                    div_date = pd.to_datetime(div.get('date'))
                    div_amount = float(div.get('dividend', 0))
                    if div_date >= pd.to_datetime(start_date):
                        dividends_list.append({'date': div_date, 'amount': div_amount})
        except Exception as e:
            print(f"   ⚠️  Dividends not available (free plan limitation): {e}")

        print(f"   ✅ Downloaded {len(df)} price records")
        print(f"   ✅ Downloaded {len(dividends_list)} dividend records")

        return {
            'name': stock_name,
            'prices': df,
            'dividends': dividends_list,
            'info': {'sector': sector}
        }, None

    except Exception as e:
        error_msg = str(e)
        print(f"   ❌ Error: {error_msg}")
        return None, error_msg


# ---------------------------------------------------------
#  SAVE TO DATABASE
# ---------------------------------------------------------

def save_to_database(session, ticker, data):
    """Salva dati nel database"""
    print("\n📈 PRIME RIGHE DEI PREZZI:")
    print(data['prices'][['Open', 'High', 'Low', 'Close']].head())
    print(f"\n💾 Saving {ticker} to database...")

    # Check if stock exists
    stock = session.query(Stock).filter_by(ticker=ticker).first()

    if stock:
        print(f"   ℹ️  Stock {ticker} already exists, updating...")
    else:
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
    for div in data['dividends']:
        existing = session.query(Dividend).filter_by(
            stock_id=stock.id,
            ex_date=div['date'].date()
        ).first()

        if not existing:
            dividend = Dividend(
                stock_id=stock.id,
                ex_date=div['date'].date(),
                amount=float(div['amount']),
                dividend_type='ordinary'
            )
            session.add(dividend)
            dividends_saved += 1

    print(f"   ✅ Saved {dividends_saved} new dividend records")

    # Log operation
    log = DataCollectionLog(
        source='fmp_provider',
        operation='download',
        stock_ticker=ticker,
        status='success',
        records_processed=prices_saved + dividends_saved,
        message=f"Downloaded {prices_saved} prices, {dividends_saved} dividends"
    )
    session.add(log)

    session.commit()
    print(f"   ✅ All data committed to database")


# ---------------------------------------------------------
#  MAIN
# ---------------------------------------------------------

def download_tickers(tickers, session=None, progress_callback=None):
    """
    Scarica lista di ticker

    Args:
        tickers: Lista di ticker da scaricare
        session: Sessione database (opzionale, ne crea una se None)
        progress_callback: Funzione callback(ticker, index, total, status, message)

    Returns:
        dict: Summary con statistiche download
    """
    if session is None:
        session = create_database()
        close_session = True
    else:
        close_session = False

    stats = {'success': 0, 'errors': 0, 'skipped': 0}

    total = len(tickers)
    for idx, ticker in enumerate(tickers, 1):
        print(f"\n🔍 [{idx}/{total}] Checking existing data for {ticker}...")

        if progress_callback:
            progress_callback(ticker, idx, total, 'checking', f'Checking {ticker}')

        last_date = get_last_price_date(session, ticker)

        if last_date:
            print(f"   📅 Last price in DB: {last_date}")
            start_date = (last_date + timedelta(days=1)).strftime('%Y-%m-%d')

            # Se l'ultimo dato è recentissimo, skip
            if (datetime.now().date() - last_date).days < 2:
                print(f"   ⏭️  Data already up-to-date, skipping")
                stats['skipped'] += 1
                if progress_callback:
                    progress_callback(ticker, idx, total, 'skipped', 'Already up-to-date')
                continue
        else:
            print(f"   🆕 No data found in DB, full download from 2020")
            start_date = "2020-01-01"

        if progress_callback:
            progress_callback(ticker, idx, total, 'downloading', f'Downloading {ticker}')

        data, error = download_stock_data_fmp(ticker, start_date=start_date)

        if data:
            save_to_database(session, ticker, data)
            stats['success'] += 1
            if progress_callback:
                progress_callback(ticker, idx, total, 'success', f'Downloaded {ticker}')
        else:
            print(f"\n❌ Failed to download {ticker}: {error}")
            stats['errors'] += 1

            log = DataCollectionLog(
                source='fmp_provider',
                operation='download',
                stock_ticker=ticker,
                status='error',
                message=error
            )
            session.add(log)
            session.commit()

            if progress_callback:
                progress_callback(ticker, idx, total, 'error', error)

        # Rate limiting per evitare di superare limite API
        if idx < total:  # Non aspettare dopo l'ultimo
            sleep_time = random.uniform(1.0, 2.0)
            print(f"⏳ Waiting {sleep_time:.1f} seconds (API rate limiting)...")
            time.sleep(sleep_time)

    if close_session:
        session.close()

    return stats


def main():
    """Main execution con lista ticker predefinita"""
    print("=" * 60)
    print("DIVIDEND RECOVERY SYSTEM - FMP DATA DOWNLOAD")
    print("=" * 60)

    session = create_database()

    # Lista ticker completa (come da download_stock_data_v2.py)
    tickers = [
        # TITOLI ITALIANI
        "ENEL.MI", "ENI.MI", "ISP.MI", "UCG.MI", "G.MI",
        "TRN.MI", "SRG.MI", "TEN.MI", "NEXI.MI", "STM.MI",

        # TITOLI USA (sample per test - aggiungi altri dopo test)
        "AAPL", "MSFT", "JNJ", "KO", "PG",
        "XOM", "CVX", "T", "VZ", "JPM"
    ]

    stats = download_tickers(tickers, session)

    print("\n" + "=" * 60)
    print("✅ DOWNLOAD COMPLETED")
    print("=" * 60)

    # Summary
    n_stocks = session.query(Stock).count()
    n_prices = session.query(PriceData).count()
    n_dividends = session.query(Dividend).count()

    print(f"\n📊 DOWNLOAD STATS:")
    print(f"   Success: {stats['success']}")
    print(f"   Errors: {stats['errors']}")
    print(f"   Skipped: {stats['skipped']}")

    print(f"\n📊 DATABASE SUMMARY:")
    print(f"   Stocks: {n_stocks}")
    print(f"   Price records: {n_prices}")
    print(f"   Dividend records: {n_dividends}")

    session.close()


if __name__ == '__main__':
    main()
