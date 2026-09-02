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

## Zeitregeln

Diese drei Regeln gelten fuer **jede** Buchung, egal ueber welchen Subcommand.
Sie stehen bewusst vor der Befehlsreferenz: wer sie erst dort suchen muesste,
bucht Rohzeiten, ohne es zu merken.

**Anker (`begin`):** Eine neue Buchung schliesst zeitlich an die vorige an. Anker ist das
**spaeteste `end` aller heutigen Eintraege** (`max(end)`); gibt es heute noch keinen
Eintrag, ist es **08:00**. Bewusst **nicht** `timesheets/recent[0]` — diese Liste ist nach
Bearbeitungs-Aktualitaet sortiert, nicht chronologisch, und lieferte daher keinen
verlaesslichen Anker (neue Eintraege wanderten in belegte Slots, v.a. bei parallelen
Sessions).

`log` bestimmt den Anker selbst. Bei `create-timesheet` ist er Sache des Aufrufers:
heutige Eintraege abfragen (`list-timesheets --begin <heute>T00:00:00 --end
<heute>T23:59:59`) und `--begin` auf das spaeteste `end` setzen — **nie** die aktuelle
Uhrzeit minus Dauer.

**Viertelstunden-Raster:** `begin` wird auf die naechste Viertelstunde aufgerundet
(`:00`, `:15`, `:30`, `:45`) — auch ein explizit gesetztes `--begin`. Noetig ist das, weil
der Anker der naechsten Buchung das Ende dieser hier ist: liegt **ein** Eintrag schief
(z.B. Ende 15:48), erbt der ganze restliche Tag den Versatz.

Das erzwingen `log` und `create-timesheet` **selbst** — die Regel haengt nicht daran, ob
sie hier gelesen wurde. `create-timesheet` verschiebt ein gesetztes `--end` um dieselbe
Differenz, die Dauer bleibt also erhalten. Jede Verschiebung wird auf stderr gemeldet,
still passiert sie nie. `create-timesheet --no-snap` bucht die Rohzeiten, wenn eine krumme
Zeit ausnahmsweise die richtige ist.

**Overlap-Guard (nur im Automatikfall):** Kollidiert der von `log` automatisch berechnete
Slot `[begin, end)` mit einem bestehenden heutigen Eintrag, bricht der Befehl mit klarer
Meldung ab, statt still zu buchen — das deckt auch den Race zwischen parallelen Sessions
ab. **Mit** explizitem `--begin` ist eine Ueberlappung erlaubt und wird gebucht: wer die
Startzeit selbst setzt, platziert den Eintrag bewusst, und parallel laufende Arbeit am
selben Tag ist ein realer Fall.

## Log (One-Shot-Buchung) — der Standardweg

Erledigt in einem Call: Shortcut aufloesen, Anker bestimmen, `end` berechnen, Eintrag
anlegen. Solange Dauer und Projekt bekannt sind, ist das der richtige Befehl — er haelt
die Zeitregeln von sich aus ein.

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

**`--begin`:** Uebersteuert den Auto-Anker mit einer expliziten ISO-Startzeit. Damit
entfaellt der Overlap-Guard; das Viertelstunden-Raster gilt weiterhin.

**Duration-Formate:** Dezimalstunden (`0.5`, `1.5`), Minuten (`30m`, `90m`), gemischt (`1h30m`, `2h`).

## Subcommands

Das Script deckt Timesheets, Stammdaten und den Stunden-Import ab. Die vollstaendige
Befehlsreferenz liegt daneben und wird bei Bedarf gelesen:

| Datei | Inhalt |
|---|---|
| `references/timesheets.md` | Eintraege auflisten, anzeigen, anlegen, aendern, loeschen; Timer starten, stoppen, neustarten, duplizieren; als exportiert markieren |
| `references/stammdaten.md` | Projekte, Aktivitaeten, Kunden, Benutzer, Tags, Teams |
| `references/import-hours.md` | Externe Stunden aus JSON auf Werktage verteilen (`import-hours`) |

`python3 "$SKILL_DIR/kimai" <subcommand> --help` listet die Optionen eines Subcommands
direkt aus dem Script — schneller als Nachschlagen, und nie veraltet.

**Diagnose:**

```bash
python3 "$SKILL_DIR/kimai" version
python3 "$SKILL_DIR/kimai" ping
```

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

- **Zeitregeln:** Anker, Viertelstunden-Raster und Overlap-Guard stehen oben im Abschnitt
  [Zeitregeln](#zeitregeln) — dort vollstaendig und nur dort, damit die Fassungen nicht
  auseinanderlaufen.
- **CR-Kontext beachten:** Wenn ein CR-Kontext aktiv ist (gesetzt via `/kanboard cr <id>`), die Beschreibung (`--description`) immer mit `CR{id}: ` prefixen. Bei mehreren aktiven CRs nachfragen. Details siehe Kanboard SKILL.md, Abschnitt "CR-Kontext".
- **Shortcut am Task hinterlegen (Write-back):** Wurde unter aktivem CR mit einem `--shortcut` gebucht, den Shortcut am Kanboard-Task als Tag `kimai:<shortcut>` ablegen — automatische Regel, keine Rueckfrage. Dazu den **kanboard-Skill** aufrufen: `set-kimai <task_id> --shortcut <shortcut>` (`<task_id>` = die CR-ID). Dann steht der Shortcut beim naechsten `/kanboard cr <id>` im Feld `kimai` bereit. Nur bei aktivem CR **und** verwendetem Shortcut; passt der `kimai:`-Tag schon oder wurde ohne CR/Shortcut gebucht, entfaellt es. Details siehe Kanboard SKILL.md, Abschnitt "Kimai-Prefixing".
- **Config-Quelle** (`KIMAI_HOST`, `KIMAI_TOKEN`) — in dieser Reihenfolge: `KIMAI_ENV`
  (Environment-Variable, voller Pfad), sonst `.env` im **aktuellen Arbeitsverzeichnis**
  — aber nur, wenn dort auch tatsaechlich `KIMAI_*`-Schluessel stehen —, sonst `~/.env`.
  Der Home-Fallback ist gewollt: eine Konfiguration reicht fuer alle Projekte. Ein
  projektlokales `.env` ohne Kimai-Schluessel wird uebersprungen statt zum Abbruch zu
  fuehren; der kanboard-Skill ist an dieser Stelle strenger (siehe dortige SKILL.md).
- Temporaere Dateien gehoeren ins Projekt-Verzeichnis `.tmp/`, **nicht** in `$SKILL_DIR/.tmp/`.
- Output ist JSON — relevante Felder extrahieren und lesbar darstellen.
- Alle IDs (Projekt, Aktivitaet, User, Kunde) sind numerisch.
- `create-timesheet` ohne `--end` startet einen laufenden Timer. `stop-timesheet` beendet ihn.
- Boolean-Felder (`--visible`, `--billable`, `--exported`, `--global-activities`) erwarten `0` oder `1`.
