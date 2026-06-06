# kimai -- Kimai Zeiterfassung

Zeiterfassung, Projekte, Kunden, Aktivitaeten, Tags und Teams werden ueber das gebundelte Script `kimai` (Python >=3.11, im Skill-Verzeichnis) verwaltet.

**Aufruf:** `python3 "$SKILL_DIR/kimai" <subcommand> [options]`

`$SKILL_DIR` ist das Base Directory dieses Skills (dort wo diese SKILL.md liegt).

## Setup

Beim ersten Einsatz `setup` ausfuehren:

```bash
python3 "$SKILL_DIR/kimai" setup
```

Das schreibt `instance.json` ins Skill-Verzeichnis mit allen Projekten, Aktivitaeten, Kunden und Usern. **Vor jeder Operation `$SKILL_DIR/instance.json` lesen**, um IDs und Namen zu kennen.

Falls `instance.json` nicht existiert, zuerst `setup` ausfuehren.

## Subcommands

### System

```bash
python3 "$SKILL_DIR/kimai" version
python3 "$SKILL_DIR/kimai" ping
```

### Timesheets

```bash
# Auflisten (mit Filtern)
python3 "$SKILL_DIR/kimai" list-timesheets \
  [--user <id>] [--project <id>] [--activity <id>] \
  [--begin <iso-datetime>] [--end <iso-datetime>] \
  [--exported <0|1>] [--size <n>] [--page <n>]

# Einzelnen Eintrag anzeigen
python3 "$SKILL_DIR/kimai" get-timesheet <id>

# Eintrag anlegen (ohne --end wird ein laufender Timer gestartet)
python3 "$SKILL_DIR/kimai" create-timesheet \
  --begin <iso-datetime> [--end <iso-datetime>] \
  --project <id> --activity <id> \
  [--description "<text>"] [--user <id>] \
  [--tags "tag1,tag2"] [--billable <0|1>]

# Eintrag aendern
python3 "$SKILL_DIR/kimai" update-timesheet <id> \
  [--begin <iso>] [--end <iso>] [--project <id>] [--activity <id>] \
  [--description "<text>"] [--user <id>] [--tags "tag1,tag2"] \
  [--exported <0|1>] [--billable <0|1>]

# Eintrag loeschen
python3 "$SKILL_DIR/kimai" delete-timesheet <id>

# Letzte Eintraege (expandiert, mit User/Projekt-Details)
python3 "$SKILL_DIR/kimai" recent-timesheets [--user <id>] [--begin <iso>] [--size <n>]

# Aktive Timer
python3 "$SKILL_DIR/kimai" active-timesheets

# Timer stoppen
python3 "$SKILL_DIR/kimai" stop-timesheet <id>

# Timer neustarten (erstellt neuen Eintrag basierend auf bestehendem)
python3 "$SKILL_DIR/kimai" restart-timesheet <id>

# Eintrag duplizieren
python3 "$SKILL_DIR/kimai" duplicate-timesheet <id>

# Eintrag als exportiert markieren
python3 "$SKILL_DIR/kimai" export-timesheet <id>
```

### Projekte

```bash
python3 "$SKILL_DIR/kimai" list-projects
python3 "$SKILL_DIR/kimai" get-project <id>
python3 "$SKILL_DIR/kimai" create-project --name "<name>" --customer <id> \
  [--comment "<text>"] [--color "<hex>"] [--visible <0|1>] [--billable <0|1>]
python3 "$SKILL_DIR/kimai" update-project <id> \
  [--name "<name>"] [--customer <id>] [--comment "<text>"] \
  [--color "<hex>"] [--visible <0|1>] [--billable <0|1>]
python3 "$SKILL_DIR/kimai" delete-project <id>
```

### Aktivitaeten

