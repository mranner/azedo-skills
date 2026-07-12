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

`$SKILL_DIR` ist das Base Directory dieses Skills (dort wo diese SKILL.md liegt).

## Setup

Beim ersten Einsatz (oder wenn sich Projekte/User aendern) `setup` ausfuehren:

```bash
python3 "$SKILL_DIR/kanboard" setup --default-user <username>
```

Das schreibt `instance.json` ins Skill-Verzeichnis mit allen Projekten, Swimlanes, Spalten und Usern. `--default-user` legt fest, welcher Kanboard-User als Absender fuer Kommentare verwendet wird (wenn kein `--user` angegeben).

Falls `instance.json` nicht existiert, zuerst `setup` ausfuehren.

### instance.json — Schema und Zugriff

**`instance.json` NICHT selbst roh parsen** — dafuer gibt es die Subcommands
`list-projects`, `list-columns --project <name|id>` und `list-users` (liefern IDs
**und** Namen). `get-task` reichert seit v1.18.3 zusaetzlich `column_title`,
`swimlane_name`, `owner_username`/`owner_name` an, sodass keine Quer-Aufloesung
noetig ist.

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
  "users": [ { "id": 4, "username": "kollege", "name": "Karin Musterfrau" } ]
}
```

Merke: `columns`/`swimlanes` sind **Strings ohne IDs** — die Spalten-ID einer
Position ergibt sich nicht aus `instance.json`, dafuer `list-columns` verwenden.

## Subcommands

### CR-Kontext laden

```bash
python3 "$SKILL_DIR/kanboard" cr <task_ref> [<task_ref2> ...]
```

Laedt einen oder mehrere Tasks als aktiven CR-Kontext. Akzeptiert alle gaengigen Schreibweisen: `4326`, `CR4326`, `cr4326`, `CR 4326`, `#4326`.

Beispiele:

```bash
python3 "$SKILL_DIR/kanboard" cr 4326
python3 "$SKILL_DIR/kanboard" cr CR4326 CR4330
```

**Handoff-Feld wird automatisch mitgeladen:** Ist das Handoff-Feld (TaskHandoff-Plugin,
siehe unten) befuellt, erscheint sein Volltext im Feld `handoff`. Ist es leer — oder
das Plugin gar nicht installiert — entfaellt das Feld und die Ausgabe bleibt schlank.
Datei-**Anhaenge** werden bewusst **nicht** automatisch geladen; die holt man bei
Bedarf gezielt mit `list-files`/`download-file`.

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

### Task in anderes Projekt verschieben

```bash
python3 "$SKILL_DIR/kanboard" move-project <task_id> --project <name|id> [--column <name>] [--swimlane <name>]
```

`move-task` verschiebt nur **innerhalb** eines Projekts (`moveTaskPosition`). Fuer
einen Projektwechsel `move-project` verwenden — nutzt `moveTaskToProject` und setzt
danach optional Spalte/Swimlane im Zielprojekt. Ohne `--column` landet der Task in
der von Kanboard gewaehlten Standardspalte; ohne `--swimlane` in der ersten
aktiven Swimlane des Zielprojekts.

### Task oeffnen / schliessen

```bash
python3 "$SKILL_DIR/kanboard" open-task <task_id>
python3 "$SKILL_DIR/kanboard" close-task <task_id>
```

**Wichtig:** "Task erledigen" bedeutet: `move-task --column erledigt`. Tasks werden im Regelfall nur in der Spalte "erledigt" geschlossen. `close-task` nur ausfuehren, wenn der User es explizit verlangt — andernfalls nachfragen.

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

### Projekt-Verwaltung (Anlegen, Mitglieder, Owner)

Projekte anlegen und die Projekt-Mitgliedschaften/Rollen verwalten. Rollen sind
`project-manager`, `project-member`, `project-viewer` (Kanboard-Standardrollen).

