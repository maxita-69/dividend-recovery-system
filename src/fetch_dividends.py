from providers.provider_manager import get_provider

def fetch_dividends(symbol: str):
    provider = get_provider()
    return provider.fetch_dividends(symbol)
