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
                    # Dexscreener WS per nuovi pair su Solana spesso invia dati automaticamente
                    # senza necessità di sottoscrizione esplicita a "new_pairs"
                    # ma è buona pratica inviare un PING per mantenere la connessione attiva
                    # e avviare il send_ping_task in background.
                    asyncio.create_task(self.send_ping_task())

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
            
            # Formato comune per update (o a volte nuovi pair in una lista)
            if isinstance(data, dict) and data.get("type") == "data" and isinstance(data.get("data"), dict) and isinstance(data["data"].get("pairs"), list):
                for pair_data in data["data"]["pairs"]:
                    for listener in self.listeners:
                        await listener({"type": "pair_update", "pair": pair_data}) # Usa 'pair_update' per distinguere
            
            # Formato per un singolo pair (es. un nuovo lancio)
elif isinstance(data, dict) and data.get("type") == "pair" and isinstance(data.get("pair"), dict):
                for listener in self.listeners:
                    await listener({"type": "pair_new", "pair": data["pair"]})
            
            # Se non corrisponde a nessuno dei formati attesi, lo stampiamo per debug
            else:
                print(f"[{datetime.now()}] Formato messaggio Dexscreener WS sconosciuto: {json.dumps(data)}")
                
        def add_listener(self, listener_func):
            """Aggiunge una funzione listener per i nuovi messaggi."""
            self.listeners.append(listener_func)

        async def send_ping_task(self):
            """Task per inviare ping regolarmente e mantenere viva la connessione."""
            while True:
                if self.is_connected and self.websocket:
                    try:
                        await self.websocket.send(json.dumps({"type": "ping"}))
                        print(f"[{datetime.now()}] Inviato ping a Dexscreener WS.")
                    except websockets.exceptions.ConnectionClosed:
                        print(f"[{datetime.now()}] Connessione WS chiusa durante il ping.")
                        break # Esci dal loop per innescare la riconnessione
                    except Exception as e:
                        print(f"[{datetime.now()}] Errore nell'invio del ping: {e}")
                await asyncio.sleep(30) # Invia ping ogni 30 secondi
    
