#!/usr/bin/env python3
"""
Script di test STANDALONE per verificare Finnhub API
================================================

SCOPO:
  Verificare cosa supporta Finnhub nel piano gratuito:
  - Titoli USA (dovrebbero funzionare)
  - Titoli italiani (probabile richiesta piano a pagamento)
  Test endpoint: dividendi, prezzi storici, quote, profilo azienda

COME USARE:
  1. Esegui questo script localmente sul tuo PC (NON in sandbox)
  2. Verifica l'output per ogni ticker
  3. Confronta titoli USA vs titoli italiani

REQUISITI:
  pip install requests

ESECUZIONE:
  python test_finnhub.py
"""
import requests
import json
from datetime import datetime

# ============================================================
# CONFIGURAZIONE
# ============================================================
API_KEY = "d5hv4spr01qu7bqq9fj0d5hv4spr01qu7bqq9fjg"
BASE_URL = "https://finnhub.io/api/v1"

# Titoli da testare
TEST_TICKERS = [
    # Titoli USA (per verificare piano gratuito)
    "AAPL",        # Apple Inc.
    "MSFT",        # Microsoft
    "KO",          # Coca-Cola (paga dividendi)

    # Titoli italiani (richiede piano a pagamento)
    "ENI.MI",      # Eni SpA
    "ENEL.MI",     # Enel SpA
]

def test_dividends(symbol):
    """Test endpoint dividendi"""
    url = f"{BASE_URL}/stock/dividend"
    params = {
        'symbol': symbol,
        'from': '2023-01-01',
        'to': '2025-12-31',
        'token': API_KEY
    }

    print(f"\n{'='*60}")
    print(f"TEST DIVIDENDI - {symbol}")
    print(f"{'='*60}")

    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Risposta: {json.dumps(data, indent=2)}")
            if isinstance(data, list) and len(data) > 0:
                print(f"\n✅ Trovati {len(data)} dividendi")
                print(f"Esempio primo dividendo: {data[0]}")
                return True
            elif isinstance(data, list) and len(data) == 0:
                print("⚠️  Array vuoto - nessun dividendo trovato")
                return False
            else:
                print(f"⚠️  Formato inaspettato: {type(data)}")
                return False
        else:
            print(f"❌ Errore: {response.status_code}")
            print(f"Messaggio: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Eccezione: {str(e)}")
        return False

def test_quote(symbol):
    """Test endpoint quote corrente"""
    url = f"{BASE_URL}/quote"
    params = {
        'symbol': symbol,
        'token': API_KEY
    }

    print(f"\n{'='*60}")
    print(f"TEST QUOTE - {symbol}")
    print(f"{'='*60}")

    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Risposta: {json.dumps(data, indent=2)}")
            if data.get('c', 0) > 0:  # 'c' = current price
                print(f"✅ Prezzo corrente: {data.get('c')} EUR")
                return True
            else:
                print("⚠️  Prezzo non disponibile o zero")
                return False
        else:
            print(f"❌ Errore: {response.status_code}")
            print(f"Messaggio: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Eccezione: {str(e)}")
        return False

def test_candle(symbol):
    """Test endpoint prezzi storici (OHLCV)"""
    url = f"{BASE_URL}/stock/candle"

    # Test ultimi 7 giorni
    from_ts = int(datetime(2024, 1, 1).timestamp())
    to_ts = int(datetime(2024, 1, 31).timestamp())

    params = {
        'symbol': symbol,
        'resolution': 'D',  # Daily
        'from': from_ts,
        'to': to_ts,
        'token': API_KEY
    }

    print(f"\n{'='*60}")
    print(f"TEST PREZZI STORICI (OHLCV) - {symbol}")
    print(f"{'='*60}")

    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()

            if data.get('s') == 'ok':
                num_records = len(data.get('c', []))
                print(f"✅ Status: {data.get('s')}")
                print(f"✅ Record trovati: {num_records}")

                if num_records > 0:
                    print(f"\nPrimi 3 record:")
                    for i in range(min(3, num_records)):
                        ts = data['t'][i]
                        date = datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
                        print(f"  {date}: O={data['o'][i]}, H={data['h'][i]}, L={data['l'][i]}, C={data['c'][i]}, V={data['v'][i]}")
                    return True
                else:
                    print("⚠️  Nessun record trovato")
                    return False
            else:
                print(f"⚠️  Status: {data.get('s')} - {data}")
                return False
        else:
            print(f"❌ Errore: {response.status_code}")
            print(f"Messaggio: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Eccezione: {str(e)}")
        return False

