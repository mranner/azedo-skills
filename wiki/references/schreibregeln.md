# wiki - Schreibregeln

Was ins Wiki gehört und wie es dort steht. Vor jedem Schreiben vollständig lesen.

**Inhalt:** Fertig heißt committet · Aufnahmefilter · Dichtegebot · Kürzen · Aktualisieren heißt ersetzen (Ablösung) · Patch-Stand mit `stale_after` · `verified` · ein Befund, eine Stelle

Gelten für **jedes** Schreiben ins Wiki (`compile`, `refactor`) und für `log.md`,
in jedem Wiki. „Gegenstand" ist das, was der Artikel beschreibt - ein Server, ein
Modul, eine Schnittstelle, ein Ablauf.

**Wohin ein Eintrag in `log.md` gehört, steht im Kopf der Datei** - vor dem
Schreiben lesen, nicht blind ans Ende hängen. Ist das Log „neueste zuerst"
sortiert, landet ein angehängter Eintrag unter dem ältesten Tag. Rotiert das Wiki
sein Log (Verzeichnis `<WIKI_ROOT>/log/`), meldet `lint` abgeschlossene Monate;
dann `python3 "$SKILL_DIR/scripts/rotate-log.py" <WIKI_ROOT>` laufen lassen.

### Fertig heißt: `lint` fehlerfrei und committet

Liegt das Wiki unter Versionskontrolle (git oder SVN), vor dem ersten Edit den
Status lesen (`git status --short -- <WIKI_ROOT>` bzw. `svn status <WIKI_ROOT>`).
Uncommittete Änderungen dort melden und getrennt committen lassen, bevor
dieselben Dateien angefasst werden - sonst vermischen sich fremde und eigene
Änderungen in einem Commit.

Fertig ist das Schreiben, wenn `lint` ohne Fehler durchläuft; unter
Versionskontrolle zusätzlich, wenn committet ist und der Status für
`<WIKI_ROOT>` leer ist. Der Auftrag zum Schreiben schließt den Commit ein, er
braucht keine eigene Rückfrage. Ohne Versionskontrolle genügt `lint`.

### Aufnahmefilter: gehört das überhaupt hinein?

Vier Fragen, **alle** müssen mit Ja beantwortet sein:

1. **Gilt es in drei Monaten noch?** Ein Zwischenstand, ein „aktuell läuft noch"
   oder ein Vorhaben gehört ins Ticket, nicht in einen Artikel. Entfällt für
   Typen unter `supersede` in der `wiki-schema.json`: eine zeitgebundene
   Festlegung bleibt als Nachweis, auch wenn ihr Zeitraum vorbei ist.
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

**Kundendaten nur mit Freigabe des Wikis.** Steht in `<WIKI_ROOT>/CLAUDE.md` die
Zeile `Kundendaten: aufgenommen`, sind sie dort Gegenstand und werden
aufgenommen. Ohne diese Zeile bleiben sie ausgeschlossen, auch wenn die
`CLAUDE.md` Kunden sonst erwähnt. Die übrigen Ausschlüsse und die
Sicherheitsregeln gelten auch mit Freigabe.

**Kundendaten** sind Inhalte *über* den Kunden: Ansprechpartner und
Kontaktdaten, Verträge, Preise und Konditionen, Daten seiner eigenen Kunden
(Bestellungen, Adressen), Geschäftsinterna. Die **Nennung** des Kunden als
Bezug ist keine Kundendaten-Aufnahme: `kunde:` im Frontmatter, Hostname,
Domain, Jail, „läuft beim Kunden X", ebenso eine einzelne Vorgangsnummer
(Bestell-, Belegnummer) als Beleg - sie zählt wie eine Datensatz-ID.

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

**Ausnahme: Ablösung**, nur für Typen, die `<WIKI_ROOT>/wiki-schema.json` unter
`supersede` nennt (etwa Entscheidungen, die als Festlegung nachvollziehbar
bleiben sollen). Dort wird eine Änderung eine **neue** Entity, die den neuen Stand
vollständig beschreibt; die alte bekommt nur den Ablöse-Status und den Link auf
die Nachfolgerin (Felder laut `supersede`), ihr Text bleibt. Eine Historie im
Artikel ist das nicht: die neue Entity erzählt die alte nicht nach, die alte wird
nicht fortgeschrieben. Jeder andere Typ und jedes Wiki ohne `supersede` ersetzt
wie oben.

### Patch-Stand bekommt ein `stale_after`

Eine Aussage zum Patch- oder Sicherheitsstand („kein Fix", „nur Mitigation",
„Backport nur bei X") überholt der Hersteller ohne Ankündigung. Der Artikel, der
sie enthält, bekommt `stale_after` auf das Prüfdatum plus vier Wochen; ist das
Feld schon gesetzt, gilt das frühere Datum. Beim Ablauf wird die Aussage an der
Quelle neu geprüft, wie unter „verified / stale_after setzen"
(Pflege-Referenz laut SKILL.md).

### `verified` nennt, wer wirklich geprüft hat

`human:<kürzel>` nur, wenn der Mensch ausdrücklich sagt, dass er selbst geprüft
hat. Prüft der Agent am System, steht der Modellname. Ist offen, wer geprüft hat,
oder stützt sich der Eintrag nur auf eine Angabe im Auftrag, bleibt das Feld weg.
Format und Vertrauensstufen: Frontmatter-Referenz laut SKILL.md.

### Ein Befund gehört an genau eine Stelle

Prüffrage beim Schreiben: **Würde das jemand suchen, der diesen Gegenstand gar
nicht kennt?**

- Ja → wiederkehrendes Verfahren, gehört in einen eigenen Artikel dafür (im
  Infra-Wiki: `procedure`), und der Gegenstand verlinkt darauf.
- Nein → gehört zum Gegenstand selbst.

Diese Entscheidung fällt **beim Schreiben**. Wird sie vertagt, landet beides im
Gegenstands-Artikel und muss später per `refactor` getrennt werden.
