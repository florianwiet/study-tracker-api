# Lern-Tracker-API

kleine REST-API zum erfassen von Lerneinheiten, gebaut mit FastAPI und SQLModel

## Features

+ CRUD-Endpunkte für Lerneinträge (Fach, Beschreibung, Dauer & Datum)
+ Validierung der Eingaben
+ SQL-Datenbank
+ Health-Check-Endpunkt
+ `X-Process-Time`-Header mit der Bearbeitungszeit jeder Anfrage
+ Filtern nach Start und End Datum, Filtern nach Fach
+ statistik pro fach aufrufen
