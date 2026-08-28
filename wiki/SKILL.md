---
name: wiki
description: >
  LLM Wiki: strukturierte Wissensbasis über mehrere Wikis (Server-Infra und
  Projekt-Doku), Entities mit YAML-Frontmatter und grep-basierter Discovery.
  Wissen abfragen, eintragen, kompilieren, validieren, aufgeblähte Artikel
  entflechten; Wikis auf anderen Hosts read-only per SSH abfragen.
  Auch bei "trag das ins Wiki ein", "was steht im Wiki zu X", "wiki
  aktualisieren", "gibt es relevante Erkenntnisse fürs Wiki".
  Trigger: /wiki.
---

# wiki -- LLM Wiki Verwaltung

Verwaltet strukturierte Wiki-Entities in mehreren Wikis (IT-Infrastruktur- und
Projekt-Dokumentation).

## Ziel-Wiki bestimmen

Alle Subcommands nehmen optional einen Wiki-Namen als Praefix an:

```
/wiki <name>:<subcommand> [args]     # z.B. /wiki cris:query "Wie laeuft Auth?"
/wiki <subcommand> [args]            # ohne name → Default, siehe Schritt 1
```

Vor jeder Operation:

1. Wiki-Name aus dem Argument parsen (Muster `^([a-z0-9-]+):`). **Ohne Praefix
   den Default ableiten, nicht raten** — `wiki/` im Projekt-Root auflisten:

   | Lage | Verhalten |
   |---|---|
   | genau **ein** lokales Wiki | das ist der Default, ohne Rueckfrage |
   | **mehrere** lokale Wikis | die Namen nennen und nachfragen, keins waehlen |
   | **keins** | auf `/wiki init <name>` hinweisen |

   Ein fest verdrahteter Default-Name waere genau in dem Projekt richtig, in dem
   er gesetzt wurde, und in jedem anderen falsch: `/wiki audit` liefe dort gegen
   ein Wiki, das es nicht gibt. Der Name des Wikis richtet sich nach dem
   Projekt, nicht nach dem Skill.
2. Wiki-Root ableiten: `WIKI_ROOT = wiki/<name>/` — **relativ zum Projekt-Root**
   (dem Arbeitsverzeichnis, in dem der Skill laeuft; dort liegen die Wikis unter
   `wiki/`). Analog zur Projekt-`CLAUDE.md`, die das Wiki als `wiki/azedo/…`
   referenziert. Kein absoluter Home-Pfad — so bleibt der Skill portabel
   (Mac, andere Mitarbeiter, anderer Checkout-Ort).
3. Ziel aufloesen — in dieser Reihenfolge:
   a. `WIKI_ROOT` existiert lokal → **lokales Wiki** (wie gehabt, weiter mit Schritt 4).
   b. Lokal nicht vorhanden, aber `<name>` steht in `.claude/wiki-remotes.json`
      (projekt-relativ) → **Remote-Wiki, read-only**. Ab hier gilt der Abschnitt
      [Remote-Wikis](references/remote-wikis.md): nur lesende Subcommands (`query`,
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

## Subcommands

Haeufigster Fall ist `query` (nachschlagen) und `harvest` (Erkenntnisse aufnehmen -
Kandidaten filtern, vorlegen, erst nach Freigabe schreiben):

```bash
python3 "$SKILL_DIR/scripts/wiki" query "<suchbegriff>"
python3 "$SKILL_DIR/scripts/wiki" harvest
```

Vollstaendige Referenz daneben, bei Bedarf lesen:

| Datei | Inhalt |
|---|---|
| `references/subcommands.md` | `init`, `ingest`, `compile`, `harvest`, `query`, `lint` |
| `references/pflege.md` | `audit` (aufgeblaehte Artikel finden), `refactor` (Entity umbauen, verdichten statt verschieben), `status`, `handoff` |
| `references/remote-wikis.md` | Wikis anderer Hosts read-only per SSH abfragen, Konfiguration, Hints auf Remote-Entities |

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
