# Setup und Konfiguration

## Config-Quelle

`KANBOARD_URL` und `KANBOARD_TOKEN` kommen aus der ersten vorhandenen Datei:

1. `KANBOARD_ENV` (Environment-Variable, voller Pfad zur Datei)
2. `.env` im **aktuellen Arbeitsverzeichnis**, falls vorhanden
3. sonst `~/.env`

Der Home-Fallback ist gewollt: eine Konfiguration reicht für alle Projekte,
ein projektlokales `.env` übersteuert sie bei Bedarf. **Achtung:** entschieden
wird allein danach, ob die Datei *existiert* — enthält ein projektlokales
`.env` die Kanboard-Schlüssel nicht (weil es z.B. nur DB-Zugangsdaten führt),
bricht der Aufruf mit `KANBOARD_URL not set in <pfad>` ab, statt auf `~/.env`
auszuweichen. Dann `KANBOARD_ENV=~/.env` setzen oder die Schlüssel ergänzen.
(Der kimai-Skill prüft an dieser Stelle zusätzlich auf seine Schlüssel und
fällt zurück — siehe dortige SKILL.md.)

## instance.json — Schema

**`instance.json` NICHT selbst roh parsen** — dafür gibt es die Subcommands
`list-projects`, `list-columns --project <name|id>` und `list-users` (liefern IDs
**und** Namen). `get-task` reichert zusätzlich `column_title`,
`swimlane_name`, `owner_username`/`owner_name` an, sodass keine Quer-Auflösung
nötig ist.

Falls doch direkt gelesen wird, ist das Schema:

```json
{
  "role": "app-admin",
  "default_user": "mmuster",
  "projects": [
    { "id": 1, "name": "azedo",
      "swimlanes": ["Standard-Swimlane"],   // Liste von STRINGS (nur Namen)
      "columns":   ["Ideen", "Bereit", "In Arbeit", "Erledigt"] }  // STRINGS
  ],
  "users": [ { "id": 4, "username": "musterfrau", "name": "Karin Musterfrau", "is_active": 1 } ]
  // deaktivierte User stehen mit "is_active": 0 drin, damit sie adressierbar bleiben
}
```

Merke: `columns`/`swimlanes` sind **Strings ohne IDs** — die Spalten-ID einer
Position ergibt sich nicht aus `instance.json`, dafür `list-columns` verwenden.
