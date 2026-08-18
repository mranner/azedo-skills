---
name: swaks
description: >
  Sends emails via swaks through a Postfix relay. Use this skill whenever
  the user wants to send an email, forward a file, share documentation, or
  deliver any content by mail — even if they just say "schick mir das",
  "sende das per Mail", "mail me the result", or "send this to X".
  Standardversand ist eine multipart/alternative-Mail (Text + HTML) via
  build_mail.py; zusaetzlich moeglich: reiner Text-Body und Dateianhaenge (any type).
  Empfaenger, Absender und Mailserver kommen als Defaults aus .claude/swaks.json.
  Trigger with /swaks.
---

# swaks – E-Mail versenden

E-Mails werden über `swaks` via einen Postfix-Server versendet.

## Defaults (`.claude/swaks.json`)

Empfänger, Absender, Server und Message-ID-Domain stehen in einer Config-Datei,
nicht in dieser Doku. **Auflösungsreihenfolge:** projektlokal `.claude/swaks.json`
im Arbeitsverzeichnis (Vorrang) → global `~/.claude/swaks.json`.

```json
{
  "to": "ich@example.org",
  "from": "claude@example.org",
  "server": "mail.example.org",
  "message_id_domain": "example.org"
}
```

| Schlüssel           | Wirkung                                                        |
|---------------------|----------------------------------------------------------------|
| `to`                | Default für `--to` (Header und Envelope)                        |
| `from`              | Default für `--from` (Header und Envelope)                      |
| `server`            | Mailserver — **nur Fallback**, wenn die muttrc keinen `smtp_url` hat (siehe Versandweg) |
| `message_id_domain` | Domain der `Message-ID`; ohne Angabe die Domain des Absenders    |

`build_mail.py` liest `to` und `from` selbst — ohne `--to`/`--from` greifen die
Config-Werte, mit Angabe gewinnt die Kommandozeile. Den fertigen Versandweg
(Server, Port, TLS, Anmeldung) loest der Helper ebenfalls auf; vor dem Versand
kontrollieren mit:

```bash
python3 "$SKILL_DIR/build_mail.py" --show-config
```

Fehlt die Config und stehen auch keine `--to`/`--from` auf der Kommandozeile,
bricht der Helper mit einer klaren Meldung ab (kein Versand). Vorlage:
`swaks.json.example` im Skill-Verzeichnis.

**Fehlt die Config, nicht raten und nicht mit Platzhaltern senden** — sonst geht
Post an eine `example.org`-Adresse. Stattdessen die Einrichtung anstossen:

```bash
cp "$SKILL_DIR/swaks.json.example" ~/.claude/swaks.json
# danach to/from/server eintragen
```

`server` ist nur noch der Fallback ohne muttrc-`smtp_url` und taugt dann
ausschliesslich fuer interne Empfaenger (siehe Versandweg). Der regulaere Weg
nach draussen ist der Submission-Port aus der muttrc. `to`/`from` immer
erfragen, nie annehmen.

Abweichende Werte übernimmst du aus der Nutzeranfrage.

**Kommt der Entwurf aus `mail-as-me`**, gelten nicht diese Defaults, sondern der
`send`-Block aus dem Profil (`~/.claude/mail-as-me/<profil>/config.json`): `send.from`
als Absender (Header **und** Envelope), `send.bcc` als stille Kopie (**nur** im
Envelope-`--to`). Das ist ohne Rückfrage anzuwenden — eine Mail in der Stimme des
Nutzers, die vom Default-Absender kommt, ist beim Empfänger falsch. Details im
mail-as-me-Skill, Abschnitt „Versand".

## Versandweg und Authentifizierung

**Nicht `--server` von Hand setzen.** Den Versandweg loest `build_mail.py` auf und
gibt ihn als `SWAKS_OPT_*`-Variablen aus; `swaks` liest diese Umgebungsvariablen
selbst. Das Passwort steht damit in der Prozessumgebung und nicht in der
Kommandozeile, wo jedes `ps` es mitliest.

```bash
ENV=$(python3 ~/.claude/skills/swaks/build_mail.py --swaks-env) \
  && test -n "$ENV" \
  && eval "$ENV"
```

Danach braucht `swaks` weder `--server` noch `--port` noch Auth-Optionen. Welcher
Weg dabei herauskommt, zeigt `--show-config` (Passwort maskiert):

```bash
python3 ~/.claude/skills/swaks/build_mail.py --show-config
```

