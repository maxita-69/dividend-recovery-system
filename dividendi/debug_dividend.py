#!/usr/bin/env python3
import sys
from pathlib import Path
from datetime import datetime, timedelta

# -------------------------------------------------------------------
#  PATH FIX — permette di importare dividend_calendar.py e src/
# -------------------------------------------------------------------
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent

sys.path.insert(0, str(CURRENT_DIR))
sys.path.insert(0, str(PROJECT_ROOT))

# Importa funzioni dal tuo modulo principale
from dividend_calendar import (
    fetch_upcoming_dividend,
    fetch_dividends_alternative,
    MIN_YIELD_PERCENT,
    LOOKFORWARD_DAYS
)

# -------------------------------------------------------------------
#  COLORI ANSI
# -------------------------------------------------------------------
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"


# -------------------------------------------------------------------
#  DEBUGGER
# -------------------------------------------------------------------
def debug_ticker(ticker):
    print("=" * 80)
    print(f"{CYAN}🔍 DEBUG DIVIDENDO PER: {ticker}{RESET}")
    print("=" * 80)

    today = datetime.now().date()

    # ---------------------------------------------------------------
    # 1) Metodo principale (Yahoo Finance)
    # ---------------------------------------------------------------
    print(f"{YELLOW}➡️  Test metodo ufficiale Yahoo Finance...{RESET}")
    info = fetch_upcoming_dividend(ticker)

    if info:
        print(f"{GREEN}   ✓ Metodo ufficiale ha trovato dati{RESET}")
    else:
        print(f"{RED}   ✗ Metodo ufficiale NON ha trovato dati{RESET}")

    # ---------------------------------------------------------------
    # 2) Metodo alternativo (storico dividendi)
    # ---------------------------------------------------------------
    print(f"\n{YELLOW}➡️  Test metodo alternativo (pattern storico)...{RESET}")
    alt = fetch_dividends_alternative(ticker)

    if alt:
        print(f"{GREEN}   ✓ Metodo alternativo ha trovato dati{RESET}")
    else:
        print(f"{RED}   ✗ Metodo alternativo NON ha trovato dati{RESET}")

    # ---------------------------------------------------------------
    # 3) Se nessuno dei due funziona → fine
    # ---------------------------------------------------------------
    if not info and not alt:
        print(f"\n{RED}❌ Nessun dato disponibile per questo ticker.{RESET}")
        print("Possibili cause:")
        print(" - Yahoo Finance non fornisce dividendRate o exDividendDate")
        print(" - Nessun dividendo storico disponibile")
        print(" - Ticker errato o non supportato")
        return

    # Scegli il migliore
    chosen = info if info else alt
    source = "Yahoo Finance" if info else "Pattern storico"

    print(f"\n{CYAN}📌 Fonte utilizzata: {source}{RESET}")

    # ---------------------------------------------------------------
    # 4) Stampa dettagli
    # ---------------------------------------------------------------
    print("\n📅 Ex-Date:", chosen["ex_date"])
    print("💰 Importo:", f"{chosen['amount']:.4f}")
    print("📈 Prezzo:", f"{chosen['current_price']:.2f}")
    print("📊 Yield singolo:", f"{chosen['yield_percent']:.2f}%")
    print("📊 Yield annuale:", f"{chosen['annual_yield']:.2f}%")

    # ---------------------------------------------------------------
    # 5) Verifica criteri del calendario
    # ---------------------------------------------------------------
    print("\n" + "-" * 80)
    print(f"{CYAN}📌 VERIFICA CRITERI CALENDARIO{RESET}")

    # Ex-date passata
    if chosen["ex_date"] < today:
        print(f"{RED}❌ Escluso: ex-date già passata{RESET}")
        return

    # Ex-date troppo lontana
    if chosen["ex_date"] > today + timedelta(days=LOOKFORWARD_DAYS):
        print(f"{RED}❌ Escluso: ex-date oltre {LOOKFORWARD_DAYS} giorni{RESET}")
        return

    # Yield troppo basso
    if chosen["annual_yield"] < MIN_YIELD_PERCENT:
        print(f"{RED}❌ Escluso: yield annuale < {MIN_YIELD_PERCENT}%{RESET}")
        return

    print(f"{GREEN}✅ Questo titolo dovrebbe apparire nel calendario!{RESET}")


# -------------------------------------------------------------------
#  MAIN
# -------------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python debug_dividend.py TICKER")
        print("Esempio: python debug_dividend.py ENEL.MI")
    else:
        debug_ticker(sys.argv[1])
