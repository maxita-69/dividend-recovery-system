"""
Update Dividend Data from Interactive Brokers
Scarica dividendi ufficiali (ex-date, amount, payout, ecc.)
"""

import sys
from pathlib import Path
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from database.models import Stock, Dividend, DataCollectionLog
from ibkr_dividend_downloader import download_dividend_data


# ============================================================
# Connessione al database
# ============================================================

def create_database_session(db_path='data/dividend_recovery.db'):
    engine = create_engine(f'sqlite:///{db_path}', echo=False)
    Session = sessionmaker(bind=engine)
    return Session()


# ============================================================
# Salvataggio dividendi IBKR
# ============================================================

def save_dividend_to_db(session, stock, div_data):
    """Salva i dati dei dividendi ufficiali nel database."""

    dividend = Dividend(
        stock_id=stock.id,
        ex_date=div_data.get("ex_date"),
        amount=div_data.get("last_dividend"),
        dividend_type="official"
    )

    session.add(dividend)
    session.commit()

    print(f"💾 Salvato dividendo ufficiale per {stock.ticker}: {div_data.get('last_dividend')}")


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 60)
    print("DIVIDEND RECOVERY SYSTEM - IBKR DIVIDEND UPDATE")
    print("=" * 60)

    session = create_database_session()

    stocks = session.query(Stock).all()
    print(f"📋 Trovati {len(stocks)} titoli nel database\n")

    for stock in stocks:
        print(f"\n➡️ Elaboro {stock.ticker}...")

        div_data = download_dividend_data(stock.ticker)

        if div_data:
            save_dividend_to_db(session, stock, div_data)

            # Log
            log = DataCollectionLog(
                source="IBKR",
                operation="dividend_update",
                stock_ticker=stock.ticker,
                status="success",
                records_processed=1,
                message="Dividend updated from IBKR"
            )
            session.add(log)
            session.commit()

        else:
            print(f"⚠️ Nessun dato ricevuto per {stock.ticker}")

    session.close()
    print("\n🎉 Aggiornamento dividendi IBKR completato!")


if __name__ == "__main__":
    main()
