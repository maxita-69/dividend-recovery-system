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
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from database.models import Base, Stock, Dividend, PriceData

# ---------------------------------------------------------
#  CONFIGURATION
# ---------------------------------------------------------

MIN_YIELD_PERCENT = 3.0  # Yield minimo per essere incluso nel calendario
LOOKFORWARD_DAYS = 90    # Quanti giorni nel futuro guardare
DB_PATH = 'data/dividend_recovery.db'

# ---------------------------------------------------------
#  DATABASE
# ---------------------------------------------------------

def get_session(db_path=DB_PATH):
    """Crea sessione database"""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f'sqlite:///{db_path}', echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


def get_current_price(session, stock_id):
    """Recupera l'ultimo prezzo disponibile dal database"""
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
    """
    Recupera info sul prossimo dividendo da Yahoo Finance

    Returns:
        dict con: ex_date, amount, pay_date, current_price, yield
        None se nessun dividendo trovato o errore
    """
    try:
        stock = yf.Ticker(ticker)

        # Info dividendo
        info = stock.info

        # Prova a ottenere prossima ex-date e amount
        dividend_rate = info.get('dividendRate')  # Annuale
        dividend_yield = info.get('dividendYield')  # Yield %
        ex_dividend_date = info.get('exDividendDate')
        current_price = info.get('currentPrice') or info.get('regularMarketPrice')

        if not dividend_rate or not current_price:
            return None

        # Converti ex_dividend_date da timestamp a date
        if ex_dividend_date:
            ex_date = datetime.fromtimestamp(ex_dividend_date).date()
        else:
            # Se non c'è ex-date, usa l'ultima nota + pattern storico
            # Per ora skippiamo se non abbiamo ex-date futura
            return None

        # Verifica che la ex-date sia nel futuro
        today = datetime.now().date()
        if ex_date < today:
            # Dividendo già passato, non incluso nel calendario futuro
            return None

        # Se ex-date è troppo lontana, skippa
        if ex_date > today + timedelta(days=LOOKFORWARD_DAYS):
            return None

        # Calcola yield (per singolo dividendo)
        # dividend_rate è annuale, dividiamo per frequenza
        # Assumiamo quarterly (4x/anno) come default per USA
        frequency = info.get('dividendFrequency', 4)
        single_dividend = dividend_rate / frequency if frequency > 0 else dividend_rate

        dividend_yield_single = (single_dividend / current_price) * 100 if current_price > 0 else 0

        result = {
            'ticker': ticker,
            'ex_date': ex_date,
            'amount': single_dividend,
            'pay_date': None,  # Yahoo non sempre ha questa info
            'current_price': current_price,
            'yield_percent': dividend_yield_single,
            'annual_rate': dividend_rate,
            'annual_yield': dividend_yield * 100 if dividend_yield else dividend_yield_single * frequency
        }

        return result

    except Exception as e:
        print(f"   ⚠️  Error fetching {ticker}: {str(e)}")
        return None


