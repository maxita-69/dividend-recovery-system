"""
Hybrid Download System - Usa provider diversi per ticker diversi
- Titoli USA: FMP (richiede API key)
- Titoli Italiani (.MI): Yahoo Finance (gratuito)
"""

import sys
import time
import random
from pathlib import Path
from datetime import datetime, timedelta, date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.database.models import Base, Stock, Dividend, PriceData
from providers.provider_manager import get_provider


def parse_date(date_str):
    """
    Converte stringa 'YYYY-MM-DD' in datetime.date object.
    Se input è None o già un date object, ritorna as-is.

    Args:
        date_str: Stringa data 'YYYY-MM-DD', date object, o None

    Returns:
        datetime.date object o None
    """
    if date_str is None:
        return None
    if isinstance(date_str, date):
        return date_str
    if isinstance(date_str, str):
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    return date_str


def create_database(db_path='data/dividend_recovery.db'):
    """Crea database e tabelle se non esistono"""
    db_file = project_root / db_path
    db_file.parent.mkdir(parents=True, exist_ok=True)

    engine = create_engine(f'sqlite:///{db_file}', echo=False)
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    return Session()


def get_provider_for_ticker(ticker: str):
    """
    Determina quale provider usare in base al ticker.

    - Titoli italiani (.MI) → Yahoo Finance
    - Altri titoli (USA, etc.) → FMP
    """
    if ticker.endswith('.MI'):
        return get_provider('YAHOO'), 'Yahoo Finance'
    else:
        return get_provider('FMP'), 'FMP'


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


def download_ticker_data(ticker, provider, start_date, end_date=None):
    """Scarica dati usando il provider specificato"""
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')

    try:
        # Fetch prices
        prices = provider.fetch_prices(
            ticker,
            start_date=start_date,
            end_date=end_date
        )

        # Fetch dividends
        dividends = provider.fetch_dividends(
            ticker,
            start_date=start_date,
            end_date=end_date
        )

        return {
            'prices': prices,
            'dividends': dividends,
            'name': ticker  # Provider-specific name retrieval can be added
        }, None

    except Exception as e:
        return None, str(e)


def save_to_database(session, ticker, data):
    """Salva dati nel database"""

    # Trova o crea lo stock
    stock = session.query(Stock).filter_by(ticker=ticker).first()
    if not stock:
        stock = Stock(
            ticker=ticker,
            name=data.get('name', ticker),
            sector='Unknown',
            created_at=datetime.now()
        )
        session.add(stock)
        session.flush()

    # Salva prices
    prices_saved = 0
    for price_record in data['prices']:
        # Check if already exists
        existing = session.query(PriceData).filter_by(
            stock_id=stock.id,
            date=price_record['date']
        ).first()

        if not existing:
            price = PriceData(
                stock_id=stock.id,
                date=parse_date(price_record['date']),
                open=price_record.get('open'),
                high=price_record.get('high'),
                low=price_record.get('low'),
                close=price_record.get('close'),
                volume=price_record.get('volume', 0)
            )
            session.add(price)
            prices_saved += 1

    # Salva dividends
    dividends_saved = 0
    for div_record in data['dividends']:
        # Check if already exists
        existing = session.query(Dividend).filter_by(
            stock_id=stock.id,
            ex_date=div_record['ex_date']
        ).first()

        if not existing:
            dividend = Dividend(
                stock_id=stock.id,
                ex_date=parse_date(div_record['ex_date']),
                amount=div_record['amount'],
                payment_date=parse_date(div_record.get('payment_date')),
                record_date=parse_date(div_record.get('record_date'))
            )
            session.add(dividend)
            dividends_saved += 1

    session.commit()

    return prices_saved, dividends_saved


