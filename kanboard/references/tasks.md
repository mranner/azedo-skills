# Tasks - Subcommands

Anlegen, Anzeigen, Ändern, Verschieben, Schließen, Löschen, Auflisten, Suchen.
Aufruf durchgehend `python3 "$SKILL_DIR/kanboard" <subcommand>`.

### Task erstellen

```bash
python3 "$SKILL_DIR/kanboard" create-task \
  --project <name|id> --title "<titel>" \
  [--description "<text>" | --description-file <pfad>] [--column <name>] \
  [--owner <username>] [--swimlane <name>]
```

`--description` und `--description-file` schliessen einander aus. Bei laengeren
Beschreibungen (Tabellen, Codebloecke, mehrere Absaetze) `--description-file`
nehmen: `--description "$(cat datei.md)"` schickt den Inhalt durch die Shell, wo
Backticks, `$` und Anfuehrungszeichen ausgewertet werden.

Ohne `--owner` wird der Task dem `default_user` aus `instance.json` zugewiesen (wie
bei `add-comment`). Ist dort kein `default_user` gesetzt, bleibt der Task unassigned.

### Task anzeigen

```bash
python3 "$SKILL_DIR/kanboard" get-task <task_id>
```

### Task aendern

```bash
python3 "$SKILL_DIR/kanboard" update-task <task_id> \
  [--title "<titel>"] [--description "<text>" | --description-file <pfad>] [--owner <username>]
```

`--description-file` liest die neue Beschreibung aus einer Datei, sonst wie bei
`create-task`.

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

Nennt `move-task` ein `--project`, das vom Projekt des Tasks abweicht, delegiert es
seit 1.49.11 intern an `move-project` — Kanboard wies `moveTaskPosition` in dem Fall
mit einem blossen `false` ab, ohne zu sagen warum. Die Ausgabe ist dann die von
`move-project` (mit `project_id`, ggf. `reclosed`).

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

### Task loeschen

```bash
python3 "$SKILL_DIR/kanboard" remove-task <task_id> [--force]
```

**Nicht umkehrbar** — Kommentare, Anhaenge und Teilaufgaben gehen mit. Ohne
`--force` wird deshalb nichts geloescht, sondern nur gezeigt, was getroffen
waere (Titel, Projekt, Spalte), mit `success: false` und Exit-Code 1. Erst der
zweite Aufruf mit `--force` fuehrt aus. Der Titel in dieser Vorschau ist der
eigentliche Zweck: eine vertippte ID loescht sonst still den falschen Task.

**Abgrenzung:** Loeschen ist die Ausnahme fuer Duplikate und Fehlanlagen. Der
Normalfall ist `move-task --column erledigt` (und, falls ausdruecklich
gewuenscht, `close-task` — reversibel per `open-task`). Ein erledigter Task
wird **nie** geloescht, nur weil er fertig ist.

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
