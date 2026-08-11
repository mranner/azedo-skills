# Regelkatalog Einfache Sprache

Die Regeln sind nach den vier Ebenen der DIN 8581-1 geordnet: Text, Satz, Wort,
Gestaltung. Die IDs entsprechen den Befund-Kennungen der Linter, damit sich eine
Lint-Zeile ohne Umweg auf eine Regel zurückführen lässt.

Jede Regel nennt, was sie leistet und wann sie **nicht** gilt. Der zweite Teil
ist der wichtigere: eine Regel ohne Ausnahme wird mechanisch angewendet, und
mechanische Anwendung ist der übliche Weg, aus einem schweren Text einen
schlechten zu machen.

## Textebene (T)

### T1 - Ein Gedanke je Absatz

Ein Absatz trägt eine Aussage. Braucht der Leser für den zweiten Gedanken den
ersten nicht, gehört er in einen eigenen Absatz. Zielwerte: `PLAIN` bis 6 Sätze,
`B1` bis 5, `A2` bis 3.

**Nicht:** Absätze zerhacken, bis jeder Satz allein steht. Das erzeugt
Stakkato und zerstört den Zusammenhang, den der Leser gerade braucht.

### T2 - Das Wichtigste zuerst

Die Antwort steht vor der Begründung, die Handlung vor der Rechtsgrundlage, das
Ergebnis vor dem Verfahren. Wer erst nach drei Absätzen erfährt, dass er nichts
tun muss, hat drei Absätze umsonst gelesen.

Der typische Amtstext ist genau andersherum gebaut: Rechtsgrundlage, Verfahren,
Ergebnis. Die Umstellung ist meist der größte einzelne Gewinn - und sie kostet
keine Genauigkeit, nur Reihenfolge.

### T3 - Überschriften sagen den Inhalt

`Was Sie jetzt tun müssen` statt `Verfahrenshinweise`. Höchstens acht Wörter.
Die Überschrift ist für viele Leser der einzige Text, den sie vollständig lesen.

### T4 - Aufzählungen als Liste

Drei oder mehr gleichrangige Glieder in einem Satz gehören in eine Liste. Der
Linter meldet solche Sätze als Listenkandidaten.

**Nicht:** alles zur Liste machen. Eine Liste aus zwei Punkten ist meistens ein
Satz, und ein Argument, das aus Begründungsschritten besteht, verliert als Liste
seinen Zusammenhang.

### T5 - Verweise mit Ziel

`siehe oben`, `wie bereits erwähnt`, `an anderer Stelle` zwingen den Leser zum
Zurückblättern. Entweder die Information wiederholen oder konkret benennen
(`in Abschnitt "Fristen"`).

### T6 - Beispiel statt Abstraktion

Ein konkretes Beispiel ersetzt zwei Sätze Erklärung. Bedingung: das Beispiel
steht im Ausgangstext oder im Kontext. Erfundene Beispiele sind neue Fakten.

## Satzebene (S)

### S1 - Satzlänge

Zielwerte: `PLAIN` maximal 30 Wörter, `B1` 25, `A2` 20. Der Mittelwert zählt mehr
als der Ausreißer - ein langer Satz zwischen kurzen ist Rhythmus.

Kürzen heißt teilen, nicht streichen. Wer aus einem 40-Wörter-Satz einen mit 20
macht, indem er die Hälfte weglässt, hat die Hälfte des Inhalts weggeworfen.

### S2 - Nebensätze

`PLAIN` bis zwei, `B1` einer, `A2` keiner. Gezählt werden unterordnende
Konjunktionen, Relativsätze und `um … zu`-Konstruktionen.

Die Auflösung ist fast immer dieselbe Bewegung: Der Nebensatz wird zum eigenen
Hauptsatz, und die logische Beziehung wandert in ein Signalwort am Satzanfang
(`Deshalb`, `Danach`, `Wenn das nicht klappt:`).

**Nicht:** Konditionale einebnen. `Wenn X, dann Y` ist eine Bedingung. Wird
daraus `X. Y.`, steht dort eine Behauptung.

### S3 - Passiv auflösen

Vorgangspassiv (`wird geprüft`) verschweigt, wer handelt. Genau das ist beim
Leser die offene Frage: Muss *ich* etwas tun oder nicht?

Auflösen geht nur mit dem Handelnden. Steht er nicht im Text, ist das ein
offener Punkt für den Nutzer, keine Einladung zum Raten. `Man prüft` ist keine
Lösung, sondern dasselbe Problem mit anderem Wort.

**Nicht behandeln:** Zustandspassiv (`ist geöffnet`, `ist vorgesehen`) - das
beschreibt einen Zustand und hat oft keinen Handelnden.

### S4 - Verbklammer schließen

`Der Antrag wird nach Prüfung aller eingereichten Unterlagen durch die
zuständige Stelle **bearbeitet**.` Zwischen Hilfsverb und Vollverb liegen zwölf
Wörter, die der Leser im Kopf halten muss, bis der Satz sagt, worum es geht.

Grenze: acht Wörter. Auflösen durch Umstellen oder Teilen.

### S5 - Konjunktiv nur, wenn Möglichkeit gemeint ist

`Sie könnten Widerspruch einlegen` - können sie oder nicht? Amtlicher Konjunktiv
ist meist Höflichkeit, keine Modalität. Dann Indikativ: `Sie können Widerspruch
einlegen.`

**Nicht:** indirekte Rede und echte Bedingungen in den Indikativ zwingen.

### S6 - Genitivketten auflösen

