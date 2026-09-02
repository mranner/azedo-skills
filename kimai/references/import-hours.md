# Externe Stunden importieren

Ersetzt das fruehere `kimai_stunden.py`. Liest eine JSON-Eingabedatei und verteilt die Stunden gleichmaessig auf Werktage (oesterreichische Feiertage beruecksichtigt).

```bash
python3 "$SKILL_DIR/kimai" import-hours <datei.json>
python3 "$SKILL_DIR/kimai" import-hours <datei.json> --execute
```

Ohne `--execute` wird nur eine Vorschau angezeigt. Mit `--execute` werden die Eintraege in Kimai angelegt.

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

Die Konfiguration steht vollstaendig in der Eingabedatei — der Skill kennt weder Projekte
noch Raten noch Mitarbeiter:

- `user` — Username (wird ueber `instance.json` aufgeloest) oder numerische User-ID.
- `raten.extern` — was der externe Mitarbeiter verrechnet, `raten.kimai` — der Kimai-Stundensatz.
- `projekte` — frei waehlbare Schluessel; `name` ist optional (Default: der Schluessel).
  `beide` ist reserviert und kann nicht als Projektschluessel verwendet werden.

Schluessel `projekt` in `eintraege`: einer der Schluessel aus `projekte` oder `beide` (50:50-Split).
Stundensatz-Konversion: `ceil(stunden * raten.extern / raten.kimai)` pro Eintrag, max 7h/Tag.
