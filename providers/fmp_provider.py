from providers.base_provider import BaseProvider
from fmp_client import FMPClient

class FMPProvider(BaseProvider):
    def __init__(self):
        self.client = FMPClient()

    def fetch_prices(self, symbol):
        data = self.client.get(
            f"historical-price-full/{symbol}",
            params={"serietype": "line"}
        )
        return data.get("historical", [])

    def fetch_dividends(self, symbol):
        data = self.client.get(
            f"historical-price-full/stock_dividend/{symbol}"
        )
        return data.get("historical", [])
