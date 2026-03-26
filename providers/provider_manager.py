"""
Provider Manager - Factory per data providers.
Gestisce la selezione del provider basato su configurazione.
"""
import os
from dotenv import load_dotenv
from providers.base_provider import BaseProvider
from providers.yahoo_provider import YahooProvider
from providers.fmp_provider import FMPProvider
from providers.saxo_provider import SaxoProvider

load_dotenv()


def get_provider(provider_name: str = None) -> BaseProvider:
    """
    Factory method per ottenere il provider corretto.

    Args:
        provider_name: Nome del provider ('FMP', 'YAHOO', 'SAXO').
                      Se None, usa variabile d'ambiente DATA_PROVIDER.

    Returns:
        BaseProvider: Istanza del provider richiesto

    Raises:
        ValueError: Se il provider non è supportato

    Examples:
        >>> provider = get_provider('FMP')
        >>> prices = provider.fetch_prices('AAPL')

        >>> provider = get_provider()  # Usa DATA_PROVIDER da .env
        >>> dividends = provider.fetch_dividends('ENEL.MI')
    """
    if provider_name is None:
        provider_name = os.getenv("DATA_PROVIDER", "FMP").upper()
    else:
        provider_name = provider_name.upper()

    if provider_name == "FMP":
        return FMPProvider()
    elif provider_name == "YAHOO":
        return YahooProvider()
    elif provider_name == "SAXO":
        return SaxoProvider()
    else:
        raise ValueError(
            f"Provider '{provider_name}' non supportato. "
            f"Provider disponibili: FMP, YAHOO, SAXO"
        )


def list_available_providers() -> list:
    """
    Restituisce la lista dei provider disponibili.

    Returns:
        list: Lista di nomi provider disponibili
    """
    return ["FMP", "YAHOO", "SAXO"]


def get_current_provider_name() -> str:
    """
    Restituisce il nome del provider corrente configurato.

    Returns:
        str: Nome del provider (es. 'FMP', 'YAHOO')
    """
    return os.getenv("DATA_PROVIDER", "FMP").upper()