### Woher die Zugangsdaten kommen

Aus der **muttrc** — derselben Datei, aus der auch der `imap`-Skill liest. Es gibt
bewusst **keine** zweite Credential-Datei:

```
set smtp_url  = "smtp://<user>@mail.example.at:587/"
set smtp_pass = "..."
```

`smtp://` bedeutet STARTTLS (Default-Port 587), `smtps://` implizites TLS
(Default-Port 465). Ein Port in der URL gewinnt. Das Passwort wird in dieser
Reihenfolge gesucht: in der URL selbst, dann `set smtp_pass`, dann das
`imap_pass` desselben Hosts aus dem `account-hook` — in der Praxis ist das
dasselbe Konto. Backticks funktionieren wie bei mutt, ein Keystore statt
Klartext ist also moeglich:

```
set smtp_pass = `pass show mail/example`
```

Nennt `smtp_url` einen Benutzer, findet sich aber **kein** Passwort, bricht
`build_mail.py` ab, statt unauthentifiziert zu senden.

### Fallback ohne muttrc

Fehlt die muttrc oder steht dort kein `smtp_url`, bleibt es beim bisherigen
Verhalten: `server` aus `swaks.json`, Port 25, ohne Auth und ohne TLS.

Das traegt nur, solange die **Quell-IP im Relay privilegiert** ist
(`mynetworks`). Laeuft der Skill von einer dynamischen Leitung aus, nimmt der
Relay zwar Mail an azedo-interne Adressen an, weist externe Empfaenger aber mit
`454 4.7.1 Relay access denied` ab. Der Fehler faellt im Alltag nicht auf, weil
die interne Post weiter durchgeht — er trifft genau die Mails nach draussen.
Deshalb ist die muttrc-Variante der Normalfall und der Fallback die Ausnahme.

## Kontakte

Bekannte Empfänger sind in `.claude/swaks-contacts.tsv` im Arbeitsverzeichnis hinterlegt (TSV: `kurzname<TAB>email`, eine Zeile pro Kontakt).

**Lookup:** `grep -i <name> .claude/swaks-contacts.tsv` — liefert direkt die Zeile mit der E-Mail-Adresse (zweites Feld).

Wenn der User einen Namen statt einer E-Mail-Adresse nennt (z.B. "schick das an Karin"), zuerst per grep nachschlagen. Nur wenn kein Treffer: nachfragen.

Neue Kontakte nach dem Versand ergänzen:

```bash
printf '%s\t%s\n' "kurzname" "email@adresse" >> .claude/swaks-contacts.tsv
```

## Signatur

Zwei Signaturdateien, **automatisch aufgelöst** von `build_mail.py` – ohne `--sig-*-file` musst du nichts angeben:

- **Standard (global):** `~/.claude/swaks-signature.txt` / `~/.claude/swaks-signature.html`
- **Projektlokaler Override (Vorrang):** `.claude/swaks-signature.txt` / `.html` im Arbeitsverzeichnis, falls vorhanden

Auflösungsreihenfolge je Datei: projektlokal `.claude/` **vor** global `~/.claude/`; existiert keine, wird schlicht keine Signatur angehängt (kein Fehler). Explizite `--sig-text-file`/`--sig-html-file` überschreiben die Auto-Auflösung – ein **explizit** angegebener Pfad muss existieren (sonst Abbruch).

Beim Standardversand (Multipart, siehe unten) hängt `build_mail.py` beide an – Text-Signatur mit Leerzeile Abstand, HTML-Signatur als Block. Bei reinem Text-Body nur die `.txt`-Signatur.

**Wichtig – die globale Signatur ist die persönliche des Nutzers** (Name und Firmenwortlaut stehen in der Signaturdatei, nicht hier). Geht die Mail unter der eigenen Adresse des Nutzers raus ("in seinem Namen") → **immer** die globale Signatur dranlassen, Auto-Auflösung genügt. Das ist **kein** Ausschlussgrund. `--no-sig` hier nur, wenn der Nutzer das **ausdrücklich** sagt.

Die Signatur wird **nicht** angehängt wenn:

- Der User explizit "ohne Signatur" / "no sig" sagt → `--no-sig` an `build_mail.py` übergeben (schaltet auch die Standard-Signatur ab)
- Die Mail im Namen einer **dritten** Person verfasst wird – **weder der Nutzer noch Claude**, sondern ein anderer `--from` → dann keine Standard-Signatur, ggf. deren eigene per `--sig-*-file`. Der Wechsel vom Default-Absender (`from` aus der Config) auf die eigene Adresse des Nutzers ist **kein** solcher Fall (s.o.).

