# sniper-bot-optimized/alerts/tg.py
from datetime import datetime
from telegram import Bot
from telegram.error import TelegramError

async def send_pump_alert(
    bot: Bot, chat_id: str,
    coin_name: str, symbol: str,
    dexscreener_link: str,
    mcap: float, liquidity: float,
    age_minutes: int, holders: int,
    volume_24h: float,
    price_change_h1: float, # Aggiunto price change 1h
    price_change_h6: float, # Aggiunto price change 6h
    price_change_h24: float # Aggiunto price change 24h
):
    """
    Formatta e invia un alert di potenziale pump a Telegram.
    """
    message = (
        f"🚨 *OU SHI BRO, Tieni d'occhio una MEME COIN in movimento!* 🚨\n\n"
        f"*Nome:* {coin_name} (`{symbol}`)\n"
        f"*Market Cap:* `${mcap:,.0f}`\n"
        f"*Liquidità:* `${liquidity:,.0f}`\n"
        f"*Età:* `{age_minutes:.1f}` minuti\n"
        f"*Holders:* `{holders}`\n"
        f"*Volume 24h:* `${volume_24h:,.0f}`\n\n"
        f"📈 *Performance (cambio prezzo):*\n"
        f"  - `1h`: {price_change_h1:+.2f}%\n"
        f"  - `6h`: {price_change_h6:+.2f}%\n"
        f"  - `24h`: {price_change_h24:+.2f}%\n\n"
        f"📊 *Chart:* [Dexscreener]({dexscreener_link})\n\n"
        f"🔥 *È PURA WILD WEST, BRO. FAI LE TUE RICERCHE.* 🔥"
    )
    
    try:
        await bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown', disable_web_page_preview=True)
        print(f"[{datetime.now()}] Alert pump inviato con successo per {symbol} a {chat_id}")
    except TelegramError as e:
        print(f"[{datetime.now()}] Errore nell'invio dell'alert Telegram per {symbol}: {e}")

