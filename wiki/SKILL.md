---
name: wiki
description: >
  LLM Wiki für Server-Infra und Projekt-Doku. Vor jedem Schreiben ins Wiki und
  vor jeder Antwort auf die Frage, ob etwas ins Wiki gehört, diesen Skill laden -
  er führt Aufnahmefilter und Vorlage ("gibt es relevante Erkenntnisse fürs
  Wiki", "trag das ins Wiki ein"). Vor jedem Eingriff an Server oder Service
  zuerst nachschlagen ("was steht im Wiki zu X"). Außerdem validieren,
  entflechten und Wikis anderer Hosts read-only per SSH abfragen. Trigger: /wiki.
---

# wiki -- LLM Wiki Verwaltung

Verwaltet strukturierte Wiki-Entities in mehreren Wikis (IT-Infrastruktur- und
Projekt-Dokumentation).

Zwei Pfade sind auseinanderzuhalten und werden im Folgenden konsequent
unterschieden:

| Platzhalter | Was | Woher |
|---|---|---|
| `$SKILL_DIR` | Base Directory dieses Skills (dort wo diese SKILL.md liegt) | üblicherweise unter `~/.claude/skills/wiki` -- der Skill ist **global** installiert, nicht im Projekt |
| `<WIKI_ROOT>` | die Wiki-**Daten** | projekt-relativ, siehe [Ziel-Wiki bestimmen](#ziel-wiki-bestimmen) |

Die Scripts des Skills werden immer über `$SKILL_DIR` aufgerufen, das Wiki
selbst immer projekt-relativ:

```
python3 "$SKILL_DIR/scripts/lint-wiki.py" <WIKI_ROOT>
```

Ein Aufruf als `.claude/skills/wiki/scripts/…` (projekt-relativ) scheitert mit
`No such file or directory` -- und sieht damit aus wie ein fehlendes Script,
nicht wie ein falscher Pfad.

## Ziel-Wiki bestimmen

Alle Subcommands nehmen optional einen Wiki-Namen als Präfix an:

```
/wiki <name>:<subcommand> [args]     # z.B. /wiki cris:query "Wie läuft Auth?"
/wiki <subcommand> [args]            # ohne name → Default, siehe Schritt 1
```

Vor jeder Operation:

1. Wiki-Name aus dem Argument parsen (Muster `^([a-z0-9-]+):`). **Ohne Präfix
   den Default ableiten, nicht raten** — `wiki/` im Projekt-Root auflisten:

   | Lage | Verhalten |
   |---|---|
   | genau **ein** lokales Wiki | das ist der Default, ohne Rückfrage |
   | **mehrere** lokale Wikis | die Namen nennen und nachfragen, keins wählen |
   | **keins** | auf `/wiki init <name>` hinweisen |

2. Wiki-Root ableiten: `WIKI_ROOT = wiki/<name>/` — **relativ zum Projekt-Root**
   (dem Arbeitsverzeichnis, in dem der Skill läuft; dort liegen die Wikis unter
   `wiki/`). Kein absoluter Home-Pfad - der Skill läuft auch auf dem Mac und
   in anderen Checkouts.
3. Ziel auflösen — in dieser Reihenfolge:
   a. `WIKI_ROOT` existiert lokal → **lokales Wiki** (wie gehabt, weiter mit Schritt 4).
   b. Lokal nicht vorhanden, aber `<name>` steht in der Remote-Config
      ([`wiki-remotes.json`](references/remote-wikis.md#konfiguration-wiki-remotesjson);
      `python3 "$SKILL_DIR/scripts/wiki_remotes.py" list` zeigt sie mit Herkunft)
      → **Remote-Wiki, read-only**. Ab hier gilt der Abschnitt
      [Remote-Wikis](references/remote-wikis.md): nur lesende Subcommands (`query`,
      `status`) sind erlaubt, Dateien werden per SSH gelesen.
   c. Weder lokal noch als Remote bekannt → **nicht** auf einen Home-Pfad ausweichen:
      bei einem neuen Wiki auf `/wiki init <name>` hinweisen; sonst melden, dass das
      Wiki relativ zum aktuellen Verzeichnis nicht gefunden wurde (ggf. nicht im
      Projekt-Root gestartet).
4. `<WIKI_ROOT>/CLAUDE.md` lesen — jedes Wiki hat sein eigenes Entity-Modell und
   eigene Konventionen (z.B. Infra `kunde` vs. Projekt-Wiki `projekt`). Bei einem
   Remote-Wiki diese Datei per SSH lesen (siehe Remote-Wikis).

Im Folgenden steht `<WIKI_ROOT>` für den in Schritt 2 ermittelten Pfad.
Die Sicherheitsregeln (keine Secrets) und das Cross-Referencing gelten
wikiübergreifend: ein `[[<präfix>:<slug>]]` zeigt in derselben Schreibweise auf ein
Nachbar-Wiki unter `wiki/` wie auf ein Remote-Wiki - siehe
[Hints](references/remote-wikis.md#auf-entities-anderer-wikis-verweisen-hints).

## Subcommands

Der Anlass bestimmt den Subcommand:

| Anlass | Subcommand |
|---|---|
| „was steht im Wiki zu X", vor einem Eingriff an Server oder Service | `query` |
| „gibt es Erkenntnisse fürs Wiki", „aktualisiere das Wiki" | `harvest`: Kandidaten filtern, Vorlage ausgeben, schreiben erst nach Freigabe |
| „trag ins Wiki ein, dass …" - der Auftrag nennt den Befund | `harvest` mit direktem Auftrag: der Auftrag ist die Freigabe, nach dem Aufnahmefilter schreiben, ohne Vorlage |
| eine Datei oder Quelle wird übergeben | `ingest`, danach `compile` |

`query` und `harvest` führt das Modell selbst aus, es gibt dafür **kein Script**: `query` greppt
nach den Begriffen der Frage, liest den Index nur für den Überblick und folgt Backlinks; `harvest` sammelt Kandidaten,
schickt sie durch den Aufnahmefilter und legt sie vor. Der Ablauf steht in
`references/subcommands.md`. Scripts gibt es für `lint` und `audit` -
`python3 "$SKILL_DIR/scripts/lint-wiki.py" <WIKI_ROOT>` und
`python3 "$SKILL_DIR/scripts/audit-wiki.py" <WIKI_ROOT>` - sowie für die
Remote-Config (`scripts/wiki_remotes.py list` / `add`, siehe
[Remote-Wikis](references/remote-wikis.md#remotes-anzeigen-und-eintragen)).

Vollständige Referenz daneben, bei Bedarf lesen:

| Datei | Inhalt |
|---|---|
| `references/subcommands.md` | `init`, `ingest`, `compile`, `harvest`, `query`, `lint` |
| `references/pflege.md` | `audit` (aufgeblähte Artikel finden), `refactor` (Entity umbauen, verdichten statt verschieben), `status`, `handoff` |
| `references/compilation-guide.md` | Compile-Regeln: Source-first, Entity-Extraktion, Duplikate, Cross-Referencing, Widersprüche, Compile-Checkliste |
| `references/frontmatter-schemas.md` | Entity-Templates und Pflichtfelder je Typ (Infra-Modell), `verified`/`stale_after` |
| `references/schreibregeln.md` | Aufnahmefilter, Dichtegebot, ersetzen statt anhängen, Ablösung, `stale_after` beim Patch-Stand, Ablage in `log.md` |
| `references/remote-wikis.md` | Wikis anderer Hosts read-only per SSH abfragen, Konfiguration, Hints auf Entities anderer Wikis (Nachbar-Wiki wie Remote) |

## Schreibregeln

Vor **jedem** Schreiben `references/schreibregeln.md` vollständig lesen - bei `compile`,
`refactor` und vor einem Eintrag in `log.md`, bei `harvest` schon vor dem Filtern der
Kandidaten, in jedem Wiki. Dort stehen der
Aufnahmefilter (gehört es überhaupt hinein), das Dichtegebot und „aktualisieren heißt
ersetzen". Geschrieben wird erst, wenn die Datei in dieser Sitzung gelesen ist; `query`,
`lint`, `audit` und `status` brauchen sie nicht.

## Sicherheitsregeln

- **KEINE Klartext-Passwörter** in Wiki-Entities — nur Verweis auf Passwortmanager
- **KEINE Private Keys oder API-Tokens**
- Vor dem Kompilieren Quellen auf Secrets scannen und diese durch Platzhalter ersetzen
- Geschützte Verwaltungs- und Kundenzugänge (IP-Whitelist) niemals als "zu blockieren"
  dokumentieren — die konkreten Adressen stehen außerhalb des Repos
