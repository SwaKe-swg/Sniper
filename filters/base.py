# sniper-bot-optimized/filters/base.py
from datetime import datetime

class Filters:
    def __init__(self, min_liquidity: float = 5000, max_mcap: float = 50000,
                 max_age_minutes: int = 5, min_holders: int = 10):
        self.min_liquidity = min_liquidity
        self.max_mcap = max_mcap
        self.max_age_minutes = max_age_minutes
        self.min_holders = min_holders

    def check(self, pair_data: dict) -> bool:
        """
        Controlla se un pair soddisfa i criteri di filtro.
        pair_data è il dizionario con i dati del pair da Dexscreener.
        """
        try:
            # Assicurati che il pair_data contenga le chiavi necessarie
            # Alcuni campi potrebbero essere assenti, gestiamo con valori default
            liquidity = pair_data.get('liquidity', 0)
            market_cap = pair_data.get('market_cap', 0)
            age_minutes = pair_data.get('age_minutes', 99999) # Se età non c'è, è vecchio
            holders = pair_data.get('holders', 0)
            
            # Filtro per liquidità minima
            if liquidity < self.min_liquidity:
                # print(f"[{datetime.now()}] Filtro liquidità: {liquidity} < {self.min_liquidity}")
                return False
            
            # Filtro per market cap massimo (solo per coin appena nate)
            if market_cap > self.max_mcap:
                # print(f"[{datetime.now()}] Filtro market cap: {market_cap} > {self.max_mcap}")
                return False

            # Filtro per età massima del pair (solo coin molto recenti)
            if age_minutes > self.max_age_minutes:
                # print(f"[{datetime.now()}] Filtro età: {age_minutes} > {self.max_age_minutes}")
                return False
            
            # Filtro per numero minimo di holders
            if holders < self.min_holders:
                # print(f"[{datetime.now()}] Filtro holders: {holders} < {self.min_holders}")
                return False
            
            # Se tutti i filtri passano
            return True
            
        except Exception as e:
            print(f"[{datetime.now()}] Errore durante l'applicazione dei filtri: {e}")
            return False