def download_tickers(tickers, session=None, progress_callback=None, start_date='2020-01-01'):
    """
    Scarica dati per una lista di tickers usando provider ibridi.

    Args:
        tickers: Lista di ticker da scaricare
        session: SQLAlchemy session (se None, ne crea uno nuovo)
        progress_callback: Funzione callback(ticker, idx, total, status, message)
        start_date: Data di inizio download (default: 2020-01-01)

    Returns:
        dict: Statistiche download {success, errors, skipped}
    """
    if session is None:
        session = create_database()
        close_session = True
    else:
        close_session = False

    stats = {'success': 0, 'errors': 0, 'skipped': 0}

    for idx, ticker in enumerate(tickers, 1):

        try:
            # Determina provider
            provider, provider_name = get_provider_for_ticker(ticker)

            if progress_callback:
                progress_callback(ticker, idx, len(tickers), 'checking', f'Checking {ticker}...')

            # Check dati esistenti
            last_date = get_last_price_date(session, ticker)

            if last_date:
                # Download incrementale
                download_start = (last_date + timedelta(days=1)).strftime('%Y-%m-%d')
                today = datetime.now().strftime('%Y-%m-%d')

                if download_start >= today:
                    if progress_callback:
                        progress_callback(ticker, idx, len(tickers), 'skipped', 'Already up-to-date')
                    stats['skipped'] += 1
                    continue

                print(f"\n🔍 [{idx}/{len(tickers)}] Checking existing data for {ticker}...")
                print(f"   📅 Last price in DB: {last_date}")
            else:
                download_start = start_date
                print(f"\n📥 [{idx}/{len(tickers)}] New ticker: {ticker}")

            # Download
            if progress_callback:
                progress_callback(ticker, idx, len(tickers), 'downloading', f'Downloading from {provider_name}...')

            print(f"\n📊 Downloading {ticker} from {provider_name}...")
            print(f"   Period: {download_start} to {datetime.now().strftime('%Y-%m-%d')}")

            data, error = download_ticker_data(ticker, provider, download_start)

            if error:
                print(f"   ❌ Error: {error}")
                if progress_callback:
                    progress_callback(ticker, idx, len(tickers), 'error', f'Error: {error}')
                stats['errors'] += 1

                # Rate limiting pause anche in caso di errore
                time.sleep(random.uniform(1.0, 3.0))
                continue

            if not data or not data['prices']:
                print(f"   ❌ No data found")
                if progress_callback:
                    progress_callback(ticker, idx, len(tickers), 'error', 'No data found')
                stats['errors'] += 1
                continue

            # Save to DB
            prices_saved, divs_saved = save_to_database(session, ticker, data)

            print(f"   ✅ Saved {prices_saved} prices, {divs_saved} dividends")
            if progress_callback:
                progress_callback(ticker, idx, len(tickers), 'success', f'Saved {prices_saved} prices, {divs_saved} dividends')

            stats['success'] += 1

            # Rate limiting
            time.sleep(random.uniform(1.0, 3.0))

        except Exception as e:
            print(f"   ❌ Failed to download {ticker}: {str(e)}")
            if progress_callback:
                progress_callback(ticker, idx, len(tickers), 'error', str(e))
            stats['errors'] += 1

            # Rate limiting anche in caso di errore
            time.sleep(random.uniform(1.0, 3.0))

    if close_session:
        session.close()

    return stats


if __name__ == "__main__":
    # Test con alcuni ticker
    test_tickers = [
        'AAPL',      # USA → FMP
        'ENEL.MI',   # Italia → Yahoo
        'MSFT',      # USA → FMP
        'STM.MI'     # Italia → Yahoo
    ]

    print("🚀 Starting Hybrid Download Test...")
    print(f"Tickers: {test_tickers}")
    print("=" * 50)

    session = create_database()
    stats = download_tickers(test_tickers, session=session)

    print("\n" + "=" * 50)
    print("📊 Download Statistics:")
    print(f"   ✅ Success: {stats['success']}")
    print(f"   ❌ Errors: {stats['errors']}")
    print(f"   ⏭️  Skipped: {stats['skipped']}")
