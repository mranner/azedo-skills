---
name: privatebin
description: >
  PrivateBin-Anbindung: teilt Text, Logausschnitte, Configs und ganze Dateien als
  Ende-zu-Ende-verschluesselte Paste und gibt den Link zurueck. Legt Pastes an
  (create), liest und entschluesselt fremde wie eigene Paste-Links (read), loescht
  sie wieder (delete) und fuehrt eine kurze lokale History der zuletzt geteilten
  Links samt Delete-Token (history). Ablauf, burn-after-reading, Passwortschutz,
  Markdown/Syntax-Highlighting und Dateianhaenge sind pro Aufruf steuerbar. Die
  Verschluesselung laeuft lokal (AES-256-GCM, PBKDF2, PrivateBin-Format v2), der
  Schluessel steht nur im URL-Fragment und erreicht den Server nie. Nutze diesen
  Skill wenn etwas per Link geteilt werden soll, statt es in Chat, Ticket oder Mail
  zu kleben -- "teil das per PrivateBin", "mach einen Paste draus", "schick mir das
  als Link", "das Log als Paste", "Zugangsdaten sicher teilen", "gib mir den Inhalt
  von dieser Paste-URL", "loesch die Paste wieder". Instanz-URL und Zugangsdaten in
  ~/.claude/privatebin.json. Trigger: /privatebin.
---

# privatebin -- verschluesselte Pastes teilen

Alles laeuft ueber das gebundelte Script `privatebin` (Python >= 3.9, stdlib plus
`cryptography`). Kein Browser, kein Server-Prozess: jeder Aufruf verschluesselt
lokal und spricht die JSON-API der Instanz an.

**Aufruf:** `python3 "$SKILL_DIR/privatebin" <subcommand> [options]`

`$SKILL_DIR` ist das Base Directory dieses Skills (dort wo diese SKILL.md liegt).

## Wofuer

Ein Paste ist der richtige Weg, wenn Inhalt **zu gross, zu sensibel oder zu
formatiert** fuer den direkten Weg ist: ein 400-Zeilen-Log, eine Config mit
Passwoertern, ein Fehler-Stacktrace fuer einen Kollegen, Zugangsdaten, die nicht
dauerhaft in einem Ticket stehen sollen. Der Empfaenger braucht nur den Link.

Der Schluessel steckt im `#`-Fragment der URL. Browser senden Fragmente nicht mit,
die Instanz sieht also nur Chiffrat. **Wer den Link hat, hat den Inhalt** -- ein
Link im falschen Chat ist genauso schlimm wie der Klartext dort.

## Konfiguration

`~/.claude/privatebin.json` (Vorlage: `privatebin.json.example` im Skill).
Anderer Pfad per `--config` oder `PRIVATEBIN_CONFIG`.

```json
{
  "default_instance": "office",
  "instances": {
    "office": { "url": "https://example.org/privatebin/", "user": "", "password": "" }
  },
  "defaults": { "expire": "1week", "formatter": "plaintext", "burn": false, "discussion": false },
  "sizelimit": 10000000,
  "history": "~/.claude/privatebin-pastes.log",
  "history_limit": 25
}
```

`user`/`password` nur setzen, wenn die Instanz das Anlegen hinter Basic-Auth legt;
sie werden dann preemptiv mitgeschickt. Mehrere Instanzen sind moeglich, die Wahl
trifft `--instance <name>`.

## create -- Paste anlegen

```sh
python3 "$SKILL_DIR/privatebin" create --text "kurzer Inhalt"
python3 "$SKILL_DIR/privatebin" create --file /pfad/auszug.log --format syntaxhighlighting
tail -200 /var/log/messages | python3 "$SKILL_DIR/privatebin" create
python3 "$SKILL_DIR/privatebin" create --text "Zugang" --password "$PW" --expire 1day --burn
python3 "$SKILL_DIR/privatebin" create --attach bericht.pdf --text "Bericht anbei"
```

Der Inhalt kommt aus `--text`, `--file` oder von stdin (automatisch, sobald stdin
keine TTY ist; `--stdin` erzwingt es). Ausgabe ist die fertige URL auf stdout --
genau eine Zeile, direkt weiterverwendbar. `--json` liefert stattdessen den vollen
Datensatz inklusive Delete-Token.

