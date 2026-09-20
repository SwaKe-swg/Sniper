    # sniper-bot-optimized/dex/ws_client.py
    import asyncio  # <--- Questa riga deve iniziare esattamente qui, senza spazi
    import websockets
    import json
    from datetime import datetime

    class DexscreenerWSClient: # <--- Anche la definizione della classe deve iniziare qui
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
            # Dexscreener WebSocket invia messaggi di tipo "data" con "pairs" all'interno
            # e a volte singoli "pair" di tipo "pair"
            
# Se il messaggio è di tipo "data" e contiene una lista di pairs
            if isinstance(data, dict) and data.get("type") == "data" and isinstance(data.get("data"), dict) and isinstance(data["data"].get("pairs"), list):
                for pair_data in data["data"]["pairs"]:
                    # Inoltriamo come "pair_update" con il pair estratto
                    for listener in self.listeners:
                        await listener({"type": "pair_update", "pair": pair_data})
            
            # Se il messaggio è di tipo "pair" e contiene un singolo pair
            elif isinstance(data, dict) and data.get("type") == "pair" and isinstance(data.get("pair"), dict):
                # Inoltriamo come "pair_new" con il pair estratto
                for listener in self.listeners:
                    await listener({"type": "pair_new", "pair": data["pair"]})
            
            # Altri messaggi (es. ping/pong, init) ignorati o processati se necessario
            # else:
                # print(f"[{datetime.now()}] Messaggio Dexscreener WS non gestito: {json.dumps(data)}")
                
        def add_listener(self, listener_func):
            """Aggiunge una funzione listener per i nuovi messaggi."""
            self.listeners.append(listener_func)

        async def send_ping_task(self):
            """Task per inviare ping regolarmente e mantenere viva la connessione."""
            while True:
                if self.is_connected and self.websocket:
                    try:
                        await self.websocket.send(json.dumps({"type": "ping"}))
                        # print(f"[{datetime.now()}] Inviato ping a Dexscreener WS.") # Rimosso per non spammare i log
                    except websockets.exceptions.ConnectionClosed:
                        print(f"[{datetime.now()}] Connessione WS chiusa durante il ping.")
                        break # Esci dal loop per innescare la riconnessione
                    except Exception as e:
                        print(f"[{datetime.now()}] Errore nell'invio del ping: {e}")
                await asyncio.sleep(30) # Invia ping ogni 30 secondi
    
