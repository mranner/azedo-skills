---
name: kanboard
description: >
  Verwaltet eine Kanboard-Instanz via JSON-RPC API: Tasks (erstellen, anzeigen,
  verschieben, zuweisen, schliessen, kommentieren, Subtasks, Tags, Verknuepfungen,
  Handoff-Feld, Dateien) sowie Projekte inkl. Anlage und Mitglieder-/Rollen-Verwaltung.
  Nutze diesen Skill wenn der User Tasks oder Projekte verwalten will.
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
  "users": [ { "id": 4, "username": "musterfrau", "name": "Karin Musterfrau" } ]
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

**Feldauswahl von `cr` (bewusst gewaehlt, nicht zufaellig):** Der CR-Kontext ist die
Arbeitsgrundlage der ganzen Session, deshalb laedt `cr` den *Inhalt* des Tasks mit —
nicht nur die Metadaten.

| Feld | Verhalten |
|---|---|
| `title`, `column`, `owner`, `project_name` | immer |
| `modified` | immer — Aenderungszeitpunkt, lesbar (`YYYY-MM-DD HH:MM`) |
| `description` | **immer, Volltext** — enthaelt i.d.R. die menschlich verfasste Ausgangslage (Zusammenfassung, Mail-Auszug). Ohne sie sieht ein voller Task faelschlich leer aus. |
| `handoff` | nur wenn befuellt (TaskHandoff-Plugin) |
| `tags` | nur wenn vorhanden — Liste der Tag-Namen |
| `kimai` | nur wenn ein Tag `kimai:<shortcut>` gesetzt ist (siehe Tags) |
| `jira` | nur wenn ein Tag `jira:<KEY>` gesetzt ist — verknuepftes Jira-Issue (siehe Tags) |
| `comments`, `attachments` | Zaehler, nur wenn > 0 |

`description` und `handoff` sind **nicht** redundant: Description = *was ist die
Aufgabe* (von Menschen gesetzt), Handoff = *wo stehen wir / wie geht es weiter*
(Uebergabestand fuer die naechste Bearbeitung).

Bewusst **nicht** automatisch geladen — dafuer gibt es eigene Befehle: Kommentar-
Volltext (`get-comments`), Teilaufgaben (`list-subtasks`), Task-Links
(`list-task-links`), Datei-**Anhaenge** (`list-files`/`download-file`). Von
Kommentaren und Anhaengen kommt nur der Zaehler als Signal mit.

### Task erstellen

```bash
python3 "$SKILL_DIR/kanboard" create-task \
  --project <name|id> --title "<titel>" \
  [--description "<text>"] [--column <name>] \
  [--owner <username>] [--swimlane <name>]
```

Ohne `--owner` wird der Task dem `default_user` aus `instance.json` zugewiesen (wie
bei `add-comment`). Ist dort kein `default_user` gesetzt, bleibt der Task unassigned.

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

**Status-Erhaltung:** `moveTaskToProject` oeffnet geschlossene Tasks automatisch
wieder (is_active 0 → 1). `move-project` faengt das ab und schliesst einen zuvor
geschlossenen Task nach dem Move wieder (Feld `reclosed: true` in der Ausgabe) —
der Offen/Geschlossen-Zustand bleibt also erhalten.

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

### Tasks suchen (Stichwort/Query)

```bash
python3 "$SKILL_DIR/kanboard" search "<text>" [--project <name|id>] [--all] [--anywhere | --in <felder>]
```

Findet Tasks per Stichwort — praktisch, wenn die Task-ID unbekannt ist. Ohne
`--project` wird ueber **alle** zugaenglichen Projekte gesucht. Standardmaessig nur
**offene** Tasks; `--all` bezieht geschlossene mit ein. Ausgabe: `id`, `title`,
`project_name`, `column`, `owner`, `is_active` pro Treffer.

#### ⚠️ Ein bloßes Wort trifft nur den Titel

