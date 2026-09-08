# swaks - Bausteine

Grundbefehl, Body, Empfänger, HTML, Anhänge.

Alle Beispiele gehen über `build_mail.py`; gesendet wird mit `--send`. Ein
`swaks`-Aufruf von Hand kommt hier nicht mehr vor - er bräuchte Zugangsdaten,
die der Helper bewusst nicht herausgibt (siehe `versandweg.md`).

Zwei Zeilen stehen vor jedem Beispiel und werden dort nicht wiederholt:

```bash
M=$(mktemp -d .tmp/mail.XXXXXX)
B=~/.claude/skills/swaks/build_mail.py
```

Was früher als `--header "Content-Type: …"` und
`--header "Content-Transfer-Encoding: …"` dabeistand, entfällt: Zeichensatz und
Encoding setzt der Helper selbst. `--subject` und `--text-file` sind Pflicht,
einen Inline-Body wie `swaks --body` gibt es nicht - der Text kommt aus einer
Datei.

Der Versand ist in jedem Fall ein **eigener** Befehl nach dem Bau. Die
`--verify`-Zeile aus der SKILL.md („Vor dem Versand prüfen") gehört dazwischen,
sobald der Inhalt vom Nutzer freigegeben wurde; sie ist hier der Kürze halber
weggelassen.

## Grundbefehl

Die einfachste Mail: Betreff, Empfänger, Absender, Text aus einer Datei.

```bash
printf 'Nachrichtentext hier\n' > $M/body.txt

python3 $B \
  --subject "<betreff>" \
  --to <empfaenger> \
  --from <absender> \
  --text-file $M/body.txt \
  > $M/mail.eml \
  && test -s $M/mail.eml

python3 $B --send $M/mail.eml --to <empfaenger> --from <absender>
```

Den HTML-Part baut der Helper aus dem Text (Leerzeilen werden `<p>`, einfache
Umbrüche `<br>`), solange `--html-file` fehlt. Eine reine Text-Mail ohne
HTML-Part entsteht dabei nicht - der Regelweg ist immer `multipart/alternative`.

## Mehrere Empfänger

Kommasepariert, und zwar an **beiden** Stellen: beim Bau für den `To:`-Header,
beim `--send` für den SMTP-Envelope.

```bash
python3 $B \
  --subject "Betreff" \
  --to "alice@example.com,bob@example.com" \
  --from <absender> \
  --text-file $M/body.txt \
  > $M/mail.eml \
  && test -s $M/mail.eml

python3 $B --send $M/mail.eml \
  --to "alice@example.com,bob@example.com" --from <absender>
```

Genau hier ist die Ergebnisprüfung nicht optional: lehnt der Relay **einen**
der Empfänger ab, läuft der Versand fuer die übrigen durch. `--send` fängt
das ab (siehe SKILL.md, „Ergebnis prüfen").

## HTML-Body

Eigene HTML-Fassung statt der aus dem Text erzeugten:

```bash
python3 $B \
  --subject "Betreff" \
  --to <empfaenger> \
  --from <absender> \
  --text-file $M/body.txt \
  --html-file $M/body.html \
  > $M/mail.eml \
  && test -s $M/mail.eml

python3 $B --send $M/mail.eml --to <empfaenger> --from <absender>
```

**Nie dieselbe Datei an `--text-file` und `--html-file`** - der HTML-Part hätte
dann kein einziges Tag und käme beim Empfänger als eine einzige Zeile an.

## Dateianhang

Ein `--attach` je Datei, mit **absolutem** Pfad. Das `@`-Präfix von `swaks`
entfällt, den MIME-Type errät der Helper aus der Endung:

```bash
python3 $B \
  --subject "Betreff" \
  --to <empfaenger> \
  --from <absender> \
  --text-file $M/body.txt \
  --attach /absoluter/pfad/zur/datei.ext \
  > $M/mail.eml \
  && test -s $M/mail.eml

python3 $B --send $M/mail.eml --to <empfaenger> --from <absender>
```

## Mehrere Anhänge

`--attach` schlicht wiederholen:

```bash
python3 $B \
  --subject "Mehrere Anhänge" \
  --to <empfaenger> \
  --from <absender> \
  --text-file $M/body.txt \
  --attach /pfad/zu/datei1.md \
  --attach /pfad/zu/datei2.pdf \
  > $M/mail.eml \
  && test -s $M/mail.eml

python3 $B --send $M/mail.eml --to <empfaenger> --from <absender>
```

Um das Text- und HTML-Part legt der Helper dann ein `multipart/mixed`.
