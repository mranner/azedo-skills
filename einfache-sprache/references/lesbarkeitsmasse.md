# Lesbarkeitsmaße: Formeln, Einordnung, Grenzen

## Was diese Formeln messen - und was nicht

Alle hier verwendeten Indizes rechnen mit denselben drei Größen: Satzlänge,
Wortlänge und Silbenzahl. Mehr sehen sie nicht.

Sie messen **Oberflächenkomplexität**, nicht Verständlichkeit. Ein Text kann
kurze Sätze und kurze Wörter haben und trotzdem unverständlich sein - weil die
Reihenfolge falsch ist, das Wichtigste fehlt oder jeder Satz eine andere Sache
behauptet. Umgekehrt kann ein Fachtext mit langen Komposita für sein Publikum
vollkommen klar sein.

Daraus folgt die einzige Regel, die im Umgang mit diesen Zahlen zählt:

**Nie den Text ändern, um den Wert zu ändern.** Wer Wörter streicht, damit die
mittlere Satzlänge fällt, verbessert die Kennzahl und verschlechtert den Text.
Die Zahl ist ein Hinweis, wo man hinschauen soll - nicht das Ziel.

Ein zweiter Punkt, der oft untergeht: Die Formeln stammen aus der Zeit vor dem
Bildschirmlesen und sind an Fließtext kalibriert. Für Listen, Tabellen und
Formulare sagen sie wenig. Der Audit-Sammelcheck schließt Überschriften,
Tabellen und Codeblöcke deshalb aus der Satzstatistik aus.

## Wiener Sachtextformel (WSTF)

Für deutsche Sachtexte entwickelt (Bamberger/Vanecek 1984), am besten passendes
Maß für unsere Textsorten. Das Ergebnis ist eine **Schulstufe**: 4 = sehr
leicht, 15 = sehr schwer.

Vier Varianten, alle aus denselben Variablen:

- `MS` - Anteil der Wörter mit drei oder mehr Silben, in Prozent
- `SL` - mittlere Satzlänge in Wörtern
- `IW` - Anteil der Wörter mit mehr als sechs Buchstaben, in Prozent
- `ES` - Anteil der einsilbigen Wörter, in Prozent

```
WSTF1 = 0,1935·MS + 0,1672·SL + 0,1297·IW − 0,0327·ES − 0,875
WSTF2 = 0,2007·MS + 0,1682·SL + 0,1373·IW − 2,779
WSTF3 = 0,2963·MS + 0,1905·SL − 1,1144
WSTF4 = 0,2656·SL + 0,2744·MS − 1,693
```

Der Skill bewertet gegen **WSTF1** (alle vier Variablen); die anderen drei stehen
im JSON-Ausgabeformat und sind nützlich, wenn ein Wert auffällig aus der Reihe
fällt: WSTF3 und WSTF4 rechnen ohne Wortlänge, ein großer Abstand zu WSTF1 zeigt
also einen Text mit auffällig langen Wörtern bei sonst normalem Bau.

Einordnung: unter 6 sehr leicht, 6-9 leicht, 9-12 mittel, 12-14 schwer, darüber
sehr schwer. Zielwerte des Skills: `PLAIN` ≤ 11, `B1` ≤ 9, `A2` ≤ 7.

## LIX (Läsbarhetsindex)

Schwedischer Ursprung (Björnsson 1968), sprachübergreifend brauchbar, sehr
einfach:

```
LIX = (Wörter / Sätze) + (100 · Wörter mit mehr als 6 Buchstaben / Wörter)
```

Einordnung: unter 40 leicht, 40-50 mittel, 50-60 schwer, über 60 sehr schwer.
Deutsche Texte liegen systematisch höher als englische, weil Komposita
zusammengeschrieben werden - `Krankenversicherung` zählt als ein langes Wort,
`health insurance` als zwei kurze. Der LIX bestraft also die deutsche
Wortbildung als solche. Deshalb steht er hier neben der WSTF, nicht an ihrer
Stelle.

