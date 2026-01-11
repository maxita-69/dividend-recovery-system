from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibkr_dividend_parser import parse_dividend_xml
import time

class IBApp(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.fundamental_data = None

    def error(self, reqId, errorCode, errorString):
        print(f"❌ Errore IBKR [{errorCode}]: {errorString}")

    def fundamentalData(self, reqId, data):
        self.fundamental_data = data
        self.disconnect()

def download_dividend_data(ticker):
    app = IBApp()
    app.connect("127.0.0.1", 4002, clientId=3)

    contract = Contract()
    contract.symbol = ticker
    contract.secType = "STK"
    contract.exchange = "SMART"
    contract.currency = "USD"

    print(f"\n🔍 Richiesta dati fondamentali per {ticker}...")

    app.reqFundamentalData(1, contract, "ReportSnapshot", [])
    app.run()

    if not app.fundamental_data:
        print("❌ Nessun dato ricevuto da IBKR")
        return None

    return parse_dividend_xml(app.fundamental_data)
