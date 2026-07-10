---
name: swaks
description: >
  Sends emails via swaks through mom.azedo.at (Postfix). Use this skill whenever
  the user wants to send an email, forward a file, share documentation, or
  deliver any content by mail — even if they just say "schick mir das",
  "sende das per Mail", "mail me the result", or "send this to X".
  Standardversand ist eine multipart/alternative-Mail (Text + HTML) via
  build_mail.py; zusaetzlich moeglich: reiner Text-Body und Dateianhaenge (any type).
  Default recipient is ich@example.org, default sender is claude@azedo.at,
  default server is mom.azedo.at.
  Trigger with /swaks.
---

# swaks – E-Mail versenden

E-Mails werden über `swaks` via `mom.azedo.at` (Postfix) versendet.

## Defaults

| Feld       | Wert                        |
|------------|-----------------------------|
| `--to`     | `ich@example.org`   |
| `--from`   | `claude@azedo.at`           |
| `--server` | `mom.azedo.at`              |

Abweichende Werte übernimmst du aus der Nutzeranfrage.

## Kontakte

Bekannte Empfänger sind in `.claude/swaks-contacts.tsv` im Arbeitsverzeichnis hinterlegt (TSV: `kurzname<TAB>email`, eine Zeile pro Kontakt).

**Lookup:** `grep -i <name> .claude/swaks-contacts.tsv` — liefert direkt die Zeile mit der E-Mail-Adresse (zweites Feld).

Wenn der User einen Namen statt einer E-Mail-Adresse nennt (z.B. "schick das an Dagmar"), zuerst per grep nachschlagen. Nur wenn kein Treffer: nachfragen.

Neue Kontakte nach dem Versand ergänzen:

```bash
printf '%s\t%s\n' "kurzname" "email@adresse" >> .claude/swaks-contacts.tsv
```

## Signatur

Zwei Signaturdateien im Arbeitsverzeichnis:

- `.claude/swaks-signature.txt` – Plain-Text-Signatur (für den Text-Part)
- `.claude/swaks-signature.html` – HTML-Signatur (für den HTML-Part)

Beim Standardversand (Multipart, siehe unten) hängt `build_mail.py` beide automatisch an – Text-Signatur mit Leerzeile Abstand, HTML-Signatur als Block. Bei reinem Text-Body nur die `.txt`-Signatur.

Die Signatur wird **nicht** angehängt wenn:

- Der User explizit "ohne Signatur" / "no sig" sagt
- Die Mail im Namen einer anderen Person verfasst wird (anderer `--from`)

## Encoding

Immer UTF-8 Header mitgeben, damit Umlaute korrekt ankommen:

```
--header "Content-Type: text/plain; charset=utf-8" \
--header "Content-Transfer-Encoding: 8bit"
```

Für HTML-Mails stattdessen `text/html; charset=utf-8` (siehe Abschnitt HTML-Body).

## Standardversand: Multipart (Text + HTML)

**Default für zusammengesetzte Mails.** Es wird eine `multipart/alternative`-Mail erzeugt (Text- **und** HTML-Part im selben Objekt) – gut für Copy/Paste in Thunderbird und beim Weiterleiten, mit Fallback für Plain-Text-Clients. HTML bewusst schlicht halten (Absätze `<p>`, Umbrüche `<br>`, keine CSS-Spielereien).

Ablauf: `build_mail.py` baut die MIME-DATA (korrekte Boundaries/Encoding, hängt Signaturen an), die Ausgabe geht per `swaks --data @-` raus.

1. Text-Body als `.txt` und HTML-Body als `.html` in `.tmp/` schreiben (jeweils **ohne** Signatur – die hängt der Helper an).
2. Senden:

```bash
python3.11 ~/.claude/skills/swaks/build_mail.py \
  --subject "Betreff" \
  --to "empfaenger@example.com" \
  --from claude@azedo.at \
  --text-file .tmp/body.txt \
  --html-file .tmp/body.html \
  --sig-text-file .claude/swaks-signature.txt \
  --sig-html-file .claude/swaks-signature.html \
  | swaks --server mom.azedo.at \
      --to "empfaenger@example.com" \
      --from claude@azedo.at \
      --data @-
```

