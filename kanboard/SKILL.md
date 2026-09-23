---
name: kanboard
description: >
  Verwaltet eine Kanboard-Instanz via JSON-RPC API: Tasks (erstellen, anzeigen,
  verschieben, zuweisen, schließen, löschen, kommentieren, Subtasks, Tags, Verknüpfungen,
  Handoff-Feld, Dateien) sowie Projekte inkl. Anlage und Mitglieder-/Rollen-Verwaltung.
  Nutze diesen Skill wenn der User Tasks oder Projekte verwalten will.
  Auch aktiv verwenden wenn der User sagt "leg mir ein Ticket an",
  "mach ein Task draus", "ins Kanboard eintragen", o.ä. - und sobald eine
  CR-Nummer fällt ("CR4326", "ich arbeite an CR4326", "Commit unter CR"), weil
  dann Commit- und Kimai-Präfix gelten. Tasks nur für Handlungen; Befunde ohne
  Folgehandlung gehören ins Wiki, nicht in einen Task.
  Trigger: /kanboard.
---

# kanboard -- Kanboard Task-Verwaltung

Tasks werden über das gebündelte Script `kanboard` (Python ≥3.11, im Skill-Verzeichnis) verwaltet.

**Aufruf:** `python3 "$SKILL_DIR/kanboard" <subcommand> [options]`

`$SKILL_DIR` ist das Base Directory dieses Skills (dort wo diese SKILL.md liegt).

## Setup

Beim ersten Einsatz (oder wenn sich Projekte/User ändern) `setup` ausführen:

```bash
python3 "$SKILL_DIR/kanboard" setup --default-user <username>
```

Das schreibt `instance.json` ins Skill-Verzeichnis mit allen Projekten, Swimlanes, Spalten und Usern. `--default-user` legt fest, welcher Kanboard-User als Absender für Kommentare verwendet wird (wenn kein `--user` angegeben).

Falls `instance.json` nicht existiert, zuerst `setup` ausführen.

### instance.json — Schema und Zugriff

**`instance.json` NICHT selbst roh parsen** — dafür gibt es die Subcommands
`list-projects`, `list-columns --project <name|id>` und `list-users` (liefern IDs
**und** Namen). `get-task` reichert zusätzlich `column_title`,
`swimlane_name`, `owner_username`/`owner_name` an, sodass keine Quer-Auflösung
nötig ist.

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
  "users": [ { "id": 4, "username": "musterfrau", "name": "Karin Musterfrau", "is_active": 1 } ]
  // deaktivierte User stehen mit "is_active": 0 drin, damit sie adressierbar bleiben
}
```

Merke: `columns`/`swimlanes` sind **Strings ohne IDs** — die Spalten-ID einer
Position ergibt sich nicht aus `instance.json`, dafür `list-columns` verwenden.

## Subcommands

Das Script kennt 56 Subcommands. Hier stehen die häufigsten Aufrufe; die
vollständige Referenz liegt daneben und wird bei Bedarf gelesen:

| Datei | Inhalt |
|---|---|
| `references/tasks.md` | Task anlegen, anzeigen, ändern, verschieben, schließen, löschen, auflisten, suchen, eigene Tasks |
| `references/task-inhalte.md` | Kommentare, Anhänge, Teilaufgaben, Verknüpfungen, Tags, Handoff-Feld |
| `references/projekte.md` | Projekte anlegen und löschen, Mitglieder und Rollen, Gruppen, Spalten und User auflisten |

`python3 "$SKILL_DIR/kanboard" <subcommand> --help` listet die Optionen eines
Subcommands direkt aus dem Script - schneller als Nachschlagen, und nie veraltet.

### Die häufigsten Aufrufe

```bash
# Task anlegen
python3 "$SKILL_DIR/kanboard" create-task --project <name|id> --title "..." [--description "..." | --description-file <pfad>] [--column <name>] [--owner <username>] [--due YYYY-MM-DD] [--start YYYY-MM-DD]

# Task anzeigen (inkl. column_title, swimlane_name, owner_username)
python3 "$SKILL_DIR/kanboard" get-task <task_id>

