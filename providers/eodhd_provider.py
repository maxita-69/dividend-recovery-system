"""
EODHD Provider - Wrapper per EOD Historical Data API.

Utilizza la libreria ufficiale eodhd per accedere a dati finanziari storici,
dividendi e informazioni di mercato.

Documentazione: https://eodhd.com/financial-apis/
Installazione: pip install eodhd
"""
from providers.base_provider import BaseProvider
from eodhd import APIClient
import os
from datetime import datetime


class EODHDProvider(BaseProvider):
    """
    Provider per EOD Historical Data API.
    
    Wrapper leggero che utilizza la libreria ufficiale eodhd,
    adattando l'output al formato standard del sistema.
    """
    
    def __init__(self, api_token=None):
        """
        Inizializza il client EODHD.
        
        Args:
            api_token: Token API per EODHD. Se None, cerca in EODHD_API_TOKEN
        """
        self.api_token = api_token or os.getenv("EODHD_API_TOKEN")
        if not self.api_token:
            raise ValueError(
                "EODHD API token non trovato. Imposta EODHD_API_TOKEN nel .env"
            )
        try:
            self.client = APIClient(api_key=self.api_token)
        except ValueError as e:
            raise ValueError(f"EODHD API token non valido: {str(e)}")
    
    def fetch_prices(self, symbol, start_date=None, end_date=None):
        """
        Scarica dati storici da EODHD.
        
        Args:
            symbol: Ticker symbol (es. 'AAPL.US', 'ENEL.MI')
            start_date: Data inizio (format: YYYY-MM-DD) - optional
            end_date: Data fine (format: YYYY-MM-DD) - optional
        
        Returns:
            list: Lista di dict con campi: date, open, high, low, close, volume
        """
        try:
            # Recupera dati storici
            data = self.client.get_eod_historical_stock_market_data(
                symbol=symbol,
                period='d',
                from_date=start_date,
                to_date=end_date,
                order='a'  # ascending order
            )
            
            # Converti nel formato standard
            result = []
            for row in data:
                result.append({
                    'date': row['date'],
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close']),
                    'volume': int(row['volume']) if row.get('volume') else 0
                })
            
            return result
            
        except Exception as e:
            raise RuntimeError(f"EODHD fetch_prices error per {symbol}: {str(e)}")
    
    def fetch_dividends(self, symbol, start_date=None, end_date=None):
        """
        Scarica storico dividendi da EODHD.
        
        Args:
            symbol: Ticker symbol (es. 'AAPL.US', 'ENEL.MI')
            start_date: Data inizio (format: YYYY-MM-DD) - optional
            end_date: Data fine (format: YYYY-MM-DD) - optional
        
        Returns:
            list: Lista di dict con dividendi
        """
        try:
            # Recupera dividendi
            data = self.client.get_historical_dividends_data(
                ticker=symbol,
                date_from=start_date,
                date_to=end_date
            )
            
            # Converti nel formato standard
            result = []
            for row in data:
                result.append({
                    'ex_date': row['date'],
                    'amount': float(row['value']),
                    'payment_date': None,  # EODHD non fornisce queste info separatamente
                    'record_date': None,
                    'declaration_date': None
                })
            
            return result
            
        except Exception as e:
            raise RuntimeError(f"EODHD fetch_dividends error per {symbol}: {str(e)}")
