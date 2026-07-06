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
2. Wiki-Root ableiten: `WIKI_ROOT = ~/azedo.ai/wiki/<name>/`.
3. Existenz von `WIKI_ROOT` pruefen. Fehlt es → Hinweis auf `/wiki init <name>`.
4. `WIKI_ROOT/CLAUDE.md` lesen — jedes Wiki hat sein eigenes Entity-Modell und
   eigene Konventionen (z.B. Infra `kunde` vs. Projekt-Wiki `projekt`).

Im Folgenden steht `<WIKI_ROOT>` fuer den in Schritt 2 ermittelten Pfad.
Die Sicherheitsregeln (keine Secrets) und das Cross-Referencing gelten
wikiuebergreifend.

## Subcommands

### init

Neues Wiki-Unterverzeichnis anlegen.

```
/wiki init <name>
```

Erstellt die Standard-Verzeichnisstruktur unter `~/azedo.ai/wiki/<name>/` und legt
eine Default-`wiki-schema.json` (Infra-Modell) an, damit das neue Wiki sofort
lintbar ist:

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

### lint

Wiki auf strukturelle Probleme pruefen.

```
/wiki lint
```

Fuehrt `python3 "$SKILL_DIR/scripts/lint-wiki.py" <WIKI_ROOT>` aus (z.B.
`~/azedo.ai/wiki/azedo/` fuer das Default-Wiki, `~/azedo.ai/wiki/cris/` fuer `cris`).

Das erlaubte Entity-Modell (Typen + Pflichtfelder) liest der Linter aus
`<WIKI_ROOT>/wiki-schema.json`; fehlt die Datei, gilt das Infra-Default.

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

## Sicherheitsregeln

- **KEINE Klartext-Passwoerter** in Wiki-Entities — nur Verweis auf Passwortmanager
- **KEINE Private Keys oder API-Tokens**
- Vor dem Kompilieren Quellen auf Secrets scannen und diese durch Platzhalter ersetzen
- IP-Whitelist (203.0.113.10, 203.0.113.20) niemals als "zu blockieren" dokumentieren