# Task erledigen -- Spalte wechseln, NICHT close-task (siehe Sicherheitsregeln)
python3 "$SKILL_DIR/kanboard" move-task <task_id> --column erledigt

# Fälligkeits- bzw. Startdatum setzen (leerer Wert löscht es)
python3 "$SKILL_DIR/kanboard" update-task <task_id> [--due YYYY-MM-DD] [--start "YYYY-MM-DD HH:MM"]

# Task in ein anderes Projekt verschieben
python3 "$SKILL_DIR/kanboard" move-project <task_id> --project <name|id> [--column <name>]

# irgendwo suchen (Titel + Beschreibung + Kommentare)
python3 "$SKILL_DIR/kanboard" search "<stichwort>" --all --in description,comment

# eigene offene Tasks über alle Projekte
python3 "$SKILL_DIR/kanboard" my-tasks
```

`move-task` wechselt die **Spalte innerhalb** des Projekts, `move-project` das
**Projekt**. Ein `move-task --project <fremdes Projekt>` wird intern an
`move-project` weitergereicht, weil Kanboard den Positionswechsel über
Projektgrenzen hinweg nicht ausführt.

## Teilaufgaben und Kommentare benennen

Im Kanboard-UI haben Teilaufgaben und Kommentare **keine sichtbare ID**. Eine
nackte Zahl aus der API ist dort also nicht auffindbar. Jede Referenz in einer
Ausgabe trägt deshalb das, was im UI zu sehen ist, und die ID nur nachgestellt
in Klammern:

- Teilaufgabe: `T3 "Log-Rotation umstellen" (812)`
- Kommentar: `K2 Michael, 09.09. 14:12: "…Rollout zweite Tranche…" (4471)`

Titel auf ~40 Zeichen kürzen, beim Kommentar Autor, Tag und Uhrzeit sowie die
ersten ~50 Zeichen des Textes.

`T<n>` und `K<n>` kommen als Feld `ref` aus `list-subtasks` bzw. `get-comments` -
nicht selbst zählen, sonst wandert die Nummer zwischen zwei Aufrufen. Sie
entspricht der Reihenfolge im UI: Teilaufgaben sortiert Kanboard nach
`position`, Kommentare nach Erstellzeit, beide aufsteigend
(`SubtaskModel::getQuery()` und `CommentModel::getAll()`).

**Vorbehalt bei Kommentaren:** Die Sortierrichtung ist im UI pro Benutzer
umkehrbar (`KEY_COMMENT_SORTING_DIRECTION`, Default aufsteigend), die API liefert
immer aufsteigend. Steht sie auf absteigend, steht K1 im UI unten - die
Nummerierung bleibt "ältester Kommentar = K1".

Einen Permalink gibt es nur für Kommentare, über das Link-Icon am Kommentar:
`…/kanboard/?controller=TaskViewController&action=show&task_id=<task_id>#comment-<id>`
(office.azedo.at läuft ohne URL-Rewrite). Nur auf Nachfrage ausgeben - in einer
Aufzählung macht er jede Zeile unlesbar.

## Sicherheitsregeln

Diese fünf Regeln gelten unabhängig davon, welche Referenzdatei gelesen wurde:

- **"Task erledigen" heißt `move-task --column erledigt`.** Tasks werden im
  Regelfall nur in der Spalte "erledigt" geschlossen. `close-task` nur
  ausführen, wenn der User es ausdrücklich verlangt - sonst nachfragen.
  (`close-task` ist per `open-task` umkehrbar.)
- **`remove-task` ist nicht umkehrbar** - Kommentare, Anhänge und Teilaufgaben
  gehen mit. Ohne `--force` zeigt der Aufruf nur, was getroffen wäre, und
  bricht mit Exit-Code 1 ab; erst der zweite Aufruf mit `--force` löscht.
  Löschen ist die Ausnahme für Duplikate und Fehlanlagen. Ein erledigter Task
  wird **nie** gelöscht, nur weil er fertig ist.
- **`remove-project --force` löscht die enthaltenen Tasks mit.** Ohne `--force`
  bricht es ab, solange Tasks im Projekt liegen.