```bash
# Projekt anlegen (--owner optional: wird Owner UND project-manager-Mitglied)
python3 "$SKILL_DIR/kanboard" create-project --name "<name>" [--owner <username>]

# Mitglieder eines Projekts mit Rolle + Owner anzeigen
python3 "$SKILL_DIR/kanboard" list-project-users --project <name|id>

# User zum Projekt hinzufuegen (--role Default: project-member)
python3 "$SKILL_DIR/kanboard" add-project-user --project <name|id> --user <username> [--role <rolle>]

# Rolle eines vorhandenen Mitglieds aendern
python3 "$SKILL_DIR/kanboard" set-project-user-role --project <name|id> --user <username> --role <rolle>

# User aus Projekt entfernen
python3 "$SKILL_DIR/kanboard" remove-project-user --project <name|id> --user <username>

# Owner des Projekts setzen (User wird bei Bedarf zuerst als Mitglied ergaenzt)
python3 "$SKILL_DIR/kanboard" set-project-owner --project <name|id> --user <username>
```

**Hinweise:**

- Nach `create-project` einmal `setup` ausfuehren, damit das neue Projekt in
  `instance.json` bekannt ist (sonst schlaegt `--project <name>` fehl; die
  numerische `--project <id>` funktioniert sofort).
- `--user` wird ueber `instance.json` aufgeloest — ist ein User dort nicht
  gelistet (z.B. neu angelegt), zuerst `setup` ausfuehren.
- „Gleiche Rechte wie in Projekt X" = Rolle mit `list-project-users --project X`
  ablesen und beim Ziel via `add-project-user --role <rolle>` setzen.

### Kommentare lesen

```bash
python3 "$SKILL_DIR/kanboard" get-comments <task_id>
```

### Kommentar hinzufuegen

```bash
python3 "$SKILL_DIR/kanboard" add-comment <task_id> --text "<text>" [--user <username>]
```

Ohne `--user` wird der `default_user` aus `instance.json` verwendet (gesetzt via `setup --default-user`).

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

### Handoff-Feld (TaskHandoff-Plugin)

Auf der Kanboard-Instanz ist das Plugin **TaskHandoff** installiert: es speichert pro Task
ein Handoff-Dokument (Volltext, Markdown) in einer eigenen aufklappbaren „Handoff"-Sektion
auf der Task-Seite (Spalte `content` als `LONGTEXT`, keine Laengengrenze — anders als
Task-Metadata mit `VARCHAR(255)`). Der Handoff ist **nicht** die Beschreibung, **nicht** ein
Kommentar und **nicht** ein Anhang, sondern ein eigenes Feld. Ein Handoff pro Task (erneutes
`set-handoff` ueberschreibt).

```bash
# Handoff setzen (Text aus Datei ODER direkt)
python3 "$SKILL_DIR/kanboard" set-handoff <task_id> --file /pfad/handoff.md
python3 "$SKILL_DIR/kanboard" set-handoff <task_id> --value "# Titel ..."

# Handoff auslesen (roher Markdown-Text auf stdout, oder in Datei)
python3 "$SKILL_DIR/kanboard" get-handoff <task_id>
python3 "$SKILL_DIR/kanboard" get-handoff <task_id> --output /pfad/handoff.md

# Handoff entfernen
python3 "$SKILL_DIR/kanboard" remove-handoff <task_id>
```

Die Ablage im Handoff-Feld ist im handoff-Skill eine bewusst gewaehlte **Alternative** zur
lokalen `.md`-Datei (Default bleibt die Datei) — siehe handoff-Skill.

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

### Task-Verbindungen (interne Links)

Kanboard kann zwei Tasks ueber "interne Verbindungen" verknuepfen (z.B. "relates to", "is a child of", "blocks"). Diese Link-Typen sind instanzweit definiert.

**Verfuegbare Link-Typen auflisten** (immer zuerst, um das richtige Label/ID zu finden):

```bash
python3 "$SKILL_DIR/kanboard" list-links
```

