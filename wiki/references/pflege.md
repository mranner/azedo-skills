# wiki - Pflege und Umbau

Aufgeblaehte Artikel finden und entflechten, Status, Handoff.

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
  „inzwischen"/„früher", über den ganzen Artikel gerechnet.
- **LOGBUCH** — datierte Aufzählungspunkte unter `## Quellen`, ab dem dritten.
  Dorthin gehört die Rohquelle, nicht die Chronologie der eigenen Sessions.
- **PROZEDURAL** — Codeblöcke und FALSCH/RICHTIG-Rezepte in einer server-,
  service-, access- oder site-Entity. Das gehört in eine procedure.
- **DOMINANT** — ein Abschnitt frisst den Grossteil der Datei. Gemeldet nur,
  wenn zusätzlich LANG oder HISTORIE zutrifft: für sich genommen ist ein
  Schwerpunkt die Bauform und nicht der Mangel. Der Befund sagt bei einem ohnehin
  auffälligen Artikel, **wo** der Ballast sitzt; als eigener Auslöser trifft er
  nur kurze, thematisch fokussierte Artikel, bei denen Zerlegen falsch wäre.
- **MEHRTHEMIG** — viele gleichrangige H2-Themen ohne Unterbau in einem
  ohnehin zu langen Artikel: das Kennzeichen eines Sammelbeckens, in dem
  mehrere Gegenstände unter einem Namen stehen. Wie DOMINANT nur mit zweitem
  Grund gemeldet; eine flache Gliederung allein ist die Bauform kurzer Artikel.
  Gezählt werden H2 ab 15 Zeilen, ohne Schrittnummern („## 6. Datenbank") und
  ohne Verwaltungsabschnitte - ein nummerierter Ablauf ist ein Gegenstand, kein
  Sammelbecken.
- **TIEF** — viele H3 oder Verschachtelung ab H4. Punktet nur, wenn der Befund
  auch gemeldet wird; ein Signal, das die Rangfolge verschiebt, ohne in der
  Ausgabe zu stehen, ist nicht nachvollziehbar. In einem flach gegliederten Wiki
  ist TIEF damit schlicht inaktiv statt unsichtbar wirksam.

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
4. **Jeden** H2/H3-Abschnitt in genau eine Kategorie einordnen:

   | Kategorie | Bedeutung | Aktion im Vorschlag |
   |---|---|---|
   | `BLEIBT` | beschreibt den Ist-Zustand des Systems | unverändert |
   | `→ PROCEDURE` | operative Anleitung | in bestehende Procedure X oder neue anlegen |
   | `→ EIGENER ARTIKEL` | eigener Gegenstand, nur zufällig hier gelandet | herauslösen, siehe [Zerlegen statt kürzen](#zerlegen-statt-kürzen) |
   | `HISTORIE` | Zustand, der nicht mehr gilt | streichen, git hält die Fassung |
   | `LOGBUCH` | Chronologie der eigenen Arbeit | streichen, Beleg bleibt nur als Nebensatz im Fachteil |
   | `DUPLIKAT` | steht schon in Artikel Y | streichen, Wikilink setzen |
   | `→ TASK` | offene Aufgabe, keine Doku | ins Ticketsystem, aus dem Wiki raus |

5. **Zweiter Durchgang auf Satzebene** über die `BLEIBT`-Abschnitte (siehe
   [Verdichten statt verschieben](#verdichten-statt-verschieben) unten).
6. Vorschlag als Tabelle im Chat ausgeben, mit Zeilenumfang je Abschnitt und der
   erwarteten Restlänge. Nichts schreiben.
7. Erst **nach Freigabe** umsetzen, und dann vollständig: Zielartikel anlegen
   bzw. ergänzen, Wikilink im Restartikel setzen, `index.md` ergänzen,
   Frontmatter-Datum aktualisieren, Zeile in `log.md`, danach `/wiki lint`.

#### Zerlegen statt kürzen

Der häufigste Grund für einen zu langen Artikel ist Fülle - manchmal ist es
aber die Sammlung. Ein Artikel, dessen Name ein Thema verspricht und der fünf
enthält, wird durch Kürzen nicht besser: er bleibt an der falschen Stelle
auffindbar. `freebsd-shell-pitfalls` hatte 811 Zeilen und war kein verrotteter
Artikel, sondern ein Sammelbecken; vier der fünf Themen sind heute eigene
Procedures, der Rumpf hat 241 Zeilen.

`→ EIGENER ARTIKEL` bekommt ein Abschnitt, wenn **alle drei** zutreffen:

1. Er beschreibt einen **anderen Gegenstand** als der Artikeltitel verspricht -
   nicht eine Facette desselben.
2. Jemand würde ihn suchen, **ohne den Artikel zu kennen** (die Prüffrage aus
   [Ein Befund gehört an genau eine Stelle](../SKILL.md#ein-befund-gehört-an-genau-eine-stelle)).
3. Er trägt allein: Behauptung, Folge und Beleg stehen im Abschnitt selbst, er
   braucht den Rahmen des Quellartikels nicht.

Trifft nur 2 zu, ist es `→ PROCEDURE` - operative Anleitung, die aus einer
Gegenstands-Entity herausgehört. `→ EIGENER ARTIKEL` meint den anderen Fall:
der Quellartikel ist selbst schon eine Procedure oder ein Sammelartikel und
wird geteilt.

**Was das Script dazu sagen kann und was nicht.** `MEHRTHEMIG` misst die
Bauform (viele gleichrangige H2, wenig Unterbau), nicht die Themen. Ob zwei
Abschnitte denselben Gegenstand meinen, entscheidet nur, wer sie liest -
umgekehrt ist ein Artikel ohne den Befund nicht automatisch unteilbar. Der
Befund ist ein Anlass, die drei Fragen zu stellen, keine Antwort darauf.

Beim Umsetzen kommt zu Schritt 7 dazu:

- **Eingehende Verweise umhängen.** `grep -rn "\[\[<slug>\]\]" <WIKI_ROOT>`
  vor dem Teilen: jeder Verweis zeigt auf *ein* Thema, und nach dem Teilen
  meistens auf das falsche. Beim Zerlegen von `freebsd-shell-pitfalls` waren 38
  von 62 Verweisen umzuhängen - das ist die eigentliche Arbeit, nicht das
  Verschieben des Textes.
- **Der Rumpf behält eine Verweisliste** („Weitere Pitfalls in eigenen
  Artikeln") mit einem Halbsatz je Ziel, damit der Weg vom bekannten Namen zum
  ausgelagerten Thema bestehen bleibt.
- **Ein Name, ein Versprechen.** Der Rumpf behält seinen Slug nur, wenn er
  danach wirklich das beschreibt, was der Name sagt. Sonst gehört er
  umbenannt - mit Eintrag in `index.md` und den Verweisen hinterher.
- **Nicht in einem Durchgang mit dem Verdichten.** Erst teilen, `lint`, dann in
  einem zweiten Aufruf je Artikel verdichten. Sonst steht ein Vorschlag im
  Chat, den niemand mehr prüfen kann.

#### Verdichten statt verschieben

Ein Artikel kann strukturell fertig sein - jeder Abschnitt gehört dorthin, wo er
steht, und der Artikel beschreibt genau einen Gegenstand - und trotzdem ein
Fünftel zu lang. Schritt 4 verschiebt Abschnitte,
Schritt 5 kürzt Sätze innerhalb der bleibenden. Beide Durchgänge sind nötig; wer
nur den ersten macht, verteilt die Fülle bloss auf mehr Dateien.

Der zweite Durchgang sucht fünf Muster. Sie sind mechanisch erkennbar, deshalb
gehören sie in den Vorschlag mit **Vorher/Nachher am konkreten Satz** - nicht als
Rat, sondern als Ersetzung, die man freigeben oder ablehnen kann:

| Muster | Erkennungszeichen | Behandlung |
|---|---|---|
| **Dieselbe Aussage mehrfach** | Behauptung, ihre Umkehrung, dann die Handlungsanweisung daraus - drei Sätze, ein Inhalt | einen behalten, meist den mit der Konsequenz |
| **Fremdcode als Beweis** | zitierter Codeblock aus einem fremden Projekt, der nur belegt, was ein Satz sagt | Satz statt Block. Eigener Code, der den Fehler *zeigt*, bleibt |
| **Erzählrahmen vor dem Inhalt** | „X ist darauf vorbereitet:", „Wer … testet, braucht …:", „Praktischer Nebeneffekt:" | Rahmen streichen, Inhalt direkt |
| **Duplikat im selben Artikel** | derselbe Hinweis an zwei Stellen, einmal als Randnotiz, einmal am Ort der Handlung | am Ort der Handlung behalten, Randnotiz streichen |
| **Quellen als Session-Liste** | Aufzählung „Session &lt;Datum&gt;: &lt;was ich tat&gt;" unter `## Quellen` | streichen; was fachlich trägt, steht schon oben, der Rest ist Arbeitsprotokoll |

Die Grenze nach unten: gekürzt wird der **Weg zur Aussage**, nie die Aussage.
Bleiben müssen Behauptung, Folge und Beleg (das
[Dichtegebot](../SKILL.md#dichtegebot-behauptung-folge-beleg)) - ein Artikel, aus dem man
den Prüfbefehl herausgekürzt hat, ist nicht dichter, sondern unbrauchbar.

**Was dieser Durchgang nicht leistet:** er räumt keinen `LANG`-Befund ab, und er
ist nicht der Weg aus einem Sammelbecken - dort ist zuerst
[Zerlegen](#zerlegen-statt-kürzen) an der Reihe.
Realistisch sind 10-20 % der Zeilen. Ein Artikel, der drei Fehlerbilder und zwei
Instanzen beschreibt, bleibt danach über der Typ-Schwelle - das ist Substanz,
keine Fülle, und im Vorschlag auch so zu benennen, statt weiter zu kürzen, bis
die Zahl stimmt.

**Die Historie-Regel.** Nicht „alt" ist das Kriterium, sondern „gilt nicht mehr".
Ein datierter Beleg („verifiziert 2026-07-28 auf [[fry-azedo-at]]") ist eine
zeitlose Begründung und **bleibt** — er sieht nur aus wie Historie. Gestrichen
wird ein beschriebener Zustand, den es so nicht mehr gibt. Im Zweifel: der
Vorschlag markiert den Abschnitt als unklar und fragt, statt ihn einzuordnen.

Ein überholter Zustand wird gelöscht, nicht umgelagert - `## Quellen` nimmt nur
echte Rohquellen auf (Datei unter `raw/`, externes Dokument, Ticket) und ist
sonst wegzulassen. Das Argument fürs Streichen ist nie „ist alt", sondern dass
git die Fassung ohnehin vorhält.

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
[Remote-Wikis](remote-wikis.md#remote-wikis-read-only)); Lint entfaellt (laeuft nur auf lokaler
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
   [Remote-Wikis](remote-wikis.md#remote-wikis-read-only)): `wiki-schema.json` (Pflichtfelder +
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
