from src.fetch_prices import fetch_prices
from src.fetch_dividends import fetch_dividends

def test_all():
    symbol = "AAPL"  # puoi cambiarlo con un titolo italiano se preferisci

    print("\n=== TEST FETCH PRICES ===")
    prices = fetch_prices(symbol)
    print(f"Numero di prezzi scaricati: {len(prices)}")
    if prices:
        print("Esempio:", prices[0])

    print("\n=== TEST FETCH DIVIDENDS ===")
    dividends = fetch_dividends(symbol)
    print(f"Numero di dividendi scaricati: {len(dividends)}")
    if dividends:
        print("Esempio:", dividends[0])

if __name__ == "__main__":
    test_all()
