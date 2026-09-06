---
name: swaks
description: >
  Versendet E-Mails über swaks und einen Postfix-Relay: Text- und HTML-Mail
  (multipart/alternative), reiner Text-Body, Dateianhänge jeder Art;
  Empfänger und Absender als Defaults aus der Config. Zuständig für den
  Versand, nicht für die Formulierung - soll die Mail nach dem Nutzer
  klingen, vorher mail-as-me den Text schreiben lassen. Auch bei "schick mir
  das", "sende das per Mail", "mail me the result", "send this to X".
  Trigger: /swaks.
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

## Arbeitsverzeichnis: pro Versand ein eigenes

**Nicht in feste Pfade wie `.tmp/mail.eml` oder `.tmp/reply/` bauen.** Laufen zwei
Sessions parallel, schreiben sie dieselben Dateien: Session A baut ihre `.eml`,
Session B überschreibt sie, Session A sendet den Inhalt von B. Der Versand meldet
dabei nichts — swaks quittiert die übertragenen Bytes, nicht die gebauten. Beim
Empfänger steht dann eine fremde Mail unter korrektem Betreff und korrekter
Anrede.

Deshalb bekommt **jeder Versand ein eigenes Verzeichnis**, das kein zweiter
Prozess kennt:

```bash
M=$(mktemp -d .tmp/mail.XXXXXX)
```

Ein `mktemp -d` unter dem Projekt-`.tmp/` reicht; das Scratchpad-Verzeichnis der
Session tut es genauso. Der gemeinsame `.tmp/` bleibt für Artefakte, die
absichtlich sessionübergreifend liegen bleiben.