## Encoding

Immer UTF-8 Header mitgeben, damit Umlaute korrekt ankommen:

```
--header "Content-Type: text/plain; charset=utf-8" \
--header "Content-Transfer-Encoding: 8bit"
```

Für HTML-Mails stattdessen `text/html; charset=utf-8` (siehe Abschnitt HTML-Body).

## Standardversand: Multipart (Text + HTML)

**Default für zusammengesetzte Mails.** Es wird eine `multipart/alternative`-Mail erzeugt (Text- **und** HTML-Part im selben Objekt) – gut für Copy/Paste in Thunderbird und beim Weiterleiten, mit Fallback für Plain-Text-Clients. HTML bewusst schlicht halten (Absätze `<p>`, Umbrüche `<br>`, keine CSS-Spielereien).

Ablauf: `build_mail.py` baut die MIME-DATA (korrekte Boundaries/Encoding, hängt Signaturen an) in eine Datei, danach geht diese per `swaks --data @<datei>` raus.

1. Text-Body als `.txt` und HTML-Body als `.html` in `.tmp/` schreiben (jeweils **ohne** Signatur – die hängt der Helper an).
2. Versandweg laden, MIME-DATA bauen, senden, Ergebnis prüfen. **Erst in eine Datei bauen, dann senden** – nicht direkt in `swaks` pipen: schlägt der Bau fehl (Exit ≠ 0 oder Interpreter nicht gefunden), würde `swaks` sonst auf leerem STDIN laufen und seine eingebaute **Default-Test-Mail** verschicken. Die `&&`-Kette stoppt vor `swaks`, sobald der Bau fehlschlägt oder die Datei leer ist:

```bash
ENV=$(python3 ~/.claude/skills/swaks/build_mail.py --swaks-env) \
  && test -n "$ENV" \
  && python3 ~/.claude/skills/swaks/build_mail.py \
      --subject "Betreff" \
      --to "empfaenger@example.com" \
      --from <absender> \
      --text-file .tmp/body.txt \
      --html-file .tmp/body.html \
      > .tmp/mail.eml \
  && test -s .tmp/mail.eml \
  && ( eval "$ENV"; swaks \
      --to "empfaenger@example.com" \
      --from <absender> \
      --data @.tmp/mail.eml ) > .tmp/swaks.log 2>&1
RC=$?

test $RC -eq 0 && grep -q "queued as" .tmp/swaks.log \
  && grep "queued as" .tmp/swaks.log \
  || echo "FEHLGESCHLAGEN (rc=$RC) — nicht versendet, siehe .tmp/swaks.log"
```