def fetch_dividends_alternative(ticker):
    """
    Metodo alternativo: usa dividends history + pattern per predire prossimo
    """
    try:
        stock = yf.Ticker(ticker)

        # Get dividends storici
        dividends = stock.dividends

        if len(dividends) == 0:
            return None

        # Ultimo dividendo
        last_div_date = dividends.index[-1].date()
        last_div_amount = float(dividends.iloc[-1])

        # Calcola frequenza media (in giorni)
        if len(dividends) >= 2:
            dates = [d.date() for d in dividends.index[-5:]]  # Ultimi 5
            intervals = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]
            avg_interval = sum(intervals) / len(intervals) if intervals else 90
        else:
            avg_interval = 90  # Default quarterly

        # Predici prossima ex-date
        predicted_ex_date = last_div_date + timedelta(days=int(avg_interval))

        # Verifica che sia nel futuro e nel range
        today = datetime.now().date()
        if predicted_ex_date < today or predicted_ex_date > today + timedelta(days=LOOKFORWARD_DAYS):
            return None

        # Get current price
        info = stock.info
        current_price = info.get('currentPrice') or info.get('regularMarketPrice')

        if not current_price:
            return None

        # Calcola yield
        dividend_yield = (last_div_amount / current_price) * 100 if current_price > 0 else 0

        result = {
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

        return result

    except Exception as e:
        return None


# ---------------------------------------------------------
#  CALENDAR BUILDER
# ---------------------------------------------------------

def build_dividend_calendar(session, min_yield=MIN_YIELD_PERCENT):
    """
    Costruisce calendario dividendi per tutti i titoli nel portfolio

    Returns:
        list of dicts con info dividendi futuri (solo yield >= min_yield)
    """
    print("=" * 80)
    print("📅 DIVIDEND CALENDAR - Prossimi Dividendi")
    print("=" * 80)
    print(f"🔍 Filtro: Yield >= {min_yield}%")
    print(f"📆 Range: Prossimi {LOOKFORWARD_DAYS} giorni")
    print()

    # Get all stocks from database
    stocks = session.query(Stock).all()
    print(f"📊 Analizzando {len(stocks)} titoli...")
    print()

    calendar = []
    processed = 0
    found = 0

    for stock in stocks:
        ticker = stock.ticker
        processed += 1

        # Progress indicator
        if processed % 10 == 0:
            print(f"   ... {processed}/{len(stocks)} processati ({found} con yield >= {min_yield}%)")

        # Try primary method first
        div_info = fetch_upcoming_dividend(ticker)

        # If fails, try alternative method (pattern-based prediction)
        if not div_info:
            div_info = fetch_dividends_alternative(ticker)

        if not div_info:
            continue

        # Filter by yield
        if div_info['yield_percent'] < min_yield:
            continue

        # Add stock info
        div_info['stock_name'] = stock.name or ticker
        div_info['market'] = stock.market
        div_info['currency'] = stock.currency

        calendar.append(div_info)
        found += 1

    print()
    print(f"✅ Trovati {found} dividendi con yield >= {min_yield}%")
    print()

    # Sort by ex_date
    calendar.sort(key=lambda x: x['ex_date'])

    return calendar


# ---------------------------------------------------------
#  SAVE TO DATABASE
# ---------------------------------------------------------

def save_to_database(session, calendar_items):
    """
    Salva i dividendi futuri nel database
    Status: PREDICTED o ANNOUNCED
    """
    print("💾 Salvataggio nel database...")

    saved = 0
    updated = 0

    for item in calendar_items:
        ticker = item['ticker']

        # Get stock
        stock = session.query(Stock).filter_by(ticker=ticker).first()
        if not stock:
            continue

        # Check if dividend already exists
        existing = session.query(Dividend).filter_by(
            stock_id=stock.id,
            ex_date=item['ex_date']
        ).first()

        if existing:
            # Update if amount changed
            if existing.amount != item['amount']:
                existing.amount = item['amount']
                existing.payment_date = item.get('pay_date')
                existing.status = 'ANNOUNCED' if not item.get('is_predicted') else 'PREDICTED'
                existing.prediction_source = 'YAHOO_FINANCE'
                existing.confidence = 0.7 if item.get('is_predicted') else 0.95
                updated += 1
        else:
            # Insert new
            dividend = Dividend(
                stock_id=stock.id,
                ex_date=item['ex_date'],
                amount=item['amount'],
                payment_date=item.get('pay_date'),
                currency=item['currency'],
                dividend_type='ordinary',
                status='ANNOUNCED' if not item.get('is_predicted') else 'PREDICTED',
                prediction_source='YAHOO_FINANCE',
                confidence=0.7 if item.get('is_predicted') else 0.95
            )
            session.add(dividend)
            saved += 1

    session.commit()
    print(f"   ✅ Salvati {saved} nuovi dividendi")
    print(f"   ✅ Aggiornati {updated} dividendi esistenti")
    print()


# ---------------------------------------------------------
#  OUTPUT
# ---------------------------------------------------------

def display_calendar(calendar_items):
    """
    Mostra calendario in formato tabella
    """
    if not calendar_items:
        print("❌ Nessun dividendo trovato con i criteri specificati")
        return

    print("=" * 80)
    print("📅 CALENDARIO DIVIDENDI - Prossimi Eventi")
    print("=" * 80)
    print()

    # Prepare table data
    table_data = []
    for item in calendar_items:
        days_until = (item['ex_date'] - datetime.now().date()).days

        row = [
            item['ticker'],
            item['stock_name'][:30],  # Truncate name
            item['ex_date'].strftime('%Y-%m-%d'),
            f"{days_until}d",
            f"${item['amount']:.4f}",
            f"${item['current_price']:.2f}",
            f"{item['yield_percent']:.2f}%",
            f"{item['annual_yield']:.2f}%",
            "⚠️" if item.get('is_predicted') else "✓"
        ]
        table_data.append(row)

    headers = [
        'Ticker',
        'Nome',
        'Ex-Date',
        'In',
        'Dividendo',
        'Prezzo',
        'Yield',
        'Annual %',
        'Status'
    ]

    print(tabulate(table_data, headers=headers, tablefmt='simple'))
    print()
    print(f"📊 Totale: {len(calendar_items)} dividendi")
    print(f"✓ = Announced | ⚠️ = Predicted (basato su pattern storico)")
    print()


# ---------------------------------------------------------
#  MAIN
# ---------------------------------------------------------

def main():
    """Main entry point"""
    session = get_session()

    # Build calendar
    calendar = build_dividend_calendar(session, min_yield=MIN_YIELD_PERCENT)

    # Display
    display_calendar(calendar)

    # Save to database
    if calendar:
        save_to_database(session, calendar)

    print("=" * 80)
    print("✅ Aggiornamento calendario completato!")
    print("=" * 80)


if __name__ == "__main__":
    main()