Das allein genügt nicht — es schließt nur die häufigste Ursache aus. Die Prüfung
unmittelbar vor dem Versand (siehe „Vor dem Versand prüfen") fängt auch die
übrigen ab.

## Standardversand: Multipart (Text + HTML)

**Default für zusammengesetzte Mails.** Es wird eine `multipart/alternative`-Mail erzeugt (Text- **und** HTML-Part im selben Objekt) – gut für Copy/Paste in Thunderbird und beim Weiterleiten, mit Fallback für Plain-Text-Clients. HTML bewusst schlicht halten (Absätze `<p>`, Umbrüche `<br>`, keine CSS-Spielereien).

Ablauf: `build_mail.py` baut die MIME-DATA (korrekte Boundaries/Encoding, hängt Signaturen an) in eine Datei, danach geht diese per `swaks --data @<datei>` raus.

1. Text-Body als `.txt` und HTML-Body als `.html` ins Versand-Verzeichnis `$M` schreiben (jeweils **ohne** Signatur – die hängt der Helper an). Liegt nur Text vor, `--html-file` schlicht weglassen – der Helper baut den HTML-Part daraus (siehe „HTML-Part").
2. MIME-DATA bauen und **prüfen**, dann in einem **zweiten Befehl** senden. **Erst in eine Datei bauen, dann senden** – nicht direkt in `swaks` pipen: schlägt der Bau fehl (Exit ≠ 0 oder Interpreter nicht gefunden), würde `swaks` sonst auf leerem STDIN laufen und seine eingebaute **Default-Test-Mail** verschicken. Die `&&`-Kette stoppt, sobald der Bau fehlschlägt, die Datei leer ist oder die Prüfung anschlägt:

```bash
M=$(mktemp -d .tmp/mail.XXXXXX)
B=~/.claude/skills/swaks/build_mail.py

# Bodies nach $M/body.txt und $M/body.html schreiben, dann:

python3 $B \
    --subject "Betreff" \
    --to "empfaenger@example.com" \
    --from <absender> \
    --text-file $M/body.txt \
    --html-file $M/body.html \
    --sha-file $M/mail.sha256 \
    > $M/mail.eml \
  && test -s $M/mail.eml \
  && python3 $B --verify $M/mail.eml \
      --expect-sha256 "$(cat $M/mail.sha256)" \
      --expect-marker "<wörtliches Stück aus dem freigegebenen Entwurf>"
```

Erst wenn dieser Befehl mit Exit `0` durchgelaufen ist, folgt der Versand als **eigener Befehl**:

```bash
python3 $B --send $M/mail.eml --to "empfaenger@example.com" --from <absender>
```

`--send` lädt den Versandweg selbst, ruft `swaks` auf und prüft das Ergebnis (Exit-Code, `queued as`, abgelehnte Empfänger – siehe „Ergebnis prüfen"). Exit `0` heißt versendet, Exit `1` heißt Fehlschlag; das JSON nennt Queue-ID bzw. Befund, das vollständige swaks-Protokoll steht in `$M/mail.eml.swaks.log`.

**Warum zwei Befehle und nicht eine `&&`-Kette?** Eine Bash-Freigabe greift auf den **Anfang** des Befehls. In einer Kette, die mit `ENV=$(…)` oder `python3 $B --verify …` beginnt, steht der Versand irgendwo in der Mitte und ist von keiner Regel erreichbar – der Versand scheitert dann an der Freigabe, nachdem Recherche, Bau und Prüfung bereits gelaufen sind (CR4613). `python3 $B --send …` steht am Anfang und ist freigebbar. Die Trennung kostet nichts: die Prüfkette davor bricht bei jedem Befund mit Exit ≠ 0 ab, und `--send` prüft die `.eml` nochmals auf Existenz und Größe.

Die Prüfung am Ende ist **kein Beiwerk** – ohne sie geht ein Reject als Erfolg durch (siehe „Ergebnis prüfen").

Hinweise:
- `--to`/`--from` bei **beiden** (Helper *und* swaks) angeben: der Helper setzt die Header, swaks den SMTP-Envelope.
- **Cc:** `--cc "adr"` an `build_mail.py` setzt den sichtbaren `Cc:`-Header. Die Cc-Adresse **zusätzlich** in den swaks-Envelope `--to` aufnehmen (kommasepariert), sonst wird sie nicht zugestellt.
- **Bcc:** `--bcc "adr"` an `build_mail.py` setzt **bewusst keinen** Header (sonst wären die Empfänger sichtbar). Die Bcc-Adresse **nur** in den swaks-Envelope `--to` aufnehmen — sie bleibt für die anderen Empfänger unsichtbar. Beispiel: Header via `build_mail.py --to a@x --cc cc@x --bcc bcc@x`, Envelope via `swaks --to "a@x,cc@x,bcc@x" …`.
- **Leerer Body / Bau-Fehler:** `build_mail.py` bricht mit Exit ≠ 0 ab, wenn Text *und* HTML leer sind. Deshalb **nie direkt in `swaks` pipen** — bei einem Bau-Fehler (Exit ≠ 0 oder Interpreter nicht gefunden) läuft `swaks` sonst auf leerem STDIN und sendet seine eingebaute Default-Test-Mail. Immer erst in eine Datei bauen und mit `&& test -s <datei> && swaks … --data @<datei>` absichern. `set -o pipefail` allein genügt **nicht**, da `swaks` in der Pipe trotzdem startet.
- **`--data` braucht zwingend das `@`:** `swaks --data <datei>` liest die Datei **nicht**, sondern verschickt den **Pfad als Body-Text**. Es gibt keine Fehlermeldung — swaks quittiert mit `250 Ok`, zugestellt wird eine Mail ohne Betreff und ohne die gebauten Header, mit dem Dateinamen als einzigem Inhalt. Beim Empfänger sieht das nach Spam oder kompromittiertem Konto aus, und zurückholen lässt es sich nicht. Immer `--data @<datei>` schreiben. Gegenprobe direkt nach dem Versand: die `size=`-Angabe der Queue-ID im Maillog des Relays gegen die Größe der `.eml` halten — ein paar hundert Bytes statt einiger KB heißt, das `@` hat gefehlt.
- **HTML-Part:** `--html-file` ist **optional**. Fehlt es, baut der Helper den HTML-Part aus dem Text (Leerzeilen werden `<p>`, einfache Umbrüche `<br>`). **Niemals dieselbe Datei an `--text-file` und `--html-file` geben** — der HTML-Part hätte dann kein einziges Tag und käme beim Empfänger als eine einzige Zeile an („in einer Wurst"), inklusive Tabellen und Kennwortlisten. Der Helper erkennt diesen Fall inzwischen, warnt auf stderr und wandelt um; die Warnung ist trotzdem ein Grund, den Aufruf zu korrigieren.
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

## Vor dem Versand prüfen — was `250 Ok` nicht abdeckt

Ein erfolgreicher Rückgabewert von swaks sagt nur, dass der Server die Bytes
angenommen hat. Er sagt **nicht**, dass die richtigen Bytes drinstanden, und
**nicht**, dass sie beim Empfänger lesbar ankommen. Beides ist schon passiert,
beide Male ohne jede Auffälligkeit beim Versand. Die Prüfung gehört deshalb an
die fertige `.eml`, nicht an den Exit-Code:

```bash
python3 $B --verify $M/mail.eml \
  --expect-sha256 "$(cat $M/mail.sha256)" \
  --expect-marker "hier die Zugangsdaten"
```

Exit `0` und ein JSON-Bericht heißt: senden. Exit `1` heißt: **nicht senden**,
den Befund dem Nutzer nennen. Geprüft wird:

| Prüfung | fängt |
|---|---|
| `--expect-sha256` gegen die Datei | die `.eml` wurde zwischen Bauen und Senden überschrieben — typischerweise von einer parallel laufenden Session mit demselben Pfad |
| Text-Part vorhanden und nicht leer | Bau ohne Body |
| HTML-Part enthält Markup | der „Wurst"-Fall: rohem Text als HTML-Part, alles in einer Zeile |
| Text- und HTML-Part nicht identisch | dieselbe Datei an `--text-file` und `--html-file` |
| `--expect-marker` im **dekodierten** Text-Part | die `.eml` trägt nicht den freigegebenen Entwurf |

Weicht der Marker **nur in der Groß-/Kleinschreibung** ab, sagt die Meldung das
ausdrücklich („Marker nur mit abweichender Groß-/Kleinschreibung gefunden") —
dann ist der Marker falsch getippt und nicht die Mail falsch. Der Befund bleibt
trotzdem Exit `1`: erst den Marker korrigieren, dann erneut prüfen.

Zum Marker: ein wörtliches Stück aus dem Entwurf, das in keiner anderen Mail
vorkommt — ein halber Satz genügt. **Ein `grep` auf die rohe `.eml` genügt
dafür nicht**: der Body ist quoted-printable kodiert, Umlaute stehen dort als
`=C3=A4` und Zeilen sind an anderer Stelle umgebrochen als im Entwurf. `--verify`
dekodiert den Part und ebnet Leerraum ein, bevor es vergleicht.

Die `--sha-file`-Datei entsteht beim Bau; ohne sie steht die Prüfsumme auch auf
stderr (`build_mail.py: sha256(DATA) = …`).

## Ergebnis prüfen — Pflicht nach jedem Versand

`swaks` meldet Fehler über den **Exit-Code** (gemessen: 23 bei Ablehnung auf
`MAIL FROM`, 24 auf `RCPT TO`, 0 bei Annahme). Verlorengehen kann das nicht,
übersehen schon: in der langen Protokollausgabe steht der Reject als eine Zeile
unter dreißig. Deshalb wird das Ergebnis **nicht gelesen, sondern geprüft**.

Die `&&`-Kette beim Bau sichert nur die `.eml` ab, nicht den Versand. Die drei
Prüfungen übernimmt deshalb `--send` selbst — Exit `0` heißt versendet, Exit `1`
nennt den Befund im JSON und auf stderr:

```bash
python3 $B --send $M/mail.eml --to "empfänger@example.com" --from <absender>
```

Wer stattdessen von Hand mit `swaks` sendet, muss dieselben drei Prüfungen
nachbauen:

```bash
( eval "$ENV"; swaks --to "empfänger@example.com" --from <absender> \
    --data @.tmp/mail.eml ) > .tmp/swaks.log 2>&1
RC=$?

test $RC -eq 0 && grep -q "queued as" .tmp/swaks.log && ! grep -qE '^<.\*' .tmp/swaks.log \
  && echo "OK — versendet" \
  || { echo "FEHLGESCHLAGEN (rc=$RC) — siehe .tmp/swaks.log"; grep -E '^<.\*' .tmp/swaks.log; }
```

**Alle drei Bedingungen prüfen, nicht eine davon.** Jede deckt einen Fall ab,
den die anderen durchlassen:

| Prüfung | fängt |
|---|---|
| `rc -eq 0` | Verbindungs-, TLS-, Auth- und Totalablehnungen |
| `queued as` | „`@` bei `--data` vergessen" — swaks quittiert mit `250 Ok`, verschickt aber den Pfad als Body |
| kein `^<.\*` | **abgelehnte einzelne Empfänger** bei mehreren Adressen |

Der dritte Punkt ist der Fall aus CR4519 und der unauffälligste: stehen im
Envelope mehrere Empfänger und der Relay lehnt nur **einen** ab, läuft swaks
trotzdem in die DATA-Phase, bekommt für die übrigen ein `250 … queued as` und
endet mit **Exit-Code 0**. Nachgestellt mit einem simulierten Gegenüber
(ein Empfänger angenommen, einer mit `454` abgelehnt): `EXIT=0`, Queue-ID
vorhanden — die ersten beiden Prüfungen melden Erfolg, obwohl die Mail einen
Teil ihrer Empfänger nie erreicht.

Genau so verschwanden die beiden Mails, die dem CR zugrunde liegen: der eigene
Kopie-Empfänger wurde angenommen, der externe abgewiesen. Die Kopie landete
im Postfach und sah aus wie ein erfolgreicher Versand.

`swaks` markiert jede abgelehnte Antwort mit einem `*` an dritter Stelle des
Zeilenpräfixes — unverschlüsselt `<**`, innerhalb einer TLS-Sitzung `<~*`.
Beide trifft `^<.\*`. Im Erfolgsfall ist die Zeilenzahl null (verifiziert).

**Fehlschlag heißt: die Mail ist nicht raus.** Das dem Nutzer so sagen, mit dem
Statuscode aus dem Log. Nie „versendet" melden, ohne die Queue-ID gesehen zu
haben — der Empfänger merkt den Ausfall sonst, der Absender nicht.

Bei Erfolg zusätzlich die Gegenprobe auf das fehlende `@`: die `size=`-Angabe
zur Queue-ID im Maillog gegen die Größe der `.eml` halten. Ein paar hundert
Bytes statt einiger KB heißt, es ging der Dateiname statt der Mail raus.

### Was in der Erfolgsmeldung stehen muss

„Versendet" darf sich **nicht allein auf `250 Ok` stützen** — der Satz bezieht
sich sonst auf das, was übertragen wurde, nicht auf das, was gebaut wurde. In
die Meldung an den Nutzer gehören deshalb vier Angaben:

- die **Queue-ID** aus dem swaks-Log,
- **welche Datei** übertragen wurde (`$M/mail.eml`) mit ihrer **sha256** und Größe,
- die **Empfänger** des Envelope (inklusive Bcc — die stehen in keinem Header),
- **wo die Kopie liegt** (siehe unten).

Mit Prüfsumme und Dateiname kann der Nutzer eine Verwechslung überhaupt erst
erkennen; ohne sie bleibt ihm nur der Betreff, und genau der stimmt im
Verwechslungsfall.

### Ablage: swaks legt nichts in „Gesendet"

`swaks` spricht SMTP und sonst nichts — es gibt **keine Kopie im Sent-Ordner**.
Die einzige Spur ist die Bcc-Kopie im Posteingang (`send.bcc` aus dem
mail-as-me-Profil bzw. eine ausdrücklich gesetzte Bcc-Adresse). Wer die Mail
später sucht, sucht zuerst im falschen Ordner und verliert Zeit.

Deshalb die Kopie **nach dem erfolgreichen Versand selbst ablegen** — mit
`imap append`, das genau dafür da ist:

```bash
python3 ~/.claude/skills/imap/imap append $M/mail.eml -a <konto>
```

Abgelegt wird **die Datei, die versendet wurde** — dieselbe, die an
`swaks --data @…` ging. Ein zweiter Bau wäre eine andere Mail: Message-ID und
`Date` entstehen bei jedem Lauf neu. Liegt dieselbe Message-ID schon im Ordner,
schreibt `append` nichts (`duplicate: true`), ein wiederholter Lauf legt also
keinen zweiten Eintrag an. Details im imap-Skill, Abschnitt „`append`".

**Erst nach dem Versand ablegen, nicht davor.** Eine Kopie in „Gesendet" zu
einer Mail, die der Relay abgewiesen hat, ist eine Falschaussage im Postfach —
und zwar die unauffälligste Sorte.

Geht das nicht (kein IMAP-Konto zur Hand, Ordner nicht auffindbar), dann
wenigstens **die Fundstelle in der Erfolgsmeldung nennen** — „Kopie liegt im
Posteingang von `<konto>` (Bcc), nicht in Gesendet". Ist keine Bcc gesetzt, gibt
es außer dem Maillog des Relays gar keine Spur; dann das ausdrücklich sagen.
Die lokale `$M/mail.eml` ist die dritte Spur, hält aber nur bis zum nächsten
Aufräumen.

## Bausteine und Sonderfaelle

Die vollstaendige Optionsreferenz liegt daneben und wird bei Bedarf gelesen:

| Datei | Inhalt |
|---|---|
| `references/bausteine.md` | Grundbefehl, Freitext-Body, mehrere Empfaenger, HTML-Body, Dateianhaenge, MIME-Types |
| `references/antworten.md` | Antwort auf eine Mail (Zitat + Threading), einfache Sonderfaelle |
| `references/versandweg.md` | Versandweg und Authentifizierung, Kontakte, Signatur, Encoding |

## Ablauf

1. **Empfänger auflösen:** Wenn ein Name statt E-Mail-Adresse genannt wird, `grep -i <name> .claude/swaks-contacts.tsv` ausführen. Bei Treffer: E-Mail aus zweitem Feld verwenden. Bei keinem Treffer: nachfragen.
2. **Versandart wählen:** Default ist **Multipart (Text + HTML)** via `build_mail.py`. Nur reinen Text senden, wenn der User das will oder es rein um einen Dateiversand ohne formatierten Body geht.
3. **Body erstellen:** Versand-Verzeichnis mit `mktemp -d` anlegen (kein fester Pfad, siehe „Arbeitsverzeichnis"), Text- und HTML-Body dort ablegen (ohne Signatur). HTML schlicht halten; liegt nur Text vor, `--html-file` weglassen statt die Textdatei doppelt anzugeben.
4. **Signatur:** wird automatisch aufgelöst (global `~/.claude/swaks-signature.*`, projektlokal `.claude/` mit Vorrang) – nichts zu übergeben. Unter der eigenen Adresse des Nutzers **immer** dranlassen (globale Signatur = dessen persönliche). `--no-sig` nur bei explizitem "ohne Signatur" oder einem **dritten** Absender (weder der Nutzer noch Claude); für eine abweichende Signatur explizit `--sig-text-file`/`--sig-html-file`.
5. Fehlende Angaben aus dem Kontext ableiten (Betreff, Body, Anhänge).
6. Befehl zusammenbauen und dem Nutzer kurz zeigen; auf Bestätigung warten – außer der Nutzer hat bereits „ja" gesagt oder den Versand klar angeordnet.
7. **Vor dem Versand prüfen:** `--verify` auf die fertige `.eml`, mit `--expect-sha256` aus der `--sha-file` und einem `--expect-marker` aus dem freigegebenen Entwurf (siehe „Vor dem Versand prüfen"). Exit ≠ 0 heißt: nicht senden.
8. **Senden:** `python3 $B --send $M/mail.eml --to … --from …` als **eigener Befehl** (nicht an die Prüfkette aus Schritt 7 hängen — sonst steht der Versand nicht am Befehlsanfang und ist von keiner Bash-Freigabe erreichbar). `--send` lädt den Versandweg selbst und prüft Exit-Code, `queued as` *und* die `^<.\*`-Zeile. Nur bei Exit `0` „versendet" melden, sonst den Fehlschlag mit Statuscode aus dem JSON nennen.
9. **Ablegen:** nach erfolgreichem Versand die `.eml` mit `imap append $M/mail.eml -a <konto>` in „Gesendet" legen — swaks tut das nicht (siehe „Ablage").
10. **Erfolgsmeldung:** Queue-ID, übertragene Datei mit sha256 und Größe, Envelope-Empfänger (inkl. Bcc) und die Fundstelle der Kopie nennen (siehe „Was in der Erfolgsmeldung stehen muss").
11. **Kontakt ergänzen:** Wenn eine neue E-Mail-Adresse verwendet wurde, die noch nicht in `.claude/swaks-contacts.tsv` steht, per `printf` anhängen.

## Hinweise

- **`--subject` gilt für `build_mail.py`, nicht für `swaks`.** Der Helper verlangt `--subject` **zwingend** (ohne bricht der Bau mit Exit 2 ab); `swaks` selbst kennt die Option in dieser Version **nicht** — wird dort ein Betreff gebraucht (nur bei den einfachen Sonderfällen ohne Helper), geht das über `--header "Subject: ..."`. Beim Regelweg über `build_mail.py` steht der Betreff ohnehin schon in der gebauten `.eml` und gehört nicht ein zweites Mal an `swaks`.
- MX-Routing ist nicht verfügbar (Net::DNS fehlt). Ohne geladenen Versandweg nimmt swaks deshalb **stillschweigend `localhost:25`** — kein Fehler, aber der falsche Weg. `--send` lädt den Weg selbst; beim Aufruf von Hand immer erst `eval "$ENV"`.
- Erfolg erkennbar an: `250 2.0.0 Ok: queued as <ID>` **bei Exit-Code 0 und ohne `<**`/`<~*`-Zeile**. Alle drei prüfen — bei mehreren Empfängern ist ein einzelner Reject sonst unsichtbar.
- Zum Ausprobieren einer Route ohne Zustellung: `--quit-after RCPT` — die Verbindung endet vor `DATA`, es geht nichts raus.
- Ein `250 Ok` sagt nur, dass der Server die Bytes genommen hat. Ob es die **richtigen** Bytes waren (Datei zwischenzeitlich überschrieben) und ob sie beim Empfänger **lesbar** ankommen (HTML-Part ohne Markup), sagt es nicht — dafür gibt es `--verify`.
- `swaks` legt **keine Kopie in „Gesendet"** ab. Nach erfolgreichem Versand `imap append $M/mail.eml -a <konto>` nachziehen; geht das nicht, wenigstens die Fundstelle (Bcc-Kopie im Posteingang) in der Erfolgsmeldung nennen.