Hinweise:
- `--to`/`--from` bei **beiden** (Helper *und* swaks) angeben: der Helper setzt die Header, swaks den SMTP-Envelope.
- **Cc:** `--cc "adr"` an `build_mail.py` setzt den sichtbaren `Cc:`-Header. Die Cc-Adresse **zusätzlich** in den swaks-Envelope `--to` aufnehmen (kommasepariert), sonst wird sie nicht zugestellt.
- **Bcc:** `--bcc "adr"` an `build_mail.py` setzt **bewusst keinen** Header (sonst wären die Empfänger sichtbar). Die Bcc-Adresse **nur** in den swaks-Envelope `--to` aufnehmen — sie bleibt für die anderen Empfänger unsichtbar. Beispiel: Header via `build_mail.py --to a@x --cc cc@x --bcc bcc@x`, Envelope via `swaks --to "a@x,cc@x,bcc@x" …`.
- **Leerer Body:** `build_mail.py` bricht mit Exit ≠ 0 ab, wenn Text *und* HTML leer sind — so sendet swaks nie versehentlich seine eingebaute Default-Test-Mail. In Pipelines ggf. `set -o pipefail` nutzen, damit der Abbruch durchschlägt.
- Signatur weglassen: `--sig-text-file`/`--sig-html-file` einfach nicht übergeben.
- **Anhänge:** pro Datei ein `--attach <pfad>` an `build_mail.py` – dann wird `multipart/mixed` um das Text+HTML-Part gelegt (MIME-Type wird automatisch erraten):

```bash
python3.11 ~/.claude/skills/swaks/build_mail.py ... \
  --attach /pfad/zu/datei1.pdf \
  --attach /pfad/zu/datei2.png \
  | swaks --server mom.azedo.at --to "..." --from claude@azedo.at --data @-
```

Die folgenden Abschnitte (reiner Text-Body, HTML-Body, `--attach` direkt an swaks) sind **einfachere Sonderfälle** – nur nutzen, wenn explizit nur Text gewünscht ist oder es rein um einen Dateiversand ohne formatierten Body geht.

## Grundbefehl

```bash
swaks \
  --server mom.azedo.at \
  --to <empfänger> \
  --from <absender> \
  --header "Subject: <betreff>" \
  --header "Content-Type: text/plain; charset=utf-8" \
  --header "Content-Transfer-Encoding: 8bit"
```

## Body (Freitext)

```bash
swaks \
  --server mom.azedo.at \
  --to ich@example.org \
  --from claude@azedo.at \
  --header "Subject: Betreff" \
  --header "Content-Type: text/plain; charset=utf-8" \
  --header "Content-Transfer-Encoding: 8bit" \
  --body "Nachrichtentext hier"
```

## Mehrere Empfänger

Mehrere Adressen kommasepariert an `--to` übergeben:

```bash
swaks \
  --server mom.azedo.at \
  --to "alice@example.com,bob@example.com" \
  --from claude@azedo.at \
  --header "Subject: Betreff" \
  --header "Content-Type: text/plain; charset=utf-8" \
  --header "Content-Transfer-Encoding: 8bit" \
  --body "Nachricht an mehrere Empfänger."
```

## HTML-Body

Für HTML-Mails `Content-Type: text/html` setzen:

```bash
swaks \
  --server mom.azedo.at \
  --to ich@example.org \
  --from claude@azedo.at \
  --header "Subject: Betreff" \
  --header "Content-Type: text/html; charset=utf-8" \
  --header "Content-Transfer-Encoding: 8bit" \
  --body "<html><body><h1>Titel</h1><p>Inhalt</p></body></html>"
```

## Dateianhang

Wichtig: Dateipfad **immer** mit `@`-Präfix übergeben, sonst wird der Pfad als Text gesendet statt die Datei einzulesen.

```bash
swaks \
  --server mom.azedo.at \
  --to ich@example.org \
  --from claude@azedo.at \
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
  --server mom.azedo.at \
  --to ich@example.org \
  --from claude@azedo.at \
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
4. **Signatur:** Sofern kein Ausschlussgrund vorliegt, `--sig-text-file`/`--sig-html-file` an `build_mail.py` übergeben (bzw. bei reinem Text die `.txt`-Signatur anhängen).
5. Fehlende Angaben aus dem Kontext ableiten (Betreff, Body, Anhänge).
6. Befehl zusammenbauen und dem Nutzer kurz zeigen; auf Bestätigung warten – außer der Nutzer hat bereits „ja" gesagt oder den Versand klar angeordnet.
7. Befehl ausführen und Ergebnis (Queue-ID oder Fehler) melden. Erfolg: `250 2.0.0 Ok: queued as <ID>`.
8. **Kontakt ergänzen:** Wenn eine neue E-Mail-Adresse verwendet wurde, die noch nicht in `.claude/swaks-contacts.tsv` steht, per `printf` anhängen.

## Hinweise

- `--subject` existiert in dieser swaks-Version nicht → immer `--header "Subject: ..."` verwenden.
- MX-Routing ist nicht verfügbar (Net::DNS fehlt) – kein Problem, da mom.azedo.at verwendet wird.
- Erfolg erkennbar an: `250 2.0.0 Ok: queued as <ID>`.