Die groesste Falle: Die Query geht 1:1 an Kanboards `searchTasks`, und ein
**unqualifiziertes** Stichwort matcht **ausschliesslich den Titel**. Steht der
gesuchte String nur in der **Beschreibung** oder in einem **Kommentar**, liefert
`search "printsrv"` faelschlich **nichts** — obwohl der Text existiert. Dann den
passenden Feld-Filter verwenden (oder `--anywhere`, siehe unten).

#### Feld-Filter (nativ von Kanboard, case-insensitiv, Teilstring)

Alle drei Text-Felder sind einzeln durchsuchbar; der Match ist **gross/klein-egal**
und ein Teilstring:

| Query | sucht in |
|---|---|
| `printsrv` (bloß) | **nur Titel** |
| `title:printsrv` | Titel (explizit) |
| `description:printsrv` | Beschreibung |
| `comment:printsrv` | Kommentartext |

Weitere native Operatoren wie in der Web-Oberflaeche: `status:open|closed`,
`assignee:mmuster`, `column:...`, `swimlane:...`, `color:...`, `category:...`,
`tag:...`, Datums-Filter (`created:`, `modified:`, `due:` mit `>=`, `T-2d` …).

**AND/ODER-Semantik:** *verschiedene* Felder in einer Query werden **UND**-verknuepft
(`title:site1 description:Drucker` = beides), **dasselbe** Feld doppelt wird
**ODER**-verknuepft (`description:A description:B` = A oder B). Phrasen mit Leerzeichen
quoten: `description:"neue WLAN"`.

#### `--anywhere` / `--in` — über mehrere Felder gleichzeitig

Kanboard kennt **keinen** Operator, der Titel *oder* Beschreibung *oder* Kommentar in
**einer** Query trifft. Dafuer kapselt der Skill die Mehrfeld-Suche: die `query` wird
als **reiner Begriff** behandelt, in jeden gewaehlten Feld-Filter gewickelt, und die
Treffer werden nach `id` **unioniert**. Jeder Treffer bekommt zusaetzlich
`matched_in` (Liste der Felder, in denen er gefunden wurde).

```bash
# Titel + Beschreibung + Kommentar (der haeufige "finde das irgendwo"-Fall)
python3 "$SKILL_DIR/kanboard" search "print_and_follow" --all --anywhere

# nur eine Teilmenge der Felder
python3 "$SKILL_DIR/kanboard" search "Drucker" --all --in description,comment
```

`--anywhere` ist die Kurzform fuer `--in title,description,comment`. Erlaubte Felder:
`title`, `description`, `comment`. In diesem Modus **keine** Kanboard-Operatoren in die
`query` schreiben (sie wird ja selbst als Suchbegriff gequotet) — Filter wie
`status:`/`assignee:` gehoeren in den klassischen Modus ohne `--anywhere`/`--in`.

**Faustregel:** String-Suche nach etwas, das evtl. nicht im Titel steht → `--anywhere`.
Gezielte Filter-Query (Status, Assignee, ein bestimmtes Feld) → klassischer Modus.

### Eigene Tasks (projektuebergreifend)

```bash
python3 "$SKILL_DIR/kanboard" my-tasks [--user <username>]
```

Listet **offene** Tasks, die einem User zugewiesen sind, ueber alle Projekte hinweg.
Ohne `--user` gilt der `default_user` aus `instance.json`. Schneller Tagesueberblick.
(Hinweis: „offen" heisst `is_active=1` — Tasks, die in der Spalte „Erledigt" liegen,
aber nicht per `close-task` geschlossen wurden, erscheinen weiterhin; die Spalte
steht im Feld `column`.)

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

# Projekt loeschen (bricht ab, solange Tasks drin sind; --force loescht sie mit)
python3 "$SKILL_DIR/kanboard" remove-project --project <name|id> [--force]

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
  numerische `--project <id>` funktioniert sofort). Dasselbe gilt nach
  `remove-project` — sonst zeigt `instance.json` ein Projekt, das es nicht
  mehr gibt.
