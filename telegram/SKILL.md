---
name: telegram
description: >
  Telegram-Bot: sendet Nachrichten in einen Chat, aus Claude Code, Loops und
  cron-Jobs - und kann als einziger der Melde-Skills auf eine Antwort warten
  (Long-Poll), etwa um unterwegs eine Freigabe einzuholen.
  Trigger: /telegram.
disable-model-invocation: true
---

# telegram -- Telegram-Bot (outbound-first)

Nachrichten werden ueber das gebundelte Script `telegram` (Python >=3.11,
stdlib only, im Skill-Verzeichnis) an die Bot-API gesendet. **Kein
Server-Prozess** noetig — jeder Aufruf ist ein einzelner HTTPS-Call und laeuft
ueberall, auch aus cron.

**Aufruf:** `python3 "$SKILL_DIR/telegram" <subcommand> [options]`

`$SKILL_DIR` ist das Base Directory dieses Skills (dort wo diese SKILL.md liegt).

## Konfiguration (.env)

Credentials werden aus `.env` gelesen (wie kimai/kanboard): zuerst `.env` im
Arbeitsverzeichnis (sofern sie `TELEGRAM_BOT_TOKEN` enthaelt), sonst `~/.env`.
Mit `TELEGRAM_ENV=/pfad/zur/.env` laesst sich die Datei explizit setzen.
Environment-Variablen **ueberschreiben** die .env (praktisch fuer cron/CI).

| Variable             | Zweck                                                        |
|----------------------|-------------------------------------------------------------|
| `TELEGRAM_BOT_TOKEN` | Bot-Token von BotFather (Pflicht)                           |
| `TELEGRAM_CHAT_ID`   | Standard-Ziel-Chat (sonst `--chat-id` je Aufruf)            |
| `TELEGRAM_CA_BUNDLE` | optional: CA-Bundle-Pfad (FreeBSD-TLS-Escape-Hatch)         |

```
TELEGRAM_BOT_TOKEN=123456789:AAE...
TELEGRAM_CHAT_ID=987654321
```

## Ersteinrichtung

1. **Bot anlegen:** In Telegram **@BotFather** → `/newbot` → Name + Username
   (endet auf `bot`) → Token notieren. Token in die `.env` als
   `TELEGRAM_BOT_TOKEN` eintragen.
2. **Bot anschreiben:** Dem neuen Bot in Telegram einmal eine Nachricht senden
   (z.B. `hi`) — sonst liefert `getUpdates` keine `chat_id`.
3. **chat_id ermitteln:**
   ```bash
   python3 "$SKILL_DIR/telegram" setup
   ```
   Zeigt die gefundenen Chats mit `chat_id`. Direkt in die .env schreiben:
   ```bash
   python3 "$SKILL_DIR/telegram" setup --write            # genau ein Chat
   python3 "$SKILL_DIR/telegram" setup --write --chat-id <id>   # mehrere Chats
   ```
4. **Token pruefen:** `python3 "$SKILL_DIR/telegram" me` → `Bot OK: @...`.

## Subcommands

### Nachricht senden (Kernbefehl)

```bash
python3 "$SKILL_DIR/telegram" send "Text der Nachricht"
python3 "$SKILL_DIR/telegram" send --file .tmp/report.txt
echo "aus einer Pipe" | python3 "$SKILL_DIR/telegram" send -
```

Optionen:

- `--chat-id <id>` — abweichender Ziel-Chat (Default: `TELEGRAM_CHAT_ID`).
- `--parse-mode {none,html,markdown,markdownv2,markdown-legacy}` — Default
  `none` (**Klartext**, sicherste Wahl fuer beliebigen Text). Bei `html` bzw.
  `markdown(v2)` ist der Aufrufer fuer gueltige/geescapte Markup-Zeichen
  verantwortlich.
- `--silent` — stille Zustellung (`disable_notification`).
- `--no-preview` — Link-Vorschau unterdruecken.
- `--json` — Roh-Antwort der API ausgeben.

Text-Quelle: Positional-Argument **oder** `--file <pfad>` **oder** STDIN
(Argument `-` bzw. weglassen).

### Vorlagen (Alert / Recovery / Digest)

Fertige HTML-Vorlagen mit Emoji — gedacht fuer Monitoring-Loops. Dynamische
Werte werden HTML-escaped, `parse_mode=HTML` wird automatisch gesetzt.

```bash
# roter Alert mit Titel + Host-Fusszeile
python3 "$SKILL_DIR/telegram" alert --title "natd CPU 95%" --host gatekeeper "Details ..."

# gruene Entwarnung
python3 "$SKILL_DIR/telegram" recovery --title "natd wieder normal" --host gatekeeper "CPU 4%"

# Tages-Digest: je Eingabezeile ein Bullet-Punkt
python3 "$SKILL_DIR/telegram" digest --title "Post-Update mom" --file .tmp/status.txt
```

Alle drei akzeptieren dieselben Text-Quellen wie `send` (Positional/`--file`/STDIN)
sowie `--silent`/`--json`.

### Auf Antwort/Anweisung warten (interaktiv, `wait` / `ask`)