Die Prüfung am Ende ist **kein Beiwerk** – ohne sie geht ein Reject als Erfolg durch (siehe „Ergebnis prüfen").

Hinweise:
- `--to`/`--from` bei **beiden** (Helper *und* swaks) angeben: der Helper setzt die Header, swaks den SMTP-Envelope.
- **Cc:** `--cc "adr"` an `build_mail.py` setzt den sichtbaren `Cc:`-Header. Die Cc-Adresse **zusätzlich** in den swaks-Envelope `--to` aufnehmen (kommasepariert), sonst wird sie nicht zugestellt.
- **Bcc:** `--bcc "adr"` an `build_mail.py` setzt **bewusst keinen** Header (sonst wären die Empfänger sichtbar). Die Bcc-Adresse **nur** in den swaks-Envelope `--to` aufnehmen — sie bleibt für die anderen Empfänger unsichtbar. Beispiel: Header via `build_mail.py --to a@x --cc cc@x --bcc bcc@x`, Envelope via `swaks --to "a@x,cc@x,bcc@x" …`.
- **Leerer Body / Bau-Fehler:** `build_mail.py` bricht mit Exit ≠ 0 ab, wenn Text *und* HTML leer sind. Deshalb **nie direkt in `swaks` pipen** — bei einem Bau-Fehler (Exit ≠ 0 oder Interpreter nicht gefunden) läuft `swaks` sonst auf leerem STDIN und sendet seine eingebaute Default-Test-Mail. Immer erst in eine Datei bauen und mit `&& test -s <datei> && swaks … --data @<datei>` absichern. `set -o pipefail` allein genügt **nicht**, da `swaks` in der Pipe trotzdem startet.
- **`--data` braucht zwingend das `@`:** `swaks --data <datei>` liest die Datei **nicht**, sondern verschickt den **Pfad als Body-Text**. Es gibt keine Fehlermeldung — swaks quittiert mit `250 Ok`, zugestellt wird eine Mail ohne Betreff und ohne die gebauten Header, mit dem Dateinamen als einzigem Inhalt. Beim Empfänger sieht das nach Spam oder kompromittiertem Konto aus, und zurückholen lässt es sich nicht. Immer `--data @<datei>` schreiben. Gegenprobe direkt nach dem Versand: die `size=`-Angabe der Queue-ID im Maillog des Relays gegen die Größe der `.eml` halten — ein paar hundert Bytes statt einiger KB heißt, das `@` hat gefehlt.
- **Signatur:** wird automatisch aus `~/.claude/swaks-signature.*` (bzw. projektlokal `.claude/`) aufgelöst – die `--sig-*-file`-Zeilen sind **optional** und nur als expliziter Override nötig. Ganz weglassen: `--no-sig`.
- **Antwort auf eine Mail:** `--quote-text-file` / `--quote-html-file` hängen den Zitatblock **unter** Body und Signatur an (Top-Posting), `--in-reply-to` / `--references` setzen die Threading-Header. Der Quote wird **nicht getippt**, sondern mit `imap quote` erzeugt — siehe eigener Abschnitt unten.
- **Anhänge:** pro Datei ein `--attach <pfad>` an `build_mail.py` – dann wird `multipart/mixed` um das Text+HTML-Part gelegt (MIME-Type wird automatisch erraten):

```bash
python3 ~/.claude/skills/swaks/build_mail.py ... \
  --attach /pfad/zu/datei1.pdf \
  --attach /pfad/zu/datei2.png \
  > .tmp/mail.eml \
  && test -s .tmp/mail.eml \
  && swaks --to "..." --from <absender> --data @.tmp/mail.eml
```

Die folgenden Abschnitte (reiner Text-Body, HTML-Body, `--attach` direkt an swaks) sind **einfachere Sonderfälle** – nur nutzen, wenn explizit nur Text gewünscht ist oder es rein um einen Dateiversand ohne formatierten Body geht.

## Ergebnis pruefen — Pflicht nach jedem Versand

`swaks` meldet Fehler ueber den **Exit-Code** (gemessen: 23 bei Ablehnung auf
`MAIL FROM`, 24 auf `RCPT TO`, 0 bei Annahme). Verlorengehen kann das nicht,
uebersehen schon: in der langen Protokollausgabe steht der Reject als eine Zeile
unter dreissig. Deshalb wird das Ergebnis **nicht gelesen, sondern geprueft**.

Die `&&`-Kette beim Bau sichert nur die `.eml` ab, nicht den Versand. Dafuer die
Ausgabe mitschreiben und danach beides pruefen — Exit-Code **und** Queue-ID:

```bash
( eval "$ENV"; swaks --to "empfaenger@example.com" --from <absender> \
    --data @.tmp/mail.eml ) > .tmp/swaks.log 2>&1
RC=$?

grep -E "queued as|^ *<[~-]+ +2[0-9][0-9] " .tmp/swaks.log | tail -3

test $RC -eq 0 && grep -q "queued as" .tmp/swaks.log \
  && echo "OK — versendet" \
  || echo "FEHLGESCHLAGEN (rc=$RC) — nicht versendet, siehe .tmp/swaks.log"
```

**Beides pruefen, nicht nur eines.** Der Exit-Code allein uebersieht den Fall
„`@` bei `--data` vergessen" (swaks quittiert mit `250 Ok`, verschickt aber den
Pfad als Body). Die Queue-ID allein uebersieht nichts, ist aber nur zusammen mit
`rc=0` aussagekraeftig.

**Fehlschlag heisst: die Mail ist nicht raus.** Das dem Nutzer so sagen, mit dem
Statuscode aus dem Log. Nie „versendet" melden, ohne die Queue-ID gesehen zu
haben — der Empfaenger merkt den Ausfall sonst, der Absender nicht.

Bei Erfolg zusaetzlich die Gegenprobe auf das fehlende `@`: die `size=`-Angabe
zur Queue-ID im Maillog gegen die Groesse der `.eml` halten. Ein paar hundert
Bytes statt einiger KB heisst, es ging der Dateiname statt der Mail raus.

## Antwort auf eine Mail (Zitat + Threading)

