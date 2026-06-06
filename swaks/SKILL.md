---
name: swaks
description: >
  Sends emails via swaks through mom.azedo.at (Postfix). Use this skill whenever
  the user wants to send an email, forward a file, share documentation, or
  deliver any content by mail — even if they just say "schick mir das",
  "sende das per Mail", "mail me the result", or "send this to X".
  Handles plain text, HTML body, and file attachments (any type).
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

## Encoding

Immer UTF-8 Header mitgeben, damit Umlaute korrekt ankommen:

```
--header "Content-Type: text/plain; charset=utf-8" \
--header "Content-Transfer-Encoding: 8bit"
```

Für HTML-Mails stattdessen `text/html; charset=utf-8` (siehe Abschnitt HTML-Body).

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

1. Fehlende Angaben aus dem Kontext ableiten (Empfänger, Betreff, Body, Anhänge).
2. Befehl zusammenbauen.
3. Befehl dem Nutzer kurz zeigen und auf Bestätigung warten – außer der Nutzer hat bereits explizit „ja" gesagt oder den Versand klar angeordnet.
4. Befehl ausführen und Ergebnis (Queue-ID oder Fehler) melden.

## Hinweise

- `--subject` existiert in dieser swaks-Version nicht → immer `--header "Subject: ..."` verwenden.
- MX-Routing ist nicht verfügbar (Net::DNS fehlt) – kein Problem, da mom.azedo.at verwendet wird.
- Erfolg erkennbar an: `250 2.0.0 Ok: queued as <ID>`.

