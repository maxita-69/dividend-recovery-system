from providers.provider_manager import get_provider

def fetch_prices(symbol: str):
    provider = get_provider()
    return provider.fetch_prices(symbol)