`die Prüfung der Vollständigkeit der Unterlagen des Antrags` - drei Genitive,
und der Leser hat die Reihenfolge verloren. In `von`-Fügungen oder eigene Sätze.
Ab zwei Genitivattributen im Satz meldet der Linter.

### S7 - Positiv formulieren

`Anträge ohne vollständige Unterlagen können nicht berücksichtigt werden` →
`Schicken Sie alle Unterlagen mit. Sonst können wir Ihren Antrag nicht
bearbeiten.` Zwei Verneinungen in einem Satz sind eine zu viel.

**Nicht:** Verbote in Erlaubnisse verdrehen. `Sie dürfen nicht X` ist kein
`Sie dürfen Y`.

### S8 - Einschübe ans Satzende

Klammern und Gedankenstrich-Einschübe unterbrechen den Satzbogen. Kurze
Einschübe sind harmlos; alles ab etwa fünf Wörtern gehört in einen eigenen Satz.

## Wortebene (W)

### W1 - Nominalstil in Verben zurückverwandeln

`Die Durchführung der Prüfung erfolgt` → `Wir prüfen`. Endungen auf `-ung`,
`-heit`, `-keit`, `-nis`, `-tion`, `-ität` sind das Erkennungszeichen.

Gemessen wird die **Dichte**, nicht das Einzelwort: `Rechnung`, `Wohnung`,
`Zeitung`, `Version` sind konkrete Dinge, keine Nominalisierungen. Grenzen:
`PLAIN` 8, `B1` 6, `A2` 4 je 100 Wörter.

### W2 - Funktionsverbgefüge auflösen

`zur Anwendung bringen` → `anwenden`, `eine Entscheidung treffen` →
`entscheiden`. Das Verb steckt bereits im Substantiv; das Hilfsverb trägt nichts.

**Nicht:** feste Fachwendungen zerlegen, die als Ganzes ein Begriff sind
(`in Kraft treten` hat eine juristische Bedeutung, die `gelten` nicht deckt).

### W3 - Amtsdeutsch ersetzen

`in Kenntnis setzen` → `informieren`, `unverzüglich` → `sofort`, `seitens` →
`von`. Liste in `scripts/data/wortlisten.json`.

**Achtung bei Rechtsbegriffen:** `unverzüglich` heißt juristisch *ohne
schuldhaftes Zögern*, nicht *sofort*. In einem rechtsverbindlichen Text ist die
Ersetzung falsch. Solche Wörter erklären statt ersetzen.

### W4 - Fremdwörter ersetzen oder erklären

`evaluieren` → `bewerten`, `Deadline` → `Termin`. In Stufe `PLAIN` kein Befund:
dort liest Fachpublikum, und die deutsche Ersatzform ist oft die unschärfere.

### W5 - Lange Wörter aufbrechen

Grenzen: `PLAIN` 20 Zeichen, `B1` 16, `A2` 14. Zwei Wege: in eine Wortgruppe
auflösen (`Antragsbearbeitung` → `Wir bearbeiten Ihren Antrag`) oder mit
Bindestrich gliedern (`IT-Sicherheits-Richtlinie`).

**Nicht:** etablierte Komposita künstlich trennen. `Krankenversicherung` ist ein
Wort, das jeder kennt - die Länge ist kein Verständnisproblem.

### W6 - Abkürzungen einführen

Bei der ersten Nennung ausschreiben, Abkürzung in Klammern dahinter. Danach
durchgehend die Abkürzung. Allgemein bekannte (EU, PDF, GmbH) brauchen das nicht.

### W7 - Ein Begriff pro Sache

`Antrag`, `Formular`, `Gesuch`, `Anmeldung` für dieselbe Sache erzeugen vier
Dinge im Kopf des Lesers. Synonyme sind hier kein Stilmittel, sondern ein Fehler.
Der Linter prüft bekannte Variantengruppen; für Fachterminologie eines Projekts
ist das eine manuelle Prüfung.

### W8 - Füllwörter streichen

`selbstverständlich`, `grundsätzlich`, `im Prinzip`, `eigentlich`, `durchaus`.
Sie tragen nichts, kosten aber Lesezeit. `grundsätzlich` ist ein Sonderfall: es
signalisiert oft eine unausgesprochene Ausnahme. Dann nicht streichen, sondern
die Ausnahme benennen.

## Gestaltung (G)

### G1 - Eine Anrede

`Sie` oder `du`, nicht beides. In Behörden- und Kundentexten in der Regel `Sie`.
Direkte Anrede schlägt unpersönliche Konstruktion: `Sie brauchen` statt
`es wird benötigt`.

### G2 - Ein Datums- und Zahlformat

Durchgehend `15. März 2026` oder durchgehend `15.03.2026`. Zahlen als Ziffern
schreiben (`3` statt `drei`), sie werden schneller erfasst. Große Zahlen und
Prozentangaben runden, wenn die Genauigkeit nicht gebraucht wird - aber nie bei
Beträgen, Fristen und Messwerten.

### G3 - Keine Versalien, kein Kursiv als Hervorhebung

Durchgehende Großbuchstaben nehmen dem Wort die Umrissform und verlangsamen das
Lesen. Kursiv ist auf Bildschirmen schlecht lesbar. Fett, sparsam, ist die
brauchbare Hervorhebung.

### G4 - Linksbündig, ohne Blocksatz

Blocksatz erzeugt ungleiche Wortabstände und "Löcher", die den Zeilenfluss
stören. Silbentrennung sparsam.

### G5 - Kurze Zeilen

Etwa 60 bis 70 Zeichen. Längere Zeilen erschweren das Zurückfinden an den
Zeilenanfang - für geübte Leser ein Detail, für ungeübte ein echtes Hindernis.
