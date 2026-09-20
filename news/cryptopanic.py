# sniper-bot-optimized/news/cryptopanic.py
import requests
from datetime import datetime, timedelta

class CryptoPanicClient:
    BASE_URL = "https://cryptopanic.com/api/v1/posts/"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def get_news(self, query: str = "solana memecoin", days_ago: int = 1):
        """
        Recupera notizie da Cryptopanic relative a una query.
        """
        if not self.api_key:
            return [] # Non fare chiamate se l'API key non è configurata
            
        params = {
            "auth_token": self.api_key,
            "public": "true",
            "filter": "hot", # o "latest", "rising"
            "currencies": "sol", # Filtra per Solana
            "regions": "en",
            "kind": "news",
            "page": 1
        }
        
        # Aggiungi la query di ricerca se specificata
        if query:
            params["query"] = query

        try:
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Filtra gli articoli più recenti dell'ultimo giorno
            filtered_news = []
            now = datetime.now()
            for post in data.get("results", []):
                published_at = datetime.fromisoformat(post["published_at"].replace("Z", "+00:00"))
                if (now - published_at) < timedelta(days=days_ago):
                    filtered_news.append(post)
            
            return filtered_news
            
        except requests.exceptions.RequestException as e:
            print(f"[{datetime.now()}] Errore recupero notizie da Cryptopanic: {e}")
            return []

