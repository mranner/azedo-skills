# wiki - Subcommands

Anlegen, Einlesen, Kompilieren, Ernten, Abfragen, Prüfen.

**Inhalt:** init · ingest · compile · harvest · query · lint (mit Schrumpf-Guard `--check-shrink`)

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

Für ein Projekt-Wiki mit abweichendem Entity-Modell die `wiki-schema.json`
anschließend anpassen (`required_common` + Typen-Liste) und die passende
`CLAUDE.md` schreiben. `required_common` gilt für jeden Typ; die Liste pro Typ
ergänzt typ-spezifische Pflichtfelder.

### ingest

Quelle ins Wiki aufnehmen. Kopiert die Originaldatei unverändert nach `raw/`.

```
/wiki ingest <pfad>
```

Nur für **lokale** Wikis. Ist `<name>` ein Remote (siehe
„Remote-Wikis", Referenz laut SKILL.md), abbrechen: Remote ist read-only, neue
Erkenntnisse manuell auf dem Zielhost einpflegen.

Workflow:
1. Datei nach `raw/articles/` kopieren (Originalname beibehalten)
2. Eintrag in `log.md` schreiben: `INGEST: <dateiname> — <kurzbeschreibung>`
3. Datei NICHT verändern — raw/ ist immutable

Bei Verzeichnissen: alle `.md`-Dateien im Verzeichnis einzeln ingesten.

### compile

Ingested-Quellen zu Wiki-Entities verarbeiten.

```
/wiki compile [<raw-pfad>]
```

Ohne Argument: alle noch nicht kompilierten Quellen in `raw/` verarbeiten.
Mit Argument: nur die angegebene Quelle.

Nur für **lokale** Wikis. Ist `<name>` ein Remote (siehe
„Remote-Wikis", Referenz laut SKILL.md), abbrechen: Remote ist read-only.

Workflow:
1. Quelle lesen und Entity-Typen identifizieren — erlaubte Typen laut
   `<WIKI_ROOT>/CLAUDE.md` bzw. `<WIKI_ROOT>/wiki-schema.json` (Infra:
   Server/Service/Access/Site/Procedure; Projekt-Wikis abweichend)
2. Für jeden identifizierten Entity:
   a. Prüfen ob Entity bereits existiert (Dateiname-Check)
   b. Wenn ja: bestehenden Artikel lesen, dann aktualisieren
   c. Wenn nein: neuen Artikel mit vollständigem Frontmatter anlegen
3. Minimum 3 Wikilinks pro Artikel setzen
4. Index aktualisieren: Entity in die passende Sektion von `index.md` eintragen bzw. in die
   `index-*.md`, die ihren Typ führt (steht im Kopf von `index.md`)
5. Backlink-Audit: bestehende Artikel durchsuchen, die den neuen Entity erwähnen sollten
6. Eintrag in `log.md`: `COMPILE: <quelle> → <entity1>, <entity2>, ...`
7. Bei aktualisierten Artikeln (Schritt 2b) den [Schrumpf-Guard](#schrumpf-guard---check-shrink)
   laufen lassen und jede Meldung einzeln beantworten, bevor committet wird

**Vor Schritt 2 die Schreibregeln lesen** (Referenz laut SKILL.md) - Aufnahmefilter
(gehört es überhaupt hinein), Dichtegebot und „aktualisieren heißt ersetzen".

Detaillierte Compile-Regeln (Cross-Referencing, Compile-Checkliste): Compile-Referenz laut SKILL.md

Entity-Templates (Infra-Modell; für Projekt-Wikis gilt deren `<WIKI_ROOT>/CLAUDE.md`): Frontmatter-Referenz laut SKILL.md

### harvest

Aus der laufenden Arbeit die Erkenntnisse herausziehen, die ins Wiki gehören -
**als Vorlage, ohne zu schreiben**. Einzige Ausnahme ist der direkte Auftrag, siehe unten.

```
/wiki harvest                 # alles aus dieser Sitzung
/wiki harvest <thema>         # nur zu einem Thema
```

Das ist der Subcommand für „gibt es relevante Erkenntnisse fürs Wiki",
„aktualisiere das Wiki", „trag das ins Wiki ein". Diese Sätze landeten früher
ungeführt in `compile` - das ist aber für Quellen aus `raw/` gedacht und hat
keinen Aufnahmefilter. Die Folge war stilles, ungefiltertes Anreichern.

**Ein direkter Auftrag ist die Freigabe.** Nennt der Auftrag den Befund selbst
(„trag ins Wiki ein, dass …", „trag das ins Wiki ein" zu einem eben besprochenen
Befund), entfällt die Vorlage für genau diesen Befund. Aufnahmefilter (Schritt 3)
und Zielbestimmung (Schritt 4) laufen trotzdem: besteht er, wird nach Schritt 6
geschrieben; fällt er durch, den Grund melden und nichts schreiben. Weitere
Erkenntnisse der Sitzung deckt der Auftrag nicht, die gehen in die Vorlage. Eine
offene Frage („gibt es Erkenntnisse", „aktualisiere das Wiki") nennt keinen Befund
und bleibt immer bei der Vorlage.

Workflow:

1. `<WIKI_ROOT>/CLAUDE.md` lesen (Entity-Modell). Den Bestand klärt Schritt 4 per grep.
2. Kandidaten sammeln: jede Erkenntnis der Sitzung, die nicht offensichtlich
   schon dokumentiert ist.
3. **Jeden Kandidaten durch den Aufnahmefilter schicken** (Schreibregeln, Referenz laut SKILL.md) - vorher lesen,
   nicht aus dem Gedächtnis anwenden. Wer durchfällt, wird verworfen - aber **mit Grund und sichtbar**,
   nicht stillschweigend. Beschreibt ein Kandidat einen Zustand, den die Sitzung
   selbst verändert hat, wird er gegen den Stand nach der Änderung formuliert,
   nicht gegen den Befund davor.
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

6. Erst **nach Freigabe** schreiben. Vorher `git status --short -- <WIKI_ROOT>`
   lesen: Liegen dort schon uncommittete Änderungen, diese melden und getrennt
   committen lassen, bevor der Harvest dieselben Dateien anfasst - sonst
   vermischen sich fremde und eigene Änderungen in einem Commit. Dann
   vollständig schreiben: Artikel, Wikilinks, Index, Frontmatter-Datum,
   `log.md`, danach `lint`. Fertig ist der Harvest, wenn `lint` ohne Fehler
   durchläuft, committet ist und `git status --short -- <WIKI_ROOT>` leer ist.

Die verworfene Liste ist kein Beiwerk, sondern der Zweck: sie macht den Filter
überprüfbar. Ohne sie ist nicht erkennbar, ob etwas geprüft und aussortiert oder
schlicht übersehen wurde.

Für die Einträge selbst gelten die Schreibregeln (Referenz laut SKILL.md) - vor allem
das Dichtegebot. Eine Erkenntnis, die in der Vorlage einen Satz braucht, wird im
Artikel nicht zu einem Absatz.

Bei einem **Remote-Wiki** nicht erlaubt (schreibend) - dort `<remote>:handoff`.

### query

Frage gegen das Wiki beantworten.

```
/wiki query <frage>
```

Workflow:
1. Begriffe der Frage greppen (Hostname, Dienst, Fehlermeldung):
   `grep -rli '<begriff>' <WIKI_ROOT>/wiki/`. Den Index nur lesen, wenn die Frage einen
   Überblick verlangt („welche Server hat Kunde X") oder grep nichts trifft: `index.md`,
   von den `index-*.md` nur die, die laut Kopf von `index.md` den gesuchten Typ führt
2. Bei einer Frage nach Typ oder Kunde per Frontmatter-grep eingrenzen (z.B. `grep -r "type: server" wiki/` im Infra-Wiki bzw. `grep -r "type: concept" wiki/` in einem Projekt-Wiki)
3. Gefundene Artikel lesen
4. Backlinks in Artikeln folgen für verwandte Informationen
5. Antwort mit Wikilink-Zitaten formulieren (`[[entity-slug]]`). Eine abgelöste
   Entity (Ablöse-Status eines `supersede`-Typs) ist nicht der aktuelle Stand:
   dem Link auf die Nachfolgerin folgen und diese zitieren
6. Optional: Antwort als Query-Output in `wiki/queries/` speichern

Ein Präfix-Pointer `[[<präfix>:<slug>]]` in einem gefundenen Artikel darf in Schritt 4
mitgelesen werden: zeigt er auf ein Nachbar-Wiki unter `wiki/`, ist das eine ganz
normale lokale Datei (`wiki/<präfix>/wiki/**/<slug>.md`); zeigt er auf ein Remote-Wiki,
per SSH (siehe „Hints", Referenz laut SKILL.md).

Bei einem **Remote-Wiki** dieselben Schritte, aber `index.md` und Entities per SSH
lesen statt lokal (`ssh <host> "cat/grep …"`, siehe
„Remote-Wikis", Referenz laut SKILL.md). Schritt 6 (Speichern) entfällt — Remote
ist read-only.

### lint

Wiki auf strukturelle Probleme prüfen.

```
/wiki lint
```

Führt `python3 "$SKILL_DIR/scripts/lint-wiki.py" <WIKI_ROOT>` aus (z.B.
`wiki/azedo/`, `wiki/cris/` — jeweils relativ zum Projekt-Root; welches Wiki ohne
Präfix gemeint ist, klärt Schritt 1 unter [Ziel-Wiki bestimmen](../SKILL.md#ziel-wiki-bestimmen)).

Das erlaubte Entity-Modell (Typen + Pflichtfelder) liest der Linter aus
`<WIKI_ROOT>/wiki-schema.json`; fehlt die Datei, gilt das Infra-Default.

Präfix-Pointer `[[<präfix>:<slug>]]` (siehe
„Hints", Referenz laut SKILL.md) löst der Linter
erst gegen die Nachbar-Wikis unter `wiki/` auf - dort wird das Ziel direkt geprüft,
ein fehlender Slug ist ein Fehler - und danach gegen die
„Remote-Config" (Referenz laut SKILL.md);
Remote-Ziele gelten ungeprüft als gültig, `--check-remotes` verifiziert sie per SSH.
Unbekanntes Präfix bleibt ein toter Link.

Prüft:
- **Orphaned pages**: Artikel, auf den kein anderer Artikel verlinkt. Links aus
  `index.md` und `log.md` zählen nicht als eingehend, die Meldung nennt sie aber
  (`… (nur aus index.md)`) - ein Artikel, den nur der Index kennt, ist im Wiki
  selbst nicht erreichbar
- **Dead links**: Wikilinks zu nicht-existierenden Artikeln - in den Artikeln als
  Fehler, in `log.md` und `index.md` als Warnung (beide liegen außerhalb von
  `wiki/` und zählen nur als Quelle, nicht als Ziel; `log.md` ist historisch,
  ein alter Eintrag darf auf einen aufgelösten Artikel zeigen)
- **Missing frontmatter**: Fehlende Pflichtfelder laut Wiki-Schema (Infra: type, kunde, date, status; Projekt-Wikis abweichend)
- **Missing index entries**: Artikel, die in keiner Index-Datei gelistet sind. Als Index
  zählen `index.md` und jede `index-*.md` im Wiki-Root; `index.md` muss es geben
- **Länge der Index-Einträge** (optional): Nur mit `index_desc_max` in der
  `wiki-schema.json`. Ist die Beschreibung hinter `- [[slug]] - ` länger, Warnung mit
  Datei und Zeile. Ein Index-Eintrag nennt den Artikel, er fasst ihn nicht zusammen -
  ohne Grenze wächst der Index zur Zweitfassung, die bei jeder Abfrage mitgelesen wird:

  ```json
  "index_desc_max": 100
  ```
- **Sortierung von `log.md`**: Tagesabschnitte `## YYYY-MM-DD` gegen die Richtung
  aus dem Kopf der Datei („älteste zuerst" bzw. „aufsteigend", sonst neueste
  zuerst) - Fehler mit Zeilennummer. Fängt den ans Ende gehängten Eintrag ab
- **Abgeschlossene Monate in `log.md`**: nur wenn es `<WIKI_ROOT>/log/` gibt, das Wiki sein
  Log also rotiert. Warnung, sobald `log.md` Tagesabschnitte aus einem früheren Monat
  enthält; `python3 "$SKILL_DIR/scripts/rotate-log.py" <WIKI_ROOT>` verschiebt sie nach
  `log/YYYY-MM.md`. Der erste Lauf des Scripts legt `log/` an und schaltet die Rotation ein
- **Naming violations**: Dateinamen die nicht der Konvention entsprechen
- **Low connectivity**: Artikel mit weniger als 3 verschiedenen Linkzielen
  (Frontmatter und Text zusammen, Wiederholungen zählen einmal); das Minimum
  ist je Typ über `min_links` in der `wiki-schema.json` einstellbar:
  `"min_links": {"entscheidung": 1}`
- **Abschnittsverweise**: `[[x]], Abschnitt Y`, `[[x]], Abschnitt „Y"` und
  `[[x]] (Y-Abschnitt)` - steht Y noch in einer Überschrift von `x`? Eine
  Kurzform reicht, wenn alle ihre Wörter in einer Überschrift vorkommen.
  Beschreibende Nennungen („Abschnitt zu `localhost` in Jails") prüft der Lint
  nicht. Nach dem Zerlegen eines Artikels ist der Link selbst nicht tot, zeigt
  aber auf den Rumpf, während das Thema längst woanders steht - diese Warnung
  ist der einzige Hinweis darauf
- **Vertrauensfelder**: Format von `verified` und `stale_after`, abgelaufene Inhalte
  (siehe „Frontmatter-Schemas", Referenz laut SKILL.md)
- **Patch-Stand ohne `stale_after`**: Fließtext mit „kein Patch", „ohne
  Sicherheitsfix", „nur Mitigation", „Backport nur" oder „nicht gepatcht" in einem
  Artikel ohne `stale_after` (Warnung, Regel in den Schreibregeln). „kein Update"
  und „kein Fix" zählen nicht - sie meinen meist etwas anderes
- **Frontmatter-Verweise** (optional): Einträge wie `tests:` oder `config:`, die
  in ihrer Prüfquelle nicht mehr vorkommen - etwa nach dem Umbenennen eines Tests.
  Nur mit `references` in der `wiki-schema.json`, ohne diesen Eintrag entfällt der Check:

  ```json
  "references": {
    "tests":  {"pattern": "def {name}\\b",     "path": "tests"},
    "config": {"pattern": "\"{name}\"\\s*:", "path": "config/settings.json"}
  }
  ```

  `path` ist relativ zum Projekt-Root, eine Datei oder ein Verzeichnis (alle Dateien
  darunter). `{name}` wird durch den Eintrag ersetzt, der Rest ist ein Regex. Ein
  nicht gefundener Eintrag ist ein Fehler, ebenso eine fehlende Prüfquelle.
- **Erlaubte Feldwerte** (optional): Nur mit `values` in der `wiki-schema.json`.
  Ein Feld mit einem Wert außerhalb der Liste ist ein Fehler, eine Liste wird
  elementweise geprüft; ob das Feld da sein muss, regeln weiter die Pflichtfelder:

  ```json
  "values": {"status": ["aktiv", "abgelöst"], "herkunft": ["benutzer", "agent"]}
  ```

- **Ablösung** (optional): Nur mit `supersede` in der `wiki-schema.json`, Regel
  unter „Aktualisieren heißt ersetzen" (Schreibregeln, Referenz laut SKILL.md). Trägt eine Entity eines der
  genannten Typen den Ablöse-Status, muss das Link-Feld einen Wikilink enthalten,
  sonst Fehler; zeigt er ins Leere, greift die Regel für tote Links:

  ```json
  "supersede": {"types": ["entscheidung"], "status": "abgelöst", "field": "abgelöst_durch"}
  ```

#### Schrumpf-Guard (`--check-shrink`)

Nach einem `compile` oder `refactor` aufrufen, **bevor** committet wird:

```
python3 "$SKILL_DIR/scripts/lint-wiki.py" --check-shrink <WIKI_ROOT>
```

Vergleicht jeden geänderten Artikel mit seiner Fassung in `git HEAD` und meldet,
was verschwunden ist: ein Frontmatter-Feld, ein `##`-Abschnitt, ein Wikilink auf
eine andere Entity. Liegt kein git-Repo über dem Wiki, aber eine SVN-Arbeitskopie,
kommt die Vergleichsfassung aus `svn cat -r BASE`. Ungetrackte Artikel und
unveränderte Dateien bleiben still, ohne beides entfällt die Prüfung mit einem
Hinweis. Ein **umgehängter** Link
zählt nicht als Verlust: steht in einem geänderten Zeilenblock statt `[[a]]` ein
neuer Link, gilt `[[a]]` als ersetzt. Beim Zerlegen eines Artikels kämen sonst
Dutzende Warnungen, die alle Absicht sind.

Gemeint ist **nicht** die Länge - Verdichten ist erwünscht, siehe
„Kürzen heißt Wörter streichen, nicht Sachverhalte" (Schreibregeln, Referenz laut SKILL.md).
Gemeint ist, was sich aufzählen lässt: dass ein Artikel beim Ueberschreiben
seine Beziehung zu einer anderen Entity oder einen ganzen Abschnitt verliert,
fällt beim Durchlesen des neuen Textes niemandem auf - dem Diff schon.

Deshalb Warnung und nicht Fehler: ob ein weggefallener Abschnitt Absicht war
oder ein Versehen, kann nur ein Mensch entscheiden. Jede Meldung einzeln
beantworten, nicht pauschal wegnicken.
