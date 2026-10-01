# mail-as-me - Versand und Entwurfsablage

**Inhalt:** Absender und Ablage aus dem Profil · Bau, Pruefung und Versand · Kontakt ergaenzen · als Entwurf ablegen (`draft`)

## Absender und Ablage aus dem Profil

Gesendet wird ueber **swaks** - dessen Defaults (`--from claude@azedo.at`) sind aber
die von Claude, nicht die des Profils. Eine Mail, die in der eigenen Stimme verfasst
wurde, aber von `claude@azedo.at` kommt, ist beim Empfaenger schlicht falsch. Damit
das nicht bei jedem Versand haendisch nachgezogen werden muss, steht die
Versand-Identitaet im Profil:

```json
"send":  { "from": "ich@example.org", "account": "<imap-konto>" },
"draft": { "account": "<imap-konto>" }
```

`send.from` ist der Absender (fehlt er, gilt der swaks-Default). `send.account` und
`draft.account` sind Aliase aus `imap accounts`: dort landet die Mail in "Gesendet"
bzw. in den Entwuerfen. Eine Bcc-Kopie an sich selbst gibt es nur noch als
Fallback ohne IMAP-Konto (siehe unten): ob die Mail raus ist, belegt die Queue-ID,
ob sie abgelegt ist, das Zuruecklesen nach der Ablage. Ein Bcc an Dritte,
das der Nutzer im Auftrag nennt, geht weiterhin mit.

Welche Kopie der versendeten Mail entsteht, entscheidet das Profil in dieser
Reihenfolge:

1. **`send.account` gesetzt:** `--file-sent <send.account>`. Steht daneben noch
   `send.bcc` im Profil, wird es nicht verwendet: einmal darauf hinweisen und
   anbieten, den Eintrag zu entfernen. Mitgeschickt landete die Kopie zusaetzlich
   zur Ablage in "Gesendet".
2. **Kein `send.account`, aber `send.bcc`:** Bcc an die Adresse aus `send.bcc`, an
   beide Aufrufe (Bau und `--send`), ohne Rueckfrage. Das ist der Weg auf
   Rechnern ohne eingerichtete IMAP-Konten (`imap accounts` leer).
3. **Weder noch:** nicht raten. Liefert `imap accounts` Konten, sie zur Auswahl
   zeigen und die Antwort als `send.account` ins Profil schreiben, damit die Frage
   nur einmal kommt. Ist die Liste leer, nach einer Adresse fuer `send.bcc` fragen.

Fehlt `draft.account`, gilt Schritt 3 sinngemaess; ohne IMAP-Konto gibt es keine
Entwurfsablage.

`send` aus dem geladenen Profil wird ohne Rueckfrage angewendet, wie die Signatur.
Eine Angabe des Nutzers im Auftrag ("schick das von X") hat Vorrang.

## Bau, Pruefung und Versand

`from` geht an beide Aufrufe - den Bau und den Versand. Gebaut und geprueft wird in
einem Befehl, gesendet und abgelegt im naechsten:

```bash
M=$(mktemp -d .tmp/mail.XXXXXX)
B=~/.claude/skills/swaks/build_mail.py

python3 $B \
  --subject "Betreff" \
  --to "empfaenger@example.com" \
  --from ich@example.org \
  --text-file $M/body.txt \
  --html-file $M/body.html \
  --sha-file $M/mail.sha256 \
  > $M/mail.eml \
  && test -s $M/mail.eml \
  && python3 $B --verify $M/mail.eml \
      --expect-sha256 "$(cat $M/mail.sha256)" \
      --expect-marker "<woertliches Stueck aus dem freigegebenen Entwurf>"
```

```bash
python3 $B --send $M/mail.eml \
  --to "empfaenger@example.com" \
  --from ich@example.org \
  --file-sent <send.account>
```

