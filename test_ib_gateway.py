from ib_insync import IB

ib = IB()
try:
    print("🔌 Connessione a IB Gateway...")
    ib.connect('127.0.0.1', 4002, clientId=1)
    print("✅ CONNESSO a IB Gateway!")
    print(f"Account: {ib.managedAccounts()}")
    ib.disconnect()
except Exception as e:
    print(f"❌ Errore: {e}")
