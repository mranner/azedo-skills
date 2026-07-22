---
name: pushover
description: >
  Pushover-Anbindung (outbound-only): sendet Push-Notifications von Claude Code,
  Loops und cron-Jobs via api.pushover.net an iOS/Android/Desktop. Kernbefehl
  send plus Vorlagen (Alert/Recovery/Digest), Prioritaeten -2..1, Sounds,
  anklickbarer Zusatz-Link, HTML/Monospace-Formatierung, TTL und Bildanhang
  (<=5 MB). stdlib-only Python, lauffaehig auf macOS + FreeBSD, kein
  Server-Prozess. Benannte Empfaenger ueber ein Verzeichnis (Adressbuch), z.B.
  `--user kollege` statt Roh-Key; Default ist der Alias 'me'. Nutze diesen Skill
  wenn eine Meldung als Handy-Push raus soll ("push mir eine Nachricht", "push
  kollege eine Nachricht", "schick mir das per Pushover", "Push aufs Handy",
  "Alert nach Pushover", "melde den Post-Update-Status per Pushover"). Credentials
  in .env (PUSHOVER_TOKEN), Empfaenger in ~/.pushover-recipients. Trigger:
  /pushover (Slash) sowie Natuerlichsprache mit "push ..." ("push mir/kollege
  eine Nachricht").
---

# pushover -- Pushover-Notifications (outbound-only)

Notifications werden ueber das gebundelte Script `pushover` (Python >=3.11,
stdlib only, im Skill-Verzeichnis) an die Pushover-API gesendet. **Kein
Server-Prozess** noetig — jeder Aufruf ist ein einzelner HTTPS-Call und laeuft
ueberall, auch aus cron. Reiner **Outbound**-Versand (kein Empfang; Pushover ist
eine Einweg-Push-API).

**Aufruf:** `python3 "$SKILL_DIR/pushover" <subcommand> [options]`

`$SKILL_DIR` ist das Base Directory dieses Skills (dort wo diese SKILL.md liegt).

## Konfiguration (.env)

Credentials werden aus `.env` gelesen (wie kimai/kanboard/telegram): zuerst
`.env` im Arbeitsverzeichnis (sofern sie `PUSHOVER_TOKEN` enthaelt), sonst
`~/.env`. Mit `PUSHOVER_ENV=/pfad/zur/.env` laesst sich die Datei explizit
setzen. Environment-Variablen **ueberschreiben** die .env (praktisch fuer
cron/CI).

| Variable             | Zweck                                                        |
|----------------------|-------------------------------------------------------------|
| `PUSHOVER_TOKEN`     | Application-API-Token (Pflicht)                             |
| `PUSHOVER_USER`      | Fallback-Empfaenger, falls kein Alias `me` im Verzeichnis   |
| `PUSHOVER_DEVICE`    | optional: Standard-Zielgeraet(e), sonst alle Geraete        |
| `PUSHOVER_CA_BUNDLE` | optional: CA-Bundle-Pfad (FreeBSD-TLS-Escape-Hatch)         |

```
PUSHOVER_TOKEN=azGDORePK8gMaC0QOYAMyEEuzJnyUi
```

Der Standard-Empfaenger kommt aus dem **Empfaenger-Verzeichnis** (Alias `me`,
siehe unten); `PUSHOVER_USER` ist nur der Fallback, wenn kein Verzeichnis
angelegt ist.

## Ersteinrichtung

1. **Application registrieren:** Auf [pushover.net](https://pushover.net)
   einloggen → *Create an Application/API Token* → Name (z.B. "Claude Code") →
   der erzeugte **API-Token** wird `PUSHOVER_TOKEN` in der `.env`.
2. **Eigenen Empfaenger anlegen:** Der **User-Key** steht im Dashboard → als
   Default-Alias `me` ins Verzeichnis:
   `python3 "$SKILL_DIR/pushover" recipients add me <user-key>`.
3. **Pushover-App** auf Handy/Desktop installieren und mit demselben Account
   anmelden (sonst kommt die Push nicht an).
4. **Pruefen:** `python3 "$SKILL_DIR/pushover" validate` → `OK: Token + User-Key
   gueltig.` und die Liste der aktiven Geraete.

## Subcommands

### Notification senden (Kernbefehl)

```bash
python3 "$SKILL_DIR/pushover" send "Text der Nachricht"
python3 "$SKILL_DIR/pushover" send --file .tmp/report.txt --title "Report"
echo "aus einer Pipe" | python3 "$SKILL_DIR/pushover" send -
```

Optionen:

- `--title <text>` — Titelzeile (Default: App-Name).
- `--user <name|key>` — abweichender Empfaenger: **Alias** aus dem Verzeichnis
  (z.B. `kollege`) oder ein roher User-/Group-Key. Ohne Angabe der Alias `me`.
  Siehe **Empfaenger-Verzeichnis** unten.
- `--device <a,b>` — nur an genannte Geraete (kommasepariert). Ohne Angabe an
  **alle** Geraete des Users (bzw. `PUSHOVER_DEVICE`).
- `--priority {-2,-1,0,1}` — `-2` keine Notification (nur Badge), `-1` leise
  (kein Sound), `0` normal (Default), `1` hoch (umgeht Ruhezeiten, immer Sound).
  **Emergency (2)** wird bewusst **nicht** unterstuetzt (braucht retry/expire +
  Receipt-Handling).
- `--sound <name>` — Benachrichtigungston (Kennungen via `sounds`).
- `--url <url>` / `--url-title <text>` — anklickbarer Zusatz-Link in der Push
  (z.B. Deploy-Log, Kanboard-Task).
- `--html` **oder** `--monospace` — Formatierung. `--html` erlaubt
  `<b> <i> <u> <a href>`; `--monospace` setzt die ganze Nachricht in
  Festbreitenschrift (gut fuer Log-Schnipsel/Tabellen). Nicht kombinierbar.
- `--ttl <sek>` — Notification verschwindet nach N Sekunden von selbst.
- `--attachment <datei>` — Bild (<=5 MB) mitschicken (Screenshot, Graph).
- `--silent` — stille Zustellung (entspricht Prioritaet -1).
- `--json` — Roh-Antwort der API ausgeben.

Text-Quelle: Positional-Argument **oder** `--file <pfad>` **oder** STDIN
(Argument `-` bzw. weglassen).

Bei `--html` ist der Aufrufer fuer gueltige/geescapte Markup-Zeichen
verantwortlich; ohne `--html`/`--monospace` wird der Text als Klartext gesendet.

### Vorlagen (Alert / Recovery / Digest)

Fertige Vorlagen mit Emoji-Titel — gedacht fuer Monitoring-Loops. Dynamische
Werte werden HTML-escaped, `html=1` wird automatisch gesetzt. `--host` ergaenzt
eine Fusszeile.

```bash
# roter Alert, Prioritaet hoch (1) als Default
python3 "$SKILL_DIR/pushover" alert --title "natd CPU 95%" --host gatekeeper "Details ..."

# gruene Entwarnung, Prioritaet normal (0)
python3 "$SKILL_DIR/pushover" recovery --title "natd wieder normal" --host gatekeeper "CPU 4%"

# Tages-Digest, Prioritaet leise (-1): je Eingabezeile ein Bullet-Punkt
python3 "$SKILL_DIR/pushover" digest --title "Post-Update mom" --file .tmp/status.txt
```

Alle drei akzeptieren dieselben Optionen wie `send` (inkl. `--priority` zum
Ueberschreiben des Vorlagen-Defaults, `--user`, `--device`, `--sound`,
`--attachment`, `--json`) und dieselben Text-Quellen.

### Pruefen / Diagnose

```bash
python3 "$SKILL_DIR/pushover" validate            # Token + User/Group-Key pruefen
python3 "$SKILL_DIR/pushover" validate --user <group-key>
python3 "$SKILL_DIR/pushover" sounds              # verfuegbare Sound-Kennungen
```

`validate` zeigt die aktiven Geraetenamen (nutzbar fuer `--device`).

## Empfaenger-Verzeichnis (Adressbuch)

Damit man `--user kollege` statt eines 30-Zeichen-Keys tippt, mappt ein
Verzeichnis-File Alias-Namen auf Keys. **Auto-Discovery** wie bei der `.env`:
`PUSHOVER_RECIPIENTS` (Env) → `./.pushover-recipients` → `~/.pushover-recipients`.

Format je Zeile `name = key [device]`, `#`-Kommentare erlaubt:

```
# ~/.pushover-recipients
me     = uAAAAAAAAAAAAAAAAAAAAAAAAAAAAA   # eigenes Handy (Default)
kollege = uBBBBBBBBBBBBBBBBBBBBBBBBBBBBB
```

Verwalten per Subcommand:

```bash
python3 "$SKILL_DIR/pushover" recipients            # auflisten (Keys maskiert)
python3 "$SKILL_DIR/pushover" recipients list --json
python3 "$SKILL_DIR/pushover" recipients add kollege uBBBBBBBBBBBBBBBBBBBBBBBBBBBBB
python3 "$SKILL_DIR/pushover" recipients add ops <group-key> --device pager
```

**Empfaenger-Aufloesung:**

1. `--user kollege` → Alias-Treffer im Verzeichnis → dessen Key (Aliase gewinnen).
2. `--user <30-Zeichen-Key>` → kein Alias → als roher Key genommen.
3. kein `--user` → Alias **`me`**; fehlt der, greift `PUSHOVER_USER`.

Ein Alias kann auch ein **Group-Key** sein (Delivery Group auf pushover.net
angelegt) — fuer die API nicht von einem User-Key zu unterscheiden. So erreicht
ein `send --user team` alle Gruppenmitglieder ohne Multi-Call.

Das Verzeichnis enthaelt Keys (kein Geheimnis-Level wie der App-Token, aber
personenbezogen) — es gehoert **nicht** ins Repo (liegt in `~` bzw. cwd).

## Anbindung an Loops

Bestehende Loops (Wetter-Alarm, Post-Update-Monitoring) koennen statt/zusaetzlich
zu Mail (swaks) oder Telegram per Pushover melden — nur der Sende-Call in die
Loop-Aktion:

```bash
python3 "$SKILL_DIR/pushover" alert --title "..." --host <host> "$MELDUNG"
```

## FreeBSD-Hinweise

- **Ausgehendes HTTPS** zu `api.pushover.net` muss erlaubt sein.
- **TLS-Zertifikate:** `pkg install ca_root_nss`. Falls die Default-CA-Pfade
  nicht greifen, `PUSHOVER_CA_BUNDLE=/usr/local/share/certs/ca-root-nss.crt`
  in der .env setzen.
- Python auf FreeBSD via `pkg install python311` (oder neuer).

## Hinweise / Limits

- **Kein MCP** — reiner HTTPS-Wrapper, kein laufender Prozess.
- Nachricht max **1024** Zeichen, Titel max 250, Attachment max **5 MB** — das
  Script bricht bei Ueberschreitung vorab mit klarer Meldung ab.
- Kontingent: Free-Accounts 10.000 Nachrichten/Monat. Nach jedem `send` zeigt
  das Script (ohne `--json`) das verbleibende Kontingent aus den Response-Headern.
- Bei `status:0` bricht das Script mit der Pushover-Fehlerbeschreibung ab
  (z.B. `user identifier is invalid`, `application token is invalid`).
- Der `.env`-Token ist ein Secret: `.env` ist per `.gitignore` ausgeschlossen.