Die `label`-Werte sind die im Kanboard gespeicherten (meist englischen) Bezeichnungen -- die deutsche Oberflaeche uebersetzt sie nur bei der Anzeige. Fuer `--link` das Label aus dieser Liste oder die numerische `id` verwenden.

Zuordnung deutsche UI → gespeichertes Label auf der azedo-Instanz: **"gehört zu" == "relates to"** (link_id 1, symmetrisch). Fuer eine echte Eltern-/Kind-Beziehung stattdessen `is a child of` / `is a parent of` (link_id 6/7).

**Verbindungen eines Tasks anzeigen:**

```bash
python3 "$SKILL_DIR/kanboard" list-task-links <task_id>
```

**Zwei Tasks verknuepfen:**

```bash
python3 "$SKILL_DIR/kanboard" create-task-link <task_id> <opposite_task_id> --link "<label|id>"
```

Richtung beachten: `create-task-link A B --link "is a child of"` bedeutet **"A is a child of B"**. Die Gegenrichtung (opposite link) wird von Kanboard automatisch am anderen Task angelegt. Beispiel:

```bash
python3 "$SKILL_DIR/kanboard" create-task-link 4366 4296 --link "relates to"
```

**Verbindung loeschen:**

```bash
python3 "$SKILL_DIR/kanboard" remove-task-link <task_link_id>
```

Die `task_link_id` (Feld `id`) stammt aus `list-task-links`.

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

## CR-Kontext (Change Request)

Der CR-Kontext verknuepft Kanboard-Tasks mit Commits und Zeiterfassung. Die Schreibweise `CR{id}` (z.B. `CR4326`) bezieht sich immer auf einen Kanboard-Task.

### Erkennung

Wenn der User irgendwo eine CR-Referenz verwendet, wird das als Kanboard-Task interpretiert. Alle Schreibweisen werden erkannt und auf die kanonische Form normalisiert:

- `CR4326`, `cr4326`, `CR 4326`, `cr 4326`, `#4326` → **CR4326**

### Aktivierung

- **Explizit:** Der User fuehrt `cr <id>` aus oder sagt "ich arbeite an CR4326"
- **Mehrere CRs:** `cr 4326 4330` aktiviert beide Tasks als Kontext
- Der aktive CR-Kontext gilt fuer die gesamte Session, bis der User ihn aendert oder beendet ("CR fertig", "kein CR mehr")

### Commit-Prefixing

Wenn ein CR-Kontext aktiv ist und der User einen Commit macht (`git commit`, `svn commit`):

- Commit-Message immer mit `CR{id}: ` prefixen
- Beispiel: `git commit -m "CR4326: Login-Formular validiert jetzt E-Mail-Adressen"`
- Beispiel: `svn commit -m "CR4326: Timeout auf 30s erhoeht"`

### Kimai-Prefixing

Wenn ein CR-Kontext aktiv ist und der User Zeit erfasst (via `/kimai`):

- Beschreibung (`--description`) immer mit `CR{id}: ` prefixen
- Beispiel: `--description "CR4326: Login-Validierung implementiert"`

### Mehrere aktive CRs

Wenn mehrere CRs aktiv sind, **vor dem Commit oder der Zeiterfassung nachfragen**, welcher CR zutrifft. Nicht raten.

### Ohne aktiven CR-Kontext

Wenn kein CR aktiv ist, Commits und Kimai-Eintraege ganz normal ohne Prefix erstellen.

### Handoff

Wird ein Uebergabedokument erstellt (`/handoff`), gehoert der aktive CR-Kontext ins Dokument. Der handoff-Skill legt dafuer einen eigenen Abschnitt „Aktiver CR-Kontext" an (CR-ID, Titel, Task-URL, aktuelle Spalte/Status), damit der naechste Agent weiss, an welchem Task gearbeitet wird, und ihn mit `/kanboard cr <id>` wiederherstellen kann.
