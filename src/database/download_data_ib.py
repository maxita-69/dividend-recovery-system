#!/usr/bin/env python3
"""
Download Stock Data - Versione Interactive Brokers (IBKR)
Popola il database SQLite con dati ufficiali da IBKR
"""

import sys
import time
import random
from pathlib import Path
from datetime import datetime, timedelta

# Fix per Python 3.12+ (event loop mancante)
import asyncio
asyncio.set_event_loop(asyncio.new_event_loop())

from ib_insync import IB, Stock as IBStock

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from database.models import Base, Stock, Dividend, PriceData, DataCollectionLog


# ---------------------------------------------------------
#  MAPPATURA COMPLETA YAHOO → IBKR
# ---------------------------------------------------------

IBKR_MAP = {
    # --- ITALIA (BVME / EUR) ---
    "BMPS.MI": ("BMPS", "BVME", "EUR"),
    "MB.MI": ("MB", "BVME", "EUR"),
    "BAMI.MI": ("BAMI", "BVME", "EUR"),
    "INW.MI": ("INW", "BVME", "EUR"),
    "BPSO.MI": ("BPSO", "BVME", "EUR"),
    "ENI.MI": ("ENI", "BVME", "EUR"),
    "ISP.MI": ("ISP", "BVME", "EUR"),
    "SPM.MI": ("SPM", "BVME", "EUR"),
    "NEXI.MI": ("NEXI", "BVME", "EUR"),
    "BPE.MI": ("BPE", "BVME", "EUR"),
    "PST.MI": ("PST", "BVME", "EUR"),
    "BMED.MI": ("BMED", "BVME", "EUR"),
    "ENEL.MI": ("ENEL", "BVME", "EUR"),
    "TEN.MI": ("TEN", "BVME", "EUR"),
    "SRG.MI": ("SRG", "BVME", "EUR"),
    "UNI.MI": ("UNI", "BVME", "EUR"),
    "AZM.MI": ("AZM", "BVME", "EUR"),
    "UCG.MI": ("UCG", "BVME", "EUR"),
    "G.MI": ("G", "BVME", "EUR"),
    "TRN.MI": ("TRN", "BVME", "EUR"),
    "A2A.MI": ("A2A", "BVME", "EUR"),
    "IG.MI": ("IG", "BVME", "EUR"),
    "HER.MI": ("HER", "BVME", "EUR"),
    "FBK.MI": ("FBK", "BVME", "EUR"),
    "REC.MI": ("REC", "BVME", "EUR"),
    "STLAM.MI": ("STLAM", "BVME", "EUR"),
    "MONC.MI": ("MONC", "BVME", "EUR"),
    "IVG.MI": ("IVG", "BVME", "EUR"),
    "AMP.MI": ("AMP", "BVME", "EUR"),
    "TIT.MI": ("TIT", "BVME", "EUR"),
    "LTMC.MI": ("LTMC", "BVME", "EUR"),
    "DIA.MI": ("DIA", "BVME", "EUR"),
    "BZU.MI": ("BZU", "BVME", "EUR"),
    "STM.MI": ("STM", "BVME", "EUR"),
    "CPR.MI": ("CPR", "BVME", "EUR"),
    "BC.MI": ("BC", "BVME", "EUR"),
    "PRY.MI": ("PRY", "BVME", "EUR"),
    "RACE.MI": ("RACE", "BVME", "EUR"),
    "LDO.MI": ("LDO", "BVME", "EUR"),
    "IP.MI": ("IP", "BVME", "EUR"),

    # --- USA (SMART / USD) ---
    "JNJ": ("JNJ", "SMART", "USD"),
    "PG": ("PG", "SMART", "USD"),
    "ABBV": ("ABBV", "SMART", "USD"),
    "PFE": ("PFE", "SMART", "USD"),
    "BMY": ("BMY", "SMART", "USD"),
    "MRK": ("MRK", "SMART", "USD"),
    "KO": ("KO", "SMART", "USD"),
    "PEP": ("PEP", "SMART", "USD"),
    "MCD": ("MCD", "SMART", "USD"),
    "MO": ("MO", "SMART", "USD"),
    "KMB": ("KMB", "SMART", "USD"),
    "GIS": ("GIS", "SMART", "USD"),
    "WEN": ("WEN", "SMART", "USD"),
    "CRI": ("CRI", "SMART", "USD"),
    "WMT": ("WMT", "SMART", "USD"),
    "TGT": ("TGT", "SMART", "USD"),
    "HD": ("HD", "SMART", "USD"),
    "BBY": ("BBY", "SMART", "USD"),
    "XOM": ("XOM", "SMART", "USD"),
    "CVX": ("CVX", "SMART", "USD"),
    "COP": ("COP", "SMART", "USD"),
    "EOG": ("EOG", "SMART", "USD"),
    "SLB": ("SLB", "SMART", "USD"),
    "HAL": ("HAL", "SMART", "USD"),
    "CTRA": ("CTRA", "SMART", "USD"),
    "APA": ("APA", "SMART", "USD"),
    "T": ("T", "SMART", "USD"),
    "VZ": ("VZ", "SMART", "USD"),
    "JPM": ("JPM", "SMART", "USD"),
    "BAC": ("BAC", "SMART", "USD"),
    "RF": ("RF", "SMART", "USD"),
    "FITB": ("FITB", "SMART", "USD"),
    "CMA": ("CMA", "SMART", "USD"),
    "COLB": ("COLB", "SMART", "USD"),
    "CVBF": ("CVBF", "SMART", "USD"),
    "BANR": ("BANR", "SMART", "USD"),
    "NWBI": ("NWBI", "SMART", "USD"),
    "CHCO": ("CHCO", "SMART", "USD"),
    "STBA": ("STBA", "SMART", "USD"),
    "GABC": ("GABC", "SMART", "USD"),
    "CINF": ("CINF", "SMART", "USD"),
    "RDN": ("RDN", "SMART", "USD"),
    "LMT": ("LMT", "SMART", "USD"),
    "UPS": ("UPS", "SMART", "USD"),
    "FAST": ("FAST", "SMART", "USD"),
    "ADM": ("ADM", "SMART", "USD"),
    "PKG": ("PKG", "SMART", "USD"),
    "AMCR": ("AMCR", "SMART", "USD"),
    "PH": ("PH", "SMART", "USD"),
    "WHR": ("WHR", "SMART", "USD"),
    "AFAM": ("AFAM", "SMART", "USD"),
    "ETD": ("ETD", "SMART", "USD"),
    "OXM": ("OXM", "SMART", "USD"),
    "MSFT": ("MSFT", "SMART", "USD"),
    "AAPL": ("AAPL", "SMART", "USD"),
    "INTC": ("INTC", "SMART", "USD"),
    "IBM": ("IBM", "SMART", "USD"),
    "CSCO": ("CSCO", "SMART", "USD"),
    "TXN": ("TXN", "SMART", "USD"),
    "PAYX": ("PAYX", "SMART", "USD"),
    "SWKS": ("SWKS", "SMART", "USD"),
    "NSP": ("NSP", "SMART", "USD"),
    "TROW": ("TROW", "SMART", "USD"),
    "UNM": ("UNM", "SMART", "USD"),
    "JHG": ("JHG", "SMART", "USD"),
    "ALV": ("ALV", "SMART", "USD"),
    "IPAR": ("IPAR", "SMART", "USD"),
    "LYB": ("LYB", "SMART", "USD"),
    "CF": ("CF", "SMART", "USD"),
    "FMC": ("FMC", "SMART", "USD"),
    "NXST": ("NXST", "SMART", "USD"),
    "MCS": ("MCS", "SMART", "USD"),
    "SIG": ("SIG", "SMART", "USD"),
    "CNS": ("CNS", "SMART", "USD"),
    "OZK": ("OZK", "SMART", "USD"),
    "MSM": ("MSM", "SMART", "USD"),
    "IBOC": ("IBOC", "SMART", "USD"),
    "WU": ("WU", "SMART", "USD"),
    "DH": ("DH", "SMART", "USD"),
    "GVMX": ("GVMX", "SMART", "USD"),
    "OFG": ("OFG", "SMART", "USD"),
    "FCF": ("FCF", "SMART", "USD"),
    "KFRC": ("KFRC", "SMART", "USD"),
    "CNA": ("CNA", "SMART", "USD"),
    "CPF": ("CPF", "SMART", "USD"),
    "TRFF": ("TRFF", "SMART", "USD"),
    "SRCE": ("SRCE", "SMART", "USD"),
    "PRFC": ("PRFC", "SMART", "USD"),
    "CWENA": ("CWENA", "SMART", "USD"),
    "F": ("F", "SMART", "USD"),
    "EWBC": ("EWBC", "SMART", "USD"),
}


