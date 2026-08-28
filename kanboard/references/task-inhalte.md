# Task-Inhalte - Subcommands

Kommentare, Anhänge, Teilaufgaben, Verknüpfungen, Tags und das Handoff-Feld.
Aufruf durchgehend `python3 "$SKILL_DIR/kanboard" <subcommand>`.

### Datei anhaengen

```bash
python3 "$SKILL_DIR/kanboard" attach-file <task_id> --file /absoluter/pfad/zur/datei
```

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

### Tags (Schlagworte)

Tags sind farbige Schlagworte am Task (in der Kanboard-Oberflaeche sichtbar,
projektuebergreifend durchsuchbar). `setTaskTags` legt unbekannte Tags automatisch
am Projekt an — ein separater Anlage-Schritt entfaellt.

```bash
# Tags eines Tasks anzeigen (Liste der Namen)
python3 "$SKILL_DIR/kanboard" get-tags <task_id>

# ALLE Tags ersetzen (Komma-separiert; leerer Wert entfernt alle)
python3 "$SKILL_DIR/kanboard" set-tags <task_id> --tags "Doku,dringend"

# einen Tag ergaenzen, ohne bestehende zu ueberschreiben
python3 "$SKILL_DIR/kanboard" add-tag <task_id> --tag "dringend"

# einen Tag entfernen
python3 "$SKILL_DIR/kanboard" remove-tag <task_id> --tag "dringend"
```

**Achtung:** `set-tags` ersetzt den **gesamten** Tag-Satz. Zum Ergaenzen `add-tag`
verwenden (liest bestehende Tags und schreibt sie mit zurueck).

#### Kimai-Verknuepfung: `kimai:<shortcut>`-Tag

Ein Tag der Form `kimai:<shortcut>` verknuepft den Task mit einem Kimai-Shortcut
(Key aus `.claude/kimai-shortcuts.json`). `cr` hebt ihn als eigenes Feld `kimai`
heraus — damit steht der Zeiterfassungs-Kontext direkt im CR-Kontext, und spaetere
Buchungen koennen den richtigen Shortcut automatisch waehlen.

```bash
# Kimai-Shortcut am Task hinterlegen (ersetzt einen bereits vorhandenen kimai:*-Tag)
python3 "$SKILL_DIR/kanboard" set-kimai <task_id> --shortcut acme-it-support
```

Genau **ein** Kimai-Shortcut pro Task: `set-kimai` entfernt einen evtl. schon
vorhandenen `kimai:*`-Tag, bevor der neue gesetzt wird. Wann der Tag gesetzt wird,
regelt der Abschnitt [Kimai-Prefixing](#kimai-prefixing).

#### Jira-Verknuepfung: `jira:<KEY>`-Tag

Ein Tag der Form `jira:<KEY>` verknuepft den Task mit einem **Jira-Issue** (z.B.
`jira:OPS-69`, `jira:PROJ-1762`). `cr` hebt ihn als eigenes Feld `jira` heraus —
damit steht der Jira-Bezug direkt im CR-Kontext und der `jira`-Skill kann auf dem
Issue arbeiten (`issue`/`comment`/`transition`/`attach` …), ohne dass der Key erneut
genannt werden muss. Analog zu `kimai:` und ohne Kollision mit dem CR-Commit-Prefix.

```bash
# Jira-Issue am Task hinterlegen (ersetzt einen bereits vorhandenen jira:*-Tag)
python3 "$SKILL_DIR/kanboard" set-jira <task_id> --key OPS-69
```

Genau **ein** Jira-Key pro Task: `set-jira` entfernt einen evtl. schon vorhandenen
`jira:*`-Tag, bevor der neue gesetzt wird (Key wird auf Grossschreibung normiert).
