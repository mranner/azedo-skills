---
name: kanboard
description: >
  Verwaltet eine Kanboard-Instanz via JSON-RPC API: Tasks (erstellen, anzeigen,
  verschieben, zuweisen, schliessen, loeschen, kommentieren, Subtasks, Tags, Verknuepfungen,
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

Das Script kennt 48 Subcommands. Hier stehen der CR-Kontext und die haeufigsten
Aufrufe; die vollstaendige Referenz liegt daneben und wird bei Bedarf gelesen:

| Datei | Inhalt |
|---|---|
| `references/tasks.md` | Task anlegen, anzeigen, aendern, verschieben, schliessen, loeschen, auflisten, suchen, eigene Tasks |
| `references/task-inhalte.md` | Kommentare, Anhaenge, Teilaufgaben, Verknuepfungen, Tags, Handoff-Feld |
| `references/projekte.md` | Projekte anlegen und loeschen, Mitglieder und Rollen, Spalten und User auflisten |

`python3 "$SKILL_DIR/kanboard" <subcommand> --help` listet die Optionen eines
Subcommands direkt aus dem Script - schneller als Nachschlagen, und nie veraltet.

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

### Die haeufigsten Aufrufe

```bash
# Task anlegen
python3 "$SKILL_DIR/kanboard" create-task --project <name|id> --title "..." [--description "..."] [--column <name>] [--owner <username>]

# Task anzeigen (inkl. column_title, swimlane_name, owner_username)
python3 "$SKILL_DIR/kanboard" get-task <task_id>

# Task erledigen -- Spalte wechseln, NICHT close-task (siehe Sicherheitsregeln)
python3 "$SKILL_DIR/kanboard" move-task <task_id> --column erledigt

# Task in ein anderes Projekt verschieben
python3 "$SKILL_DIR/kanboard" move-project <task_id> --project <name|id> [--column <name>]

# irgendwo suchen (Titel + Beschreibung + Kommentare)
python3 "$SKILL_DIR/kanboard" search "<stichwort>" --all --in description,comment

# eigene offene Tasks ueber alle Projekte
python3 "$SKILL_DIR/kanboard" my-tasks
```

`move-task` wechselt die **Spalte innerhalb** des Projekts, `move-project` das
**Projekt**. Ein `move-task --project <fremdes Projekt>` wird intern an
`move-project` weitergereicht, weil Kanboard den Positionswechsel ueber
Projektgrenzen hinweg nicht ausfuehrt.

## Sicherheitsregeln

Diese vier Regeln gelten unabhaengig davon, welche Referenzdatei gelesen wurde:

- **"Task erledigen" heisst `move-task --column erledigt`.** Tasks werden im
  Regelfall nur in der Spalte "erledigt" geschlossen. `close-task` nur
  ausfuehren, wenn der User es ausdruecklich verlangt - sonst nachfragen.
  (`close-task` ist per `open-task` umkehrbar.)
- **`remove-task` ist nicht umkehrbar** - Kommentare, Anhaenge und Teilaufgaben
  gehen mit. Ohne `--force` zeigt der Aufruf nur, was getroffen waere, und
  bricht mit Exit-Code 1 ab; erst der zweite Aufruf mit `--force` loescht.
  Loeschen ist die Ausnahme fuer Duplikate und Fehlanlagen. Ein erledigter Task
  wird **nie** geloescht, nur weil er fertig ist.
- **`remove-project --force` loescht die enthaltenen Tasks mit.** Ohne `--force`
  bricht es ab, solange Tasks im Projekt liegen.
- **Zustandsaendernde Aufrufe einzeln absetzen.** `move-task`, `close-task`,
  `remove-task` und `remove-project` gehoeren nicht mit weiteren Subcommands in eine
  Shell-Befehlskette. Schlaegt ein vorangehender Aufruf fehl - ein falsch erinnerter
  Parametername genuegt -, laeuft die Kette weiter und der Task wird trotzdem
  geschlossen: die Begruendung, die der Kommentar davor tragen sollte, fehlt dann im
  Task. Das Ergebnis eines Aufrufs pruefen, bevor der naechste folgt; die
  Rueckfrage-Regel zu `close-task` traegt nur, wenn beim Schliessen auch stimmt, was
  vorher passiert sein sollte.

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

- **Config-Quelle** (`KANBOARD_URL`, `KANBOARD_TOKEN`) — in dieser Reihenfolge:
  1. `KANBOARD_ENV` (Environment-Variable, voller Pfad zur Datei)
  2. `.env` im **aktuellen Arbeitsverzeichnis**, falls vorhanden
  3. sonst `~/.env`

  Der Home-Fallback ist gewollt: eine Konfiguration reicht fuer alle Projekte,
  ein projektlokales `.env` uebersteuert sie bei Bedarf. **Achtung:** entschieden
  wird allein danach, ob die Datei *existiert* — enthaelt ein projektlokales
  `.env` die Kanboard-Schluessel nicht (weil es z.B. nur DB-Zugangsdaten fuehrt),
  bricht der Aufruf mit `KANBOARD_URL not set in <pfad>` ab, statt auf `~/.env`
  auszuweichen. Dann `KANBOARD_ENV=~/.env` setzen oder die Schluessel ergaenzen.
  (Der kimai-Skill prueft an dieser Stelle zusaetzlich auf seine Schluessel und
  faellt zurueck — siehe dortige SKILL.md.)
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
