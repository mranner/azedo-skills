---
name: wiki
description: >
  LLM Wiki: Strukturierte Wissensbasis, mehrere Wikis (Server-Infra + Projekt-Doku).
  Verwaltet Wiki-Entities mit YAML-Frontmatter, Cross-Referencing und
  grep-basierter Discovery. Jedes Wiki hat sein eigenes Entity-Modell
  (Infra: Server/Service/Access/Site/Procedure; Projekt-Wikis abweichend).
  Nutze diesen Skill wenn der User Wissen ins Wiki eintragen, abfragen,
  kompilieren oder validieren will.
  Auch aktiv verwenden wenn der User sagt "trag das ins Wiki ein",
  "wiki aktualisieren", "was steht im Wiki zu X", o.ae.
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

Detaillierte Compile-Regeln (Cross-Referencing, Compile-Checkliste): @references/compilation-guide.md

Entity-Templates (Infra-Modell; fuer Projekt-Wikis gilt deren `<WIKI_ROOT>/CLAUDE.md`): @references/frontmatter-schemas.md

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

## Sicherheitsregeln

- **KEINE Klartext-Passwoerter** in Wiki-Entities — nur Verweis auf Passwortmanager
- **KEINE Private Keys oder API-Tokens**
- Vor dem Kompilieren Quellen auf Secrets scannen und diese durch Platzhalter ersetzen
- IP-Whitelist (203.0.113.10, 203.0.113.20) niemals als "zu blockieren" dokumentieren