# ---------------------------------------------------------
#  DATABASE SETUP (IBKR VERSION)
# ---------------------------------------------------------

def create_database(db_path='data/dividend_recovery_ib.db'):
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    print("USING IBKR DB:", Path(db_path).resolve())

    engine = create_engine(f'sqlite:///{db_path}', echo=False)
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    return Session()


# ---------------------------------------------------------
#  IBKR CONNECTION
# ---------------------------------------------------------

def connect_ibkr():
    ib = IB()
    print("🔌 Connecting to IBKR Gateway (porta 4001)...")
    ib.connect('127.0.0.1', 4001, clientId=1)
    print("   ✅ Connected to IBKR")
    return ib


# ---------------------------------------------------------
#  DOWNLOAD DATA FROM IBKR
# ---------------------------------------------------------

def download_stock_data_ib(ib, ticker, start_date='2020-01-01'):
    print(f"\n📊 IBKR Downloading {ticker}...")

    if ticker not in IBKR_MAP:
        print(f"   ❌ Ticker {ticker} non mappato per IBKR")
        return None

    ib_ticker, exchange, currency = IBKR_MAP[ticker]
    contract = IBStock(ib_ticker, exchange, currency)

    bars = ib.reqHistoricalData(
        contract,
        endDateTime='',
        durationStr='10 Y',
        barSizeSetting='1 day',
        whatToShow='ADJUSTED_LAST',
        useRTH=False,
        formatDate=1
    )

    if not bars:
        print(f"   ❌ No price data from IBKR for {ticker}")
        return None

    prices = []
    for bar in bars:
        prices.append({
            'date': bar.date,
            'open': bar.open,
            'high': bar.high,
            'low': bar.low,
            'close': bar.close,
            'volume': bar.volume
        })

    divs = ib.reqDividends(contract)
    dividends = []
    for d in divs:
        dividends.append({
            'ex_date': d.exDate,
            'amount': d.amount
        })

    print(f"   ✅ Downloaded {len(prices)} price records")
    print(f"   ✅ Downloaded {len(dividends)} dividend records")

    return {
        'name': ib_ticker,
        'prices': prices,
        'dividends': dividends
    }


