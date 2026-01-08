from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract

class IBApp(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.fundamental_data = None

    # Mostra eventuali errori IBKR
    def error(self, reqId, errorCode, errorString):
        print(f"❌ Errore IBKR [{errorCode}]: {errorString}")

    # Ricezione dei dati fondamentali (XML)
    def fundamentalData(self, reqId, data):
        print("\n📄 Dati fondamentali ricevuti:\n")
        print(data)
        self.fundamental_data = data
        self.disconnect()

def get_dividends(symbol):
    app = IBApp()
    app.connect("127.0.0.1", 4002, clientId=2)

    contract = Contract()
    contract.symbol = symbol
    contract.secType = "STK"
    contract.exchange = "SMART"
    contract.currency = "USD"

    print(f"\n🔍 Richiesta dati fondamentali per {symbol}...\n")

    # "ReportSnapshot" contiene dividendi, payout, ex-date, ecc.
    app.reqFundamentalData(1, contract, "ReportSnapshot", [])
    app.run()

if __name__ == "__main__":
    get_dividends("AAPL")  # Test con Apple
