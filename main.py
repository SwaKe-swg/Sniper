import os
import json
import asyncio
import traceback
from datetime import datetime
from telegram import Bot
from telegram.error import TelegramError

# Importa le configurazioni
from config import Config
from dex.ws_client import DexscreenerWSClient
from dex.rest import DexscreenerRESTClient
from filters.base import Filters
from alerts.tg import send_pump_alert
from news.cryptopanic import CryptoPanicClient
from news.gnews import GNewsClient
from utils.helius import HeliusClient # Per ora Helius non è integrato nei filtri di base

# --- DEBUG INIZIALE PER VARIABILI D'AMBIENTE ---
print(f"DEBUG: TELEGRAM_BOT_TOKEN dal config: {Config.TELEGRAM_BOT_TOKEN[:5]}...{Config.TELEGRAM_BOT_TOKEN[-5:] if Config.TELEGRAM_BOT_TOKEN else 'None'}")
print(f"DEBUG: CHAT_ID dal config: {Config.TELEGRAM_CHAT_ID}")
if not Config.TELEGRAM_BOT_TOKEN:
    print("ERRORE CRITICO: TELEGRAM_BOT_TOKEN è vuoto o None. Controlla le variabili d'ambiente su Railway!")
    raise ValueError("TELEGRAM_BOT_TOKEN non configurato o non letto correttamente.")
# --- FINE DEBUG INIZIALE ---


# Inizializza il bot Telegram
telegram_bot = Bot(Config.TELEGRAM_BOT_TOKEN)


# Inizializza i client per i servizi
dexscreener_ws_client = DexscreenerWSClient(Config.DEXSCREENER_WS_URL)
dexscreener_rest_client = DexscreenerRESTClient(Config.HELIUS_API_KEY) # Helius API key per arricchire dati
filters_logic = Filters(
    min_liquidity=Config.MIN_LIQUIDITY,
    max_mcap=Config.MAX_MARKET_CAP,
    max_age_minutes=Config.MAX_AGE_MINUTES,
    min_holders=Config.MIN_HOLDERS
)
cryptopanic_client = CryptoPanicClient(Config.CRYPTOPANIC_API_KEY) if Config.CRYPTOPANIC_API_KEY else None
gnews_client = GNewsClient(Config.GNEWS_API_KEY) if Config.GNEWS_API_KEY else None
helius_client = HeliusClient(Config.HELIUS_API_KEY) if Config.HELIUS_API_KEY else None


# Cache per evitare alert duplicati
alerted_pairs_cache = set()
NEWS_CACHE = set()

# --- Funzioni di Monitoraggio ---
async def process_new_pair(data: dict):
    """Processa i dati di un nuovo pair ricevuto da Dexscreener WebSocket."""
    # ws_client.py ora dovrebbe passare dati in formato {"type": "pair_new"/"pair_update", "pair": {...}}
    event_type = data.get("type")
    pair_info = data.get("pair")
    
    if not pair_info or event_type not in ["pair_new", "pair_update"]:
        # print(f"[{datetime.now()}] Messaggio WS non processato (tipo non supportato o dati mancanti): {data}") # Debug se necessario
        return # Se non è un evento di pair valido, non processare

    if pair_info.get("chain") == "solana":
        # Estrai dati necessari per i filtri
        # Tentiamo di leggere i dati da pair_info, se mancano usiamo default 0
        liquidity = pair_info.get("liquidity", {}).get("usd", 0) if isinstance(pair_info.get("liquidity"), dict) else 0
        market_cap = pair_info.get("fdv", 0) if pair_info.get("fdv") else pair_info.get("marketCap", 0) # FDV o marketCap
        pair_created_at_timestamp = pair_info.get("pairCreatedAt")
        age_minutes = (datetime.now().timestamp() - pair_created_at_timestamp) / 60 if pair_created_at_timestamp else 0
        holders = pair_info.get("holders", 0) # Dexscreener WS potrebbe non fornire holders direttamente
        volume_24h = pair_info.get("volume", {}).get("h24", 0) if isinstance(pair_info.get("volume"), dict) else 0

        # Estrai l'indirizzo del token base per il check REST e la cache
        token_address = pair_info.get("baseToken", {}).get("address")
        
        if token_address and token_address not in alerted_pairs_cache:
            print(f"[{datetime.now()}] Potenziale pair WS: {pair_info.get('baseToken', {}).get('symbol')}. Recupero info REST per dettagli...")
            rest_data = dexscreener_rest_client.get_token_info(token_address)
            
            if rest_data and rest_data.get("pairs"):
                full_pair_data = rest_data["pairs"][0] # Prendi il primo (o il più rilevante)
                
                # Aggiorna i dati per i filtri con info REST più accurate
                liquidity = full_pair_data.get("liquidity", {}).get("usd", liquidity)
                market_cap = full_pair_data.get("fdv", market_cap) if full_pair_data.get("fdv") else full_pair_data.get("marketCap", market_cap)
                age_minutes = (datetime.now().timestamp() - full_pair_data.get("pairCreatedAt", datetime.now().timestamp())) / 60 if full_pair_data.get("pairCreatedAt") else age_minutes
                # holders = full_pair_data.get("holders", holders) # Dexscreener REST raramente ha holders
                volume_24h = full_pair_data.get("volume", {}).get("h24", volume_24h)

                # Simula un valore di holders se non disponibile (assumi che abbia abbastanza per il filtro)
                # Questo è un workaround finché non integriamo Helius per holders reali
                if holders == 0 and Config.MIN_HOLDERS > 0:
                    holders = Config.MIN_HOLDERS + 1 
                
                synthetic_pair_for_filter = {
                    'liquidity': liquidity,
                    'market_cap': market_cap,
                    'age_minutes': age_minutes,
                    'holders': holders
                }

                if filters_logic.check(synthetic_pair_for_filter): # Controlla i filtri
                    coin_name = full_pair_data.get("baseToken", {}).get("name", "N/A")
                    symbol = full_pair_data.get("baseToken", {}).get("symbol", "N/A")
                    dexscreener_link = f"https://www.dextools.io/app/en/solana/pair-explorer/{full_pair_data.get('pairAddress')}"
                    
                    price_change_h1 = full_pair_data.get("priceChange", {}).get("h1", 0)
                    price_change_h6 = full_pair_data.get("priceChange", {}).get("h6", 0)
                    price_change_h24 = full_pair_data.get("priceChange", {}).get("h24", 0)

                    await send_pump_alert(
                        telegram_bot,
                        Config.TELEGRAM_CHAT_ID,
                        coin_name, symbol,
                        dexscreener_link,
                        synthetic_pair_for_filter['market_cap'],
                        synthetic_pair_for_filter['liquidity'],
                        synthetic_pair_for_filter['age_minutes'],
                        synthetic_pair_for_filter['holders'],
                        volume_24h,
                        price_change_h1, price_change_h6, price_change_h24
                    )
                    alerted_pairs_cache.add(token_address)
                    print(f"[{datetime.now()}] Alert inviato per {symbol}.")
                else:
                    print(f"[{datetime.now()}] Pair {symbol} non ha superato i filtri dopo REST check o non è valido per i filtri: {synthetic_pair_for_filter}")
            else:
                print(f"[{datetime.now()}] Nessun dato REST trovato per {token_address} o pairs non valido.")
        else:
            print(f"[{datetime.now()}] Token {token_address} già in cache o non valido per alert.")
    else:
        print(f"[{datetime.now()}] Pair WS non su Solana: {pair_info.get('chain')}")

