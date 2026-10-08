---
name: kimai
description: >
  Kimai Zeiterfassung: Timesheets, Projekte, Kunden, Aktivitäten, Tags und
  Teams verwalten. Nutze diesen Skill wenn der User Zeiten erfassen, Stunden
  auswerten, Projekte oder Kunden anlegen/ändern will.
  Auch aktiv verwenden wenn der User sagt "trag die Stunden ein",
  "wie viele Stunden diese Woche", "Zeitauswertung", o.ä.
  Trigger: /kimai.
---

# kimai -- Kimai Zeiterfassung

Zeiterfassung, Projekte, Kunden, Aktivitäten, Tags und Teams werden über das gebündelte Script `kimai` (Python >=3.11, im Skill-Verzeichnis) verwaltet.

**Aufruf:** `python3 "$SKILL_DIR/kimai" <subcommand> [options]`

`$SKILL_DIR` ist das Base Directory dieses Skills (dort wo diese SKILL.md liegt).

## Setup

Beim ersten Einsatz `setup` ausführen:

```bash
python3 "$SKILL_DIR/kimai" setup
```

Das schreibt `instance.json` ins Skill-Verzeichnis mit allen Projekten, Aktivitäten, Kunden und Usern.

Falls `instance.json` nicht existiert, zuerst `setup` ausführen.

**ID-Lookup:** Zuerst `.claude/kimai-shortcuts.json` im Arbeitsverzeichnis prüfen (kompakte Zuordnung häufiger Projekt/Aktivitäts-Kombinationen). Nur bei unbekannten Projekten auf `$SKILL_DIR/instance.json` zurückfallen.

**Aufbau von `.claude/kimai-shortcuts.json`:**

Flaches JSON — ein Key pro Zeile, Wert ist `[project_id, activity_id, "Label"]`:

```json
{
"acme": [1, 2, "acme Support (0640) / IT-Support"],
"cris-entwicklung": [55, 62, "CRIS Entwicklung (BBT) / Entwicklung"]
}
```

- Key: Kurzname (lowercase, Bindestrich-getrennt) — wird case-insensitive und per Teilmatch gegen die Nutzeranfrage geprüft
- Wert: Array `[project_id, activity_id, "Label"]`
- Label dient auch als Match-Ziel
- **Lookup per grep:** `grep -i <suchbegriff> .claude/kimai-shortcuts.json` liefert die passende Zeile direkt — die Datei muss nicht komplett gelesen werden
- Neue Kombinationen werden im Workflow automatisch ergänzt (Schritt 7)

**Altes Format:** Liefert der grep `"project":` statt eines Arrays, zuerst migrieren:
jeden Eintrag von `"key": {"project": P, "activity": A, "label": "L"}` nach
`"key": [P, A, "L"]` umschreiben, eine Zeile pro Key, ohne Einrückung.

## Zeitregeln

Diese drei Regeln gelten für **jede** Buchung, egal über welchen Subcommand.
Sie stehen bewusst vor der Befehlsreferenz: wer sie erst dort suchen müsste,
bucht Rohzeiten, ohne es zu merken.

**Anker (`begin`):** Eine neue Buchung schließt zeitlich an die vorige an. Anker ist das
**späteste `end` aller heutigen Einträge** (`max(end)`); gibt es heute noch keinen
Eintrag, ist es **08:00**. Bewusst **nicht** `timesheets/recent[0]` — diese Liste ist nach
Bearbeitungs-Aktualität sortiert, nicht chronologisch, und taugt daher nicht als
Anker (neue Einträge landen sonst in belegten Slots, v.a. bei parallelen Sessions).

`log` bestimmt den Anker selbst. Bei `create-timesheet` ist er Sache des Aufrufers:
heutige Einträge abfragen (`list-timesheets --begin <heute>T00:00:00 --end
<heute>T23:59:59`) und `--begin` auf das späteste `end` setzen — **nie** die aktuelle
Uhrzeit minus Dauer.

