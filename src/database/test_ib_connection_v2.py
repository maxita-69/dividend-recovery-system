#!/usr/bin/env python3
"""
Test connessione a IB Gateway usando ib-insync (versione migliorata)
Versione 2.0 - Usa ib-insync invece di ibapi nativo
"""
from ib_insync import IB, util
import asyncio

def test_connection():
    """
    Testa la connessione a IB Gateway
    Porta standard: 4002 (IB Gateway paper trading)
                    7497 (TWS paper trading)
                    4001 (IB Gateway live)
                    7496 (TWS live)
    """
    ib = IB()

    print("🔌 Connessione a IB Gateway in corso...")
    print("   Porta: 4002 (IB Gateway Paper Trading)")
    print("   Host: 127.0.0.1")
    print("   Client ID: 1")
    print()

    try:
        # Connessione a IB Gateway (paper trading porta 4002)
        ib.connect('127.0.0.1', 4002, clientId=1, timeout=10)

        print("✅ Connessione a IB Gateway riuscita!")
        print(f"   Server version: {ib.client.serverVersion()}")
        print(f"   Connection time: {ib.client.connTime}")
        print(f"   Accounts: {ib.managedAccounts()}")

        # Disconnessione
        ib.disconnect()
        print("\n✅ Test completato con successo!")
        return True

    except Exception as e:
        print(f"\n❌ Errore di connessione: {e}")
        print("\n🔍 Possibili cause:")
        print("   1. IB Gateway non è in esecuzione")
        print("   2. Porta non corretta (prova 4002, 7497, 4001, o 7496)")
        print("   3. IB Gateway non configurato per accettare connessioni API")
        print("   4. Firewall che blocca la connessione")
        print("\n📖 Come risolvere:")
        print("   1. Avvia IB Gateway (o TWS)")
        print("   2. In IB Gateway vai su: Configure > Settings > API > Settings")
        print("   3. Abilita 'Enable ActiveX and Socket Clients'")
        print("   4. Aggiungi 127.0.0.1 a 'Trusted IP addresses'")
        print("   5. Verifica che la porta sia corretta (4002 per paper trading)")
        return False
    finally:
        if ib.isConnected():
            ib.disconnect()

def main():
    """Main function"""
    success = test_connection()
    exit(0 if success else 1)

if __name__ == "__main__":
    main()
