---
name: einfache-sprache
description: >
  Deutsche Texte in Einfache Sprache bringen und auf Verständlichkeit prüfen:
  Lesbarkeit messen und Satzbau, Nominalstil, Passiv und Amtsdeutsch
  aufdecken, in drei Stufen. Nicht zuständig für Leichte Sprache (A1); geht
  es darum, dass ein Text nach KI klingt, ist humanizer-de gemeint.
  Auch bei "schreib das einfacher", "in Einfacher Sprache", "das versteht
  kein Mensch", "Amtsdeutsch auflösen", "Lesbarkeit prüfen".
  Trigger: /einfache-sprache.
allowed-tools: [Read, Write, Edit, Grep, Glob, Bash]
metadata:
  display_name: Einfache Sprache
  version: 1.37.0
---

# Einfache Sprache

## Auftrag

Deutschen Text so umschreiben, dass die Zielgruppe ihn beim ersten Lesen
versteht - ohne dass Inhalt, Genauigkeit oder Rechtsfolgen verloren gehen.
Einfache Sprache ist reduzierte Standardsprache: kürzere Sätze, bekannte
Wörter, klare Struktur. Der Text bleibt ein normaler deutscher Text.

Der Skill deckt zwei Aufgaben ab, die getrennt bleiben:

- **Prüfen** - messen, wie schwer ein Text ist, und die Ursachen benennen.
- **Übertragen** - den Text auf eine Zielstufe bringen.

## Abgrenzung: nicht Leichte Sprache

**Leichte Sprache** (A1, Regelwerk Netzwerk Leichte Sprache, DIN SPEC
33429:2025-03) ist eine eigene Varietät mit sichtbar abweichender Oberfläche:
Sätze unter acht Wörtern, ein Satz pro Zeile, Trennpunkte in Komposita
(`Bundes·tag`), Erklärbilder, geprüfte Fassung durch eine Prüfgruppe.

Dieser Skill macht das **nicht**. Wenn der Nutzer Leichte Sprache verlangt
(oder BITV 2.0 / BGG als Anforderung nennt), das einmal klar sagen: die
Übertragung ist möglich, aber sie ersetzt weder das Regelwerk noch die
vorgeschriebene Prüfung durch Menschen der Zielgruppe. Danach entweder auf
Stufe `A2` übertragen und als Annäherung kennzeichnen, oder abgeben.

Details: [references/din-normen.md](references/din-normen.md).

## Stufen

Zuerst die Zielstufe bestimmen. Wenn unklar, `B1` nehmen und das sagen.

| Stufe | Zielgruppe | Einsatz |
|---|---|---|
| `PLAIN` | Fachpublikum, geübte Leser | Fachdoku, B2B-Website, interne Anleitung für Kollegen |
| `B1` (Standard) | breite Öffentlichkeit | Kundenwebsite, Bürgerinformation, Kundenmail, Anleitung für Endnutzer |
| `A2` | geringe Lesekompetenz, Deutsch als Zweitsprache | Formulare, Merkblätter, Annäherung an Leichte Sprache |

`PLAIN` senkt den Wortschatz **nicht** ab: Fachbegriffe bleiben, gearbeitet wird
an Satzbau, Nominalstil, Struktur und Auffindbarkeit. Wer einem Admin
`Zertifikat` durch `Sicherheits-Ausweis` ersetzt, macht den Text schlechter.

## Zielwerte

Messwerte des Skills, nicht Wortlaut der Norm (Herkunft und Grenzen:
[references/lesbarkeitsmasse.md](references/lesbarkeitsmasse.md)).

| Kennwert | `PLAIN` | `B1` | `A2` |
|---|---|---|---|
| Sätze: Mittel (Wörter) | <= 18 | <= 15 | <= 12 |
| Sätze: Maximum | 30 | 25 | 20 |
| Nebensätze je Satz | <= 2 | <= 1 | 0 |
| Wörter mit 3+ Silben | <= 20 % | <= 15 % | <= 10 % |
| Passiv-Anteil der Sätze | <= 20 % | <= 10 % | <= 5 % |
| Absatz: Sätze | <= 6 | <= 5 | <= 3 |
| Wiener Sachtextformel 1 | <= 11 | <= 9 | <= 7 |
| LIX | <= 50 | <= 45 | <= 40 |
| Flesch (Amstad) | >= 50 | >= 60 | >= 70 |

Die Zielwerte sind Korridore, keine Quote. Ein Text, der alle Werte erfüllt und
trotzdem unverständlich bleibt, ist nicht fertig; ein Satz mit 27 Wörtern, der
sich sauber liest, ist kein Fehler. Nie Wörter streichen, nur damit eine Zahl
fällt - das ist der häufigste Weg, einen Text zu verschlechtern.

## Leitplanken