**Fuer den Fall, dass Claude Code auf eine Antwort/Anweisung per Telegram warten
soll.** Beide Befehle blockieren **einmalig** per Long-Poll, geben die
empfangene Nachricht (nur den Text) aus und beenden sich — im Gegensatz zum
Dauer-`poll` (unten). So kann der Aufrufer die Anweisung direkt weiterverarbeiten.

```bash
# blockieren bis eine Nachricht kommt, ihren Text ausgeben
python3 "$SKILL_DIR/telegram" wait [--timeout 290] [--poll 50]

# Frage senden UND auf die Antwort warten (send + wait in einem Schritt)
python3 "$SKILL_DIR/telegram" ask "Deploy jetzt starten? (ja/nein)" [--timeout 290]
```

- **Exit 0** = Nachricht(en) empfangen (Text auf stdout, eine Zeile je Nachricht).
- **Exit 2** = Timeout ohne Nachricht (Budget `--timeout` erschoepft).
- `--timeout` = gesamtes Warte-Budget in Sekunden (Default 290); intern in
  `--poll`-Zyklen (Default 50 s) aufgeteilt.
- Beide **drainen** vorab den Backlog (offset+1) → es zaehlen nur Nachrichten,
  die **nach** Start des Wartens eintreffen (`--no-drain` schaltet das ab).
- Standardmaessig werden nur Nachrichten aus `TELEGRAM_CHAT_ID`/`--chat-id`
  akzeptiert (Fremd-Chats werden ignoriert); `--any-chat` hebt das auf.
- `--json` gibt die vollen Update-Objekte aus (Absender, chat_id, message_id …).

**Interaktiver Workflow (Claude Code):** Wenn der User im Prompt anfordert, per
Telegram gefragt/gesteuert zu werden — z.B. „frag mich per Telegram, ob ich
deployen will" oder „warte auf meine Telegram-Anweisung":

1. Frage stellen und auf Antwort warten: `ask "<frage>"` (oder erst `send`/`alert`,
   dann `wait`).
2. Den ausgegebenen Antworttext lesen und danach handeln.
3. Bei Exit 2 (keine Antwort im Zeitfenster): dem User Bescheid geben bzw.
   erneut `wait` aufrufen.

> **Wichtig fuer Claude Code:** `wait`/`ask` blockieren bis zu `--timeout`
> Sekunden. Beim Aufruf ueber das Bash-Tool **den Bash-Timeout entsprechend
> hoch setzen** (>= `--timeout`, z.B. `--timeout 290` → Bash-Timeout 300000 ms),
> sonst wird der Aufruf vorzeitig abgebrochen. Fuer laengeres Warten `--timeout`
> und Bash-Timeout gemeinsam erhoehen (Bash-Max 600 s).

### Empfangen (Dauer-Scaffold, optional)

Fuer einen kontinuierlichen Empfang ist ein Geruest enthalten, aber **kein
Daemon** — die Nachrichten werden nur ausgegeben, nicht verarbeitet.

```bash
# roher getUpdates-Aufruf (Baustein)
python3 "$SKILL_DIR/telegram" get-updates [--offset <n>] [--timeout <s>]

# Long-Poll im Vordergrund (getUpdates?timeout=50 in Schleife, Ctrl-C beendet)
python3 "$SKILL_DIR/telegram" poll [--timeout 50] [--once] [--json]
```

`poll` fuehrt den `offset` automatisch mit (keine Doubletten) und loest vorab
einen evtl. gesetzten Webhook (`deleteWebhook`), da Webhook und `getUpdates`
sich gegenseitig ausschliessen. Fuer einen echten Zwei-Wege-Bot (Befehle
verarbeiten, als rc.d/daemon(8) im Jail) ist das die Ausbaubasis — separat
anfordern.

## Anbindung an Loops

Bestehende Loops (Wetter-Alarm, Post-Update-Monitoring) koennen statt/zusaetzlich
zur Mail (swaks) per Telegram melden — nur der Sende-Call in die Loop-Aktion:

```bash
python3 "$SKILL_DIR/telegram" alert --title "..." --host <host> "$MELDUNG"
```

## FreeBSD-Hinweise

- **Ausgehendes HTTPS** zu `api.telegram.org` muss erlaubt sein. Bei
  restriktivem Egress die Telegram-Netze `149.154.160.0/20` und
  `91.108.4.0/22` freigeben.
- **TLS-Zertifikate:** `pkg install ca_root_nss`. Falls die Default-CA-Pfade
  nicht greifen, `TELEGRAM_CA_BUNDLE=/usr/local/share/certs/ca-root-nss.crt`
  in der .env setzen.
- Python auf FreeBSD via `pkg install python311` (oder neuer).

## Hinweise

- **Kein MCP** — reiner HTTPS-Wrapper, kein laufender Prozess.
- Bei `ok:false` bricht das Script mit der Telegram-Fehlerbeschreibung ab
  (z.B. `chat not found`, `bot was blocked by the user`).
- Der `.env`-Token ist ein Secret: `.env` ist per `.gitignore` ausgeschlossen.
