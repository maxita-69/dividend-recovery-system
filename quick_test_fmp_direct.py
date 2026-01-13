#!/usr/bin/env python3
"""Test rapido FMP Provider - Import diretto senza yahoo"""
import sys
import os

print("=" * 60)
print("🧪 TEST FMP PROVIDER - CHIAMATE API REALI")
print("=" * 60)

# Test 1: Import diretto
print("\n[1/5] Test import diretto FMPProvider...")
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from providers.fmp_provider import FMPProvider
    print("  ✓ Import FMPProvider OK")
except Exception as e:
    print(f"  ✗ Errore import: {e}")
    exit(1)

# Test 2: Instanziazione
print("\n[2/5] Test instanziazione FMP provider...")
try:
    provider = FMPProvider()
    print(f"  ✓ Provider istanziato: {type(provider).__name__}")
    print(f"  ✓ Base URL: {provider.BASE_URL}")
except Exception as e:
    print(f"  ✗ Errore instanziazione: {e}")
    exit(1)

# Test 3: Prezzo realtime ticker USA
print("\n[3/5] Test prezzo realtime (AAPL)...")
try:
    symbol = "AAPL"
    price = provider.get_price(symbol)
    print(f"  ✓ {symbol} prezzo: ${price:.2f}")
    print(f"  ✓ API FMP funzionante!")
except Exception as e:
    print(f"  ✗ Errore get_price: {e}")
    print(f"     Possibile problema: API key invalida o limite raggiunto")
    import traceback
    traceback.print_exc()

# Test 4: Dati storici ticker USA
print("\n[4/5] Test dati storici (AAPL)...")
try:
    symbol = "AAPL"
    prices = provider.fetch_prices(symbol)

    if not prices:
        print(f"  ⚠ Nessun dato storico ricevuto")
    else:
        print(f"  ✓ {symbol} dati storici: {len(prices)} records totali")

        # Mostra ultimi 5 record
        if len(prices) >= 5:
            print(f"\n  📊 Ultimi 5 giorni di trading:")
            for record in prices[:5]:
                date = record.get('date', 'N/A')
                close = record.get('close', 0)
                volume = record.get('volume', 0)
                print(f"     {date}: Close=${close:.2f}, Vol={volume:,}")

except Exception as e:
    print(f"  ✗ Errore fetch_prices: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Profilo azienda
print("\n[5/5] Test profilo azienda (AAPL)...")
try:
    symbol = "AAPL"
    profile = provider.get_profile(symbol)

    if profile:
        print(f"  ✓ Profilo scaricato per {symbol}")
        print(f"     Nome: {profile.get('companyName', 'N/A')}")
        print(f"     Settore: {profile.get('sector', 'N/A')}")
        print(f"     Industria: {profile.get('industry', 'N/A')}")
        if 'mktCap' in profile:
            mcap = profile['mktCap']
            print(f"     Market Cap: ${mcap:,.0f}")
    else:
        print(f"  ⚠ Nessun profilo ricevuto")

except Exception as e:
    print(f"  ✗ Errore get_profile: {e}")

print("\n" + "=" * 60)
print("✅ TEST COMPLETATO")
print("=" * 60)
print("\nℹ️  Note:")
print("  - FMP free plan: 250 chiamate/giorno")
print("  - Ticker italiani potrebbero non essere supportati nel free plan")
print("  - Per testare ticker italiani serve eventualmente upgrade")