- **Inhaltstreue.** Zahlen, Beträge, Fristen, Namen, Bedingungen, Rechtsfolgen
  und technische Werte bleiben unverändert. Vor und nach dem Umschreiben
  abgleichen. Vereinfachen heißt umformulieren, nicht weglassen.
- **Bedingungen sind Inhalt.** `wenn`, `sofern`, `es sei denn`, `nur bei`,
  `spätestens` tragen die Aussage. Sie dürfen aus dem Nebensatz in einen
  eigenen Satz wandern, aber nicht verschwinden.
- **Rechts- und sicherheitskritische Passagen** nicht stillschweigend
  umformulieren: Gesetzeszitate, Haftungs-, Widerrufs- und Datenschutztexte,
  Warnhinweise, Dosierungen, Konfigurationswerte. Entweder wörtlich stehen
  lassen und eine Erklärung danebenstellen, oder markieren und den Nutzer
  entscheiden lassen.
- **Fachbegriff behalten und erklären**, nicht ersetzen. Wer den Begriff nie
  liest, kann später nicht danach fragen oder suchen. Erklärmuster:
  [references/fachbegriffe.md](references/fachbegriffe.md).
- **Nicht infantilisieren.** Erwachsene Leser mit wenig Lesekompetenz sind keine
  Kinder. Kein betont munterer Ton, keine Ausrufezeichen, keine erklärenden
  Zusätze für Offensichtliches.
- **Keine neuen Fakten.** Wird beim Vereinfachen klar, dass eine Information
  fehlt (die Bedingung, das Subjekt der Passivkonstruktion, der gemeinte
  Zeitraum), diese Lücke markieren statt sie zu füllen.
- **Proportional eingreifen.** Nur die Stellen ändern, die einen Befund haben.
  Ist der Text sauber, das sagen und aufhören.
- Lint-Befunde sind Verdacht, kein Verdikt. Jeden vor der Änderung gegen den
  Kontext prüfen (siehe Carve-outs).

## Ablauf

**Pass 0 - Triage.** Stufe, Textsorte, Zielgruppe und Umfang bestimmen; klären,
ob geprüft oder übertragen werden soll. Dann messen:

```bash
python3 "$SKILL_DIR/scripts/einfache_sprache_audit.py" --file <pfad> --stufe B1
```

Inline-Text zuerst in eine UTF-8-Datei unter `.tmp/` schreiben, dann `--file`.
Shell-Befehle bleiben statisch, Nutzertext läuft über Dateien. Für den
jüngsten Markdown-Entwurf in einem Ordner: `--latest <dir>`. Der Sammelcheck
liefert Kennwerte, eine Ampel je Kennwert und die Befunde der vier Linter,
sortiert nach Gewicht. Läuft ein Script nicht, das melden statt blind von Hand
zu korrigieren.

Textsortenprofil festlegen:
[references/textsorten.md](references/textsorten.md).

**Pass 1 - Struktur zuerst.** Reihenfolge, Überschriften, Absätze, Listen.
Das Wichtigste nach vorn (die Antwort vor die Begründung, die Handlung vor die
Rechtsgrundlage). Ein Gedanke pro Absatz. Aufzählungen, die als Schachtelsatz
getarnt sind, in eine Liste auflösen. Überschriften sagen, was drinsteht.
Diesen Pass zuerst, weil er ganze Sätze überflüssig macht - Satzarbeit an
Text, der danach wegfällt, ist verloren.

**Pass 2 - Sätze.** Schachtelsätze teilen, Verbklammer schließen, Passiv
auflösen (mit handelndem Subjekt, sonst markieren), Konjunktiv abbauen,
Genitivketten in `von`-Fügungen oder eigene Sätze, doppelte Verneinung
positiv. Ein Satz, eine Aussage. `sentence_lint.py` liefert die Kandidaten je
Satz mit Zeilennummer.

**Pass 3 - Wörter.** Nominalstil in Verben zurückverwandeln,
Funktionsverbgefüge auflösen (`zur Anwendung bringen` -> `anwenden`),
Amtsdeutsch und Fremdwörter ersetzen oder erklären, lange Komposita
auflösen oder mit Bindestrich gliedern, Abkürzungen bei der ersten Nennung
einführen. Ersatzvorschläge kommen aus `scripts/data/wortlisten.json`; jeder
Vorschlag ist ein Vorschlag, kein Automatismus - der Kontext entscheidet.

**Pass 4 - Konsistenz.** Ein Begriff pro Sache, durchgehend. Synonyme sind in
Einfacher Sprache ein Fehler, kein Stilmittel: wer `Antrag`, `Formular` und
`Gesuch` mischt, erzeugt drei Dinge im Kopf des Lesers. Ebenso: eine Anrede
(`Sie` oder `du`, nicht beides), ein Datumsformat, eine Schreibweise pro Begriff.