```bash
python3 "$SKILL_DIR/kimai" list-activities [--project <id>]
python3 "$SKILL_DIR/kimai" get-activity <id>
python3 "$SKILL_DIR/kimai" create-activity --name "<name>" \
  [--project <id>] [--comment "<text>"] [--color "<hex>"] \
  [--visible <0|1>] [--billable <0|1>]
python3 "$SKILL_DIR/kimai" update-activity <id> \
  [--name "<name>"] [--project <id>] [--comment "<text>"] \
  [--color "<hex>"] [--visible <0|1>] [--billable <0|1>]
python3 "$SKILL_DIR/kimai" delete-activity <id>
```

### Kunden

```bash
python3 "$SKILL_DIR/kimai" list-customers
python3 "$SKILL_DIR/kimai" get-customer <id>
python3 "$SKILL_DIR/kimai" create-customer --name "<name>" \
  [--country AT] [--currency EUR] [--timezone Europe/Vienna] \
  [--company "<firma>"] [--comment "<text>"] [--color "<hex>"] \
  [--visible <0|1>] [--billable <0|1>]
python3 "$SKILL_DIR/kimai" update-customer <id> \
  [--name "<name>"] [--country <cc>] [--currency <cur>] \
  [--timezone <tz>] [--company "<firma>"] [--comment "<text>"] \
  [--color "<hex>"] [--visible <0|1>] [--billable <0|1>]
python3 "$SKILL_DIR/kimai" delete-customer <id>
```

### Benutzer

```bash
python3 "$SKILL_DIR/kimai" list-users
python3 "$SKILL_DIR/kimai" get-user <id>
```

### Tags

```bash
python3 "$SKILL_DIR/kimai" list-tags
python3 "$SKILL_DIR/kimai" create-tag --name "<name>"
python3 "$SKILL_DIR/kimai" delete-tag <id>
```

### Teams

```bash
python3 "$SKILL_DIR/kimai" list-teams
python3 "$SKILL_DIR/kimai" get-team <id>
python3 "$SKILL_DIR/kimai" create-team --name "<name>" --members "<uid1,uid2,...>" [--color "<hex>"]
python3 "$SKILL_DIR/kimai" update-team <id> [--name "<name>"] [--members "<uid1,uid2,...>"] [--color "<hex>"]
python3 "$SKILL_DIR/kimai" delete-team <id>
```

Der erste User in `--members` wird automatisch Teamlead.

### Externe Stunden importieren (khpongratz)

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
  "eintraege": [
    {"projekt": "myglobex", "stunden": 21, "beschreibung": "..."},
    {"projekt": "myacme",  "stunden": 8,  "beschreibung": "..."},
    {"projekt": "beide",     "stunden": 20, "beschreibung": "..."}
  ]
}
```

Schluessel `projekt`: `myglobex` | `myacme` | `beide` (50:50-Split).
Stundensatz-Konversion: `ceil(actual * 55 / 77)` pro Eintrag, max 7h/Tag.

## Workflow

1. Parameter aus der Nutzeranfrage ableiten (Projekt, Aktivitaet, Zeitraum, User).
2. Wenn nicht eindeutig: nachfragen.
3. Befehl zusammenbauen und ausfuehren.
4. Ergebnis dem User lesbar darstellen.

## Hinweise

- Config (`KIMAI_HOST` und `KIMAI_TOKEN`) wird aus `.env` im aktuellen Arbeitsverzeichnis gelesen (oder via `KIMAI_ENV` Environment-Variable).
- Temporaere Dateien gehoeren ins Projekt-Verzeichnis `.tmp/`, **nicht** in `$SKILL_DIR/.tmp/`.
- Output ist JSON — relevante Felder extrahieren und lesbar darstellen.
- Alle IDs (Projekt, Aktivitaet, User, Kunde) sind numerisch.
- `create-timesheet` ohne `--end` startet einen laufenden Timer. `stop-timesheet` beendet ihn.
- Boolean-Felder (`--visible`, `--billable`, `--exported`) erwarten `0` oder `1`.