- **Rechte-Entzug: erst prüfen, woher der Zugriff kommt.** `remove-project-user`
  entfernt nur **direkte** Mitgliedschaften und bleibt bei gruppenbasiertem
  Zugriff wirkungslos (Rückgabe `false`, dazu ein `hint`). Vorher
  `list-project-users` lesen: `via_group_candidates` nennt mögliche Gruppen,
  ist aber ein Verdacht, kein Nachweis — die Zuordnung Projekt->Gruppe ist über
  die API nicht lesbar. `removeGroupMember` wirkt
  umgekehrt **gruppenweit** - vor dem Entzug auflisten, welche Projekte der
  Gruppe zugeordnet sind, sonst verliert der User mehr als gemeint.
- **Zustandsändernde Aufrufe einzeln absetzen.** `move-task`, `close-task`,
  `remove-task` und `remove-project` gehören nicht mit weiteren Subcommands in eine
  Shell-Befehlskette. Schlägt ein vorangehender Aufruf fehl - ein falsch erinnerter
  Parametername genügt -, läuft die Kette weiter und der Task wird trotzdem
  geschlossen: die Begründung, die der Kommentar davor tragen sollte, fehlt dann im
  Task. Das Ergebnis eines Aufrufs prüfen, bevor der nächste folgt; die
  Rückfrage-Regel zu `close-task` trägt nur, wenn beim Schließen auch stimmt, was
  vorher passiert sein sollte.

## Kurzform: `new` / `neu`

`/kanboard new [[<user>@]<projekt>] <text>` (gleichwertig `neu`) legt einen Task an,
z.B. `/kanboard neu dagmar@azedo Text` oder `/kanboard neu dagmar@ Text`:

- **Projekt:** Das erste Wort nach `new` ist nur dann das Projekt, wenn es
  (case-insensitiv) einem Namen aus `list-projects` entspricht - sonst gehört
  es zum Text. Ohne Projekt gilt das Projekt des aktiven CR-Kontexts. Kein
  CR-Kontext, oder mehrere CRs aus verschiedenen Projekten: nachfragen.
- **User:** Ein Präfix `<user>@` setzt den Owner (`--owner`). Abgleich
  (case-insensitiv) gegen `list-users`: Username (`dmandl`) oder Vorname aus
  dem Klarnamen (`dagmar`). Kein oder kein eindeutiger Treffer: nachfragen.
  Leeres Projekt nach dem `@` (`dagmar@`) heißt Projekt aus dem CR-Kontext.
  Ohne Präfix gilt der `default_user`.
- **Titel und Beschreibung:** Titel aus dem Text ableiten (Regeln unter
  Workflow), der Text selbst geht in die Beschreibung.
- **Workflow-Schritt 0 gilt auch hier**, als stille Prüfung: Ist aus dem Text
  eine Handlung erkennbar, direkt anlegen, ohne Rückfrage zu Titel oder
  Beschreibung, dann die URL melden; Korrekturen danach per `update-task`.
  Ist keine Handlung erkennbar, nachfragen statt anlegen.

## Workflow

0. **Ist ein Task das richtige Mittel?** Ein Task steht für eine Handlung (Konfigänderung, Quellcodeänderung, Einrichtung, Klärung mit Dritten), nicht für Dokumentation. Folgt aus einem Befund keine Handlung, gehört er ins Wiki (`/wiki`) oder in die Doku des Projekts. Das gilt besonders für Nebenbefunde beim Abschließen eines Tasks: nicht als Ablage in neue Tasks auslagern.
1. Parameter aus der Nutzeranfrage ableiten (Projekt, Titel, Beschreibung, Zuweisung, Spalte).
2. **Titel kurz halten** -- max. ~60 Zeichen. Details in die Beschreibung. Klare, allgemein verständliche Abkürzungen sind erlaubt (z.B. "Netzwerk" statt "Netzwerkproblem", "DB" für Datenbank). Keine selbst erfundenen oder unüblichen Abkürzungen.
3. Wenn nicht eindeutig: nachfragen.
4. Befehl zusammenbauen und ausführen.
5. Ergebnis (Task-ID, URL, Status) dem User melden.

## Task-URL