async def monitor_dexscreener_solana():
    """Connette e monitora Dexscreener WS per nuovi pair e aggiornamenti."""
    dexscreener_ws_client.add_listener(process_new_pair)
    await dexscreener_ws_client.connect()

async def monitor_news_narrative():
    """Monitora news e narrative rilevanti (Cryptopanic/Gnews) e invia alert."""
    while True:
        try:
            news_items = []
            if cryptopanic_client:
                news_items.extend(cryptopanic_client.get_news())
            if gnews_client:
                news_items.extend(gnews_client.get_news())

            for news in news_items:
                title = news.get("title", "N/A")
                url = news.get("url", "#")
                
                if url not in NEWS_CACHE:
                    message = (
                        f"📰 *News/Narrative Alert!* 📰\n\n"
                        f"*{title}*\n"
                        f"[Link all'articolo]({url})\n\n"
                        f"Controlla se c'è hype bro."
                    )
                    await telegram_bot.send_message(
                        chat_id=Config.TELEGRAM_CHAT_ID,
                        text=message,
                        parse_mode="Markdown"
                    )
                    NEWS_CACHE.add(url)
                    print(f"[{datetime.now()}] News alert inviato: {title}")
        except Exception as e:
            print(f"[{datetime.now()}] Errore nel monitoraggio news: {traceback.format_exc()}")
        
        await asyncio.sleep(Config.MONITOR_INTERVAL_NEWS)

# --- Main Loop del Bot ---
async def main():
    print(f"[{datetime.now()}] Zephyr Sniper Bot avviato. BOT_TOKEN: {Config.TELEGRAM_BOT_TOKEN[:5]}...{Config.TELEGRAM_BOT_TOKEN[-5:] if Config.TELEGRAM_BOT_TOKEN else 'None'} CHAT_ID: {Config.TELEGRAM_CHAT_ID}")
    print(f"[{datetime.now()}] Filtri attivi: Liq > ${Config.MIN_LIQUIDITY}, MC < ${Config.MAX_MARKET_CAP}, Age < {Config.MAX_AGE_MINUTES} min, Holders > {Config.MIN_HOLDERS}")
    
    # Avvia il monitoraggio Dexscreener WS in background
    asyncio.create_task(monitor_dexscreener_solana())
    
    # Avvia il monitoraggio News/Narrative se le API key sono configurate
    if cryptopanic_client or gnews_client:
        asyncio.create_task(monitor_news_narrative())

    # Mantieni il bot in esecuzione
    while True:
        await asyncio.sleep(60)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"[{datetime.now()}] Bot terminato manualmente.")
    except Exception as e:
        print(f"[{datetime.now()}] Errore critico nel main loop: {traceback.format_exc()}")
