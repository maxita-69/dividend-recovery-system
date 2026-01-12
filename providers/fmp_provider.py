import os
import requests
from dotenv import load_dotenv
from providers.base_provider import BaseProvider

load_dotenv()


class FMPProvider(BaseProvider):
    """Financial Modeling Prep provider - Free plan compatible."""

    BASE_URL = "https://financialmodelingprep.com/stable"

    def __init__(self):
        self.api_key = os.getenv("FMP_API_KEY")
        if not self.api_key:
            raise ValueError("FMP_API_KEY non trovato nel file .env")

    def _make_request(self, endpoint: str, params: dict = None) -> dict:
        """Helper method to make API requests with error handling."""
        if params is None:
            params = {}

        params["apikey"] = self.api_key
        url = f"{self.BASE_URL}/{endpoint}"

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            raise RuntimeError(f"Timeout chiamata FMP per {endpoint}")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Errore HTTP {response.status_code}: {response.text}") from e

    def fetch_prices(self, symbol: str) -> list:
        """
        Scarica dati storici completi (OHLCV) per un simbolo.
        Endpoint: /historical-price-eod/full?symbol={symbol}

        Returns:
            list: Lista di dict con campi: date, open, high, low, close, volume
        """
        data = self._make_request(f"historical-price-eod/full", params={"symbol": symbol})

        # FMP potrebbe restituire dict con chiave 'historical' o lista diretta
        if isinstance(data, dict):
            return data.get("historical", [])
        return data if isinstance(data, list) else []

    def fetch_dividends(self, symbol: str) -> list:
        """
        Scarica storico dividendi per un simbolo.
        Nota: FMP free plan potrebbe non avere questo endpoint.
        Endpoint alternativo da verificare.

        Returns:
            list: Lista di dict con dividendi
        """
        # Provo endpoint standard (se esiste nel free plan)
        try:
            # Tentativo 1: endpoint dedicato dividendi (se disponibile)
            data = self._make_request(f"historical-price-full/stock_dividend/{symbol}")
            if isinstance(data, dict):
                return data.get("historical", [])
            return data if isinstance(data, list) else []
        except RuntimeError:
            # Se fallisce, ritorno lista vuota (free plan limitation)
            return []

    def get_price(self, symbol: str) -> float:
        """
        Restituisce il prezzo realtime (o last close).
        Endpoint: /quote?symbol={symbol}

        Returns:
            float: Prezzo corrente del titolo
        """
        data = self._make_request("quote", params={"symbol": symbol})

        if not isinstance(data, list) or len(data) == 0:
            raise ValueError(f"Nessun dato trovato per il simbolo {symbol}")

        price = data[0].get("price")
        if price is None:
            raise ValueError(f"Il campo 'price' non è presente nella risposta per {symbol}")

        return float(price)

    def get_profile(self, symbol: str) -> dict:
        """
        Scarica profilo completo azienda.
        Endpoint: /profile?symbol={symbol}

        Returns:
            dict: Dati profilo azienda (nome, settore, capitalizzazione, etc.)
        """
        data = self._make_request("profile", params={"symbol": symbol})

        if isinstance(data, list) and len(data) > 0:
            return data[0]
        return data if isinstance(data, dict) else {}

    def search_symbol(self, query: str) -> list:
        """
        Cerca ticker symbol per nome azienda.
        Endpoint: /search-name?query={name}

        Returns:
            list: Lista di aziende trovate
        """
        data = self._make_request("search-name", params={"query": query})
        return data if isinstance(data, list) else []