**Viertelstunden-Raster:** `begin` wird auf die nächste Viertelstunde aufgerundet
(`:00`, `:15`, `:30`, `:45`) — auch ein explizit gesetztes `--begin`. Nötig ist das, weil
der Anker der nächsten Buchung das Ende dieser hier ist: liegt **ein** Eintrag schief
(z.B. Ende 15:48), erbt der ganze restliche Tag den Versatz.

Das erzwingen `log` und `create-timesheet` **selbst** — die Regel hängt nicht daran, ob
sie hier gelesen wurde. `create-timesheet` verschiebt ein gesetztes `--end` um dieselbe
Differenz, die Dauer bleibt also erhalten. Jede Verschiebung wird auf stderr gemeldet,
still passiert sie nie. `create-timesheet --no-snap` bucht die Rohzeiten, wenn eine krumme
Zeit ausnahmsweise die richtige ist.

**Overlap-Guard (nur im Automatikfall):** Kollidiert der von `log` automatisch berechnete
Slot `[begin, end)` mit einem bestehenden heutigen Eintrag, bricht der Befehl mit klarer
Meldung ab, statt still zu buchen — das deckt auch den Race zwischen parallelen Sessions
ab. **Mit** explizitem `--begin` ist eine Überlappung erlaubt und wird gebucht: wer die
Startzeit selbst setzt, platziert den Eintrag bewusst, und parallel laufende Arbeit am
selben Tag ist ein realer Fall.

## Log (One-Shot-Buchung) — der Standardweg

Erledigt in einem Call: Shortcut auflösen, Anker bestimmen, `end` berechnen, Eintrag
anlegen. Solange Dauer und Projekt bekannt sind, ist das der richtige Befehl — er hält
die Zeitregeln von sich aus ein.

```bash
# Mit Shortcut (aus .claude/kimai-shortcuts.json)
python3 "$SKILL_DIR/kimai" log --duration 0.5 --shortcut initech \
  [--description "..."]

# Mit expliziten IDs
python3 "$SKILL_DIR/kimai" log --duration 1h30m --project 84 --activity 196 \
  [--description "..."]

# Startzeit explizit vorgeben (übersteuert den Auto-Anker)
python3 "$SKILL_DIR/kimai" log --duration 0.5 --shortcut initech \
  --begin 2026-07-16T14:00:00 [--description "..."]
```

**`--begin`:** Übersteuert den Auto-Anker mit einer expliziten ISO-Startzeit. Damit
entfällt der Overlap-Guard; das Viertelstunden-Raster gilt weiterhin.

**Duration-Formate:** Dezimalstunden (`0.5`, `1.5`), Minuten (`30m`, `90m`), gemischt (`1h30m`, `2h`).

## Subcommands

Das Script deckt Timesheets, Stammdaten und den Stunden-Import ab. Die vollständige
Befehlsreferenz liegt daneben und wird bei Bedarf gelesen:

| Datei | Inhalt |
|---|---|
| `references/timesheets.md` | Einträge auflisten, anzeigen, anlegen, ändern, löschen; Timer starten, stoppen, neustarten, duplizieren; als exportiert markieren |
| `references/stammdaten.md` | Projekte, Aktivitäten, Kunden, Benutzer, Tags, Teams; Stundensätze (Rates) an Aktivität, Projekt und Kunde |
| `references/import-hours.md` | Externe Stunden aus JSON auf Werktage verteilen (`import-hours`) |

`python3 "$SKILL_DIR/kimai" <subcommand> --help` listet die Optionen eines Subcommands
direkt aus dem Script — schneller als Nachschlagen, und nie veraltet.

**Diagnose:**

```bash
python3 "$SKILL_DIR/kimai" version
python3 "$SKILL_DIR/kimai" ping
```

## Workflow

