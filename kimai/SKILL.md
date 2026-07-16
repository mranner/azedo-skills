---
name: kimai
description: >
  Kimai Zeiterfassung: Timesheets, Projekte, Kunden, Aktivitaeten, Tags und
  Teams verwalten. Nutze diesen Skill wenn der User Zeiten erfassen, Stunden
  auswerten, Projekte oder Kunden anlegen/aendern will.
  Auch aktiv verwenden wenn der User sagt "trag die Stunden ein",
  "wie viele Stunden diese Woche", "Zeitauswertung", o.ae.
  Trigger: /kimai.
---

# kimai -- Kimai Zeiterfassung

Zeiterfassung, Projekte, Kunden, Aktivitaeten, Tags und Teams werden ueber das gebundelte Script `kimai` (Python >=3.11, im Skill-Verzeichnis) verwaltet.

**Aufruf:** `python3 "$SKILL_DIR/kimai" <subcommand> [options]`

`$SKILL_DIR` ist das Base Directory dieses Skills (dort wo diese SKILL.md liegt).

## Setup

Beim ersten Einsatz `setup` ausfuehren:

```bash
python3 "$SKILL_DIR/kimai" setup
```

Das schreibt `instance.json` ins Skill-Verzeichnis mit allen Projekten, Aktivitaeten, Kunden und Usern.

Falls `instance.json` nicht existiert, zuerst `setup` ausfuehren.

**ID-Lookup:** Zuerst `.claude/kimai-shortcuts.json` im Arbeitsverzeichnis pruefen (kompakte Zuordnung haeufiger Projekt/Aktivitaets-Kombinationen). Nur bei unbekannten Projekten auf `$SKILL_DIR/instance.json` zurueckfallen.

**Aufbau von `.claude/kimai-shortcuts.json`:**

Flaches JSON — ein Key pro Zeile, Wert ist `[project_id, activity_id, "Label"]`:

```json
{
"acme": [1, 2, "acme Support (0640) / IT-Support"],
"cris-entwicklung": [55, 62, "CRIS Entwicklung (BBT) / Entwicklung"]
}
```

- Key: Kurzname (lowercase, Bindestrich-getrennt) — wird case-insensitive und per Teilmatch gegen die Nutzeranfrage geprueft
- Wert: Array `[project_id, activity_id, "Label"]`
- Label dient auch als Match-Ziel
- **Lookup per grep:** `grep -i <suchbegriff> .claude/kimai-shortcuts.json` liefert die passende Zeile direkt — die Datei muss nicht komplett gelesen werden
- Neue Kombinationen werden im Workflow automatisch ergaenzt (Schritt 7)

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

### Log (One-Shot-Buchung)

```bash
# Mit Shortcut (aus .claude/kimai-shortcuts.json)
python3 "$SKILL_DIR/kimai" log --duration 0.5 --shortcut initech \
  [--description "..."]

# Mit expliziten IDs
python3 "$SKILL_DIR/kimai" log --duration 1h30m --project 84 --activity 196 \
  [--description "..."]

# Startzeit explizit vorgeben (uebersteuert den Auto-Anker)
python3 "$SKILL_DIR/kimai" log --duration 0.5 --shortcut initech \
  --begin 2026-07-16T14:00:00 [--description "..."]
```

Erledigt in einem Call: Shortcut aufloesen, Anker bestimmen, `end` berechnen, Eintrag anlegen.

**Anker (`begin`):** Der Befehl holt **alle heutigen Eintraege** und setzt `begin` auf
das **spaeteste `end`** des Tages (`max(end)`); ohne heutige Eintraege auf 08:00. Bewusst
**nicht** `timesheets/recent[0]` — diese Liste ist nach Bearbeitungs-Aktualitaet sortiert,
nicht chronologisch, und lieferte daher keinen verlaesslichen Anker (neue Eintraege
wanderten in belegte Slots, v.a. bei parallelen Sessions).

**Overlap-Guard:** Kollidiert der berechnete Slot `[begin, end)` mit einem bestehenden
heutigen Eintrag, bricht der Befehl mit klarer Meldung ab, statt still zu buchen (deckt
auch den Race zwischen parallelen Sessions ab).

**`--begin`:** Uebersteuert den Auto-Anker mit einer expliziten ISO-Startzeit; der
Overlap-Guard greift weiterhin.

**Duration-Formate:** Dezimalstunden (`0.5`, `1.5`), Minuten (`30m`, `90m`), gemischt (`1h30m`, `2h`).

### Projekte

```bash
python3 "$SKILL_DIR/kimai" list-projects
python3 "$SKILL_DIR/kimai" get-project <id>
python3 "$SKILL_DIR/kimai" create-project --name "<name>" --customer <id> \
  [--comment "<text>"] [--color "<hex>"] [--visible <0|1>] [--billable <0|1>] \
  [--global-activities <0|1>]
python3 "$SKILL_DIR/kimai" update-project <id> \
  [--name "<name>"] [--customer <id>] [--comment "<text>"] \
  [--color "<hex>"] [--visible <0|1>] [--billable <0|1>] [--global-activities <0|1>]
python3 "$SKILL_DIR/kimai" delete-project <id>
```

