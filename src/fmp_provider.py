import os
import requests
from dotenv import load_dotenv

load_dotenv()

class FMPProvider:
    BASE_URL = "https://financialmodelingprep.com/stable"

    def __init__(self):
        self.api_key = os.getenv("FMP_API_KEY")
        if not self.api_key:
            raise ValueError("FMP_API_KEY non trovato nel file .env")

    def get_price(self, symbol: str) -> float:
        """
        Restituisce il prezzo realtime usando la nuova API /stable/quote.
        """
        url = f"{self.BASE_URL}/quote?symbol={symbol}&apikey={self.api_key}"
        response = requests.get(url)

        if response.status_code != 200:
            raise RuntimeError(f"Errore HTTP {response.status_code}: {response.text}")

        data = response.json()

        if not isinstance(data, list) or len(data) == 0:
            raise ValueError(f"Nessun dato trovato per il simbolo {symbol}")

        price = data[0].get("price")
        if price is None:
            raise ValueError(f"Il campo 'price' non è presente nella risposta per {symbol}")

        return price
