from ibapi.client import EClient
from ibapi.wrapper import EWrapper
import time

class IBApp(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)

    # Evento chiamato quando la connessione è stabilita
    def nextValidId(self, orderId):
        print("✅ Connessione a IB Gateway riuscita!")
        self.disconnect()

def main():
    app = IBApp()
    print("🔌 Connessione a IB Gateway in corso...")
    
    # Porta standard IB Gateway = 4002
    app.connect("127.0.0.1", 4002, clientId=1)

    # Avvia il loop della API
    app.run()

if __name__ == "__main__":
    main()