- `remove-project` ist **nicht umkehrbar** und nimmt alle Tasks des Projekts mit
  (offene wie geschlossene). Der Befehl zaehlt sie deshalb vorher und bricht mit
  `success: false` und Exit-Code 1 ab, solange welche vorhanden sind; erst
  `--force` fuehrt aus. Bei einem leeren Projekt braucht es kein `--force`.
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
`jira:SADM-69`, `jira:CORTAB-1762`). `cr` hebt ihn als eigenes Feld `jira` heraus —
damit steht der Jira-Bezug direkt im CR-Kontext und der `jira`-Skill kann auf dem
Issue arbeiten (`issue`/`comment`/`transition`/`attach` …), ohne dass der Key erneut
genannt werden muss. Analog zu `kimai:` und ohne Kollision mit dem CR-Commit-Prefix.

```bash
# Jira-Issue am Task hinterlegen (ersetzt einen bereits vorhandenen jira:*-Tag)
python3 "$SKILL_DIR/kanboard" set-jira <task_id> --key SADM-69
```

Genau **ein** Jira-Key pro Task: `set-jira` entfernt einen evtl. schon vorhandenen
`jira:*`-Tag, bevor der neue gesetzt wird (Key wird auf Grossschreibung normiert).

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

**Kimai-Shortcut am Task hinterlegen (Write-back):** Nach einer Kimai-Buchung unter
aktivem CR den verwendeten Shortcut am Task als Tag `kimai:<shortcut>` ablegen, falls
noch nicht vorhanden — analog zum Commit-Prefixing eine automatische Regel, keine
Rueckfrage noetig:

```bash
python3 "$SKILL_DIR/kanboard" set-kimai <task_id> --shortcut <shortcut>
```

So steht der Shortcut beim naechsten `cr <id>` im Feld `kimai` und die Zeiterfassung
kann ihn direkt uebernehmen, ohne erneut zu suchen. Steht der `kimai:`-Tag bereits und
passt, entfaellt der Aufruf. (Der Tag traegt den Shortcut-**Key** aus
`.claude/kimai-shortcuts.json`, nicht Projekt-/Aktivitaets-IDs.)

### Jira-Verknuepfung

Anders als `kimai:` prefixt die Jira-Verknuepfung **nichts** — sie merkt sich nur das
zum CR gehoerende Jira-Issue, damit der `jira`-Skill ohne erneute Key-Angabe darauf
arbeiten kann. Es gibt daher **keinen** Jira-Commit-Prefix (der CR bleibt der einzige
Commit-Anker).

**Write-back:** Sobald unter aktivem CR ein Jira-Issue eindeutig zum Task gehoert (der
User nennt es, oder es wird im Zuge der Arbeit angelegt/bearbeitet), den Key am Task als
Tag `jira:<KEY>` ablegen, falls noch nicht vorhanden:

```bash
python3 "$SKILL_DIR/kanboard" set-jira <task_id> --key <KEY>
```

So erscheint der Key beim naechsten `cr <id>` im Feld `jira`. Steht der `jira:`-Tag schon
und passt, entfaellt der Aufruf. Anders als beim Kimai-Shortcut **nicht ungefragt raten**,
welches Issue gemeint ist — nur setzen, wenn der Bezug eindeutig ist.

### Mehrere aktive CRs

Wenn mehrere CRs aktiv sind, **vor dem Commit oder der Zeiterfassung nachfragen**, welcher CR zutrifft. Nicht raten.

### Ohne aktiven CR-Kontext

Wenn kein CR aktiv ist, Commits und Kimai-Eintraege ganz normal ohne Prefix erstellen.

### Handoff

Wird ein Uebergabedokument erstellt (`/handoff`), gehoert der aktive CR-Kontext ins Dokument. Der handoff-Skill legt dafuer einen eigenen Abschnitt „Aktiver CR-Kontext" an (CR-ID, Titel, Task-URL, aktuelle Spalte/Status), damit der naechste Agent weiss, an welchem Task gearbeitet wird, und ihn mit `/kanboard cr <id>` wiederherstellen kann.
