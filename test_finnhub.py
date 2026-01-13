#!/usr/bin/env python3
"""
Test script per verificare le capacità dell'API Finnhub
"""
import requests
import json
from datetime import datetime

API_KEY = "d5hv4spr01qu7bqq9fj0d5hv4spr01qu7bqq9fjg"
BASE_URL = "https://finnhub.io/api/v1"

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
            elif isinstance(data, list) and len(data) == 0:
                print("⚠️  Array vuoto - nessun dividendo trovato")
            else:
                print(f"⚠️  Formato inaspettato: {type(data)}")
        else:
            print(f"❌ Errore: {response.status_code}")
            print(f"Messaggio: {response.text}")

    except Exception as e:
        print(f"❌ Eccezione: {str(e)}")

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
            else:
                print("⚠️  Prezzo non disponibile o zero")
        else:
            print(f"❌ Errore: {response.status_code}")
            print(f"Messaggio: {response.text}")

    except Exception as e:
        print(f"❌ Eccezione: {str(e)}")

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
            else:
                print(f"⚠️  Status: {data.get('s')} - {data}")
        else:
            print(f"❌ Errore: {response.status_code}")
            print(f"Messaggio: {response.text}")

    except Exception as e:
        print(f"❌ Eccezione: {str(e)}")

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
            if data:
                print(f"✅ Nome: {data.get('name')}")
                print(f"✅ Exchange: {data.get('exchange')}")
                print(f"✅ Country: {data.get('country')}")
                print(f"✅ Currency: {data.get('currency')}")
                print(f"✅ Ticker: {data.get('ticker')}")
            else:
                print("⚠️  Nessun dato profilo disponibile")
        else:
            print(f"❌ Errore: {response.status_code}")
            print(f"Messaggio: {response.text}")

    except Exception as e:
        print(f"❌ Eccezione: {str(e)}")

if __name__ == "__main__":
    print("="*60)
    print("TEST FINNHUB API - TITOLI ITALIANI")
    print("="*60)

    # Test con ENI.MI
    test_profile("ENI.MI")
    test_quote("ENI.MI")
    test_candle("ENI.MI")
    test_dividends("ENI.MI")

    # Test con ENEL.MI
    print("\n\n")
    test_profile("ENEL.MI")
    test_quote("ENEL.MI")
    test_candle("ENEL.MI")
    test_dividends("ENEL.MI")

    print("\n" + "="*60)
    print("TEST COMPLETATO")
    print("="*60)
