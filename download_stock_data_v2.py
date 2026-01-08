"""
Download Stock Data - Scarica dati storici completi o incrementali
Popola il database SQLite con dati da Yahoo Finance
"""

import sys
import time
import random
from pathlib import Path
from datetime import datetime, timedelta
import yfinance as yf
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from database.models import Base, Stock, Dividend, PriceData, DataCollectionLog


# ---------------------------------------------------------
#  DATABASE SETUP
# ---------------------------------------------------------

def create_database(db_path='data/dividend_recovery.db'):
    """Crea database e tabelle se non esistono"""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    engine = create_engine(f'sqlite:///{db_path}', echo=False)
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
#  DOWNLOAD DATA
# ---------------------------------------------------------

def download_stock_data(ticker, start_date='2020-01-01', end_date=None):
    """Scarica dati storici da Yahoo Finance"""
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    print(f"\n📊 Downloading {ticker}...")
    print(f"   Period: {start_date} to {end_date}")
    
    try:
        stock = yf.Ticker(ticker)

        # ⚠️ Dati NON aggiustati
        hist = stock.history(start=start_date, end=end_date, auto_adjust=False, back_adjust=False)
        
        if hist.empty:
            print(f"   ❌ No price data found for {ticker}")
            return None, None
        
        # Dividendi
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


# ---------------------------------------------------------
#  MAIN
# ---------------------------------------------------------

def main():
    print("=" * 60)
    print("DIVIDEND RECOVERY SYSTEM - DATA DOWNLOAD")
    print("=" * 60)
    
    session = create_database()

    # Inserisci qui la tua lista completa di ticker
    tickers = [
    # --- TITOLI ITALIANI ---
    "BMPS.MI",      # Banca MPS
    "MB.MI",        # Mediobanca
    "BAMI.MI",      # Banco BPM
    "INW.MI",       # Inwit
    "BPSO.MI",      # Banca Popolare di Sondrio
    "ENI.MI",       # Eni
    "ISP.MI",       # Intesa Sanpaolo
    "SPM.MI",       # Saipem
    "NEXI.MI",      # Nexi
    "BPE.MI",       # BPER Banca
    "PST.MI",       # Poste Italiane
    "BMED.MI",      # Banca Mediolanum
    "ENEL.MI",      # Enel
    "TEN.MI",       # Tenaris
    "SRG.MI",       # Snam
    "UNI.MI",       # Unipol Gruppo
    "AZM.MI",       # Azimut
    "UCG.MI",       # UniCredit
    "G.MI",         # Generali Assicurazioni
    "TRN.MI",       # Terna
    "A2A.MI",       # A2A
    "IG.MI",        # Italgas
    "HER.MI",       # Hera
    "FBK.MI",       # FinecoBank
    "REC.MI",       # Recordati
    "STLAM.MI",     # Stellantis
    "MONC.MI",      # Moncler
    "IVG.MI",       # Iveco Group
    "AMP.MI",       # Amplifon
    "TIT.MI",       # Telecom Italia
    "LTMC.MI",      # Lottomatica
    "DIA.MI",       # Diasorin
    "BZU.MI",       # Buzzi
    "STM.MI",       # STMicroelectronics
    "CPR.MI",       # Campari
    "BC.MI",        # Brunello Cucinelli
    "PRY.MI",       # Prysmian
    "RACE.MI",      # Ferrari
    "LDO.MI",       # Leonardo
    "IP.MI",        # Interpump Group

    # --- TITOLI USA (Dividend Aristocrats & High Quality) ---
    # Healthcare & Consumer Staples
    "JNJ",          # Johnson & Johnson - Dividend Aristocrat
    "PG",           # Procter & Gamble - Dividend Aristocrat
    "KO",           # Coca-Cola - Dividend Aristocrat
    "PEP",          # PepsiCo - Dividend Aristocrat
    "MCD",          # McDonald's - Dividend Aristocrat

    # Energy
    "XOM",          # Exxon Mobil - Dividend Aristocrat
    "CVX",          # Chevron - Dividend Aristocrat

    # Retail
    "WMT",          # Walmart - Dividend Aristocrat
    "TGT",          # Target - Dividend Aristocrat
    "HD",           # Home Depot

    # Telecom (High Yield)
    "T",            # AT&T - High yield
    "VZ",           # Verizon - Stable dividend

    # Pharma
    "ABBV",         # AbbVie - High yield
    "PFE",          # Pfizer

    # Financials
    "JPM",          # JP Morgan Chase
    "BAC",          # Bank of America

    # Technology (Dividend Payers)
    "MSFT",         # Microsoft
    "AAPL",         # Apple
    "INTC",         # Intel
    "IBM",          # IBM - Long dividend history
]


    for ticker in tickers:
        print(f"\n🔍 Checking existing data for {ticker}...")

        last_date = get_last_price_date(session, ticker)

        if last_date:
            print(f"   📅 Last price in DB: {last_date}")
            start_date = (last_date + timedelta(days=1)).strftime('%Y-%m-%d')
        else:
            print(f"   🆕 No data found in DB, full download from 2020")
            start_date = "2020-01-01"

        data, error = download_stock_data(ticker, start_date=start_date)

        if data:
            save_to_database(session, ticker, data)
        else:
            print(f"\n❌ Failed to download {ticker}: {error}")
            log = DataCollectionLog(
                source='yahoo_finance',
                operation='download',
                stock_ticker=ticker,
                status='error',
                message=error
            )
            session.add(log)
            session.commit()

        # 🐌 Slow down to avoid Yahoo throttling
        sleep_time = random.uniform(1.5, 4.0)
        print(f"⏳ Waiting {sleep_time:.1f} seconds to avoid Yahoo throttling...")
        time.sleep(sleep_time)

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
