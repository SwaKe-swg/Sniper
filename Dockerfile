    # Usa un'immagine Python base per lo sviluppo
    FROM python:3.10-slim-buster

    # Imposta la directory di lavoro nel container
    WORKDIR /app

    # Copia il file requirements.txt e installa le dipendenze
    # Questo passaggio è separato per sfruttare la cache di Docker
    COPY requirements.txt .
    RUN pip install --no-cache-dir -r requirements.txt

    # Copia il resto del codice dell'applicazione
    COPY . .

    # Comando per avviare l'applicazione
    CMD ["python", "main.py"]
    