| Option | Wirkung |
|---|---|
| `--expire` | `5min` `10min` `1hour` `1day` `1week` `1month` `1year` `never` (Default aus Config) |
| `--burn` | Paste loescht sich beim ersten Abruf |
| `--discussion` | Kommentare erlauben (schliesst `--burn` aus) |
| `--password` | zusaetzliches Passwort, muss separat uebermittelt werden |
| `--format` | `plaintext`, `markdown`, `syntaxhighlighting` |
| `--attach DATEI` | Datei als verschluesselten Anhang, `--name` benennt sie um |
| `--no-history` | Link nicht lokal mitschreiben |

Die **Ausgabe im Chat** ist die URL, nichts weiter -- kein Vorspann, keine
Wiederholung des Inhalts, der ja gerade nicht im Klartext stehen soll.

## read -- Paste entschluesseln

```sh
python3 "$SKILL_DIR/privatebin" read "https://example.org/privatebin/?abc123#Base58Key"
python3 "$SKILL_DIR/privatebin" read "<url>" --password geheim
python3 "$SKILL_DIR/privatebin" read "<url>" --save-attachment ./ordner/
```

Nimmt eine vollstaendige Paste-URL (inklusive `#`-Fragment) und funktioniert auch
bei **fremden Instanzen** -- die URL bestimmt den Server. Passt sie auf eine
konfigurierte Instanz, kommen deren Zugangsdaten dazu. Fehlt das Fragment, hilft
`--key`; bei einer eigenen, noch in der History stehenden Paste findet der Skill
den Schluessel selbst.

Ohne `--save-attachment` wird ein vorhandener Anhang nur gemeldet, nicht
geschrieben. Anhaenge in ein Verzeichnis speichern uebernimmt den Originalnamen.

## delete -- Paste zuruecknehmen

```sh
python3 "$SKILL_DIR/privatebin" delete "<url oder paste-id>"
python3 "$SKILL_DIR/privatebin" delete <paste-id> --token <deletetoken>
```

Das Delete-Token kommt aus der lokalen History; ist der Eintrag herausgerollt,
muss `--token` es liefern. Nach dem Loeschen faellt der History-Eintrag weg.

## history -- was zuletzt geteilt wurde

```sh
python3 "$SKILL_DIR/privatebin" history          # letzte 25
python3 "$SKILL_DIR/privatebin" history -n 5 --json
```

Die History liegt per Default in `~/.claude/privatebin-pastes.log`, ist auf 25
Eintraege begrenzt und wird mit Modus `0600` geschrieben. Sie enthaelt die
**vollstaendigen URLs samt Schluessel und die Delete-Tokens** -- das ist der Preis
dafuer, dass ein Link nachgereicht und eine Paste zurueckgenommen werden kann.
Wer das nicht will, legt einzelne Pastes mit `--no-history` an.

## Fallstricke

- **Rate-Limit.** Instanzen erzwingen typischerweise 10 Sekunden Abstand zwischen
  zwei Pastes derselben IP. Der Skill wartet einmal selbsttaetig ab und wiederholt;
  eine Serie von Pastes dauert deshalb entsprechend laenger.
- **Groessenlimit.** Es gilt fuer das **Chiffrat**, und ein Anhang wird vor der
  Verschluesselung Base64-kodiert -- rechne mit rund einem Drittel Aufschlag. Bei
  10 MB Limit passen also ungefaehr 7 MB Datei. Der Skill prueft das vorab.
- **Dateiupload kann serverseitig aus sein.** Ein Anhang laesst sich per API auch
  dann anlegen, wenn `fileupload = false` gesetzt ist -- im Browser bleibt er aber
  unerreichbar: das Template rendert den `#attachment`-Container samt Download-Link
  nur bei aktiviertem Upload. Vor dem ersten Anhang die Instanz pruefen.
- **burn-after-reading und Link-Vorschauen.** Ein Messenger, der Links automatisch
  aufloest, verbrennt die Paste, bevor der Empfaenger sie sieht. Fuer Chat-Wege
  lieber kurzer Ablauf statt `--burn`.
- **Format v2 only.** Pastes von Instanzen aelter als PrivateBin 1.3 (Format v1,
  AES-CBC/SJCL) kann `read` nicht entschluesseln.
- **Passwoerter gehen nicht im selben Kanal mit.** Sonst ist der Passwortschutz
  reine Dekoration.
