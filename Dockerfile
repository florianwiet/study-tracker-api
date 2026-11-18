FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py routes.py stats.py schemas.py db.py ./
COPY static ./static

# SQLite-Datei im Volume, damit die Daten einen Container-Neustart überleben
ENV DATABASE_URL=sqlite:////data/entries.db
VOLUME /data

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
