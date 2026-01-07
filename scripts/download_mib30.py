"""
Download FTSE MIB 40 tickers safely
Compatible with your dividend_recovery.db structure
"""

# Opzionale: randomizza l'ordine per evitare pattern riconoscibili
import random
random.shuffle(MIB30_TICKERS)

import sys
import time
import logging
from pathlib import Path
from datetime import datetime, timedelta

import yfinance as yf
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from database.models import Base, Stock, Dividend, PriceData, DataCollectionLog

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    handlers=[
        logging.FileHandler("mib30_download.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# =================================================================
# CONFIG
# =================================================================
DB_PATH = Path(__file__).parent.parent / "data" / "dividend_recovery.db"
START_DATE = "2020-01-01"
END_DATE = datetime.now().strftime("%Y-%m-%d")

# FTSE MIB 40 (aggiornato a gennaio 2026)
MIB30_TICKERS = [
    'ENEL.MI', 'INTZ.MI', 'ISP.MI', 'LDO.MI', 'STM.MI', 'UCG.MI',
    'UNI.MI', 'EXO.MI', 'DIA.MI', 'REC.MI', 'BPER.MI', 'SFER.MI',
    'TIT.MI', 'CNHI.MI', 'G.MI', 'MS.MI', 'MONC.MI', 'PRY.MI',
    'STLAM.MI', 'AZM.MI', 'CPR.MI', 'FCAU.MI', 'PIRC.MI', 'BZU.MI',
    'A2A.MI', 'ATL.MI', 'BAMI.MI', 'NEXI.MI', 'RACE.MI', 'SFERE.MI',
    'SUS.MI', 'TITB.MI', 'TRN.MI', 'URG.MI', 'VLG.MI', 'YDR.MI',
    'ZC.MI', 'AGL.MI', 'BA.MI', 'BRC.MI'
]

# =================================================================
# FUNZIONI
# =================================================================

def create_database():
    """Crea DB se non esiste"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


def safe_download(ticker, start_date, end_date, retries=2):
    """Scarica con retry e gestione errori"""
    for attempt in range(retries + 1):
        try:
            logger.info(f"[{ticker}] Tentativo {attempt + 1}/{retries + 1}")
            stock = yf.Ticker(ticker)
            
            # Scarica con auto_adjust=False per dati non-adjusted
            hist = stock.history(
                start=start_date,
                end=end_date,
                auto_adjust=False,
                back_adjust=False,
                timeout=15
            )
            
            if hist.empty:
                logger.warning(f"[{ticker}] Dati storici vuoti")
                return None, None
            
            dividends = stock.dividends
            dividends = dividends[dividends.index >= start_date]
            
            info = stock.info
            name = info.get('longName', ticker)
            
            logger.info(f"[{ticker}] ✓ {len(hist)} prezzi, {len(dividends)} dividendi")
            return {
                'name': name,
                'prices': hist,
                'dividends': dividends,
                'info': info
            }, None
            
        except Exception as e:
            logger.error(f"[{ticker}] Errore: {str(e)}")
            if attempt < retries:
                time.sleep(3)
            else:
                return None, str(e)
    
    return None, "Tutti i tentativi falliti"


def save_to_database(session, ticker, data):
    """Salva come nel tuo script originale"""
    stock = session.query(Stock).filter_by(ticker=ticker).first()
    if not stock:
        market = 'Italy'
        stock = Stock(
            ticker=ticker,
            name=data['name'],
            market=market,
            sector=data['info'].get('sector', 'Unknown')
        )
        session.add(stock)
        session.flush()
        logger.info(f"Creato nuovo stock: {ticker}")
    
    # Prezzi
    prices_saved = 0
    for date, row in data['prices'].iterrows():
        # Evita dati nulli
        if pd.isna(row['Open']) or pd.isna(row['Close']):
            continue
            
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
                volume=int(row['Volume']) if not pd.isna(row['Volume']) else 0,
                adjusted_close=float(row['Close'])
            )
            session.add(price)
            prices_saved += 1
    
    # Dividendi
    dividends_saved = 0
    for date, amount in data['dividends'].items():
        if pd.isna(amount) or amount <= 0:
            continue
            
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
    
    try:
        session.commit()
        logger.info(f"[{ticker}] Salvati {prices_saved} prezzi, {dividends_saved} dividendi")
        return True
    except Exception as e:
        session.rollback()
        logger.error(f"[{ticker}] Errore salvataggio: {e}")
        return False


# =================================================================
# MAIN
# =================================================================

def main():
    logger.info("=" * 60)
    logger.info("DOWNLOAD FTSE MIB 40 - SAFE MODE (3s delay)")
    logger.info(f"Ticker: {len(MIB30_TICKERS)}")
    logger.info(f"Periodo: {START_DATE} → {END_DATE}")
    logger.info("=" * 60)
    
    session = create_database()
    success_count = 0
    error_list = []
    
    for i, ticker in enumerate(MIB30_TICKERS, 1):
        logger.info(f"\n--- [{i}/{len(MIB30_TICKERS)}] {ticker} ---")
        
        # Download
        data, error = safe_download(ticker, START_DATE, END_DATE)
        
        if data:
            # Salva
            if save_to_database(session, ticker, data):
                success_count += 1
            else:
                error_list.append(f"{ticker}: salvataggio fallito")
        else:
            error_list.append(f"{ticker}: {error or 'dati vuoti'}")
        
        # ✅ PAUSA SICURA: 3 secondi tra un ticker e l'altro
        if i < len(MIB30_TICKERS):  # non serve dopo l'ultimo
            logger.info(f"Attesa 3 secondi prima del prossimo...")
            time.sleep(3)
    
    # Log finale
    logger.info("\n" + "=" * 60)
    logger.info(f"✅ Completato: {success_count}/{len(MIB30_TICKERS)} ticker")
    if error_list:
        logger.warning("⚠️ Errori:")
        for err in error_list:
            logger.warning(f"  - {err}")
    
    session.close()


if __name__ == "__main__":
    main()