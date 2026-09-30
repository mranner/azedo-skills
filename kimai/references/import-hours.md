# Externe Stunden importieren

Liest eine JSON-Eingabedatei und verteilt die Stunden gleichmäßig auf Werktage (österreichische Feiertage berücksichtigt).

```bash
python3 "$SKILL_DIR/kimai" import-hours <datei.json>
python3 "$SKILL_DIR/kimai" import-hours <datei.json> --execute
```

Ohne `--execute` wird nur eine Vorschau angezeigt. Mit `--execute` werden die Einträge in Kimai angelegt.

**JSON-Format:**
```json
{
  "monat": "2026-05",
  "user": "mmuster",
  "raten": { "extern": 55, "kimai": 77 },
  "projekte": {
    "projekt-a": { "id": 107, "activity_id": 230, "name": "Projekt A Entwicklung" },
    "projekt-b": { "id": 108, "activity_id": 239, "name": "Projekt B Entwicklung" }
  },
  "eintraege": [
    {"projekt": "projekt-a", "stunden": 21, "beschreibung": "..."},
    {"projekt": "projekt-b", "stunden": 8,  "beschreibung": "..."},
    {"projekt": "beide",     "stunden": 20, "beschreibung": "..."}
  ]
}
```

Die Konfiguration steht vollständig in der Eingabedatei — der Skill kennt weder Projekte
noch Raten noch Mitarbeiter:

- `user` — Username (wird über `instance.json` aufgelöst) oder numerische User-ID.
- `raten.extern` — was der externe Mitarbeiter verrechnet, `raten.kimai` — der Kimai-Stundensatz.
- `projekte` — frei wählbare Schlüssel; `name` ist optional (Default: der Schlüssel).
  `beide` ist reserviert und kann nicht als Projektschlüssel verwendet werden.

Schlüssel `projekt` in `eintraege`: einer der Schlüssel aus `projekte` oder `beide` (50:50-Split).
Stundensatz-Konversion: Summe der tatsächlichen Stunden je Projekt (50:50-Hälften ungerundet) `× raten.extern / raten.kimai`, kaufmännisch gerundet, max 7h/Tag.