def test_profile(symbol):
    """Test endpoint profilo azienda"""
    url = f"{BASE_URL}/stock/profile2"
    params = {
        'symbol': symbol,
        'token': API_KEY
    }

    print(f"\n{'='*60}")
    print(f"TEST PROFILO AZIENDA - {symbol}")
    print(f"{'='*60}")

    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            if data and data.get('name'):
                print(f"✅ Nome: {data.get('name')}")
                print(f"✅ Exchange: {data.get('exchange')}")
                print(f"✅ Country: {data.get('country')}")
                print(f"✅ Currency: {data.get('currency')}")
                print(f"✅ Ticker: {data.get('ticker')}")
                return True
            else:
                print("⚠️  Nessun dato profilo disponibile")
                return False
        else:
            print(f"❌ Errore: {response.status_code}")
            print(f"Messaggio: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Eccezione: {str(e)}")
        return False

if __name__ == "__main__":
    print("\n" + "="*70)
    print(" " * 10 + "TEST FINNHUB API - PIANO GRATUITO (USA vs ITA)")
    print("="*70)

    results = {}

    for ticker in TEST_TICKERS:
        print(f"\n{'='*70}")
        print(f" TICKER: {ticker}")
        print("="*70)

        results[ticker] = {
            'profile': False,
            'quote': False,
            'prices': False,
            'dividends': False
        }

        # Test profilo
        results[ticker]['profile'] = test_profile(ticker)

        # Test quote corrente
        results[ticker]['quote'] = test_quote(ticker)

        # Test prezzi storici
        results[ticker]['prices'] = test_candle(ticker)

        # Test dividendi
        results[ticker]['dividends'] = test_dividends(ticker)

        print("\n")

    # ============================================================
    # RIEPILOGO FINALE
    # ============================================================
    print("\n" + "="*70)
    print(" " * 25 + "RIEPILOGO FINALE")
    print("="*70)
    print("\n📊 VALUTAZIONE FINNHUB - PIANO GRATUITO:\n")

    print("✅ = Dati disponibili e funzionanti")
    print("❌ = Dati non disponibili o errori\n")
    print("-" * 70)

    for ticker in TEST_TICKERS:
        print(f"\n{ticker}:")
        print(f"  • Profilo azienda : {'✅' if results[ticker]['profile'] else '❌'}")
        print(f"  • Quote corrente  : {'✅' if results[ticker]['quote'] else '❌'}")
        print(f"  • Prezzi storici  : {'✅' if results[ticker]['prices'] else '❌'}")
        print(f"  • Dividendi       : {'✅' if results[ticker]['dividends'] else '❌'}")

    # Analisi risultati per mercato
    usa_tickers = [t for t in TEST_TICKERS if not t.endswith('.MI')]
    ita_tickers = [t for t in TEST_TICKERS if t.endswith('.MI')]

    print("\n" + "="*70)
    print("\n📈 ANALISI PER MERCATO:")

    if usa_tickers:
        usa_working = [t for t in usa_tickers if results[t]['prices']]
        print(f"\n  🇺🇸 TITOLI USA: {len(usa_working)}/{len(usa_tickers)} funzionanti")
        if usa_working:
            print(f"     ✅ Ticker funzionanti: {', '.join(usa_working)}")
        else:
            print(f"     ❌ Nessun ticker USA funzionante")

    if ita_tickers:
        ita_working = [t for t in ita_tickers if results[t]['prices']]
        print(f"\n  🇮🇹 TITOLI ITALIANI: {len(ita_working)}/{len(ita_tickers)} funzionanti")
        if ita_working:
            print(f"     ✅ Ticker funzionanti: {', '.join(ita_working)}")
        else:
            print(f"     ❌ Piano gratuito NON supporta Borsa Italiana")

    print("\n" + "="*70)
    print("\n💡 CONCLUSIONI:")
    if any(results[t]['prices'] for t in usa_tickers):
        print("   ✅ Finnhub funziona per titoli USA nel piano gratuito")
    if not any(results[t]['prices'] for t in ita_tickers):
        print("   ❌ Finnhub richiede piano a pagamento per titoli italiani")
        print("   → Mantieni Yahoo Finance per .MI (gratuito e funzionante)")

    print("\n" + "="*70 + "\n")
