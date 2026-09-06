# swaks - Antworten und Sonderfaelle

Zitat und Threading, einfache Sonderfaelle.

## Antwort auf eine Mail (Zitat + Threading)

Zwei Dinge unterscheiden eine Antwort von einer neuen Mail: der **Zitatblock** und die
**Threading-Header**. Beide kommen fertig aus `imap quote` und werden hier nur noch
eingesetzt — von Hand getippte `> `-Präfixe weichen bei jeder Mail leicht ab und
ignorieren `format=flowed`.

```bash
Q=$(mktemp -d .tmp/reply.XXXXXX)
B=~/.claude/skills/swaks/build_mail.py

python3 ~/.claude/skills/imap/imap quote <uid> -a <konto> > $Q/quote.txt
python3 ~/.claude/skills/imap/imap quote <uid> -a <konto> --format html > $Q/quote.html
python3 ~/.claude/skills/imap/imap quote <uid> -a <konto> --json > $Q/quote.json

IRT=$(python3 -c "import json;print(json.load(open('$Q/quote.json'))['reply']['in_reply_to'])")
REF=$(python3 -c "import json;print(json.load(open('$Q/quote.json'))['reply']['references'])")

python3 $B \
  --subject "Re: <betreff>" \
  --to "empfaenger@example.com" \
  --text-file $Q/body.txt \
  --html-file $Q/body.html \
  --quote-text-file $Q/quote.txt \
  --quote-html-file $Q/quote.html \
  --in-reply-to "$IRT" \
  --references "$REF" \
  --sha-file $Q/mail.sha256 \
  > $Q/mail.eml \
  && test -s $Q/mail.eml \
  && python3 $B --verify $Q/mail.eml \
      --expect-sha256 "$(cat $Q/mail.sha256)" \
      --expect-marker "<wörtliches Stück aus dem Entwurf>"
```

Erst wenn das mit Exit `0` durchgelaufen ist, folgt der Versand als **eigener
Befehl** — `--send` lädt den Versandweg selbst und prüft das Ergebnis:

```bash
python3 $B --send $Q/mail.eml --to "empfaenger@example.com"
```

- **Eigenes Verzeichnis, kein festes `.tmp/reply`.** Genau dieser feste Pfad ist der Kollisionspunkt gewesen: eine zweite Session schrieb dieselbe `mail.eml`, und die Antwort ging mit fremdem Inhalt an den Kunden. `mktemp -d` plus die `--verify`-Zeile schließen das aus.
- **Position:** Antwort oben, Zitat unten (Top-Posting). Die Reihenfolge im fertigen Part ist Body → Signatur → Zitat. Der Body-Text enthält also **kein** Zitat, das hängt der Helper an.
- **Beide Parts:** Der Quote geht in den Text- **und** den HTML-Part. Fehlt `--quote-html-file`, wird die HTML-Fassung aus dem Text escaped nachgebaut (`<blockquote type="cite">` mit `<br>`). Umgekehrt geht nicht: `--quote-html-file` **ohne** `--quote-text-file` bricht ab, sonst hätte ein Part das Zitat und der andere nicht.
- **Leere Quote-Datei bricht ab.** Sie entsteht, wenn `imap quote` fehlschlägt (falsche UID, Mail inzwischen verschoben) und die Ausgabe trotzdem umgeleitet wurde. Ohne diese Prüfung ginge die Antwort still ohne Zitat raus.
- **`reply`, nicht die Originalheader:** `--in-reply-to` und `--references` kommen aus dem Feld `reply` des `--json` — das sind die Werte für die **Antwort**. Die gleichnamigen Felder auf oberster Ebene sind die Header der Originalmail und gehören **nicht** hierher.
- **Ohne Threading-Header startet die Antwort beim Empfänger einen neuen Thread.** Das fällt beim Versand nicht auf, sondern erst beim Gegenüber — und dort nur als "die Antwort ist untergegangen".
- **Betreff:** `Re: ` genau einmal. Trägt der Originalbetreff schon `Re:` oder `AW:`, bleibt das vorhandene Präfix stehen.

Kommt der Entwurf aus `mail-as-me`, ist der `imap quote`-Aufruf dort ohnehin
Pflichtschritt — siehe dessen SKILL.md.

## Einfache Sonderfälle

Die folgenden Blöcke setzen **voraus, dass der Versandweg geladen ist** (siehe
Versandweg und Authentifizierung):

```bash
ENV=$(python3 ~/.claude/skills/swaks/build_mail.py --swaks-env) \
  && test -n "$ENV" && eval "$ENV"
```

**Ohne das fällt `swaks` still auf `localhost:25` zurück**, weil MX-Routing
mangels `Net::DNS` nicht verfügbar ist:

```
*** MX Routing not available: requires Net::DNS.  Using localhost as mail server
```

Auf einem Host, der selbst einen Postfix betreibt, ist das kein Fehler, sondern
ein *anderer* Versandweg: unauthentifiziert über Port 25, mit genau der
Relay-Beschränkung, die externe Empfänger abweist. Es gibt keine Warnung —
die Zeile oben ist der einzige Hinweis, und sie steht im Protokoll, nicht im
Ergebnis. Die Ergebnisprüfung gilt hier deshalb genauso.
