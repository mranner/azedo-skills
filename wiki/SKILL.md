---
name: wiki
description: >
  LLM Wiki: Strukturierte Wissensbasis, mehrere Wikis (Server-Infra + Projekt-Doku).
  Verwaltet Wiki-Entities mit YAML-Frontmatter, Cross-Referencing und
  grep-basierter Discovery. Jedes Wiki hat sein eigenes Entity-Modell
  (Infra: Server/Service/Access/Site/Procedure; Projekt-Wikis abweichend).
  Nutze diesen Skill wenn der User Wissen ins Wiki eintragen, abfragen,
  kompilieren, validieren oder aufgeblaehte Artikel entflechten will
  (audit findet lange/historienlastige Artikel, refactor baut eine Entity um).
  Auch aktiv verwenden wenn der User sagt "trag das ins Wiki ein",
  "wiki aktualisieren", "was steht im Wiki zu X", o.ae. -- bei
  "gibt es relevante Erkenntnisse fuers Wiki" bzw. "aktualisiere das Wiki"
  ist `harvest` gemeint: Kandidaten filtern und vorlegen, erst nach
  Freigabe schreiben.
  Kann Wikis eines anderen Hosts read-only per SSH abfragen (Config
  .claude/wiki-remotes.json) — nutze das, wenn der User ein Wiki abfragt,
  das auf einem anderen Server liegt (z.B. "frag das azedo-Wiki von hier aus ab").
  Trigger: /wiki.
---

# wiki -- LLM Wiki Verwaltung

Verwaltet strukturierte Wiki-Entities in mehreren Wikis (IT-Infrastruktur- und
Projekt-Dokumentation).

## Ziel-Wiki bestimmen

Alle Subcommands nehmen optional einen Wiki-Namen als Praefix an:

```
/wiki <name>:<subcommand> [args]     # z.B. /wiki cris:query "Wie laeuft Auth?"
/wiki <subcommand> [args]            # ohne name → Wiki 'azedo' (Default)
```

Vor jeder Operation:

1. Wiki-Name aus dem Argument parsen (Muster `^([a-z0-9-]+):`), sonst `azedo`.
2. Wiki-Root ableiten: `WIKI_ROOT = wiki/<name>/` — **relativ zum Projekt-Root**
   (dem Arbeitsverzeichnis, in dem der Skill laeuft; dort liegen die Wikis unter
   `wiki/`). Analog zur Projekt-`CLAUDE.md`, die das Wiki als `wiki/azedo/…`
   referenziert. Kein absoluter Home-Pfad — so bleibt der Skill portabel
   (Mac, andere Mitarbeiter, anderer Checkout-Ort).
3. Ziel aufloesen — in dieser Reihenfolge:
   a. `WIKI_ROOT` existiert lokal → **lokales Wiki** (wie gehabt, weiter mit Schritt 4).
   b. Lokal nicht vorhanden, aber `<name>` steht in `.claude/wiki-remotes.json`
      (projekt-relativ) → **Remote-Wiki, read-only**. Ab hier gilt der Abschnitt
      [Remote-Wikis](#remote-wikis-read-only): nur lesende Subcommands (`query`,
      `status`) sind erlaubt, Dateien werden per SSH gelesen.
   c. Weder lokal noch als Remote bekannt → **nicht** auf einen Home-Pfad ausweichen:
      bei einem neuen Wiki auf `/wiki init <name>` hinweisen; sonst melden, dass das
      Wiki relativ zum aktuellen Verzeichnis nicht gefunden wurde (ggf. nicht im
      Projekt-Root gestartet).
4. `<WIKI_ROOT>/CLAUDE.md` lesen — jedes Wiki hat sein eigenes Entity-Modell und
   eigene Konventionen (z.B. Infra `kunde` vs. Projekt-Wiki `projekt`). Bei einem
   Remote-Wiki diese Datei per SSH lesen (siehe Remote-Wikis).

Im Folgenden steht `<WIKI_ROOT>` fuer den in Schritt 2 ermittelten Pfad.
Die Sicherheitsregeln (keine Secrets) und das Cross-Referencing gelten
wikiuebergreifend.

## Remote-Wikis (read-only)

