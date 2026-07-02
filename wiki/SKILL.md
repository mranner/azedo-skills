---
name: wiki
description: >
  LLM Wiki: Strukturierte Wissensbasis fuer Server-Infra-Dokumentation.
  Verwaltet Wiki-Entities (Server, Service, Access, Site, Procedure) mit
  YAML-Frontmatter, Cross-Referencing und grep-basierter Discovery.
  Nutze diesen Skill wenn der User Wissen ins Wiki eintragen, abfragen,
  kompilieren oder validieren will.
  Auch aktiv verwenden wenn der User sagt "trag das ins Wiki ein",
  "wiki aktualisieren", "was steht im Wiki zu X", o.ae.
  Trigger: /wiki.
---

# wiki -- LLM Wiki Verwaltung

Verwaltet strukturierte Wiki-Entities fuer IT-Infrastruktur-Dokumentation.

Wiki-Verzeichnis: `~/azedo.ai/wiki/azedo/`

Vor jeder Operation die Wiki-CLAUDE.md lesen: `~/azedo.ai/wiki/azedo/CLAUDE.md`

## Subcommands

### init

Neues Wiki-Unterverzeichnis anlegen (fuer zukuenftige weitere Wikis).

```
/wiki init <name>
```

Erstellt die Standard-Verzeichnisstruktur unter `~/azedo.ai/wiki/<name>/`.

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
1. Quelle lesen und Entity-Typen identifizieren (Server, Service, Access, Site, Procedure)
2. Fuer jeden identifizierten Entity:
   a. Pruefen ob Entity bereits existiert (Dateiname-Check)
   b. Wenn ja: bestehenden Artikel lesen, dann aktualisieren
   c. Wenn nein: neuen Artikel mit vollstaendigem Frontmatter anlegen
3. Minimum 3 Wikilinks pro Artikel setzen
4. `index.md` aktualisieren (Entity in passende Kunden-Sektion eintragen)
5. Backlink-Audit: bestehende Artikel durchsuchen, die den neuen Entity erwaehnen sollten
6. Eintrag in `log.md`: `COMPILE: <quelle> → <entity1>, <entity2>, ...`

Detaillierte Compile-Regeln: @references/compilation-guide.md

Entity-Templates: @references/frontmatter-schemas.md

### query

Frage gegen das Wiki beantworten.

```
/wiki query <frage>
```

Workflow:
1. `index.md` lesen fuer Ueberblick
2. Relevante Entities per Frontmatter-grep identifizieren (z.B. `grep -r "type: server" wiki/`)
3. Gefundene Artikel lesen
4. Backlinks in Artikeln folgen fuer verwandte Informationen
5. Antwort mit Wikilink-Zitaten formulieren (`[[entity-slug]]`)
6. Optional: Antwort als Query-Output in `wiki/queries/` speichern

### lint

Wiki auf strukturelle Probleme pruefen.

```
/wiki lint
```

Fuehrt `python3.11 "$SKILL_DIR/scripts/lint-wiki.py" ~/azedo.ai/wiki/azedo/` aus.

Prueft:
- **Orphaned pages**: Artikel ohne eingehende Links
- **Dead links**: Wikilinks zu nicht-existierenden Artikeln
- **Missing frontmatter**: Fehlende Pflichtfelder (type, kunde, date, status)
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
