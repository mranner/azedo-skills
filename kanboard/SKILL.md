---
name: kanboard
description: >
  Verwaltet Tasks auf einer Kanboard-Instanz via JSON-RPC API. Nutze diesen
  Skill wenn der User Tasks erstellen, anzeigen, verschieben, zuweisen,
  schliessen, kommentieren oder Dateien anhaengen will.
  Auch aktiv verwenden wenn der User sagt "leg mir ein Ticket an",
  "mach ein Task draus", "ins Kanboard eintragen", o.ae.
  Trigger: /kanboard.
---

# kanboard -- Kanboard Task-Verwaltung

Tasks werden ueber das gebundelte Script `kanboard` (Python ≥3.11, im Skill-Verzeichnis) verwaltet.

**Aufruf:** `python3 "$SKILL_DIR/kanboard" <subcommand> [options]`

Auf FreeBSD ggf. `python3.11` statt `python3` verwenden, falls `python3` nicht im PATH ist.

`$SKILL_DIR` ist das Base Directory dieses Skills (dort wo diese SKILL.md liegt).

## Setup

Beim ersten Einsatz (oder wenn sich Projekte/User aendern) `setup` ausfuehren:

```bash
python3 "$SKILL_DIR/kanboard" setup
```

Das schreibt `instance.json` ins Skill-Verzeichnis mit allen Projekten, Swimlanes, Spalten und Usern. **Vor jeder Task-Operation `$SKILL_DIR/instance.json` lesen**, um Projekt-IDs, Swimlane-Namen und Spalten zu kennen.

Falls `instance.json` nicht existiert, zuerst `setup` ausfuehren.

## Subcommands

### Task erstellen

```bash
python3 "$SKILL_DIR/kanboard" create-task \
  --project <name|id> --title "<titel>" \
  [--description "<text>"] [--column <name>] \
  [--owner <username>] [--swimlane <name>]
```

### Task anzeigen

```bash
python3 "$SKILL_DIR/kanboard" get-task <task_id>
```

### Task aendern

```bash
python3 "$SKILL_DIR/kanboard" update-task <task_id> \
  [--title "<titel>"] [--description "<text>"] [--owner <username>]
```

### Task verschieben (Spalte aendern)

```bash
python3 "$SKILL_DIR/kanboard" move-task <task_id> --column "<spalte>" [--swimlane <name>] [--project <name|id>]
```

### Task oeffnen / schliessen

```bash
python3 "$SKILL_DIR/kanboard" open-task <task_id>
python3 "$SKILL_DIR/kanboard" close-task <task_id>
```

### Datei anhaengen

```bash
python3 "$SKILL_DIR/kanboard" attach-file <task_id> --file /absoluter/pfad/zur/datei
```

### Tasks auflisten

```bash
python3 "$SKILL_DIR/kanboard" list-tasks --project <name|id> [--column <name>] [--closed]
```

### Projekte, Spalten, User auflisten

```bash
python3 "$SKILL_DIR/kanboard" list-projects
python3 "$SKILL_DIR/kanboard" list-columns --project <name|id>
python3 "$SKILL_DIR/kanboard" list-users
```

### Kommentare lesen

```bash
python3 "$SKILL_DIR/kanboard" get-comments <task_id>
```

### Kommentar hinzufuegen

```bash
python3 "$SKILL_DIR/kanboard" add-comment <task_id> --text "<text>" [--user <username>]
```

Default-User fuer Kommentare: `mmuster`

### Kommentar aendern

```bash
python3 "$SKILL_DIR/kanboard" update-comment <comment_id> --text "<neuer text>"
```

### Kommentar loeschen

```bash
python3 "$SKILL_DIR/kanboard" remove-comment <comment_id>
```

### Anhaenge auflisten

```bash
python3 "$SKILL_DIR/kanboard" list-files <task_id>
```

### Anhang herunterladen

```bash
python3 "$SKILL_DIR/kanboard" download-file <file_id> [--output /pfad/zur/datei]
```

Ohne `--output` wird die Datei unter `.tmp/` gespeichert.

### Anhang loeschen

```bash
python3 "$SKILL_DIR/kanboard" remove-file <file_id>
```

`file_id` erhaelt man via `list-files`. Zum Aktualisieren eines Anhangs: erst `remove-file`, dann `attach-file`.

### Teilaufgaben auflisten

```bash
python3 "$SKILL_DIR/kanboard" list-subtasks <task_id>
```

### Teilaufgabe erstellen

```bash
python3 "$SKILL_DIR/kanboard" create-subtask <task_id> --title "<titel>" [--owner <username>]
```

### Teilaufgabe aendern

```bash
python3 "$SKILL_DIR/kanboard" update-subtask <subtask_id> --task-id <task_id> \
  [--title "<titel>"] [--owner <username>] [--status <0|1|2>]
```

Status: 0=Todo, 1=In Progress, 2=Done

### Teilaufgabe loeschen

```bash
python3 "$SKILL_DIR/kanboard" remove-subtask <subtask_id>
```

## Workflow

1. Parameter aus der Nutzeranfrage ableiten (Projekt, Titel, Beschreibung, Zuweisung, Spalte).
2. **Titel kurz halten** -- max. ~60 Zeichen. Details in die Beschreibung. Klare, allgemein verstaendliche Abkuerzungen sind erlaubt (z.B. "Netzwerk" statt "Netzwerkproblem", "DB" fuer Datenbank). Keine selbst erfundenen oder unueblichen Abkuerzungen.
3. Wenn nicht eindeutig: nachfragen.
4. Befehl zusammenbauen und ausfuehren.
5. Ergebnis (Task-ID, URL, Status) dem User melden.

## Task-URL

Nach Anlage oder Aenderung dem User die URL anzeigen. Die Basis-URL ergibt sich aus `KANBOARD_URL` (ohne `/jsonrpc.php`):

`<KANBOARD_BASE>/?controller=TaskViewController&action=show&task_id=<ID>&project_id=<PID>`

## Hinweise

- Config (`KANBOARD_URL` und `KANBOARD_TOKEN`) wird aus `.env` im aktuellen Arbeitsverzeichnis gelesen (oder via `KANBOARD_ENV` Environment-Variable).
- Dateipfade fuer `attach-file` muessen absolut sein.
- Temporaere Dateien (Downloads, Optimierungen etc.) gehoeren ins Projekt-Verzeichnis `.tmp/`, **nicht** in `$SKILL_DIR/.tmp/`. Das Skill-Verzeichnis darf nicht als Arbeitsverzeichnis verwendet werden.
- Spaltennamen sind case-insensitiv im Script.
- Output ist JSON -- relevante Felder extrahieren und lesbar darstellen.
- Beschreibungen unterstuetzen Markdown-Syntax.
- Neue und verschobene Tasks werden am Ende (unten) der Spalte eingefuegt.
