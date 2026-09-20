# sniper-bot-optimized/config.py
import os

class Config:
    # --- Telegram ---
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

    # --- Dexscreener ---
    # URL del WebSocket di Dexscreener per Solana.
    DEXSCREENER_WS_URL = os.getenv("DEXSCREENER_WS_URL", "wss://io.dexscreener.com/ws/solana/pairs")

    # --- Helius (per dati on-chain aggiuntivi, es. holders, bundle check) ---
    HELIUS_API_KEY = os.getenv("HELIUS_API_KEY")

    # --- Cryptopanic (per news/narrative, opzionale) ---
    CRYPTOPANIC_API_KEY = os.getenv("CRYPTOPANIC_API_KEY")

    # --- GNews (per news/narrative alternativa, opzionale) ---
    GNEWS_API_KEY = os.getenv("GNEWS_API_KEY")

    # --- Filtri per identificare meme coin potenziali (MVP) ---
    MIN_LIQUIDITY = float(os.getenv("MIN_LIQUIDITY", "5000"))   # Liquidità minima del pool in USD
    MAX_MARKET_CAP = float(os.getenv("MAX_MARKET_CAP", "50000")) # Market Cap massimo iniziale in USD
    MAX_AGE_MINUTES = int(os.getenv("MAX_AGE_MINUTES", "5"))    # Età massima del pair in minuti dal lancio
    MIN_HOLDERS = int(os.getenv("MIN_HOLDERS", "10"))       # Numero minimo di holders

    # --- Altre configurazioni ---
    MONITOR_INTERVAL_DEXSCREENER = int(os.getenv("MONITOR_INTERVAL_DEXSCREENER", "60")) 
    MONITOR_INTERVAL_NEWS = int(os.getenv("MONITOR_INTERVAL_NEWS", "300")) # Intervallo in secondi per news