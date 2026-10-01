# mail-as-me - Antworten: Zitat und Threading

**Inhalt:** Betreff und Empfänger aus `quote --json` · Position des Zitats · vollständiger Ablauf (Zitat, Threading, Betreff, Empfänger, Bau, Versand) · Betreff-Präfix · warum die Threading-Header Pflicht sind · Antwort auf eine `.eml`

Bei einer Antwort kommen fünf Dinge nicht aus dem Entwurf, sondern aus `imap quote`:
der **Text-Quote**, der **HTML-Quote**, die beiden **Threading-Header**, der **Betreff**
und die **Empfänger**. Der Grund ist derselbe wie beim humanizer-de-Audit: was das
Modell selbst tippt, weicht bei jeder Mail leicht ab. Das alles ist Formatarbeit, keine
Formulierungsarbeit.

**Betreff und Empfänger stehen in `quote --json` fertig drin** (Feld `reply`, mit
`--me <send.from>` aufgerufen) - sie werden von dort übernommen, nicht abgeschrieben
und nicht aus dem Auftrag rekonstruiert:

- **Betreff** = `reply.subject`: `Re: ` davor, außer es steht schon ein `Re:`/`AW:`
  dran; die Antwort auf eine Weiterleitung heißt `Re: Fwd: ...`. Ein abgetippter
  Betreff verliert genau die Zeichen, an denen der Mailclient den Thread erkennt:
  eine Ticketnummer in eckigen Klammern, ein `AW:` der Gegenseite, ein Umlaut aus
  einer RFC-2047-Kodierung.
- **Empfänger** = `reply.to` (Absender), bei Reply-All `reply.all` (From, To und Cc
  ohne die eigene Adresse aus `--me`). Aus dem Auftrag kommt höchstens eine
  ausdrückliche Abweichung ("nur an X"), nicht die Standardbesetzung.

Wer die Empfänger aus dem Auftrag statt aus den Kopfdaten nimmt, verliert still den
Mitleser im `Cc` -- für den Absender sieht die Antwort vollständig aus.

**Position: Antwort oben, Zitat unten** (Top-Posting). Die Reihenfolge im fertigen
Text-Part ist Antwort -> Signatur -> Zitat; `build_mail.py` setzt sie so zusammen,
solange der Quote über `--quote-text-file`/`--quote-html-file` hereinkommt. Der Entwurf
selbst enthält also **kein** Zitat. Ein von Hand getipptes Zitat - auch eines, das
ein übernommener Entwurf (`rewrite`) mitbringt - wird durch das erzeugte ersetzt:
selbst gesetzte `> `-Präfixe sehen auf den ersten Blick gleich aus, ignorieren aber
`format=flowed` und die Threading-Header.

UIDs sind ordner-lokal. Liegt die Mail nicht in der INBOX und fehlt `-f`, zitiert
`quote` die gleichnamige UID der INBOX, also eine fremde Mail - ohne Fehlermeldung.
Ist nur die Message-ID bekannt, löst `quote -m "<message-id>"` Konto, Ordner und UID
selbst auf.

```bash
Q=$(mktemp -d .tmp/reply.XXXXXX)
IMAP=~/.claude/skills/imap/imap
B=~/.claude/skills/swaks/build_mail.py

# 1. Zitat und Threading erzeugen -- nicht tippen.
#    -f gehört dazu, sobald die Mail nicht in der INBOX liegt (UIDs sind
#    ordner-lokal); alternativ -m "<message-id>" statt uid/-a/-f.
python3 $IMAP quote <uid> -a <konto> -f <ordner> > $Q/quote.txt
python3 $IMAP quote <uid> -a <konto> -f <ordner> --format html > $Q/quote.html
python3 $IMAP quote <uid> -a <konto> -f <ordner> --json --me ich@example.org > $Q/quote.json

# 2. Threading-Header, Betreff und Empfänger aus dem Feld `reply`
#    (nicht die Header der Originalmail); TO=reply.all für Reply-All
R="import json,sys;print(json.load(open('$Q/quote.json'))['reply'][sys.argv[1]])"
IRT=$(python3 -c "$R" in_reply_to)
REF=$(python3 -c "$R" references)
SUBJ=$(python3 -c "$R" subject)
TO=$(python3 -c "$R" to)

# 3. Mail bauen -- Body ohne Zitat, der Helper hängt es unter die Signatur
python3 $B \
  --subject "$SUBJ" \
  --to "$TO" \
  --from ich@example.org \
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

# 4. Versand als eigener Befehl, mit Ablage in Gesendet
#    (ohne send.account: --bcc <send.bcc> an Bau und Versand statt --file-sent)
python3 $B --send $Q/mail.eml \
  --to "$TO" --from ich@example.org --file-sent <send.account>
```

Zum Betreff: `Re: ` wird einmal vorangestellt - `Re: AW: Re: ...` ist ein sicheres
Zeichen dafür, dass der Betreff zusammengetippt statt übernommen wurde. Die
Fallunterscheidung steckt deshalb in `imap quote` und nicht im Kopf des Modells.

**Warum die Threading-Header nicht optional sind:** ohne `In-Reply-To` und `References`
startet die Antwort im Mailclient des Empfängers einen **neuen** Thread. Das fällt
beim Versand nicht auf, sondern erst beim Gegenüber -- und dort auch nur als
diffuses "die Antwort ist irgendwo untergegangen".

**Liegt die Mail als `.eml` statt im Postfach**, gibt es keine UID -- dann bleibt nur
der handgebaute Weg (Betreff und Empfänger kommen dort aus den Kopfzeilen der `.eml`,
ebenfalls nicht aus dem Auftrag). Das ist der einzige Fall, in dem das Zitat nicht aus `imap quote`
kommt; in der Ausführungszeile steht dann `Quote: aus .eml` statt einer UID.
