#!/usr/bin/env python3
"""Test rapido FMP Provider con chiamate API reali"""

print("=" * 60)
print("🧪 TEST FMP PROVIDER - CHIAMATE API REALI")
print("=" * 60)

# Test 1: Import
print("\n[1/5] Test import provider...")
try:
    from providers import get_provider
    print("  ✓ Import providers OK")
except Exception as e:
    print(f"  ✗ Errore import: {e}")
    exit(1)

# Test 2: Instanziazione
print("\n[2/5] Test instanziazione FMP provider...")
try:
    provider = get_provider("FMP")
    print(f"  ✓ Provider istanziato: {type(provider).__name__}")
except Exception as e:
    print(f"  ✗ Errore instanziazione: {e}")
    exit(1)

# Test 3: Prezzo realtime ticker USA
print("\n[3/5] Test prezzo realtime (AAPL)...")
try:
    symbol = "AAPL"
    price = provider.get_price(symbol)
    print(f"  ✓ {symbol} prezzo: ${price:.2f}")
except Exception as e:
    print(f"  ✗ Errore get_price: {e}")
    print(f"     Possibile problema: API key invalida o limite raggiunto")

# Test 4: Dati storici ticker USA
print("\n[4/5] Test dati storici (AAPL - ultimi 10 giorni)...")
try:
    symbol = "AAPL"
    prices = provider.fetch_prices(symbol)

    if not prices:
        print(f"  ⚠ Nessun dato storico ricevuto (potrebbe essere limite free plan)")
    else:
        print(f"  ✓ {symbol} dati storici: {len(prices)} records totali")

        # Mostra ultimi 5 record
        print(f"\n  📊 Ultimi 5 giorni di trading:")
        for record in prices[:5]:
            date = record.get('date', 'N/A')
            close = record.get('close', 0)
            volume = record.get('volume', 0)
            print(f"     {date}: Close=${close:.2f}, Vol={volume:,}")

except Exception as e:
    print(f"  ✗ Errore fetch_prices: {e}")

# Test 5: Ticker italiano (se supportato)
print("\n[5/5] Test ticker italiano (ENEL.MI)...")
try:
    symbol = "ENEL.MI"
    price = provider.get_price(symbol)
    print(f"  ✓ {symbol} prezzo: €{price:.2f}")
    print(f"  ✓ Ticker italiani supportati da FMP free plan!")
except Exception as e:
    print(f"  ⚠ {symbol} non disponibile nel free plan")
    print(f"     Errore: {str(e)[:100]}")
    print(f"     ℹ️  Normale per free plan - serve upgrade per mercati non-USA")

print("\n" + "=" * 60)
print("✅ TEST COMPLETATO")
print("=" * 60)
