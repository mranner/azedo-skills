# wiki - Subcommands

Anlegen, Einlesen, Kompilieren, Ernten, Abfragen, Pruefen.

### init

Neues Wiki-Unterverzeichnis anlegen.

```
/wiki init <name>
```

Erstellt die Standard-Verzeichnisstruktur unter `wiki/<name>/` (relativ zum
Projekt-Root) und legt eine Default-`wiki-schema.json` (Infra-Modell) an, damit das
neue Wiki sofort lintbar ist:

```json
{
  "required_common": ["date", "tags", "type", "status", "kunde"],
  "types": {
    "server":    ["hostname", "ip", "os", "location", "roles"],
    "service":   ["runs-on", "port"],
    "access":    ["target", "method"],
    "site":      ["location", "network-segments"],
    "procedure": ["applies-to"]
  }
}
```

Fuer ein Projekt-Wiki mit abweichendem Entity-Modell die `wiki-schema.json`
anschliessend anpassen (`required_common` + Typen-Liste) und die passende
`CLAUDE.md` schreiben. `required_common` gilt fuer jeden Typ; die Liste pro Typ
ergaenzt typ-spezifische Pflichtfelder.

### ingest

Quelle ins Wiki aufnehmen. Kopiert die Originaldatei unveraendert nach `raw/`.

```
/wiki ingest <pfad>
```