Nach Anlage oder Änderung dem User die URL anzeigen. Die Basis-URL ergibt sich aus `KANBOARD_URL` (ohne `/jsonrpc.php`):

`<KANBOARD_BASE>/?controller=TaskViewController&action=show&task_id=<ID>&project_id=<PID>`

## Hinweise

- **Config-Quelle** (`KANBOARD_URL`, `KANBOARD_TOKEN`) — in dieser Reihenfolge:
  1. `KANBOARD_ENV` (Environment-Variable, voller Pfad zur Datei)
  2. `.env` im **aktuellen Arbeitsverzeichnis**, falls vorhanden
  3. sonst `~/.env`

  Der Home-Fallback ist gewollt: eine Konfiguration reicht für alle Projekte,
  ein projektlokales `.env` übersteuert sie bei Bedarf. **Achtung:** entschieden
  wird allein danach, ob die Datei *existiert* — enthält ein projektlokales
  `.env` die Kanboard-Schlüssel nicht (weil es z.B. nur DB-Zugangsdaten führt),
  bricht der Aufruf mit `KANBOARD_URL not set in <pfad>` ab, statt auf `~/.env`
  auszuweichen. Dann `KANBOARD_ENV=~/.env` setzen oder die Schlüssel ergänzen.
  (Der kimai-Skill prüft an dieser Stelle zusätzlich auf seine Schlüssel und
  fällt zurück — siehe dortige SKILL.md.)
- Dateipfade für `attach-file` müssen absolut sein.
- Temporäre Dateien (Downloads, Optimierungen etc.) gehören ins Projekt-Verzeichnis `.tmp/`, **nicht** in `$SKILL_DIR/.tmp/`. Das Skill-Verzeichnis darf nicht als Arbeitsverzeichnis verwendet werden.
- Spaltennamen sind case-insensitiv im Script.
- Output ist JSON -- relevante Felder extrahieren und lesbar darstellen.
- Beschreibungen unterstützen Markdown-Syntax.
- Neue und verschobene Tasks werden am Ende (unten) der Spalte eingefügt.

## CR-Kontext (Change Request)

Der CR-Kontext verknüpft Kanboard-Tasks mit Commits und Zeiterfassung. Die Schreibweise `CR{id}` (z.B. `CR4326`) bezieht sich immer auf einen Kanboard-Task.

### Erkennung

Wenn der User irgendwo eine CR-Referenz verwendet, wird das als Kanboard-Task interpretiert. Alle Schreibweisen werden erkannt und auf die kanonische Form normalisiert:

- `CR4326`, `cr4326`, `CR 4326`, `cr 4326`, `#4326` → **CR4326**

### Aktivierung

- **Explizit:** Der User führt `cr <id>` aus oder sagt "ich arbeite an CR4326"
- **Mehrere CRs:** `cr 4326 4330` aktiviert beide Tasks als Kontext
- Der aktive CR-Kontext gilt für die gesamte Session, bis der User ihn ändert oder beendet ("CR fertig", "kein CR mehr")

```bash
python3 "$SKILL_DIR/kanboard" cr 4326
python3 "$SKILL_DIR/kanboard" cr CR4326 CR4330
```

### Was `cr` lädt

Der CR-Kontext ist die Arbeitsgrundlage der ganzen Session, deshalb lädt `cr`
den *Inhalt* des Tasks mit — nicht nur die Metadaten:

| Feld | Verhalten |
|---|---|
| `title`, `column`, `owner`, `project_name` | immer |
| `modified` | immer — Änderungszeitpunkt, lesbar (`YYYY-MM-DD HH:MM`) |
| `description` | **immer, Volltext** — enthält i.d.R. die menschlich verfasste Ausgangslage (Zusammenfassung, Mail-Auszug). Ohne sie sieht ein voller Task fälschlich leer aus. |
| `handoff` | nur wenn befüllt (TaskHandoff-Plugin) |
| `tags` | nur wenn vorhanden — Liste der Tag-Namen |
| `kimai` | nur wenn ein Tag `kimai:<shortcut>` gesetzt ist (siehe Kimai-Präfix) |
| `jira` | nur wenn ein Tag `jira:<KEY>` gesetzt ist — verknüpftes Jira-Issue (siehe Jira-Verknüpfung) |
| `comments`, `attachments` | Zähler, nur wenn > 0 |

