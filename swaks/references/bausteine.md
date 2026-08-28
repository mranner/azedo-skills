# swaks - Bausteine

Grundbefehl, Body, Empfaenger, HTML, Anhaenge.

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