**Einfache Buchungen** (Dauer + Projekt bekannt) → `log` verwenden, siehe
[Log](#log-one-shot-buchung--der-standardweg).

**Komplexere Fälle** (kein Shortcut, spezielle Zeitangaben, Updates, Abfragen) → manueller Workflow:

1. **Shortcuts prüfen:** `grep -i <suchbegriff> .claude/kimai-shortcuts.json` ausführen. Jede Zeile hat das Format `"key": [project_id, activity_id, "Label"]`. Grep liefert direkt die passende(n) Zeile(n) — die Datei muss nicht komplett gelesen werden. Bei Treffer: Projekt- und Aktivitäts-ID aus dem Array verwenden, `instance.json` muss nicht gelesen werden.
2. **Fallback auf instance.json:** Nur wenn kein Shortcut passt, `instance.json` lesen und dort matchen.
3. Parameter aus der Nutzeranfrage ableiten (Projekt, Aktivität, Zeitraum, User).
4. Wenn nicht eindeutig: nachfragen.
5. Befehl zusammenbauen und ausführen.
6. Ergebnis dem User lesbar darstellen.
7. **Shortcut ergänzen:** Wenn eine neue Projekt/Aktivitäts-Kombination verwendet wurde, die noch nicht in `.claude/kimai-shortcuts.json` steht, per sed einfügen — **nicht** die Datei lesen und als JSON zurückschreiben:
   ```bash
   sed -i~ '$i\
   ,"key": [project_id, activity_id, "Label"]' .claude/kimai-shortcuts.json
   ```
   Fügt eine Zeile mit führendem Komma vor der schließenden `}` ein. Key ist lowercase, Bindestrich-getrennt.

## Hinweise

- **Zeitregeln:** Anker, Viertelstunden-Raster und Overlap-Guard stehen oben im Abschnitt
  [Zeitregeln](#zeitregeln) — dort vollständig und nur dort, damit die Fassungen nicht
  auseinanderlaufen.
- **CR-Kontext beachten:** Wenn ein CR-Kontext aktiv ist (gesetzt via `/kanboard cr <id>`), die Beschreibung (`--description`) immer mit `CR{id}: ` prefixen. Bei mehreren aktiven CRs nachfragen. Details siehe Kanboard SKILL.md, Abschnitt "CR-Kontext".
- **Shortcut am Task hinterlegen (Write-back):** Wurde unter aktivem CR mit einem `--shortcut` gebucht, den Shortcut am Kanboard-Task als Tag `kimai:<shortcut>` ablegen, falls dort noch keiner gesetzt ist — automatische Regel, keine Rückfrage. Dazu den **kanboard-Skill** aufrufen: `set-kimai <task_id> --shortcut <shortcut>` (`<task_id>` = die CR-ID). Dann steht der Shortcut beim nächsten `/kanboard cr <id>` im Feld `kimai` bereit. Nur bei aktivem CR **und** verwendetem Shortcut; ist schon ein `kimai:`-Tag gesetzt oder wurde ohne CR/Shortcut gebucht, entfällt es. Weicht der vorhandene Tag ab, das nur melden, nicht überschreiben. Details siehe Kanboard SKILL.md, Abschnitt "Kimai-Präfix".
- **Config-Quelle** (`KIMAI_HOST`, `KIMAI_TOKEN`) — in dieser Reihenfolge: `KIMAI_ENV`
  (Environment-Variable, voller Pfad), sonst `.env` im **aktuellen Arbeitsverzeichnis**
  — aber nur, wenn dort auch tatsächlich `KIMAI_*`-Schlüssel stehen —, sonst `~/.env`.
  Der Home-Fallback ist gewollt: eine Konfiguration reicht für alle Projekte. Ein
  projektlokales `.env` ohne Kimai-Schlüssel wird übersprungen statt zum Abbruch zu
  führen; der kanboard-Skill ist an dieser Stelle strenger (siehe dortige SKILL.md).
- Temporäre Dateien gehören ins Projekt-Verzeichnis `.tmp/`, **nicht** in `$SKILL_DIR/.tmp/`. Fehlt `.tmp/`, mit `mkdir -m 700 .tmp` anlegen - liegt das Projekt in einem Docroot, liefert der Webserver es sonst aus.
- Output ist JSON — relevante Felder extrahieren und lesbar darstellen.
- Alle IDs (Projekt, Aktivität, User, Kunde) sind numerisch.
- `create-timesheet` ohne `--end` startet einen laufenden Timer. `stop-timesheet` beendet ihn.
- Boolean-Felder (`--visible`, `--billable`, `--exported`, `--global-activities`) erwarten `0` oder `1`.
