import sys
from datetime import datetime, timedelta
from dividend_calendar import fetch_upcoming_dividend, fetch_dividends_alternative, MIN_YIELD_PERCENT, LOOKFORWARD_DAYS

def debug_ticker(ticker):
    print("=" * 80)
    print(f"🔍 DEBUG DIVIDENDO: {ticker}")
    print("=" * 80)

    today = datetime.now().date()

    # Metodo principale
    info = fetch_upcoming_dividend(ticker)
    source = "Yahoo Finance (ufficiale)"

    if not info:
        print("❌ Metodo principale fallito. Provo metodo alternativo...")
        info = fetch_dividends_alternative(ticker)
        source = "Storico dividendi (pattern)"

    if not info:
        print("❌ Nessuna informazione trovata con entrambi i metodi.")
        return

    print(f"✅ Fonte: {source}")
    print(f"📅 Ex-Date: {info['ex_date']}")
    print(f"💰 Importo: {info['amount']:.4f}")
    print(f"📈 Prezzo: {info['current_price']:.2f}")
    print(f"📊 Yield: {info['yield_percent']:.2f}%")
    print(f"📊 Annual Yield: {info['annual_yield']:.2f}%")

    # Verifica filtro temporale
    if info['ex_date'] < today:
        print("⚠️ Escluso: ex-date già passata.")
    elif info['ex_date'] > today + timedelta(days=LOOKFORWARD_DAYS):
        print(f"⚠️ Escluso: ex-date troppo lontana (> {LOOKFORWARD_DAYS} giorni).")
    elif info['annual_yield'] < MIN_YIELD_PERCENT:
        print(f"⚠️ Escluso: yield annuale troppo basso (< {MIN_YIELD_PERCENT}%).")
    else:
        print("✅ Questo titolo dovrebbe essere incluso nel calendario.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python debug_dividend.py TICKER")
    else:
        debug_ticker(sys.argv[1])
