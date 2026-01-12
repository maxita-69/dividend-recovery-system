#!/usr/bin/env python3
"""
Test completo FMP Provider
Verifica tutti i metodi implementati
"""
from providers import get_provider, get_current_provider_name


def test_fmp_provider():
    """Test completo di FMPProvider"""

    print("=" * 60)
    print("TEST FMP PROVIDER - COMPLETO")
    print("=" * 60)

    # Verifica provider corrente
    current = get_current_provider_name()
    print(f"\n✓ Provider configurato: {current}")

    # Ottieni provider
    provider = get_provider("FMP")
    print(f"✓ Provider istanziato: {type(provider).__name__}")

    # Test 1: Prezzo realtime
    print("\n" + "-" * 60)
    print("TEST 1: Prezzo Realtime (get_price)")
    print("-" * 60)
    try:
        symbol = "AAPL"
        price = provider.get_price(symbol)
        print(f"✓ {symbol} prezzo: ${price:.2f}")
    except Exception as e:
        print(f"✗ Errore get_price: {e}")

    # Test 2: Dati storici
    print("\n" + "-" * 60)
    print("TEST 2: Dati Storici (fetch_prices)")
    print("-" * 60)
    try:
        symbol = "AAPL"
        prices = provider.fetch_prices(symbol)
        print(f"✓ {symbol} dati storici scaricati: {len(prices)} records")
        if prices:
            print(f"  Esempio primo record: {prices[0]}")
            print(f"  Esempio ultimo record: {prices[-1]}")
    except Exception as e:
        print(f"✗ Errore fetch_prices: {e}")

    # Test 3: Dividendi storici
    print("\n" + "-" * 60)
    print("TEST 3: Dividendi Storici (fetch_dividends)")
    print("-" * 60)
    try:
        symbol = "AAPL"
        dividends = provider.fetch_dividends(symbol)
        print(f"✓ {symbol} dividendi scaricati: {len(dividends)} records")
        if dividends:
            print(f"  Esempio primo record: {dividends[0]}")
        else:
            print("  ⚠ Nessun dividendo (potrebbe essere limitazione free plan)")
    except Exception as e:
        print(f"✗ Errore fetch_dividends: {e}")

    # Test 4: Profilo azienda
    print("\n" + "-" * 60)
    print("TEST 4: Profilo Azienda (get_profile)")
    print("-" * 60)
    try:
        symbol = "AAPL"
        profile = provider.get_profile(symbol)
        print(f"✓ {symbol} profilo scaricato")
        if profile:
            print(f"  Nome: {profile.get('companyName', 'N/A')}")
            print(f"  Settore: {profile.get('sector', 'N/A')}")
            print(f"  Industria: {profile.get('industry', 'N/A')}")
            print(f"  Market Cap: {profile.get('mktCap', 'N/A')}")
    except Exception as e:
        print(f"✗ Errore get_profile: {e}")

    # Test 5: Ricerca simbolo
    print("\n" + "-" * 60)
    print("TEST 5: Ricerca Simbolo (search_symbol)")
    print("-" * 60)
    try:
        query = "Apple"
        results = provider.search_symbol(query)
        print(f"✓ Ricerca '{query}': {len(results)} risultati")
        if results:
            for i, r in enumerate(results[:3], 1):
                print(f"  {i}. {r.get('symbol', 'N/A')} - {r.get('name', 'N/A')}")
    except Exception as e:
        print(f"✗ Errore search_symbol: {e}")

    # Test 6: Ticker italiano (se supportato)
    print("\n" + "-" * 60)
    print("TEST 6: Ticker Italiano (ENEL.MI)")
    print("-" * 60)
    try:
        symbol = "ENEL.MI"
        price = provider.get_price(symbol)
        print(f"✓ {symbol} prezzo: €{price:.2f}")
    except Exception as e:
        print(f"⚠ {symbol} non disponibile (normale per free plan): {e}")

    print("\n" + "=" * 60)
    print("TEST COMPLETATI")
    print("=" * 60)


if __name__ == "__main__":
    test_fmp_provider()
