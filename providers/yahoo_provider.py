from providers.base_provider import BaseProvider
import yfinance as yf

class YahooProvider(BaseProvider):
    def fetch_prices(self, symbol):
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="max")
        return hist.reset_index().to_dict(orient="records")

    def fetch_dividends(self, symbol):
        ticker = yf.Ticker(symbol)
        div = ticker.dividends.reset_index()
        return div.to_dict(orient="records")
