"""
Data Providers Package
Abstraction layer per multiple fonti dati (FMP, Yahoo Finance, Alpha Vantage, etc.)
"""
from providers.base_provider import BaseProvider
from providers.fmp_provider import FMPProvider
from providers.yahoo_provider import YahooProvider
from providers.provider_manager import get_provider, list_available_providers, get_current_provider_name

__all__ = [
    "BaseProvider",
    "FMPProvider",
    "YahooProvider",
    "get_provider",
    "list_available_providers",
    "get_current_provider_name",
]
