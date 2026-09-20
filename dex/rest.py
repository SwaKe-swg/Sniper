# sniper-bot-optimized/dex/rest.py
import requests
from datetime import datetime

class DexscreenerRESTClient:
    BASE_URL = "https://api.dexscreener.com/latest/dex/tokens/"

    def __init__(self, helius_api_key: str = None):
        self.helius_api_key = helius_api_key

    def get_token_info(self, token_address: str):
        """Recupera informazioni dettagliate su un token da Dexscreener."""
        try:
            url = f"{self.BASE_URL}{token_address}"
            response = requests.get(url, timeout=10)
            response.raise_for_status() # Lancia un'eccezione per errori HTTP
            data = response.json()
            
            # Qui potresti arricchire i dati con Helius se l'API key è fornita
            # e se ci sono chiamate specifiche da fare (es. per top holders)
            
            return data
        except requests.exceptions.RequestException as e:
            print(f"[{datetime.now()}] Errore recupero info token {token_address} da Dexscreener REST: {e}")
            return None

