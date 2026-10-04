---
name: wiki
description: >
  LLM Wiki: strukturierte Wissensbasis über mehrere Wikis (Server-Infra und
  Projekt-Doku), Entities mit YAML-Frontmatter und grep-basierter Discovery.
  Wissen abfragen, eintragen, kompilieren, validieren, aufgeblähte Artikel
  entflechten; Wikis auf anderen Hosts read-only per SSH abfragen.
  Auch bei "trag das ins Wiki ein", "was steht im Wiki zu X", "wiki
  aktualisieren", "gibt es relevante Erkenntnisse fürs Wiki".
  Ebenso vor dem Eingriff an einem Server oder Service - Deployment,
  Config-Änderung, Fehlersuche: zuerst "query" statt den Host abzuklopfen.
  Trigger: /wiki.
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

Häufigster Fall ist `query` (nachschlagen) und `harvest` (Erkenntnisse aufnehmen -
Kandidaten filtern, vorlegen, erst nach Freigabe schreiben):

```
/wiki query <frage>
/wiki harvest [thema]
```

Beide führt das Modell selbst aus, es gibt dafür **kein Script**: `query` liest
`index.md`, greppt Frontmatter und folgt Backlinks; `harvest` sammelt Kandidaten,
schickt sie durch den Aufnahmefilter und legt sie vor. Der Ablauf steht in
`references/subcommands.md`. Scripts gibt es nur für `lint` und `audit` -
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
| `references/remote-wikis.md` | Wikis anderer Hosts read-only per SSH abfragen, Konfiguration, Hints auf Entities anderer Wikis (Nachbar-Wiki wie Remote) |

## Schreibregeln

Gelten für **jedes** Schreiben ins Wiki (`compile`, `refactor`) und für `log.md`,
in jedem Wiki. „Gegenstand" ist das, was der Artikel beschreibt - ein Server, ein
Modul, eine Schnittstelle, ein Ablauf.

**Wohin ein Eintrag in `log.md` gehört, steht im Kopf der Datei** - vor dem
Schreiben lesen, nicht blind ans Ende hängen. Ist das Log „neueste zuerst"
sortiert, landet ein angehängter Eintrag unter dem ältesten Tag.

### Aufnahmefilter: gehört das überhaupt hinein?

Vier Fragen, **alle** müssen mit Ja beantwortet sein:

1. **Gilt es in drei Monaten noch?** Ein Zwischenstand, ein „aktuell läuft noch"
   oder ein Vorhaben gehört ins Ticket, nicht in einen Artikel.
2. **Kostet es jemanden Zeit, der es nicht weiß?** Wenn niemand darüber
   stolpern kann, ist es keine Erkenntnis, sondern eine Notiz.
3. **Lässt es sich *nicht* in einer halben Minute am Gegenstand selbst
   ablesen?** Was `--help`, ein Blick in die Datei, `systemctl status` oder ein
   Testlauf sofort zeigen, braucht keinen Artikel. Aufnahmewürdig ist, was man
   dort **nicht** sieht: die Reihenfolge, die entscheidet; das Feld, das anders
   heißt als es wirkt; der stille Fehlschlag.
4. **Steht es nicht schon in einem anderen Artikel?** Sonst dort ergänzen und
   von hier verlinken - nicht zweitschreiben.

Grundsätzlich **nicht** aufgenommen: transiente Fehler (Build, Netz,
Paketquelle), persönliche Vorlieben und Arbeitsweisen, Kundendaten, Namen
einzelner Mitarbeiter (auch Kanboard- oder CRIS-Usernamen) dort, wo eine Rolle
oder eine Datensatz-ID den Beleg genauso trägt, und der Vorgang selbst statt
seines Ergebnisses - der steht im Ticket.

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
- **Herleitung wird gestrichen, nicht verlagert.** Im Artikel steht das
  Ergebnis, ein Satz; der Irrweg dorthin gar nicht. Ein Messwert bleibt nur,
  wenn er die Aussage trägt - dann im Fachabsatz, mit Host und Datum im
  Nebensatz („verifiziert 2026-07-28 auf [[fry-azedo-at]]").
- **`## Quellen` ist keine Ablage.** Der Abschnitt ist optional und nimmt nur
  echte Rohquellen auf: die Datei unter `raw/`, ein externes Dokument, ein
  Ticket. Gibt es keine, entfällt er. Eine Liste der eigenen Sessions
  („Session 2026-07-05: …") ist ein Arbeitsprotokoll und fällt unter den
  Aufnahmefilter - wann etwas aufgeschrieben wurde, hält git.
- **Aufzählung wird Liste oder Tabelle**, nicht Absatz.
- **Kein Datum in einer Überschrift.** Wer „Umbau 2026-08-15" oder „Stand
  <Datum>" als Überschrift braucht, schreibt gerade ein Logbuch statt eines
  Artikels. Ein Datum im Fließtext („seit 2026-08-15") ist in Ordnung.

### Kürzen heißt Wörter streichen, nicht Sachverhalte

Knapp ist der Artikel in der Formulierung, nicht im Inhalt: Bedingung, Sonderfall
und Folge gehören vollständig hinein. Wer eine davon weglässt, macht den Artikel
nicht dichter, sondern falsch - und die Lücke ist dem Leser nicht anzusehen.

Der Aufnahmefilter entscheidet, **ob** ein Sachverhalt in den Artikel kommt.
Ist er drin, steht er ganz da.

### Aktualisieren heißt ersetzen

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

- **KEINE Klartext-Passwörter** in Wiki-Entities — nur Verweis auf Passwortmanager
- **KEINE Private Keys oder API-Tokens**
- Vor dem Kompilieren Quellen auf Secrets scannen und diese durch Platzhalter ersetzen
- Geschützte Verwaltungs- und Kundenzugänge (IP-Whitelist) niemals als "zu blockieren"
  dokumentieren — die konkreten Adressen stehen außerhalb des Repos
