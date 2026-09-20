# sniper-bot-optimized/dex/ws_client.py
import asyncio
import websockets
import json
from datetime import datetime

class DexscreenerWSClient:
    def __init__(self, ws_url: str):
        self.ws_url = ws_url
        self.websocket = None
        self.listeners = []
        self.is_connected = False
        self.reconnect_delay = 5 # Secondi prima di riprovare a connettersi

    async def connect(self):
        """Connette al WebSocket di Dexscreener e gestisce le riconnessioni."""
        while True:
            try:
                print(f"[{datetime.now()}] Tentativo di connessione a Dexscreener WebSocket: {self.ws_url}")
                self.websocket = await websockets.connect(self.ws_url, ping_interval=30, ping_timeout=10)
                self.is_connected = True
                print(f"[{datetime.now()}] Connesso a Dexscreener WebSocket.")
                
                # Invia una sottoscrizione iniziale o un ping se necessario per attivare il flusso
                # Per i nuovi pair su Solana, spesso i dati vengono push-ati dal WebSocket per default se connessi alla giusta WS URL
                # Non sempre serve una sottoscrizione esplicita per 'new_pairs' su Dexscreener
                # Questo è un esempio, potrebbe non essere strettamente necessario o potrebbe variare
                # await self.websocket.send(json.dumps({"method": "subscribe", "params": {"channels": ["new_pairs"], "chain": "solana"}}))
                # print(f"[{datetime.now()}] Inviata sottoscrizione per new_pairs su Solana.")

                await self.listen() # Inizia ad ascoltare i messaggi
            except websockets.exceptions.ConnectionClosed as e:
                print(f"[{datetime.now()}] Dexscreener WebSocket disconnesso (errore: {e}). Riconnessione tra {self.reconnect_delay} secondi...")
            except websockets.exceptions.WebSocketException as e:
                print(f"[{datetime.now()}] Errore WebSocket: {e}. Riprovo tra {self.reconnect_delay} secondi...")
            except Exception as e:
                print(f"[{datetime.now()}] Errore generico di connessione a Dexscreener WebSocket: {e}. Riprovo tra {self.reconnect_delay} secondi...")
            
            self.is_connected = False
            await asyncio.sleep(self.reconnect_delay) # Attendi prima di riprovare la connessione

    async def listen(self):
        """Ascolta i messaggi dal WebSocket."""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                if data.get("type") == "error":
                    print(f"[{datetime.now()}] Errore da Dexscreener WS: {data.get('message')}")
                    continue
                await self._process_message(data)
        except websockets.exceptions.ConnectionClosed as e:
            print(f"[{datetime.now()}] Ascolto interrotto, connessione chiusa: {e}")
            raise # Rilancia per innescare la riconnessione nel loop connect
        except Exception as e:
            print(f"[{datetime.now()}] Errore durante l'ascolto del WebSocket: {e}")
            raise # Rilancia per innescare la riconnessione nel loop connect

    async def _process_message(self, data):
        """Processa i messaggi ricevuti dal WebSocket."""
        # I messaggi di new_pairs da Dexscreener WebSocket possono arrivare in vari formati
        # Cerchiamo di normalizzare l'output per i listener
        
        # Caso 1: Messaggio che contiene una lista di pairs (comune per aggiornamenti o inizializzazione)