Nur fuer **lokale** Wikis. Ist `<name>` ein Remote (siehe
[Remote-Wikis](remote-wikis.md#remote-wikis-read-only)), abbrechen: Remote ist read-only, neue
Erkenntnisse manuell auf dem Zielhost einpflegen.

Workflow:
1. Datei nach `raw/articles/` kopieren (Originalname beibehalten)
2. Eintrag in `log.md` schreiben: `INGEST: <dateiname> — <kurzbeschreibung>`
3. Datei NICHT veraendern — raw/ ist immutable

Bei Verzeichnissen: alle `.md`-Dateien im Verzeichnis einzeln ingesten.

### compile

Ingested-Quellen zu Wiki-Entities verarbeiten.

```
/wiki compile [<raw-pfad>]
```

Ohne Argument: alle noch nicht kompilierten Quellen in `raw/` verarbeiten.
Mit Argument: nur die angegebene Quelle.

Nur fuer **lokale** Wikis. Ist `<name>` ein Remote (siehe
[Remote-Wikis](remote-wikis.md#remote-wikis-read-only)), abbrechen: Remote ist read-only.

Workflow:
1. Quelle lesen und Entity-Typen identifizieren — erlaubte Typen laut
   `<WIKI_ROOT>/CLAUDE.md` bzw. `<WIKI_ROOT>/wiki-schema.json` (Infra:
   Server/Service/Access/Site/Procedure; Projekt-Wikis abweichend)
2. Fuer jeden identifizierten Entity:
   a. Pruefen ob Entity bereits existiert (Dateiname-Check)
   b. Wenn ja: bestehenden Artikel lesen, dann aktualisieren
   c. Wenn nein: neuen Artikel mit vollstaendigem Frontmatter anlegen
3. Minimum 3 Wikilinks pro Artikel setzen
4. `index.md` aktualisieren (Entity in die passende Sektion des Wikis eintragen)
5. Backlink-Audit: bestehende Artikel durchsuchen, die den neuen Entity erwaehnen sollten
6. Eintrag in `log.md`: `COMPILE: <quelle> → <entity1>, <entity2>, ...`

**Vor Schritt 2 gelten die [Schreibregeln](../SKILL.md#schreibregeln)** - Aufnahmefilter
(gehört es überhaupt hinein), Dichtegebot und „aktualisieren heisst ersetzen".

Detaillierte Compile-Regeln (Cross-Referencing, Compile-Checkliste): @compilation-guide.md

Entity-Templates (Infra-Modell; fuer Projekt-Wikis gilt deren `<WIKI_ROOT>/CLAUDE.md`): @frontmatter-schemas.md

### harvest

Aus der laufenden Arbeit die Erkenntnisse herausziehen, die ins Wiki gehören -
**als Vorlage, ohne zu schreiben**.

```
/wiki harvest                 # alles aus dieser Sitzung
/wiki harvest <thema>         # nur zu einem Thema
```

Das ist der Subcommand für „gibt es relevante Erkenntnisse fürs Wiki",
„aktualisiere das Wiki", „trag das ins Wiki ein". Diese Sätze landeten früher
ungeführt in `compile` - das ist aber für Quellen aus `raw/` gedacht und hat
keinen Aufnahmefilter. Die Folge war stilles, ungefiltertes Anreichern.

Workflow:

1. `<WIKI_ROOT>/CLAUDE.md` und `index.md` lesen (Entity-Modell und Bestand).
2. Kandidaten sammeln: jede Erkenntnis der Sitzung, die nicht offensichtlich
   schon dokumentiert ist.
3. **Jeden Kandidaten durch den [Aufnahmefilter](../SKILL.md#aufnahmefilter-gehört-das-überhaupt-hinein)
   schicken.** Wer durchfällt, wird verworfen - aber **mit Grund und sichtbar**,
   nicht stillschweigend.
4. Für die verbleibenden das Ziel bestimmen: greppen, ob es schon irgendwo steht
   (dann dort ergänzen), sonst bestehender Artikel oder neuer.
5. **Vorlage ausgeben, nichts schreiben:**

   | Erkenntnis (ein Satz) | Ziel | neu/ergänzt | ~Zeilen |
   |---|---|---|---|
   | … | `[[slug]]` | ergänzt | 6 |

   Darunter die **verworfenen** Kandidaten mit Grund:

   ```
   Verworfen:
   - <Erkenntnis> — am Gegenstand selbst ablesbar (`<befehl>`)
   - <Erkenntnis> — Zwischenstand, gehört ins Ticket
   - <Erkenntnis> — steht bereits in [[slug]]
   ```

6. Erst **nach Freigabe** schreiben, dann vollständig: Artikel, Wikilinks,
   `index.md`, Frontmatter-Datum, `log.md`, danach `lint`.

Die verworfene Liste ist kein Beiwerk, sondern der Zweck: sie macht den Filter
überprüfbar. Ohne sie ist nicht erkennbar, ob etwas geprüft und aussortiert oder
schlicht übersehen wurde.

Für die Einträge selbst gelten die [Schreibregeln](../SKILL.md#schreibregeln) - vor allem
das Dichtegebot. Eine Erkenntnis, die in der Vorlage einen Satz braucht, wird im
Artikel nicht zu einem Absatz.

Bei einem **Remote-Wiki** nicht erlaubt (schreibend) - dort `<remote>:handoff`.

### query

Frage gegen das Wiki beantworten.

```
/wiki query <frage>
```

Workflow:
1. `index.md` lesen fuer Ueberblick
2. Relevante Entities per Frontmatter-grep identifizieren (z.B. `grep -r "type: server" wiki/` im Infra-Wiki bzw. `grep -r "type: concept" wiki/` in einem Projekt-Wiki)
3. Gefundene Artikel lesen
4. Backlinks in Artikeln folgen fuer verwandte Informationen
5. Antwort mit Wikilink-Zitaten formulieren (`[[entity-slug]]`)
6. Optional: Antwort als Query-Output in `wiki/queries/` speichern

Ein Präfix-Pointer `[[<präfix>:<slug>]]` in einem gefundenen Artikel darf in Schritt 4
mitgelesen werden: zeigt er auf ein Nachbar-Wiki unter `wiki/`, ist das eine ganz
normale lokale Datei (`wiki/<präfix>/wiki/**/<slug>.md`); zeigt er auf ein Remote-Wiki,
per SSH (siehe [Hints](remote-wikis.md#auf-entities-anderer-wikis-verweisen-hints)).

Bei einem **Remote-Wiki** dieselben Schritte, aber `index.md` und Entities per SSH
lesen statt lokal (`ssh <host> "cat/grep …"`, siehe
[Remote-Wikis](remote-wikis.md#remote-wikis-read-only)). Schritt 6 (Speichern) entfaellt — Remote
ist read-only.

### lint

Wiki auf strukturelle Probleme pruefen.

```
/wiki lint
```

Fuehrt `python3 "$SKILL_DIR/scripts/lint-wiki.py" <WIKI_ROOT>` aus (z.B.
`wiki/azedo/`, `wiki/cris/` — jeweils relativ zum Projekt-Root; welches Wiki ohne
Praefix gemeint ist, klaert Schritt 1 unter [Ziel-Wiki bestimmen](../SKILL.md#ziel-wiki-bestimmen)).

Das erlaubte Entity-Modell (Typen + Pflichtfelder) liest der Linter aus
`<WIKI_ROOT>/wiki-schema.json`; fehlt die Datei, gilt das Infra-Default.

Präfix-Pointer `[[<präfix>:<slug>]]` (siehe
[Hints](remote-wikis.md#auf-entities-anderer-wikis-verweisen-hints)) löst der Linter
erst gegen die Nachbar-Wikis unter `wiki/` auf - dort wird das Ziel direkt geprüft,
ein fehlender Slug ist ein Fehler - und danach gegen `.claude/wiki-remotes.json`;
Remote-Ziele gelten ungeprüft als gültig, `--check-remotes` verifiziert sie per SSH.
Unbekanntes Präfix bleibt ein toter Link.

Prueft:
- **Orphaned pages**: Artikel ohne eingehende Links
- **Dead links**: Wikilinks zu nicht-existierenden Artikeln - in den Artikeln als
  Fehler, in `log.md` und `index.md` als Warnung (beide liegen ausserhalb von
  `wiki/` und zaehlen nur als Quelle, nicht als Ziel; `log.md` ist historisch,
  ein alter Eintrag darf auf einen aufgeloesten Artikel zeigen)
- **Missing frontmatter**: Fehlende Pflichtfelder laut Wiki-Schema (Infra: type, kunde, date, status; Projekt-Wikis abweichend)
- **Missing index entries**: Artikel die nicht in index.md gelistet sind
- **Naming violations**: Dateinamen die nicht der Konvention entsprechen
- **Low connectivity**: Artikel mit weniger als 3 Wikilinks