Ein Wiki, das auf einem **anderen Host** liegt, kann read-only abgefragt werden —
ohne lokale Kopie, ohne Sync. `query` ist reines Datei-Lesen (CLAUDE.md + index.md
lesen, Entities greppen, Treffer lesen, synthetisieren); genau dieser Read-Path
laeuft dann ueber SSH. Es wird **nie** remote ins Wiki geschrieben.

### Konfiguration: `.claude/wiki-remotes.json`

Im Projekt-Root unter `.claude/` (Tooling-Config, kein Wiki-Inhalt), projekt-relativ
aufgeloest wie `wiki/<name>/`:

```json
{
  "azedo": {
    "host": "mom",
    "path": "~/azedo.ai/wiki/azedo",
    "readonly": true
  }
}
```

- `host` — SSH-Ziel, muss per Key erreichbar sein (kein Passwort-Prompt im
  Agent-Kontext).
- `path` — Wiki-Root auf dem Host; `~` wird von der Remote-Shell expandiert.
- Enthaelt **keine Secrets** (nur Host/Pfad) → darf eingecheckt/geteilt werden.
- Optional `.claude/wiki-remotes.local.json` fuer maschinenlokale Remotes (analog zu
  Claudes `settings.local.json`) — nur bei realem Bedarf, nicht auf Vorrat.

### Lesen ueber SSH

Die User-Shell auf den Zielhosts ist `bash` (nicht die `csh` der root-Shell), daher
normales Quoting — kein `sh -c`-Wrapping noetig. `~` **innerhalb** des
remote-quotierten Strings lassen, damit die Remote-Shell expandiert; sonst expandiert
die lokale Shell auf das falsche Home:

```bash
# CLAUDE.md + Schema + Index lesen
ssh <host> "cat <path>/CLAUDE.md"
ssh <host> "cat <path>/index.md"

# Entities nach Begriffen durchsuchen, Treffer lesen
ssh <host> "grep -rl 'suchbegriff' <path>/wiki/"
ssh <host> "cat <path>/wiki/servers/fry-azedo-at.md"
```

`<host>`/`<path>` stammen aus dem Eintrag in `.claude/wiki-remotes.json`. Die Antwort
wird **lokal** aus den gelesenen Inhalten synthetisiert.

### Read-only erzwungen