# ---------------------------------------------------------
#  SAVE TO DATABASE
# ---------------------------------------------------------

def save_to_database(session, ticker, data):
    print(f"\n💾 Saving {ticker} to IBKR database...")

    stock = session.query(Stock).filter_by(ticker=ticker).first()

    if not stock:
        market = 'Italy' if ticker.endswith('.MI') else 'USA'
        stock = Stock(
            ticker=ticker,
            name=data['name'],
            market=market,
            sector='Unknown'
        )
        session.add(stock)
        session.flush()
        print(f"   ✅ Created stock record")

    prices_saved = 0
    for row in data['prices']:
        existing = session.query(PriceData).filter_by(
            stock_id=stock.id,
            date=row['date']
        ).first()

        if not existing:
            price = PriceData(
                stock_id=stock.id,
                date=row['date'],
                open=row['open'],
                high=row['high'],
                low=row['low'],
                close=row['close'],
                volume=row['volume'],
                adjusted_close=row['close']
            )
            session.add(price)
            prices_saved += 1

    print(f"   ✅ Saved {prices_saved} new price records")

    dividends_saved = 0
    for d in data['dividends']:
        existing = session.query(Dividend).filter_by(
            stock_id=stock.id,
            ex_date=d['ex_date']
        ).first()

        if not existing:
            dividend = Dividend(
                stock_id=stock.id,
                ex_date=d['ex_date'],
                amount=d['amount'],
                dividend_type='ordinary'
            )
            session.add(dividend)
            dividends_saved += 1

    print(f"   ✅ Saved {dividends_saved} new dividend records")

    log = DataCollectionLog(
        source='IBKR',
        operation='download',
        stock_ticker=ticker,
        status='success',
        records_processed=prices_saved + dividends_saved,
        message=f"IBKR: {prices_saved} prices, {dividends_saved} dividends"
    )
    session.add(log)

    session.commit()
    print(f"   ✅ All data committed to IBKR database")


# ---------------------------------------------------------
#  MAIN
# ---------------------------------------------------------

def main():
    print("=" * 60)
    print("DIVIDEND RECOVERY SYSTEM - IBKR DATA DOWNLOAD")
    print("=" * 60)

    session = create_database()
    ib = connect_ibkr()

    tickers = list(IBKR_MAP.keys())  # tutti i 127 ticker

    for ticker in tickers:
        data = download_stock_data_ib(ib, ticker)

        if data:
            save_to_database(session, ticker, data)

        time.sleep(random.uniform(1.0, 2.0))

    print("\n" + "=" * 60)
    print("✅ IBKR DOWNLOAD COMPLETED")
    print("=" * 60)


if __name__ == '__main__':
    main()