Zwei Dinge unterscheiden eine Antwort von einer neuen Mail: der **Zitatblock** und die
**Threading-Header**. Beide kommen fertig aus `imap quote` und werden hier nur noch
eingesetzt — von Hand getippte `> `-Präfixe weichen bei jeder Mail leicht ab und
ignorieren `format=flowed`.

```bash
Q=.tmp/reply
mkdir -p $Q

ENV=$(python3 ~/.claude/skills/swaks/build_mail.py --swaks-env)

python3 ~/.claude/skills/imap/imap quote <uid> -a <konto> > $Q/quote.txt
python3 ~/.claude/skills/imap/imap quote <uid> -a <konto> --format html > $Q/quote.html
python3 ~/.claude/skills/imap/imap quote <uid> -a <konto> --json > $Q/quote.json

IRT=$(python3 -c "import json;print(json.load(open('$Q/quote.json'))['reply']['in_reply_to'])")
REF=$(python3 -c "import json;print(json.load(open('$Q/quote.json'))['reply']['references'])")

python3 ~/.claude/skills/swaks/build_mail.py \
  --subject "Re: <betreff>" \
  --to "empfaenger@example.com" \
  --text-file $Q/body.txt \
  --html-file $Q/body.html \
  --quote-text-file $Q/quote.txt \
  --quote-html-file $Q/quote.html \
  --in-reply-to "$IRT" \
  --references "$REF" \
  > $Q/mail.eml \
  && test -s $Q/mail.eml \
  && ( eval "$ENV"; swaks --to "empfaenger@example.com" --data @$Q/mail.eml ) \
     > $Q/swaks.log 2>&1
grep -q "queued as" $Q/swaks.log && grep "queued as" $Q/swaks.log \
  || echo "FEHLGESCHLAGEN — nicht versendet, siehe $Q/swaks.log"
```

- **Position:** Antwort oben, Zitat unten (Top-Posting). Die Reihenfolge im fertigen Part ist Body → Signatur → Zitat. Der Body-Text enthält also **kein** Zitat, das hängt der Helper an.
- **Beide Parts:** Der Quote geht in den Text- **und** den HTML-Part. Fehlt `--quote-html-file`, wird die HTML-Fassung aus dem Text escaped nachgebaut (`<blockquote type="cite">` mit `<br>`). Umgekehrt geht nicht: `--quote-html-file` **ohne** `--quote-text-file` bricht ab, sonst hätte ein Part das Zitat und der andere nicht.
- **Leere Quote-Datei bricht ab.** Sie entsteht, wenn `imap quote` fehlschlägt (falsche UID, Mail inzwischen verschoben) und die Ausgabe trotzdem umgeleitet wurde. Ohne diese Prüfung ginge die Antwort still ohne Zitat raus.
- **`reply`, nicht die Originalheader:** `--in-reply-to` und `--references` kommen aus dem Feld `reply` des `--json` — das sind die Werte für die **Antwort**. Die gleichnamigen Felder auf oberster Ebene sind die Header der Originalmail und gehören **nicht** hierher.
- **Ohne Threading-Header startet die Antwort beim Empfänger einen neuen Thread.** Das fällt beim Versand nicht auf, sondern erst beim Gegenüber — und dort nur als "die Antwort ist untergegangen".
- **Betreff:** `Re: ` genau einmal. Trägt der Originalbetreff schon `Re:` oder `AW:`, bleibt das vorhandene Präfix stehen.

Kommt der Entwurf aus `mail-as-me`, ist der `imap quote`-Aufruf dort ohnehin
Pflichtschritt — siehe dessen SKILL.md.

## Grundbefehl

```bash
swaks \
  --to <empfänger> \
  --from <absender> \
  --header "Subject: <betreff>" \
  --header "Content-Type: text/plain; charset=utf-8" \
  --header "Content-Transfer-Encoding: 8bit"
```

## Body (Freitext)

```bash
swaks \
  --to <empfaenger> \
  --from <absender> \
  --header "Subject: Betreff" \
  --header "Content-Type: text/plain; charset=utf-8" \
  --header "Content-Transfer-Encoding: 8bit" \
  --body "Nachrichtentext hier"
```

## Mehrere Empfänger

Mehrere Adressen kommasepariert an `--to` übergeben:

```bash
swaks \
  --to "alice@example.com,bob@example.com" \
  --from <absender> \
  --header "Subject: Betreff" \
  --header "Content-Type: text/plain; charset=utf-8" \
  --header "Content-Transfer-Encoding: 8bit" \
  --body "Nachricht an mehrere Empfänger."
```