Schreibende Subcommands (`ingest`, `compile`, `init`) sind fuer Remote-Wikis **nicht**
erlaubt — mit klarem Hinweis abbrechen, nichts remote schreiben. Neue Erkenntnisse
fuer ein Remote-Wiki werden nicht remote geschrieben, sondern mit `<remote>:handoff`
(siehe [handoff](#handoff)) als lokale Note erzeugt und **manuell auf dem Zielhost**
eingepflegt (dort lokal `ingest`/`compile`/`lint`). Read-only ist damit *by
construction*, nicht per Konvention.

### Auf Remote-Entities verweisen (Hints)

Aus einem **lokalen** Wiki kann man auf eine Entity in einem Remote-Wiki verweisen —
mit einem Wikilink samt Remote-Praefix (konsistent zur `<name>:`-Subcommand-Syntax):

```
Details zum Host im Infra-Wiki: [[azedo:fry-azedo-at]]
```

- Ist das Praefix (`azedo`) ein Key in `.claude/wiki-remotes.json`, wertet der Linter
  den Link als **gueltigen Remote-Pointer** — kein toter Link, keine
  „Waise"-Folgefehler. Das Ziel wird im Default **nicht** geprueft (offline-sicher).
- Unbekanntes Praefix (kein Remote, kein lokaler Slug) → weiterhin **toter Link**.
- `python3 "$SKILL_DIR/scripts/lint-wiki.py" --check-remotes <WIKI_ROOT>` verifiziert
  die Existenz der Remote-Ziele on demand per SSH.
- Der Verweis ist **einseitig**: das Remote-Wiki weiss nichts davon. Bestehende lokale
  `[[slug]]` ohne Praefix bleiben unveraendert.

Bei `query` darf ein solcher Pointer per SSH aufgeloest werden (Ziel-Datei lesen,
Antwort anreichern) — siehe Lesen ueber SSH oben.

## Subcommands

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
[Remote-Wikis](#remote-wikis-read-only)), abbrechen: Remote ist read-only, neue
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
[Remote-Wikis](#remote-wikis-read-only)), abbrechen: Remote ist read-only.

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

**Vor Schritt 2 gelten die [Schreibregeln](#schreibregeln)** - Aufnahmefilter
(gehört es überhaupt hinein), Dichtegebot und „aktualisieren heisst ersetzen".

Detaillierte Compile-Regeln (Cross-Referencing, Compile-Checkliste): @references/compilation-guide.md

Entity-Templates (Infra-Modell; fuer Projekt-Wikis gilt deren `<WIKI_ROOT>/CLAUDE.md`): @references/frontmatter-schemas.md

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
3. **Jeden Kandidaten durch den [Aufnahmefilter](#aufnahmefilter-gehört-das-überhaupt-hinein)
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

Für die Einträge selbst gelten die [Schreibregeln](#schreibregeln) - vor allem
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

Bei einem **Remote-Wiki** dieselben Schritte, aber `index.md` und Entities per SSH
lesen statt lokal (`ssh <host> "cat/grep …"`, siehe
[Remote-Wikis](#remote-wikis-read-only)). Schritt 6 (Speichern) entfaellt — Remote
ist read-only.

### lint

Wiki auf strukturelle Probleme pruefen.

```
/wiki lint
```

Fuehrt `python3 "$SKILL_DIR/scripts/lint-wiki.py" <WIKI_ROOT>` aus (z.B.
`wiki/azedo/` fuer das Default-Wiki, `wiki/cris/` fuer `cris` — jeweils relativ zum
Projekt-Root).

Das erlaubte Entity-Modell (Typen + Pflichtfelder) liest der Linter aus
`<WIKI_ROOT>/wiki-schema.json`; fehlt die Datei, gilt das Infra-Default.

Remote-Pointer `[[<remote>:<slug>]]` (siehe [Remote-Wikis](#remote-wikis-read-only))
gelten als gueltig, wenn `<remote>` in `.claude/wiki-remotes.json` steht — sonst als
toter Link. Mit `--check-remotes` verifiziert der Linter die Remote-Ziele per SSH.

Prueft:
- **Orphaned pages**: Artikel ohne eingehende Links
- **Dead links**: Wikilinks zu nicht-existierenden Artikeln
- **Missing frontmatter**: Fehlende Pflichtfelder laut Wiki-Schema (Infra: type, kunde, date, status; Projekt-Wikis abweichend)
- **Missing index entries**: Artikel die nicht in index.md gelistet sind
- **Naming violations**: Dateinamen die nicht der Konvention entsprechen
- **Low connectivity**: Artikel mit weniger als 3 Wikilinks

### audit

Das ganze Wiki nach aufgeblähten und historienlastigen Artikeln durchsuchen.

```
/wiki audit                       # ganzes Wiki, Top 10
/wiki audit --type service        # nur einen Entity-Typ
/wiki audit --path procedures     # nur einen Unterpfad
/wiki audit --all                 # alle Auffälligen, nicht nur Top 10
```

Führt `python3 "$SKILL_DIR/scripts/audit-wiki.py" [optionen] <WIKI_ROOT>` aus.
Zusätzlich gibt es `--top <n>` und `--json` (maschinenlesbar, für die Auswahl der
nächsten `refactor`-Kandidaten).

**Abgrenzung zu `lint`:** Der Linter meldet Fehler und liefert Exit 1. `audit`
bewertet — es gibt keine falschen Artikel, nur auffällige, deshalb immer Exit 0.
Ein Audit-Befund ist ein Kandidat, kein Auftrag.

Gemessen wird je Artikel:

- **LANG** — Zeilen relativ zum p90 des **eigenen Entity-Typs**, nicht absolut.
  Eine access-Entity mit 90 Zeilen ist auffällig, eine procedure mit 90 nicht.
  Untergrenzen je Typ verhindern Fehlalarme in einem jungen Wiki.
- **HISTORIE** — Dichte von Datumsangaben, „Session", CR-Nummern und Wörtern wie
  „inzwischen"/„früher" im Fliesstext. Der Abschnitt `## Quellen` ist ausgenommen:
  dort ist die Datierung Konvention und kein Ballast.
- **PROZEDURAL** — Codeblöcke und FALSCH/RICHTIG-Rezepte in einer server-,
  service-, access- oder site-Entity. Das gehört in eine procedure.
- **DOMINANT** — ein Abschnitt frisst den Grossteil der Datei.
- **TIEF** — viele H3 oder Verschachtelung ab H4.

Die Ausgabe zeigt **Rohwerte, nicht nur einen Score** — der Score ordnet nur die
Rangfolge, entschieden wird an den Rohwerten. Zu jedem auffälligen Artikel nennt
das Script bestehende Procedures als mögliche Verschiebeziele (Wortüberlappung
Überschrift ↔ Slug, ausdrücklich **ungeprüft**).

Bei einem **Remote-Wiki** entfällt `audit` — es läuft nur auf einer lokalen Kopie.

### refactor

Eine einzelne Entity abschnittsweise analysieren und einen Umbauvorschlag
vorlegen. **Schreibt nichts** ohne ausdrückliche Freigabe.

```
/wiki refactor <slug>             # z.B. /wiki refactor mail-azedo-at
```

Immer **eine** Entity pro Aufruf — nie im Batch über die Audit-Top-N. Der
Vorschlag muss überschaubar bleiben, sonst wird die Freigabe zur Formsache.

Ablauf:

1. `<WIKI_ROOT>/CLAUDE.md` und den Artikel **vollständig** lesen.
2. `audit` für diesen Artikel laufen lassen (`--json`), um die Befunde und die
   vorgeschlagenen Verschiebeziele zu haben.
3. Genannte Ziel-Procedures lesen — steht der Inhalt dort schon?
4. **Jeden** H2/H3-Abschnitt in genau eine der vier Kategorien einordnen:

   | Kategorie | Bedeutung | Aktion im Vorschlag |
   |---|---|---|
   | `BLEIBT` | beschreibt den Ist-Zustand des Systems | unverändert |
   | `→ PROCEDURE` | operative Anleitung | in bestehende Procedure X oder neue anlegen |
   | `HISTORIE` | Zustand, der nicht mehr gilt | streichen, einzeilig unter `## Quellen` |
   | `DUPLIKAT` | steht schon in Artikel Y | streichen, Wikilink setzen |
   | `→ TASK` | offene Aufgabe, keine Doku | ins Ticketsystem, aus dem Wiki raus |

5. Vorschlag als Tabelle im Chat ausgeben, mit Zeilenumfang je Abschnitt und der
   erwarteten Restlänge. Nichts schreiben.
6. Erst **nach Freigabe** umsetzen, und dann vollständig: Zielartikel anlegen
   bzw. ergänzen, Wikilink im Restartikel setzen, `index.md` ergänzen,
   Frontmatter-Datum aktualisieren, Zeile in `log.md`, danach `/wiki lint`.

**Die Historie-Regel.** Nicht „alt" ist das Kriterium, sondern „gilt nicht mehr".
Ein datierter Beleg („verifiziert 2026-07-28 auf [[fry-azedo-at]]") ist eine
zeitlose Begründung und **bleibt** — er sieht nur aus wie Historie. Gestrichen
wird ein beschriebener Zustand, den es so nicht mehr gibt. Im Zweifel: der
Vorschlag markiert den Abschnitt als unklar und fragt, statt ihn einzuordnen.

Ersatzlos gelöscht wird nur, was der aktuelle Stand **widerlegt**. Alles andere
wandert einzeilig unter `## Quellen` oder nach `log.md`. Das Argument fürs
Streichen ist nie „ist alt", sondern dass git die Fassung ohnehin vorhält.

**Arbeitslisten sind keine Dokumentation.** Aufzählungen der Form „X steht noch
aus", „bei Gelegenheit auch für Y" beschreiben nicht den Server, sondern die
eigene Absicht. Sie veralten still (niemand pflegt sie nach, wenn die Arbeit
getan ist) und lesen sich später wie ein Ist-Zustand. Solche Abschnitte
bekommen `→ TASK`: der Vorschlag nennt sie, den Ticket-Eintrag macht der User,
und aus dem Artikel fliegen sie raus. Ein Satz „offene Punkte siehe Ticket
CR####" darf stehen bleiben, die Liste selbst nicht.

Für **Remote-Wikis** nicht erlaubt (schreibend) — dort `<remote>:handoff` nutzen.

### status

Ueberblick ueber den Wiki-Zustand.

```
/wiki status
```

Zeigt:
- Anzahl Entities pro Typ
- Letzte Aenderungen (aus log.md)
- Offene Lint-Probleme (falls vorhanden)

Bei einem **Remote-Wiki** die Quellen per SSH lesen (`ssh <host> "cat/grep …"`, siehe
[Remote-Wikis](#remote-wikis-read-only)); Lint entfaellt (laeuft nur auf lokaler
Kopie).

### handoff

Erzeugt aus lokal erarbeiteten Erkenntnissen eine **ingest-fertige Note** fuer ein
**Remote-Wiki**, die der User **manuell** auf dem Zielhost einspielt. Schreibt nichts
remote — der asynchrone, menschlich vermittelte Gegenpart zum read-only `query`.

```
/wiki <remote>:handoff "<was gelernt wurde>"
```

Nur mit Remote-Praefix sinnvoll (das Ziel-Wiki liegt auf einem anderen Host). Fuer ein
lokales Wiki direkt `ingest`/`compile` nutzen.

Workflow:
1. Ziel-Wiki per SSH lesen (Baustein-1-Read, siehe
   [Remote-Wikis](#remote-wikis-read-only)): `wiki-schema.json` (Pflichtfelder +
   erlaubte Typen) und `index.md`. Damit kennst du die exakte Zielform **und** ob die
   Entity schon existiert.
2. Entity-Slug + Typ bestimmen. Existiert der Slug remote (via `index.md` bzw.
   `ssh <host> "grep -rl …"`)? → `mode: update` (konkret benennen, welches Feld
   ergaenzt/geaendert wird, keine Dublette). Sonst → `mode: new` (vollstaendiger
   Entity-Draft im Zielschema).
3. Note nach `.claude/wiki-outbox/<remote>-<slug>.md` schreiben (Verzeichnis anlegen,
   falls noetig). Secrets-Regeln gelten wie im Wiki (keine Passwoerter/Keys).
4. **Nicht** remote schreiben. Am Ende dem User die Transport-Optionen nennen — er
   entscheidet, Transport ist ausdruecklich user-ausgeloest:
   - **Kanboard-Attachment** (`/kanboard`): Note an einen Task haengen (Review-Queue).
   - **scp** nach `<host>:<path>/raw/inbox/` (Pfad aus `.claude/wiki-remotes.json`).
   - **Mail** (`/swaks`) als Anhang.

Format (Kopf-Frontmatter + Body im Zielschema; Werte sind Beispiele, `source-date` =
heutiges Datum, `target-host`/Pfad aus `.claude/wiki-remotes.json`):

```markdown
---
target-wiki: azedo
target-host: mom
entity: fry-azedo-at
type: server
mode: update            # oder: new
source-project: acme.ai
source-date: 2026-07-07
---

# Update: fry-azedo-at

**Aenderung:** … Kontext …

<Entity-Body bzw. konkrete Feld-Aenderungen im Zielschema>
```

Auf dem Zielhost spielt der User die Note ueber das **bestehende** `ingest` (bzw.
Ablage in `raw/inbox/`) + `compile` + `lint` ein — kein neuer Code auf Host-B-Seite
noetig, der Mensch ist der Gate-Keeper. Ein `scp` nach `raw/inbox/` ist **kein**
Schreiben ins Wiki: die Entity entsteht erst durch das lokale `ingest` auf dem
Zielhost.

> Nicht verwechseln mit dem generischen `/handoff`-Skill (Konversations-Uebergabe) —
> dies hier ist ein **Wiki-Subcommand** und erzeugt eine Wiki-Outbox-Note.

## Schreibregeln

Gelten für **jedes** Schreiben ins Wiki (`compile`, `refactor`) und für `log.md`,
in jedem Wiki. „Gegenstand" ist das, was der Artikel beschreibt - ein Server, ein
Modul, eine Schnittstelle, ein Ablauf.

### Aufnahmefilter: gehört das überhaupt hinein?

Vier Fragen, **alle** müssen mit Ja beantwortet sein:

1. **Gilt es in drei Monaten noch?** Ein Zwischenstand, ein „aktuell läuft noch"
   oder ein Vorhaben gehört ins Ticket, nicht in einen Artikel.
2. **Kostet es jemanden Zeit, der es nicht weiss?** Wenn niemand darüber
   stolpern kann, ist es keine Erkenntnis, sondern eine Notiz.
3. **Lässt es sich *nicht* in einer halben Minute am Gegenstand selbst
   ablesen?** Was `--help`, ein Blick in die Datei, `systemctl status` oder ein
   Testlauf sofort zeigen, braucht keinen Artikel. Aufnahmewürdig ist, was man
   dort **nicht** sieht: die Reihenfolge, die entscheidet; das Feld, das anders
   heisst als es wirkt; der stille Fehlschlag.
4. **Steht es nicht schon in einem anderen Artikel?** Sonst dort ergänzen und
   von hier verlinken - nicht zweitschreiben.

Grundsätzlich **nicht** aufgenommen: transiente Fehler (Build, Netz,
Paketquelle), persönliche Vorlieben und Arbeitsweisen, Kundendaten, und der
Vorgang selbst statt seines Ergebnisses - der steht im Ticket.

Im Zweifel **fragen statt aufnehmen**. Ein zu voller Artikel kostet jeden
späteren Leser Zeit; eine fehlende Erkenntnis kostet einmal eine Rückfrage.

### Dichtegebot: Behauptung, Folge, Beleg

Ein Befund besteht aus drei Teilen: **was gilt**, **was daraus folgt**, und
**womit man es prüft**. Der Weg zur Erkenntnis gehört nicht dazu.

```
Zu weit:  "Aufgefallen ist das beim Durchsehen der Logs am 15.08. - zunächst
           sah es nach X aus, erst der Vergleich mit Y zeigte, dass in
           Wirklichkeit Z zutrifft, weil ..."

Dicht:    "Z gilt, nicht X. Folge: <Konsequenz>.
           Prüfen mit `<befehl>`."
```

- **Registermarker streichen.** „Aufgefallen ist…", „Sichtbar wurde…", „Der
  Ablauf lässt sich… ablesen", „Ausschlaggebend war…", „Zunächst… erst dann…"
  leiten alle eine Erzählung ein. Wo einer steht, gehört der Absatz gekürzt.
- **Messwerte und Herleitung nach `## Quellen`.** Im Artikel steht das Ergebnis,
  ein Satz. Die 7-Tage-Messung, die Fallzahlen und der Irrweg stehen unten.
- **Aufzählung wird Liste oder Tabelle**, nicht Absatz.
- **Kein Datum in einer Überschrift.** Wer „Umbau 2026-08-15" oder „Stand
  <Datum>" als Überschrift braucht, schreibt gerade ein Logbuch statt eines
  Artikels. Ein Datum im Fliesstext („seit 2026-08-15") ist in Ordnung.

### Aktualisieren heisst ersetzen

Die häufigste Ursache aufgeblähter Artikel ist die naheliegende Handlung:
anhängen. Beim Aktualisieren wird die **alte Aussage überschrieben**, nicht
danebengestellt - die Vorfassung hält die Versionsverwaltung. Nur wenn der alte
Zustand für das Verständnis des neuen nötig ist, bleibt er, und dann als
Nebensatz.

### Ein Befund gehört an genau eine Stelle

Prüffrage beim Schreiben: **Würde das jemand suchen, der diesen Gegenstand gar
nicht kennt?**

- Ja → wiederkehrendes Verfahren, gehört in einen eigenen Artikel dafür (im
  Infra-Wiki: `procedure`), und der Gegenstand verlinkt darauf.
- Nein → gehört zum Gegenstand selbst.

Diese Entscheidung fällt **beim Schreiben**. Wird sie vertagt, landet beides im
Gegenstands-Artikel und muss später per `refactor` getrennt werden.

## Sicherheitsregeln

- **KEINE Klartext-Passwoerter** in Wiki-Entities — nur Verweis auf Passwortmanager
- **KEINE Private Keys oder API-Tokens**
- Vor dem Kompilieren Quellen auf Secrets scannen und diese durch Platzhalter ersetzen
- Geschuetzte Verwaltungs- und Kundenzugaenge (IP-Whitelist) niemals als "zu blockieren"
  dokumentieren — die konkreten Adressen stehen ausserhalb des Repos
