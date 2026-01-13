from providers.base_provider import BaseProvider
import yfinance as yf
from datetime import datetime


class YahooProvider(BaseProvider):
    def fetch_prices(self, symbol, start_date=None, end_date=None):
        """
        Scarica dati storici da Yahoo Finance.

        Args:
            symbol: Ticker symbol
            start_date: Data inizio (format: YYYY-MM-DD) - optional
            end_date: Data fine (format: YYYY-MM-DD) - optional

        Returns:
            list: Lista di dict con campi: date, open, high, low, close, volume
        """
        ticker = yf.Ticker(symbol)

        # Se specificate le date, usa start/end, altrimenti scarica tutto
        if start_date or end_date:
            hist = ticker.history(start=start_date, end=end_date, auto_adjust=False)
        else:
            hist = ticker.history(period="max", auto_adjust=False)

        # Converti in lista di dict con formato standard
        hist_reset = hist.reset_index()
        result = []
        for _, row in hist_reset.iterrows():
            result.append({
                'date': row['Date'].strftime('%Y-%m-%d') if hasattr(row['Date'], 'strftime') else str(row['Date']),
                'open': float(row['Open']),
                'high': float(row['High']),
                'low': float(row['Low']),
                'close': float(row['Close']),
                'volume': int(row['Volume'])
            })

        return result

    def fetch_dividends(self, symbol, start_date=None, end_date=None):
        """
        Scarica storico dividendi da Yahoo Finance.

        Args:
            symbol: Ticker symbol
            start_date: Data inizio (format: YYYY-MM-DD) - optional
            end_date: Data fine (format: YYYY-MM-DD) - optional

        Returns:
            list: Lista di dict con dividendi
        """
        ticker = yf.Ticker(symbol)

        # Scarica dividendi
        if start_date or end_date:
            # yfinance non supporta date filter per dividends, filtriamo dopo
            div = ticker.dividends
        else:
            div = ticker.dividends

        if div.empty:
            return []

        # Converti in dataframe e filtra
        div_df = div.reset_index()
        div_df.columns = ['Date', 'amount']

        # Filtra per date
        if start_date:
            div_df = div_df[div_df['Date'] >= start_date]
        if end_date:
            div_df = div_df[div_df['Date'] <= end_date]

        # Converti in lista di dict con formato standard
        result = []
        for _, row in div_df.iterrows():
            result.append({
                'ex_date': row['Date'].strftime('%Y-%m-%d') if hasattr(row['Date'], 'strftime') else str(row['Date']),
                'amount': float(row['amount']),
                'payment_date': None,  # Yahoo non fornisce queste info
                'record_date': None,
                'declaration_date': None
            })

        return result