Zielwerte: `PLAIN` ≤ 50, `B1` ≤ 45, `A2` ≤ 40.

## Flesch-Reading-Ease, deutsche Fassung (Amstad)

Der Flesch-Index wurde für das Englische entwickelt; Toni Amstad hat 1978 die
Koeffizienten für das Deutsche angepasst:

```
FRE(de) = 180 − (Wörter / Sätze) − 58,5 · (Silben / Wörter)
```

Skala: 0-30 sehr schwer (akademisch), 30-50 schwer, 50-60 mittelschwer, 60-70
mittel (Standard für Sachtexte), 70-80 leicht, über 80 sehr leicht.

Zielwerte: `PLAIN` ≥ 50, `B1` ≥ 60, `A2` ≥ 70.

Der Flesch reagiert stark auf die Silbenzahl - und damit auf die Schwachstelle
der Messung (siehe unten). Bei Texten mit vielen Fremdwörtern und Eigennamen ist
er der unzuverlässigste der drei Werte.

## Die Silbenzählung ist eine Heuristik

`textcore.silben()` zählt Vokalgruppen, fasst Diphthonge zusammen
(`au`, `äu`, `eu`, `ei`, `ie`, …), addiert Bindestrich-Komposita teilweise und
korrigiert die Endung `-tion`. Das trifft normales Deutsch gut und liegt bei
Fremdwörtern, Eigennamen und Buchstabenfolgen regelmäßig um eine Silbe daneben.

Konsequenz: Ein Unterschied von 0,3 Schulstufen zwischen zwei Fassungen ist
Rauschen. Interessant sind Sprünge - von 12 auf 8, nicht von 9,1 auf 8,8.

## Kurze Texte

Unter etwa zehn Sätzen sind alle drei Indizes unbrauchbar: ein einzelner langer
Satz verschiebt den Mittelwert um mehrere Punkte. Der Sammelcheck weist darauf
hin (`hinweis_kurztext`), rechnet aber trotzdem - die Einzelbefunde der Linter
(Passiv, Nominalstil, Schachtelsatz) sind auch bei drei Sätzen gültig.

Bei kurzen Texten wie Mails also die Befunde lesen, nicht die Indizes.

## Was der Skill zusätzlich misst

Die eigentliche Arbeit steckt nicht in den Formeln, sondern in den vier Lintern.
Diese Werte sind aussagekräftiger als jeder Index, weil sie auf eine konkrete
Stelle zeigen statt auf einen Durchschnitt:

| Wert | Linter | warum er zählt |
|---|---|---|
| Passiv-Anteil | `sentence_lint` | verschweigt den Handelnden - die häufigste Ursache für "ich verstehe nicht, was ich tun soll" |
| Nebensätze je Satz | `sentence_lint` | direkter Treiber der Verarbeitungslast |
| Verbklammer-Weite | `sentence_lint` | misst, wie lange der Leser den Satzanfang halten muss |
| Nominalstil-Dichte | `lexicon_lint` | Verben zu Substantiven zu machen ist die Hauptquelle von Amtsdeutsch |
| Begriffsvarianten | `lexicon_lint` | Synonyme erzeugen mehr Dinge, als es gibt |
| Absatzlänge, Listenkandidaten | `structure_lint` | Strukturbefunde, die kein Index sieht |

## Vergleichsmessung

```bash
python3 scripts/einfache_sprache_audit.py \
    --file neu.md --vergleich alt.md --stufe B1
```

Zeigt beide Stände nebeneinander. Was der Vergleich **nicht** zeigt: ob Inhalt
verloren ging. Ein Text, der um 40 Prozent kürzer wurde und in allen Werten grün
ist, kann eine Frist verloren haben. Der Abgleich von Zahlen, Fristen,
Bedingungen und Rechtsfolgen bleibt Handarbeit - er steht deshalb als eigener
Schritt in Pass 5.
