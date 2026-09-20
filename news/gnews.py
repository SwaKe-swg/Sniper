# sniper-bot-optimized/news/gnews.py
import requests
from datetime import datetime, timedelta

class GNewsClient:
    BASE_URL = "https://gnews.io/api/v4/search"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def get_news(self, query: str = "solana memecoin", lang: str = "en", days_ago: int = 1):
        """
        Recupera notizie da GNews relative a una query.
        """
        if not self.api_key:
            return [] # Non fare chiamate se l'API key non è configurata
            
        params = {
            "q": query,
            "lang": lang,
            "token": self.api_key,
            "sortby": "relevance", # o "publishedAt"
        }
        
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Filtra gli articoli più recenti dell'ultimo giorno
            filtered_news = []
            now = datetime.now()
            for article in data.get("articles", []):
                published_at = datetime.fromisoformat(article["publishedAt"].replace("Z", "+00:00"))
                if (now - published_at) < timedelta(days=days_ago):
                    filtered_news.append(article)
            
            return filtered_news
            
        except requests.exceptions.RequestException as e:
            print(f"[{datetime.now()}] Errore recupero notizie da GNews: {e}")
            return []

