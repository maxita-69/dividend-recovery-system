#!/usr/bin/env python3
"""
Dividend Calendar - Calendario Dividendi Futuri
Recupera e visualizza i prossimi dividendi per il portfolio
Filtro per yield >= 3% (configurabile)
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import yfinance as yf
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from tabulate import tabulate

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))


from database.models import Base, Stock, Dividend, PriceData

# ---------------------------------------------------------
#  CONFIGURATION
# ---------------------------------------------------------

MIN_YIELD_PERCENT = 3.0
LOOKFORWARD_DAYS = 90

# 🔥 DATABASE UNICO E CORRETTO
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "dividend_recovery.db"

# ---------------------------------------------------------
#  DATABASE
# ---------------------------------------------------------

def get_session():
    """Crea sessione database"""
    engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


def get_current_price(session, stock_id):
    last_price = (
        session.query(PriceData)
        .filter_by(stock_id=stock_id)
        .order_by(PriceData.date.desc())
        .first()
    )
    return last_price.close if last_price else None


# ---------------------------------------------------------
#  DIVIDEND FETCHER
# ---------------------------------------------------------

def fetch_upcoming_dividend(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        dividend_rate = info.get('dividendRate')
        dividend_yield = info.get('dividendYield')
        ex_dividend_date = info.get('exDividendDate')
        current_price = info.get('currentPrice') or info.get('regularMarketPrice')

        if not dividend_rate or not current_price:
            return None

        if ex_dividend_date:
            ex_date = datetime.fromtimestamp(ex_dividend_date).date()
        else:
            return None

        today = datetime.now().date()
        if ex_date < today:
            return None

        if ex_date > today + timedelta(days=LOOKFORWARD_DAYS):
            return None

        frequency = info.get('dividendFrequency', 4)
        single_dividend = dividend_rate / frequency if frequency > 0 else dividend_rate

        dividend_yield_single = (single_dividend / current_price) * 100 if current_price > 0 else 0

        return {
            'ticker': ticker,
            'ex_date': ex_date,
            'amount': single_dividend,
            'pay_date': None,
            'current_price': current_price,
            'yield_percent': dividend_yield_single,
            'annual_rate': dividend_rate,
            'annual_yield': dividend_yield * 100 if dividend_yield else dividend_yield_single * frequency
        }

    except Exception:
        return None


def fetch_dividends_alternative(ticker):
    try:
        stock = yf.Ticker(ticker)
        dividends = stock.dividends

        if len(dividends) == 0:
            return None

        last_div_date = dividends.index[-1].date()
        last_div_amount = float(dividends.iloc[-1])

        if len(dividends) >= 2:
            dates = [d.date() for d in dividends.index[-5:]]
            intervals = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]
            avg_interval = sum(intervals) / len(intervals) if intervals else 90
        else:
            avg_interval = 90

        predicted_ex_date = last_div_date + timedelta(days=int(avg_interval))

        today = datetime.now().date()
        if predicted_ex_date < today or predicted_ex_date > today + timedelta(days=LOOKFORWARD_DAYS):
            return None

        info = stock.info
        current_price = info.get('currentPrice') or info.get('regularMarketPrice')

        if not current_price:
            return None

        dividend_yield = (last_div_amount / current_price) * 100 if current_price > 0 else 0

        return {
            'ticker': ticker,
            'ex_date': predicted_ex_date,
            'amount': last_div_amount,
            'pay_date': None,
            'current_price': current_price,
            'yield_percent': dividend_yield,
            'annual_rate': last_div_amount * (365 / avg_interval),
            'annual_yield': dividend_yield * (365 / avg_interval),
            'is_predicted': True
        }

    except Exception:
        return None


# ---------------------------------------------------------
#  CALENDAR BUILDER
# ---------------------------------------------------------

def build_dividend_calendar(session, min_yield=MIN_YIELD_PERCENT):
    print("=" * 80)
    print("📅 DIVIDEND CALENDAR - Prossimi Dividendi")
    print("=" * 80)

    stocks = session.query(Stock).all()
    print(f"📊 Analizzando {len(stocks)} titoli...\n")

    calendar = []

    for stock in stocks:
        ticker = stock.ticker

        div_info = fetch_upcoming_dividend(ticker)
        if not div_info:
            div_info = fetch_dividends_alternative(ticker)

        if not div_info:
            continue

        if div_info['yield_percent'] < min_yield:
            continue

        div_info['stock_name'] = stock.name or ticker
        div_info['market'] = stock.market
        div_info['currency'] = stock.currency

        calendar.append(div_info)

    calendar.sort(key=lambda x: x['ex_date'])
    return calendar


# ---------------------------------------------------------
#  OUTPUT
# ---------------------------------------------------------

def display_calendar(calendar_items):
    if not calendar_items:
        print("❌ Nessun dividendo trovato")
        return

    print("=" * 80)
    print("📅 CALENDARIO DIVIDENDI")
    print("=" * 80)

    table_data = []
    for item in calendar_items:
        days_until = (item['ex_date'] - datetime.now().date()).days

        row = [
            item['ticker'],
            item['stock_name'][:30],
            item['ex_date'].strftime('%Y-%m-%d'),
            f"{days_until}d",
            f"{item['amount']:.4f}",
            f"{item['current_price']:.2f}",
            f"{item['yield_percent']:.2f}%",
            f"{item['annual_yield']:.2f}%",
            "⚠️" if item.get('is_predicted') else "✓"
        ]
        table_data.append(row)

    headers = [
        'Ticker', 'Nome', 'Ex-Date', 'In', 'Dividendo',
        'Prezzo', 'Yield', 'Annual %', 'Status'
    ]

    print(tabulate(table_data, headers=headers, tablefmt='simple'))
    print()


# ---------------------------------------------------------
#  MAIN
# ---------------------------------------------------------

def main():
    session = get_session()
    calendar = build_dividend_calendar(session)
    display_calendar(calendar)
    print("=" * 80)
    print("✅ Aggiornamento calendario completato!")
    print("=" * 80)


if __name__ == "__main__":
    main()