`description` und `handoff` sind **nicht** redundant: Description = *was ist die
Aufgabe* (von Menschen gesetzt), Handoff = *wo stehen wir / wie geht es weiter*
(Übergabestand für die nächste Bearbeitung).

Bewusst **nicht** automatisch geladen — dafür gibt es eigene Befehle: Kommentar-
Volltext (`get-comments`), Teilaufgaben (`list-subtasks`), Task-Links
(`list-task-links`), Datei-**Anhänge** (`list-files`/`download-file`). Von
Kommentaren und Anhängen kommt nur der Zähler als Signal mit.

### Commit-Präfix

Wenn ein CR-Kontext aktiv ist und der User einen Commit macht (`git commit`, `svn commit`):

- Commit-Message immer mit `CR{id}: ` präfixen
- Beispiel: `git commit -m "CR4326: Login-Formular validiert jetzt E-Mail-Adressen"`
- Beispiel: `svn commit -m "CR4326: Timeout auf 30s erhöht"`

### Kimai-Präfix

Wenn ein CR-Kontext aktiv ist und der User Zeit erfasst (via `/kimai`):

- Beschreibung (`--description`) immer mit `CR{id}: ` präfixen
- Beispiel: `--description "CR4326: Login-Validierung implementiert"`

**Kimai-Shortcut am Task hinterlegen (Write-back):** Nach einer Kimai-Buchung unter
aktivem CR den verwendeten Shortcut am Task als Tag `kimai:<shortcut>` ablegen, falls
noch nicht vorhanden — analog zum Commit-Präfix eine automatische Regel, keine
Rückfrage nötig:

```bash
python3 "$SKILL_DIR/kanboard" set-kimai <task_id> --shortcut <shortcut>
```

So steht der Shortcut beim nächsten `cr <id>` im Feld `kimai` und die Zeiterfassung
kann ihn direkt übernehmen, ohne erneut zu suchen. Steht der `kimai:`-Tag bereits und
passt, entfällt der Aufruf. (Der Tag trägt den Shortcut-**Key** aus
`.claude/kimai-shortcuts.json`, nicht Projekt-/Aktivitäts-IDs.)

### Jira-Verknüpfung

Anders als `kimai:` präfixt die Jira-Verknüpfung **nichts** — sie merkt sich nur das
zum CR gehörende Jira-Issue, damit der `jira`-Skill ohne erneute Key-Angabe darauf
arbeiten kann. Es gibt daher **keinen** Jira-Commit-Präfix (der CR bleibt der einzige
Commit-Anker).

**Write-back:** Sobald unter aktivem CR ein Jira-Issue eindeutig zum Task gehört (der
User nennt es, oder es wird im Zuge der Arbeit angelegt/bearbeitet), den Key am Task als
Tag `jira:<KEY>` ablegen, falls noch nicht vorhanden:

```bash
python3 "$SKILL_DIR/kanboard" set-jira <task_id> --key <KEY>
```

So erscheint der Key beim nächsten `cr <id>` im Feld `jira`. Steht der `jira:`-Tag schon
und passt, entfällt der Aufruf. Anders als beim Kimai-Shortcut **nicht ungefragt raten**,
welches Issue gemeint ist — nur setzen, wenn der Bezug eindeutig ist.

### Mehrere aktive CRs

Wenn mehrere CRs aktiv sind, **vor dem Commit oder der Zeiterfassung nachfragen**, welcher CR zutrifft. Nicht raten.

### Ohne aktiven CR-Kontext

Wenn kein CR aktiv ist, Commits und Kimai-Einträge ganz normal ohne Präfix erstellen.

### Handoff

Wird ein Übergabedokument erstellt (`/handoff`), gehört der aktive CR-Kontext ins Dokument. Der handoff-Skill legt dafür einen eigenen Abschnitt „Aktiver CR-Kontext" an (CR-ID, Titel, Task-URL, aktuelle Spalte/Status), damit der nächste Agent weiß, an welchem Task gearbeitet wird, und ihn mit `/kanboard cr <id>` wiederherstellen kann.
