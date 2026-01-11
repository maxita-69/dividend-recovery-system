#!/usr/bin/env python3
import sys
from pathlib import Path
from datetime import datetime, timedelta

# -------------------------------------------------------------------
#  PATH FIX — IMPORT CORRETTI
# -------------------------------------------------------------------

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent

# Aggiunge la root del progetto
sys.path.insert(0, str(PROJECT_ROOT))

# Aggiunge la cartella src/
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# Importa funzioni e modelli
from dividend_calendar import (
    fetch_upcoming_dividend,
    fetch_dividends_alternative,
    MIN_YIELD_PERCENT,
    LOOKFORWARD_DAYS,
    get_session
)

from database.models import Stock

# -------------------------------------------------------------------
#  COLORI ANSI
# -------------------------------------------------------------------
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"


def analyze_ticker(ticker):
    """Analizza un singolo ticker e ritorna un dict con i risultati."""
    today = datetime.now().date()

    info = fetch_upcoming_dividend(ticker)
    alt = fetch_dividends_alternative(ticker)

    result = {
        "ticker": ticker,
        "method": None,
        "included": False,
        "reason": "",
        "ex_date": None,
        "yield": None
    }

    # Nessun dato da entrambi i metodi
    if not info and not alt:
        result["reason"] = "Nessun dato disponibile (Yahoo + storico falliti)"
        return result

    # Scegli il metodo migliore
    chosen = info if info else alt
    result["method"] = "Yahoo" if info else "Storico"

    result["ex_date"] = chosen["ex_date"]
    result["yield"] = chosen["annual_yield"]

    # Regole di esclusione
    if chosen["ex_date"] < today:
        result["reason"] = "Ex-date già passata"
        return result

    if chosen["ex_date"] > today + timedelta(days=LOOKFORWARD_DAYS):
        result["reason"] = f"Ex-date oltre {LOOKFORWARD_DAYS} giorni"
        return result

    if chosen["annual_yield"] < MIN_YIELD_PERCENT:
        result["reason"] = f"Yield < {MIN_YIELD_PERCENT}%"
        return result

    # Se arriva qui → è incluso
    result["included"] = True
    result["reason"] = "OK"
    return result


def main():
    # Usa SEMPRE il database corretto
    session = get_session()

    print("=" * 100)
    print(f"{CYAN}🔍 DEBUG COMPLETO DI TUTTI I TITOLI IN PORTAFOGLIO{RESET}")
    print("=" * 100)

    stocks = session.query(Stock).all()
    print(f"📊 Trovati {len(stocks)} titoli nel database\n")

    included = []
    excluded = []
    nodata = []

    for stock in stocks:
        r = analyze_ticker(stock.ticker)

        if r["included"]:
            included.append(r)
        elif r["method"] is None:
            nodata.append(r)
        else:
            excluded.append(r)

    # ---------------------------------------------------------------
    # RISULTATI
    # ---------------------------------------------------------------
    print("\n" + "=" * 100)
    print(f"{GREEN}📈 TITOLI CHE DOVREBBERO APPARIRE NEL CALENDARIO{RESET}")
    print("=" * 100)

    if not included:
        print("❌ Nessun titolo soddisfa i criteri")
    else:
        for r in included:
            print(f"✓ {r['ticker']} — ex-date {r['ex_date']} — yield {r['yield']:.2f}% — metodo {r['method']}")

    print("\n" + "=" * 100)
    print(f"{YELLOW}⚠️ TITOLI ESCLUSI (ma con dati disponibili){RESET}")
    print("=" * 100)

    if not excluded:
        print("Nessuno")
    else:
        for r in excluded:
            print(f"• {r['ticker']} — {r['reason']} — metodo {r['method']} — yield {r['yield']}")

    print("\n" + "=" * 100)
    print(f"{RED}❌ TITOLI SENZA ALCUN DATO (Yahoo + storico falliti){RESET}")
    print("=" * 100)

    if not nodata:
        print("Nessuno")
    else:
        for r in nodata:
            print(f"• {r['ticker']} — {r['reason']}")

    print("\n" + "=" * 100)
    print("🏁 Debug completato")
    print("=" * 100)


if __name__ == "__main__":
    main()