## HTML-Body

Für HTML-Mails `Content-Type: text/html` setzen:

```bash
swaks \
  --to <empfaenger> \
  --from <absender> \
  --header "Subject: Betreff" \
  --header "Content-Type: text/html; charset=utf-8" \
  --header "Content-Transfer-Encoding: 8bit" \
  --body "<html><body><h1>Titel</h1><p>Inhalt</p></body></html>"
```

## Dateianhang

Wichtig: Dateipfad **immer** mit `@`-Präfix übergeben, sonst wird der Pfad als Text gesendet statt die Datei einzulesen.

```bash
swaks \
  --to <empfaenger> \
  --from <absender> \
  --header "Subject: Betreff" \
  --body "Siehe Anhang." \
  --attach-type <mime-type> \
  --attach "@/absoluter/pfad/zur/datei.ext"
```

### Häufige MIME-Types

| Dateiendung | `--attach-type`       |
|-------------|-----------------------|
| `.md`       | `text/markdown`       |
| `.txt`      | `text/plain`          |
| `.pdf`      | `application/pdf`     |
| `.html`     | `text/html`           |
| `.json`     | `application/json`    |
| `.csv`      | `text/csv`            |
| `.zip`      | `application/zip`     |
| `.png`      | `image/png`           |
| `.jpg`      | `image/jpeg`          |

## Mehrere Anhänge

Für jeden Anhang ein eigenes `--attach-type` / `--attach`-Paar:

```bash
swaks \
  --to <empfaenger> \
  --from <absender> \
  --header "Subject: Mehrere Anhänge" \
  --body "Zwei Dateien im Anhang." \
  --attach-type text/markdown \
  --attach "@/pfad/zu/datei1.md" \
  --attach-type application/pdf \
  --attach "@/pfad/zu/datei2.pdf"
```

## Ablauf

1. **Empfänger auflösen:** Wenn ein Name statt E-Mail-Adresse genannt wird, `grep -i <name> .claude/swaks-contacts.tsv` ausführen. Bei Treffer: E-Mail aus zweitem Feld verwenden. Bei keinem Treffer: nachfragen.
2. **Versandart wählen:** Default ist **Multipart (Text + HTML)** via `build_mail.py`. Nur reinen Text senden, wenn der User das will oder es rein um einen Dateiversand ohne formatierten Body geht.
3. **Body erstellen:** Für Multipart Text- und HTML-Body in `.tmp/` ablegen (ohne Signatur). HTML schlicht halten.
4. **Signatur:** wird automatisch aufgelöst (global `~/.claude/swaks-signature.*`, projektlokal `.claude/` mit Vorrang) – nichts zu übergeben. Unter der eigenen Adresse des Nutzers **immer** dranlassen (globale Signatur = dessen persönliche). `--no-sig` nur bei explizitem "ohne Signatur" oder einem **dritten** Absender (weder der Nutzer noch Claude); für eine abweichende Signatur explizit `--sig-text-file`/`--sig-html-file`.
5. Fehlende Angaben aus dem Kontext ableiten (Betreff, Body, Anhänge).
6. Befehl zusammenbauen und dem Nutzer kurz zeigen; auf Bestätigung warten – außer der Nutzer hat bereits „ja" gesagt oder den Versand klar angeordnet.
7. **Versandweg laden** (`eval` des `--swaks-env`, siehe Versandweg), Befehl ausführen, Ausgabe mitschreiben und **prüfen** — Exit-Code *und* `queued as` (siehe „Ergebnis prüfen"). Nur bei beidem „versendet" melden, sonst den Fehlschlag mit Statuscode nennen.
8. **Kontakt ergänzen:** Wenn eine neue E-Mail-Adresse verwendet wurde, die noch nicht in `.claude/swaks-contacts.tsv` steht, per `printf` anhängen.

## Hinweise

- `--subject` existiert in dieser swaks-Version nicht → immer `--header "Subject: ..."` verwenden.
- MX-Routing ist nicht verfügbar (Net::DNS fehlt) – kein Problem, da ein fester Relay verwendet wird.
- Erfolg erkennbar an: `250 2.0.0 Ok: queued as <ID>` **bei Exit-Code 0**. Beides prüfen, nicht nur eines.
- Zum Ausprobieren einer Route ohne Zustellung: `--quit-after RCPT` — die Verbindung endet vor `DATA`, es geht nichts raus.