`--global-activities` steuert, ob die instanzweiten (globalen) Aktivitaeten
— z.B. *IT-Support (SP90)* — im Projekt buchbar sind. Bei `create-project` ist
der **Default `1`**; ohne globale Aktivitaeten schlaegt `create-timesheet` mit
einer globalen Aktivitaet sonst mit `400 activity … invalid choice` fehl.

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

0. **Format pruefen (einmalig):** Beim ersten grep auf `.claude/kimai-shortcuts.json` die Ausgabe pruefen. Enthaelt sie `"project":` statt eines Arrays → altes Format. **Sofort migrieren** bevor weitergearbeitet wird: Datei lesen, jeden Eintrag von `"key": {"project": P, "activity": A, "label": "L"}` nach `"key": [P, A, "L"]` konvertieren, eine Zeile pro Key, ohne Einrueckung. Erst danach weiter mit Schritt 1.

**Einfache Buchungen** (Dauer + Projekt bekannt) → `log` verwenden. Der Subcommand erledigt Shortcut-Aufloesung, Zeitberechnung und Anlage in einem Call:

```bash
python3 "$SKILL_DIR/kimai" log --duration 0.5 --shortcut initech --description "..."
```

**Komplexere Faelle** (kein Shortcut, spezielle Zeitangaben, Updates, Abfragen) → manueller Workflow:

1. **Shortcuts pruefen:** `grep -i <suchbegriff> .claude/kimai-shortcuts.json` ausfuehren. Jede Zeile hat das Format `"key": [project_id, activity_id, "Label"]`. Grep liefert direkt die passende(n) Zeile(n) — die Datei muss nicht komplett gelesen werden. Bei Treffer: Projekt- und Aktivitaets-ID aus dem Array verwenden, `instance.json` muss nicht gelesen werden.
2. **Fallback auf instance.json:** Nur wenn kein Shortcut passt, `instance.json` lesen und dort matchen.
3. Parameter aus der Nutzeranfrage ableiten (Projekt, Aktivitaet, Zeitraum, User).
4. Wenn nicht eindeutig: nachfragen.
5. Befehl zusammenbauen und ausfuehren.
6. Ergebnis dem User lesbar darstellen.
7. **Shortcut ergaenzen:** Wenn eine neue Projekt/Aktivitaets-Kombination verwendet wurde, die noch nicht in `.claude/kimai-shortcuts.json` steht, per sed einfuegen — **nicht** die Datei lesen und als JSON zurueckschreiben:
   ```bash
   sed -i~ '$i\
   ,"key": [project_id, activity_id, "Label"]' .claude/kimai-shortcuts.json
   ```
   Fuegt eine Zeile mit fuehrendem Komma vor der schliessenden `}` ein. Key ist lowercase, Bindestrich-getrennt.

## Hinweise

- **Neue Eintraege zeitlich anschliessen:** `log` erledigt das automatisch — Anker ist das spaeteste `end` aller heutigen Eintraege (`max(end)`, sonst 08:00), mit Overlap-Guard (siehe Log-Abschnitt). Bei **manuellen** `create-timesheet`-Buchungen dieselbe Regel anwenden: heutige Eintraege abfragen (`list-timesheets --begin <heute>T00:00:00 --end <heute>T23:59:59`) und `--begin` auf das **spaeteste** `end` setzen — **nicht** auf `recent-timesheets[0]` (nach Bearbeitungs-, nicht Uhrzeit-Reihenfolge sortiert).
- **CR-Kontext beachten:** Wenn ein CR-Kontext aktiv ist (gesetzt via `/kanboard cr <id>`), die Beschreibung (`--description`) immer mit `CR{id}: ` prefixen. Bei mehreren aktiven CRs nachfragen. Details siehe Kanboard SKILL.md, Abschnitt "CR-Kontext".
- Config (`KIMAI_HOST` und `KIMAI_TOKEN`) wird aus `.env` im aktuellen Arbeitsverzeichnis gelesen (oder via `KIMAI_ENV` Environment-Variable).
- Temporaere Dateien gehoeren ins Projekt-Verzeichnis `.tmp/`, **nicht** in `$SKILL_DIR/.tmp/`.
- Output ist JSON — relevante Felder extrahieren und lesbar darstellen.
- Alle IDs (Projekt, Aktivitaet, User, Kunde) sind numerisch.
- `create-timesheet` ohne `--end` startet einen laufenden Timer. `stop-timesheet` beendet ihn.
- Boolean-Felder (`--visible`, `--billable`, `--exported`, `--global-activities`) erwarten `0` oder `1`.
