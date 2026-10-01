# mail-as-me - Antworten: Zitat und Threading

**Inhalt:** Betreff und Empfaenger aus `quote --json` · Position des Zitats · vollstaendiger Ablauf (Zitat, Threading, Betreff, Empfaenger, Bau, Versand) · Betreff-Praefix · warum die Threading-Header Pflicht sind · Antwort auf eine `.eml`

Bei einer Antwort kommen fuenf Dinge nicht aus dem Entwurf, sondern aus `imap quote`:
der **Text-Quote**, der **HTML-Quote**, die beiden **Threading-Header**, der **Betreff**
und die **Empfaenger**. Der Grund ist derselbe wie beim humanizer-de-Audit: was das
Modell selbst tippt, weicht bei jeder Mail leicht ab. Das alles ist Formatarbeit, keine
Formulierungsarbeit.

**Betreff und Empfaenger stehen in `quote --json` bereits drin** (`subject`, `from`,
`to`, `cc`) -- sie werden von dort uebernommen, nicht abgeschrieben und nicht aus dem
Auftrag rekonstruiert:

- **Betreff** = `subject` plus ein vorangestelltes `Re: `. Ein abgetippter Betreff
  verliert genau die Zeichen, an denen der Mailclient den Thread erkennt: eine
  Ticketnummer in eckigen Klammern, ein `AW:` der Gegenseite, ein Umlaut aus einer
  RFC-2047-Kodierung.
- **Empfaenger** = `from`; bei Reply-All zusaetzlich `to` und `cc`, **abzueglich der
  eigenen Adressen** aus `config.json.send`. Aus dem Auftrag kommt hoechstens eine
  ausdrueckliche Abweichung ("nur an X"), nicht die Standardbesetzung.

Wer die Empfaenger aus dem Auftrag statt aus den Kopfdaten nimmt, verliert still den
Mitleser im `Cc` -- fuer den Absender sieht die Antwort vollstaendig aus.

**Position: Antwort oben, Zitat unten** (Top-Posting). Die Reihenfolge im fertigen
Text-Part ist Antwort -> Signatur -> Zitat; `build_mail.py` setzt sie so zusammen,
solange der Quote ueber `--quote-text-file`/`--quote-html-file` hereinkommt. Der Entwurf
selbst enthaelt also **kein** Zitat.

```bash
Q=$(mktemp -d .tmp/reply.XXXXXX)
IMAP=~/.claude/skills/imap/imap
B=~/.claude/skills/swaks/build_mail.py

# 1. Zitat und Threading erzeugen -- nicht tippen.
#    -f gehoert dazu, sobald die Mail nicht in der INBOX liegt (UIDs sind
#    ordner-lokal); alternativ -m "<message-id>" statt uid/-a/-f.
python3 $IMAP quote <uid> -a <konto> -f <ordner> > $Q/quote.txt
python3 $IMAP quote <uid> -a <konto> -f <ordner> --format html > $Q/quote.html
python3 $IMAP quote <uid> -a <konto> -f <ordner> --json > $Q/quote.json

# 2. Threading-Header abgreifen (Feld `reply`, nicht die Header der Originalmail)
IRT=$(python3 -c "import json;print(json.load(open('$Q/quote.json'))['reply']['in_reply_to'])")
REF=$(python3 -c "import json;print(json.load(open('$Q/quote.json'))['reply']['references'])")

# 3. Betreff und Empfaenger aus denselben Kopfdaten -- nicht abschreiben.
#    Re: nur, wenn nicht schon ein Re:/AW: dransteht; Reply-All ist
#    from + to + cc minus der eigenen Adressen aus config.json.send.
SUBJ=$(python3 -c "
import json,re
s=json.load(open('$Q/quote.json'))['subject']
print(s if re.match(r'^(re|aw)\s*:', s, re.I) else 'Re: '+s)")
TO=$(python3 -c "
import json,email.utils
q=json.load(open('$Q/quote.json'))
mine={'ich@example.org'}
addrs=email.utils.getaddresses([q['from'], q['to'], q['cc']])
seen=[]
for _,a in addrs:
    if a and a.lower() not in mine and a.lower() not in seen: seen.append(a.lower())
print(','.join(seen))")

# 4. Mail bauen -- Body ohne Zitat, der Helper haengt es unter die Signatur
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
      --expect-marker "<woertliches Stueck aus dem Entwurf>"

# 5. Versand als eigener Befehl, mit Ablage in Gesendet
#    (ohne send.account: --bcc <send.bcc> an Bau und Versand statt --file-sent)
python3 $B --send $Q/mail.eml \
  --to "$TO" --from ich@example.org --file-sent <send.account>
```

Zum Betreff: `Re: ` wird **einmal** vorangestellt. Traegt der Originalbetreff bereits
ein `Re:` (oder das deutsche `AW:`), bleibt es bei dem vorhandenen Praefix -- `Re: AW:
Re: ...` ist ein sicheres Zeichen dafuer, dass der Betreff zusammengetippt statt
uebernommen wurde. `Fwd:`/`WG:` zaehlen **nicht** als Antwort-Praefix: die Antwort
auf eine Weiterleitung heisst `Re: Fwd: ...`. Die Fallunterscheidung steckt deshalb im Snippet oben und nicht im
Kopf des Modells.

**Warum die Threading-Header nicht optional sind:** ohne `In-Reply-To` und `References`
startet die Antwort im Mailclient des Empfaengers einen **neuen** Thread. Das faellt
beim Versand nicht auf, sondern erst beim Gegenueber -- und dort auch nur als
diffuses "die Antwort ist irgendwo untergegangen".

**Liegt die Mail als `.eml` statt im Postfach**, gibt es keine UID -- dann bleibt nur
der handgebaute Weg (Betreff und Empfaenger kommen dort aus den Kopfzeilen der `.eml`,
ebenfalls nicht aus dem Auftrag). Das ist der einzige Fall, in dem das Zitat nicht aus `imap quote`
kommt; in der Ausfuehrungszeile steht dann `Quote: aus .eml` statt einer UID.
