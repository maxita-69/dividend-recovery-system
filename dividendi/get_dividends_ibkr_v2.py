#!/usr/bin/env python3
"""
Scarica dati dividendi da IBKR usando ib-insync
Versione 2.0 - Usa ib-insync invece di ibapi nativo
"""
from ib_insync import IB, Stock
import asyncio
from datetime import datetime

def get_dividend_data(ticker: str, exchange: str = 'SMART', currency: str = 'USD'):
    """
    Recupera informazioni sui dividendi da IBKR per un ticker

    Args:
        ticker: Symbol del titolo (es. 'AAPL', 'MSFT')
        exchange: Exchange (default: 'SMART' per routing intelligente)
        currency: Valuta (default: 'USD')

    Returns:
        dict con informazioni sui dividendi o None se errore
    """
    ib = IB()

    print(f"\n🔍 Richiesta dati dividendi per {ticker}...")

    try:
        # Connessione
        ib.connect('127.0.0.1', 4002, clientId=2, timeout=10)
        print(f"✅ Connesso a IB Gateway")

        # Crea contratto
        contract = Stock(ticker, exchange, currency)

        # Qualifica il contratto (ottiene dettagli completi)
        print(f"   Qualificazione contratto {ticker}...")
        ib.qualifyContracts(contract)

        if not contract.conId:
            print(f"❌ Contratto non trovato per {ticker}")
            return None

        print(f"   ✓ Contratto trovato: {contract.localSymbol}")
        print(f"   Exchange: {contract.primaryExchange}")
        print(f"   ConID: {contract.conId}")

        # Richiedi dati fondamentali (include dividendi)
        print(f"   Richiesta dati fondamentali...")
        fundamental = ib.reqFundamentalData(contract, 'ReportSnapshot')

        if not fundamental:
            print(f"❌ Nessun dato fondamentale disponibile per {ticker}")
            return None

        # Parse XML per estrarre dividendi
        # (Nota: fundamental è una stringa XML, va parsata)
        print(f"✅ Dati ricevuti (lunghezza: {len(fundamental)} caratteri)")

        # Per ora ritorna i dati raw
        # TODO: Implementare parsing XML come in ibkr_dividend_parser.py
        result = {
            'ticker': ticker,
            'exchange': contract.primaryExchange,
            'conId': contract.conId,
            'fundamental_data': fundamental,
            'timestamp': datetime.now().isoformat()
        }

        print(f"✅ Dati estratti per {ticker}")
        return result

    except Exception as e:
        print(f"❌ Errore: {e}")
        import traceback
        traceback.print_exc()
        return None

    finally:
        if ib.isConnected():
            ib.disconnect()
            print(f"   Disconnesso da IB Gateway")

def main():
    """Test con alcuni ticker di esempio"""
    test_tickers = ['AAPL', 'MSFT', 'JNJ']

    print("=" * 60)
    print("TEST DOWNLOAD DIVIDENDI DA IBKR")
    print("=" * 60)

    results = {}
    for ticker in test_tickers:
        result = get_dividend_data(ticker)
        if result:
            results[ticker] = result
            print(f"\n📊 Risultato per {ticker}:")
            print(f"   ConID: {result['conId']}")
            print(f"   Exchange: {result['exchange']}")
            print(f"   Data length: {len(result['fundamental_data'])} chars")
        print()

    print("=" * 60)
    print(f"✅ Completato: {len(results)}/{len(test_tickers)} ticker processati")
    print("=" * 60)

    return results

if __name__ == "__main__":
    main()
