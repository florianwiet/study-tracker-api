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

## Endpunkte

Basis-Pfad: `/api/v1/entries`

| Methode | Pfad                           | Beschreibung                    | Status    |
| ------- | ------------------------------ | ------------------------------- | --------- |
| POST    | `/api/v1/entries/`           | Neuen Lerneintrag anlegen       | 201       |
| GET     | `/api/v1/entries/`           | Alle Einträge abrufen          | 200       |
| GET     | `/api/v1/entries/{entry_id}` | Einzelnen Eintrag abrufen       | 200 / 404 |
| PATCH   | `/api/v1/entries/{entry_id}` | Eintrag teilweise aktualisieren | 200 / 404 |
| DELETE  | `/api/v1/entries/{entry_id}` | Eintrag löschen                | 200 / 404 |

### Weitere Endpunkte

| Methode | Pfad                                                      | Beschreibung                                  | Status    |
| ------- | --------------------------------------------------------- | --------------------------------------------- | --------- |
| GET     | `/api/v1/entries/filter?subject=&start_date=&end_date=` | Einträge nach Fach und/oder Zeitraum filtern | 200 / 400 |
| GET     | `/api/v1/entries/statistic/{subject}`                   | Anzahl & Gesamtminuten pro Fach               | 200 / 404 |
| GET     | `/health`                                               | Health-Check                                  | 200       |
