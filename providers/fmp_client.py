import requests
from config import FMP_API_KEY, FMP_BASE_URL

class FMPClient:
    def __init__(self):
        if not FMP_API_KEY:
            raise ValueError("FMP_API_KEY non trovata nel .env")
        self.api_key = FMP_API_KEY

    def get(self, endpoint, params=None):
        if params is None:
            params = {}
        params["apikey"] = self.api_key

        url = f"{FMP_BASE_URL}/{endpoint}"
        response = requests.get(url, params=params)

        if response.status_code != 200:
            raise RuntimeError(
                f"Errore FMP: {response.status_code} - {response.text}"
            )

        return response.json()