`--file-sent` legt die versendete Datei nach erfolgreichem Versand in "Gesendet"
und liest sie per Message-ID zurueck. Exit `0` heisst gesendet und abgelegt,
`1` nicht gesendet (und nichts abgelegt), `3` gesendet, aber nicht abgelegt. Bei
`3` dem Nutzer genau das sagen und den Befehl aus dem Feld `retry` nennen;
`$M/mail.eml` bleibt dafuer liegen. Details im swaks-Skill, Abschnitt „Ablage".

Ohne `send.account` (Fallback `send.bcc`, siehe oben) statt `--file-sent` an
beide Aufrufe `--bcc <send.bcc>` haengen; Exit `3` gibt es dann nicht.

**Warum `mktemp -d` und die `--verify`-Zeile:** Mit einem festen Pfad wie
`.tmp/mail.eml` schreibt eine parallel laufende Session dieselbe Datei, und der
Versand nimmt, was zuletzt drinstand - mit korrektem Betreff, korrektem Empfaenger
und dem Text einer fremden Mail. Beim Versand faellt das nicht auf: swaks quittiert
die uebertragenen Bytes, nicht die gebauten. Der Marker ist ein woertliches
Stueck aus dem freigegebenen Entwurf; `--verify` dekodiert den Text-Part und
sucht es dort (ein `grep` auf die rohe `.eml` findet es nicht, der Body ist
quoted-printable kodiert). Details im swaks-Skill, Abschnitt "Vor dem Versand
pruefen".

**Nur Text und kein HTML-Entwurf?** Dann `--html-file` weglassen, nicht die
Textdatei ein zweites Mal angeben. Ein HTML-Part aus rohem Text hat kein
einziges Tag und kommt beim Empfaenger in einer einzigen Zeile an - Aufzaehlung,
Tabelle und Zugangsdaten inklusive.

Die Signatur bleibt beim eigenen Absender aus `send.from` dran (die globale
Signatur ist die eigene, siehe swaks-Skill) - der Wechsel des Absenders ist kein
Ausschlussgrund.

## Kontakt ergaenzen (swaks Schritt 11)

Stand die Adresse nicht in `.claude/swaks-contacts.tsv` (bzw. `~/.claude/`), wird
sie nach dem Versand dort angehaengt - sonst ist die naechste Mail an dieselbe
Person wieder ein Ratespiel. Nur fuer Adressen, die ohne Thread wieder gebraucht
werden; Thread-Adressen liefert `imap contacts` jederzeit neu. Details im
swaks-Skill.

## Als Entwurf ablegen (`draft`)

Gebaut wird wie oben, mit zwei Unterschieden: `--for-draft` beim Bau und statt
`--send` die Ablage in die Entwuerfe. Eine Bcc-Kopie an sich selbst entfaellt
auch hier. Ein Bcc an Dritte steht im Entwurf als Header, sonst kennt der
Mailclient es beim Senden nicht; `--send` verweigert eine solche `.eml` deshalb.

```bash
python3 $B --for-draft --subject "Betreff" --to "empfaenger@example.com" \
  --from ich@example.org --text-file $M/body.txt --html-file $M/body.html \
  --sha-file $M/mail.sha256 > $M/mail.eml \
  && test -s $M/mail.eml \
  && python3 $B --verify $M/mail.eml --expect-sha256 "$(cat $M/mail.sha256)" \
      --expect-marker "<woertliches Stueck aus dem freigegebenen Entwurf>"
```

```bash
python3 $B --draft $M/mail.eml --account <draft.account>
```

Abgelegt wird mit `\Draft` und ungelesen, danach per Message-ID zurueckgelesen;
Exit `0` heisst: liegt in den Entwuerfen, das JSON nennt Ordner und UID. Bei einer
Antwort gehoeren Zitat und Threading-Header genauso dazu wie beim Versand. Der
Kontakt wird erst ergaenzt, wenn der Nutzer den Entwurf abgeschickt hat - das
sieht dieser Skill nicht, deshalb entfaellt der Schritt hier.
