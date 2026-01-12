class BaseProvider:
    def fetch_prices(self, symbol):
        raise NotImplementedError("fetch_prices must be implemented by the provider")

    def fetch_dividends(self, symbol):
        raise NotImplementedError("fetch_dividends must be implemented by the provider")
