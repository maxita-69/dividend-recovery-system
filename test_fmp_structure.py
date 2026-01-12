#!/usr/bin/env python3
"""
Test struttura FMP Provider (senza chiamate API)
Verifica import e struttura del codice
"""
import sys
import os

def test_structure():
    """Test struttura provider senza eseguire chiamate API"""

    print("=" * 60)
    print("TEST STRUTTURA FMP PROVIDER")
    print("=" * 60)

    # Test 1: Import providers
    print("\n[1/6] Test import providers...")
    try:
        from providers.base_provider import BaseProvider
        print("  ✓ BaseProvider importato")
    except Exception as e:
        print(f"  ✗ Errore import BaseProvider: {e}")
        return False

    try:
        from providers.fmp_provider import FMPProvider
        print("  ✓ FMPProvider importato")
    except Exception as e:
        print(f"  ✗ Errore import FMPProvider: {e}")
        return False

    try:
        from providers.yahoo_provider import YahooProvider
        print("  ✓ YahooProvider importato")
    except Exception as e:
        print(f"  ✗ Errore import YahooProvider: {e}")
        return False

    try:
        from providers.provider_manager import get_provider, list_available_providers
        print("  ✓ provider_manager importato")
    except Exception as e:
        print(f"  ✗ Errore import provider_manager: {e}")
        return False

    # Test 2: Verifica metodi BaseProvider
    print("\n[2/6] Test metodi BaseProvider...")
    required_methods = ['fetch_prices', 'fetch_dividends']
    for method in required_methods:
        if hasattr(BaseProvider, method):
            print(f"  ✓ BaseProvider.{method} presente")
        else:
            print(f"  ✗ BaseProvider.{method} MANCANTE")
            return False

    # Test 3: Verifica metodi FMPProvider
    print("\n[3/6] Test metodi FMPProvider...")
    fmp_methods = ['fetch_prices', 'fetch_dividends', 'get_price', 'get_profile', 'search_symbol']
    for method in fmp_methods:
        if hasattr(FMPProvider, method):
            print(f"  ✓ FMPProvider.{method} presente")
        else:
            print(f"  ✗ FMPProvider.{method} MANCANTE")
            return False

    # Test 4: Verifica ereditarietà
    print("\n[4/6] Test ereditarietà...")
    if issubclass(FMPProvider, BaseProvider):
        print("  ✓ FMPProvider estende BaseProvider")
    else:
        print("  ✗ FMPProvider NON estende BaseProvider")
        return False

    if issubclass(YahooProvider, BaseProvider):
        print("  ✓ YahooProvider estende BaseProvider")
    else:
        print("  ✗ YahooProvider NON estende BaseProvider")
        return False

    # Test 5: Verifica configurazione
    print("\n[5/6] Test configurazione...")
    try:
        from config import FMP_BASE_URL, DATA_PROVIDER
        print(f"  ✓ FMP_BASE_URL: {FMP_BASE_URL}")

        if FMP_BASE_URL == "https://financialmodelingprep.com/stable":
            print("  ✓ Base URL corretta (stable)")
        else:
            print(f"  ✗ Base URL sbagliata: {FMP_BASE_URL}")
            return False

        print(f"  ✓ DATA_PROVIDER: {DATA_PROVIDER}")
    except Exception as e:
        print(f"  ✗ Errore import config: {e}")
        return False

    # Test 6: Verifica file structure
    print("\n[6/6] Test struttura file...")
    required_files = [
        'providers/__init__.py',
        'providers/base_provider.py',
        'providers/fmp_provider.py',
        'providers/yahoo_provider.py',
        'providers/provider_manager.py',
    ]

    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"  ✓ {file_path}")
        else:
            print(f"  ✗ {file_path} MANCANTE")
            return False

    return True


if __name__ == "__main__":
    success = test_structure()

    print("\n" + "=" * 60)
    if success:
        print("✓ TUTTI I TEST STRUTTURA PASSATI")
        print("=" * 60)
        print("\nProssimi passi:")
        print("1. Installare dipendenze: pip install -r requirements.txt")
        print("2. Verificare FMP_API_KEY in .env")
        print("3. Eseguire: python test_fmp_complete.py")
        sys.exit(0)
    else:
        print("✗ ALCUNI TEST FALLITI")
        print("=" * 60)
        sys.exit(1)