**Pass 5 - Nachmessen und Selbstprüfung.** Audit erneut laufen lassen und
gegen den Ausgangsstand halten. Dann prüfen: Sind alle Zahlen, Fristen und
Bedingungen noch da? Ist eine Ersatzregel zur Masche geworden (dieselbe
Konstruktion 3+ Mal)? Klingt der Text kindlich? Sind neue Aussagen entstanden?
Erst danach ausgeben.

## Carve-outs: bekannte Fehlalarme

- **Fachbegriffe im Fachtext.** `lexicon_lint.py` kennt keinen Adressaten.
  `Zertifikat`, `Reverse Proxy`, `Kubernetes` sind in einer Admin-Anleitung
  richtig. In `PLAIN` grundsätzlich kein Befund, in `B1`/`A2` nur, wenn der
  Text sich an Laien richtet.
- **Zitate, Gesetzestexte, Code, Konfigurationsbeispiele, Formularfelder,
  Produktnamen** - nie stilistisch umschreiben. Der Linter blendet
  Codeblöcke und Inline-Code aus, aber keine eingerückten Zitate.
- **Passiv ohne handelndes Subjekt.** `Der Antrag wird geprüft` lässt sich nur
  auflösen, wenn im Text steht, wer prüft. Steht es nicht da, ist das ein
  Befund für den Nutzer (`wer prüft?`), keine Umschreibung ins Blaue.
- **Lange Wörter, die keine sind.** URLs, Dateipfade, Hostnamen und
  Versionsnummern zählen die Silben-Heuristik als Wortungetüm. Der Linter
  filtert die häufigen Formen, aber nicht alle.
- **Ein einzelner langer Satz** ist kein Befund. Gemessen wird die Verteilung;
  ein Ausreißer in einem sonst kurzen Text ist Rhythmus, kein Fehler.
- **Silbenzählung ist eine Heuristik.** Bei Fremdwörtern und Eigennamen liegt
  sie regelmäßig um eine Silbe daneben. Kennwerte auf Basis kurzer Texte
  (unter ~10 Sätzen) sind nicht belastbar; das Audit weist darauf hin.
- **`A2` auf einem Fachtext** erzeugt reihenweise Befunde, die alle stimmen und
  trotzdem nicht umsetzbar sind. Dann ist die Stufe falsch gewählt - das sagen,
  statt den Text zu zerlegen.

## Output

Kurz, auf die geänderten Stellen konzentriert, kein Volltext-Neuabdruck (außer
bei ausdrücklicher Übertragung einer ganzen Datei).

1. **Stufe und Textsorte:** eine Zeile.
2. **Messung:** Kennwerte vorher (bei Übertragung: vorher -> nachher), nur die
   auffälligen plus die Gesamtnote.
3. **Befunde:** maximal 6 Punkte, jeder mit kurzem Zitat und Ursache
   (`Schachtelsatz, 34 Wörter, 3 Nebensätze`).
4. **Geänderte Stellen:** Vorher/Nachher-Paare der bearbeiteten Passagen.
5. **Offene Punkte:** was ohne zusätzliche Information nicht auflösbar war
   (fehlendes Subjekt, ungeklärter Fachbegriff, rechtskritische Passage).
6. **Verworfene Kandidaten:** nur, wenn Lint-Flags vorlagen und bewusst nicht
   umgesetzt wurden, je Zeile mit Begründung.

Bei Datei-Input und Aenderungsauftrag: Datei direkt editieren, Änderungen kurz
zusammenfassen. Die Originalfassung nicht überschreiben, ohne dass der Nutzer
das weiß - bei Bedarf `<name>.einfach.md` daneben legen und fragen.

## Referenzen

- Regelkatalog Wort/Satz/Text/Gestaltung mit IDs: [references/regelkatalog.md](references/regelkatalog.md)
- Normen, Rechtsrahmen, Abgrenzung Leichte Sprache: [references/din-normen.md](references/din-normen.md)
- Profile für Website, Behörde, Techdoku, E-Mail: [references/textsorten.md](references/textsorten.md)
- Fachbegriffe erklären statt tilgen: [references/fachbegriffe.md](references/fachbegriffe.md)
- Formeln, Interpretation, Grenzen der Maße: [references/lesbarkeitsmasse.md](references/lesbarkeitsmasse.md)
- Sammelcheck: `$SKILL_DIR/scripts/einfache_sprache_audit.py`
- Einzel-Linter: `$SKILL_DIR/scripts/readability_lint.py`, `sentence_lint.py`, `lexicon_lint.py`, `structure_lint.py`
- Wortlisten (Amtsdeutsch, Funktionsverbgefüge, Fremdwörter, Varianten): `$SKILL_DIR/scripts/data/wortlisten.json`
