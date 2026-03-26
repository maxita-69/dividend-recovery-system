"""
Saxo Bank OpenAPI Provider - Integration with Saxo Bank's REST API.

Supports:
- Chart Service: Historical OHLCV data (up to 1200 samples per call)
- Corporate Actions: Dividends and stock splits
- Reference Data: Instrument details and market info

Authentication: Bearer token (OAuth2) via SAXO_TOKEN or SAXO_CLIENT_ID/SECRET
Base URL: Configurable via SAXO_BASE_URL (default: https://api.saxobank.com)

Documentation: https://www.developer.saxo/openapi/learn
"""
import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from providers.base_provider import BaseProvider

load_dotenv()


class SaxoProvider(BaseProvider):
    """
    Saxo Bank OpenAPI provider for historical prices and corporate actions.
    
    Features:
    - Historical OHLCV data via Chart Service (endpoint: /chart/v1/charts/)
    - Dividends via Corporate Actions module
    - Support for daily data (Horizon=1440 minutes)
    - Max 1200 data points per request (~5 years daily data)
    
    Authentication:
        Set SAXO_TOKEN environment variable with your bearer token,
        or use SAXO_CLIENT_ID and SAXO_CLIENT_SECRET for OAuth2 flow.
    
    Example:
        >>> provider = SaxoProvider()
        >>> prices = provider.fetch_prices('AAPL', start_date='2020-01-01')
        >>> dividends = provider.fetch_dividends('AAPL')
    """

    BASE_URL = os.getenv("SAXO_BASE_URL", "https://api.saxobank.com")

    def __init__(self, token: str = None):
        """
        Initialize Saxo provider.
        
        Args:
            token: Optional bearer token. If not provided, uses SAXO_TOKEN env var.
        
        Raises:
            ValueError: If no authentication token is found
        """
        self.token = token or os.getenv("SAXO_TOKEN")
        
        # Fallback to OAuth2 client credentials if token not provided
        self.client_id = os.getenv("SAXO_CLIENT_ID")
        self.client_secret = os.getenv("SAXO_CLIENT_SECRET")
        
        if not self.token and not (self.client_id and self.client_secret):
            raise ValueError(
                "SAXO_TOKEN non trovato nel file .env oppure fornire SAXO_CLIENT_ID e SAXO_CLIENT_SECRET"
            )
        
        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json"
        })
        
        # Cache for UIC mapping (symbol -> UIC conversion)
        self._uic_cache = {}

    def _get_auth_headers(self) -> dict:
        """Get authentication headers, refreshing token if needed."""
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        
        # TODO: Implement OAuth2 token refresh if using client credentials
        # For now, assume token is already valid
        return {}

    def _make_request(self, endpoint: str, params: dict = None) -> dict:
        """
        Helper method to make API requests with error handling.
        
        Args:
            endpoint: API endpoint path (e.g., 'chart/v1/charts')
            params: Query parameters
        
        Returns:
            dict: JSON response data
        
        Raises:
            RuntimeError: On HTTP errors or connection issues
        """
        if params is None:
            params = {}

        url = f"{self.BASE_URL}/{endpoint}"
        headers = self._get_auth_headers()

        response = None
        try:
            response = self.session.get(url, params=params, headers=headers, timeout=15)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            raise RuntimeError(f"Timeout chiamata Saxo per {endpoint}")
        except requests.exceptions.RequestException as e:
            if response is not None:
                try:
                    error_body = response.json()
                    raise RuntimeError(
                        f"Errore HTTP {response.status_code}: {error_body}"
                    ) from e
                except:
                    raise RuntimeError(
                        f"Errore HTTP {response.status_code}: {response.text}"
                    ) from e
            else:
                raise RuntimeError(f"Errore connessione: {str(e)}") from e

    def _get_uic(self, symbol: str, asset_type: str = "Stock") -> int:
        """
        Get Unique Instrument Code (UIC) for a symbol.
        
        Saxo API uses UIC instead of ticker symbols. This method attempts
        to resolve the symbol to a UIC using the reference data endpoint.
        
        Args:
            symbol: Ticker symbol (e.g., 'AAPL', 'ENEL.MI')
            asset_type: Asset type ('Stock', 'ETF', 'Index', etc.)
        
        Returns:
            int: UIC for the instrument
        
        Raises:
            ValueError: If symbol cannot be resolved
        """
        # Check cache first
        cache_key = f"{symbol}:{asset_type}"
        if cache_key in self._uic_cache:
            return self._uic_cache[cache_key]

        # Try to find UIC via reference data endpoint
        # Endpoint: /ref/v1/instruments/search/{AssetType}
        try:
            # Search by symbol
            search_endpoint = f"ref/v1/instruments/search/{asset_type}"
            params = {"Query": symbol}
            data = self._make_request(search_endpoint, params=params)
            
            if isinstance(data, list) and len(data) > 0:
                # Take first match
                uic = data[0].get("Uic")
                if uic:
                    self._uic_cache[cache_key] = uic
                    return uic
            
            # Alternative: try direct lookup if symbol format is known
            # Some markets use specific formats (e.g., ENEL.MI for Milan)
            raise ValueError(f"Impossibile risolvere UIC per simbolo: {symbol}")
            
        except RuntimeError:
            # If search fails, try assuming symbol might already be a UIC
            try:
                uic = int(symbol)
                self._uic_cache[cache_key] = uic
                return uic
            except ValueError:
                raise ValueError(
                    f"Simbolo '{symbol}' non risolto. Fornire UIC numerico o verificare il formato."
                )

    def fetch_prices(
        self, 
        symbol: str, 
        start_date: str = None, 
        end_date: str = None,
        asset_type: str = "Stock"
    ) -> list:
        """
        Download historical OHLCV data via Saxo Chart Service.
        
        Endpoint: GET /chart/v1/charts/{Uic}/{AssetType}/{Horizon}
        
        Args:
            symbol: Ticker symbol or UIC
            start_date: Start date (format: YYYY-MM-DD) - optional
            end_date: End date (format: YYYY-MM-DD) - optional
            asset_type: Asset type ('Stock', 'ETF', 'Index', 'Future', etc.)
                       Default: 'Stock'
        
        Returns:
            list: List of dicts with fields: date, open, high, low, close, volume
        
        Notes:
            - Max 1200 data points per request
            - For daily data, Horizon = 1440 (minutes)
            - Multiple requests may be needed for long date ranges
        """
        # Resolve symbol to UIC
        try:
            uic = self._get_uic(symbol, asset_type)
        except ValueError:
            # If resolution fails, user might have provided UIC directly
            try:
                uic = int(symbol)
            except ValueError:
                raise ValueError(
                    f"Simbolo '{symbol}' non valido. Fornire ticker valido o UIC numerico."
                )

        # Horizon for daily data: 1440 minutes
        horizon = "D1"  # Daily candles
        endpoint = f"chart/v1/charts/{uic}/{asset_type}/{horizon}"

        # Build query parameters
        params = {
            "CustomerKey": os.getenv("SAXO_CUSTOMER_KEY", ""),  # Optional
        }

        # Date range handling
        # Saxo uses FromDate and ToDate in ISO 8601 format
        if start_date:
            params["FromDate"] = f"{start_date}T00:00:00"
        if end_date:
            params["ToDate"] = f"{end_date}T23:59:59"

        # Make request
        data = self._make_request(endpoint, params=params)

        # Parse response
        # Expected format: { "ChartData": [{ "TimeStamp": "...", "Open": ..., ... }] }
        chart_data = data.get("ChartData", [])
        
        if not chart_data:
            # Try alternative response structure
            chart_data = data.get("data", []) if isinstance(data, dict) else []

        # Convert to standard format
        result = []
        for candle in chart_data:
            timestamp = candle.get("TimeStamp") or candle.get("Time")
            if not timestamp:
                continue
            
            # Parse timestamp (ISO 8601 or Unix timestamp)
            if isinstance(timestamp, (int, float)):
                dt = datetime.fromtimestamp(timestamp)
            else:
                # Handle ISO 8601 format
                ts_str = timestamp.replace("Z", "+00:00")
                try:
                    dt = datetime.fromisoformat(ts_str.split("+")[0])
                except:
                    dt = datetime.strptime(timestamp[:19], "%Y-%m-%dT%H:%M:%S")

            date_str = dt.strftime("%Y-%m-%d")

            # Filter by date range if specified
            if start_date and date_str < start_date:
                continue
            if end_date and date_str > end_date:
                continue

            result.append({
                'date': date_str,
                'open': float(candle.get("Open", 0)),
                'high': float(candle.get("High", 0)),
                'low': float(candle.get("Low", 0)),
                'close': float(candle.get("Close", 0)),
                'volume': int(candle.get("Volume", 0))
            })

        return result

    def fetch_dividends(
        self, 
        symbol: str, 
        start_date: str = None, 
        end_date: str = None,
        asset_type: str = "Stock"
    ) -> list:
        """
        Download dividend history via Saxo Corporate Actions module.
        
        Endpoint: GET /ref/v1/corporateactions/
        
        Args:
            symbol: Ticker symbol or UIC
            start_date: Start date (format: YYYY-MM-DD) - optional
            end_date: End date (format: YYYY-MM-DD) - optional
            asset_type: Asset type ('Stock', 'ETF', etc.)
        
        Returns:
            list: List of dicts with dividend info:
                  ex_date, amount, payment_date, record_date, declaration_date
        
        Notes:
            - Requires appropriate market data licenses
            - May need to paginate through results for long histories
        """
        # Resolve symbol to UIC
        try:
            uic = self._get_uic(symbol, asset_type)
        except ValueError:
            try:
                uic = int(symbol)
            except ValueError:
                raise ValueError(
                    f"Simbolo '{symbol}' non valido. Fornire ticker valido o UIC numerico."
                )

        # Corporate Actions endpoint
        endpoint = "ref/v1/corporateactions/"
        
        params = {
            "Uic": uic,
            "AssetType": asset_type,
        }

        # Date filtering
        if start_date:
            params["FromDateTime"] = f"{start_date}T00:00:00"
        if end_date:
            params["ToDateTime"] = f"{end_date}T23:59:59"

        try:
            data = self._make_request(endpoint, params=params)
        except RuntimeError as e:
            # Corporate Actions may require special licensing
            # Return empty list if not available
            print(f"Warning: Corporate Actions non disponibile: {e}")
            return []

        # Parse response
        # Expected format: { "CorporateActions": [...] }
        corp_actions = data.get("CorporateActions", [])
        
        if not corp_actions:
            corp_actions = data if isinstance(data, list) else []

        # Filter for dividends only
        dividends = []
        for action in corp_actions:
            action_type = action.get("Type", "").upper()
            
            # Look for dividend-related events
            if action_type not in ["DIVIDEND", "CASH DIVIDEND", "DIVIDEND PAYOUT"]:
                continue
            
            ex_date = action.get("ExDate") or action.get("ExDateTime")
            if not ex_date:
                continue
            
            # Parse ex_date
            if isinstance(ex_date, (int, float)):
                dt = datetime.fromtimestamp(ex_date)
            else:
                try:
                    dt = datetime.fromisoformat(ex_date[:19])
                except:
                    continue
            
            date_str = dt.strftime("%Y-%m-%d")

            # Filter by date range
            if start_date and date_str < start_date:
                continue
            if end_date and date_str > end_date:
                continue

            # Extract amount
            amount = action.get("Value") or action.get("Amount") or 0
            
            # Extract other dates if available
            payment_date = action.get("PaymentDate")
            record_date = action.get("RecordDate")
            declaration_date = action.get("AnnouncementDate")

            dividends.append({
                'ex_date': date_str,
                'amount': float(amount),
                'payment_date': payment_date[:10] if payment_date else None,
                'record_date': record_date[:10] if record_date else None,
                'declaration_date': declaration_date[:10] if declaration_date else None,
                'currency': action.get("Currency", "EUR"),
                'type': action_type
            })

        return dividends

    def get_price(self, symbol: str, asset_type: str = "Stock") -> float:
        """
        Get current/last price for an instrument.
        
        Uses Chart Service with single recent candle.
        
        Args:
            symbol: Ticker symbol or UIC
            asset_type: Asset type
        
        Returns:
            float: Current price
        """
        # Fetch most recent daily candle
        prices = self.fetch_prices(symbol, asset_type=asset_type)
        
        if not prices:
            raise ValueError(f"Nessun dato prezzi trovato per {symbol}")
        
        # Return last close price
        return float(prices[-1]['close'])

    def get_profile(self, symbol: str, asset_type: str = "Stock") -> dict:
        """
        Get instrument profile/reference data.
        
        Endpoint: GET /ref/v1/instruments/{AssetType}/{Uic}
        
        Args:
            symbol: Ticker symbol or UIC
            asset_type: Asset type
        
        Returns:
            dict: Instrument profile data
        """
        # Resolve symbol to UIC
        try:
            uic = self._get_uic(symbol, asset_type)
        except ValueError:
            try:
                uic = int(symbol)
            except ValueError:
                raise ValueError(
                    f"Simbolo '{symbol}' non valido. Fornire ticker valido o UIC numerico."
                )

        endpoint = f"ref/v1/instruments/{asset_type}/{uic}"
        
        try:
            data = self._make_request(endpoint)
            return data
        except RuntimeError:
            return {}

    def search_symbol(self, query: str, asset_type: str = "Stock") -> list:
        """
        Search for instruments by name/symbol.
        
        Endpoint: GET /ref/v1/instruments/search/{AssetType}
        
        Args:
            query: Search query (company name or symbol)
            asset_type: Asset type to search
        
        Returns:
            list: List of matching instruments
        """
        endpoint = f"ref/v1/instruments/search/{asset_type}"
        params = {"Query": query}
        
        try:
            data = self._make_request(endpoint, params=params)
            
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                return data.get("Instruments", [])
            else:
                return []
        except RuntimeError:
            return []

    def __del__(self):
        """Cleanup session on deletion."""
        if hasattr(self, 'session'):
            self.session.close()
