from src.fmp_provider import FMPProvider

print("Richiesta prezzo AAPL...")

provider = FMPProvider()
price = provider.get_price("AAPL")

print("Prezzo AAPL:", price)
