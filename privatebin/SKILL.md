---
name: privatebin
description: >
  PrivateBin: teilt Text, Logausschnitte, Configs und ganze Dateien als
  Ende-zu-Ende-verschlüsselte Paste und gibt den Link zurück. Paste anlegen,
  fremde wie eigene Paste-Links lesen und entschlüsseln, wieder löschen,
  zuletzt geteilte Links auflisten. Ablauf, burn-after-reading, Passwortschutz
  und Dateianhänge pro Aufruf steuerbar. Auch bei "teil das per PrivateBin",
  "mach einen Paste draus", "schick mir das als Link", "Zugangsdaten sicher
  teilen", "lösch die Paste wieder".
  Trigger: /privatebin.
---

# privatebin -- verschlüsselte Pastes teilen

Alles läuft über das gebündelte Script `privatebin` (Python >= 3.9, stdlib plus
`cryptography`). Kein Browser, kein Server-Prozess: jeder Aufruf verschlüsselt
lokal und spricht die JSON-API der Instanz an.

**Aufruf:** `python3 "$SKILL_DIR/privatebin" <subcommand> [options]`

`$SKILL_DIR` ist das Base Directory dieses Skills (dort wo diese SKILL.md liegt).

## Wofür

Ein Paste ist der richtige Weg, wenn Inhalt **zu groß, zu sensibel oder zu
formatiert** für den direkten Weg ist: ein 400-Zeilen-Log, eine Config mit
Passwörtern, ein Fehler-Stacktrace für einen Kollegen, Zugangsdaten, die nicht
dauerhaft in einem Ticket stehen sollen. Der Empfänger braucht nur den Link.

Der Schlüssel steckt im `#`-Fragment der URL. Browser senden Fragmente nicht mit,
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
sie werden dann preemptiv mitgeschickt. Mehrere Instanzen sind möglich, die Wahl
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
| `--burn` | Paste löscht sich beim ersten Abruf |
| `--discussion` | Kommentare erlauben (schließt `--burn` aus) |
| `--password` | zusätzliches Passwort, muss separat übermittelt werden |
| `--format` | `plaintext`, `markdown`, `syntaxhighlighting` |
| `--attach DATEI` | Datei als verschlüsselten Anhang, `--name` benennt sie um |
| `--no-history` | Link nicht lokal mitschreiben |

Die **Ausgabe im Chat** ist die URL, nichts weiter -- kein Vorspann, keine
Wiederholung des Inhalts, der ja gerade nicht im Klartext stehen soll.

## read -- Paste entschlüsseln

```sh
python3 "$SKILL_DIR/privatebin" read "https://example.org/privatebin/?abc123#Base58Key"
python3 "$SKILL_DIR/privatebin" read "<url>" --password geheim
python3 "$SKILL_DIR/privatebin" read "<url>" --save-attachment ./ordner/
```

Nimmt eine vollständige Paste-URL (inklusive `#`-Fragment) und funktioniert auch
bei **fremden Instanzen** -- die URL bestimmt den Server. Passt sie auf eine
konfigurierte Instanz, kommen deren Zugangsdaten dazu. Fehlt das Fragment, hilft
`--key`; bei einer eigenen, noch in der History stehenden Paste findet der Skill
den Schlüssel selbst.

`read` läuft auch **ohne Config**: die vollständige URL genügt. Eine fehlende
`privatebin.json` ist dafür kein Grund, nachzufragen oder eine anzulegen.

Ohne `--save-attachment` wird ein vorhandener Anhang nur gemeldet, nicht
geschrieben. Anhänge in ein Verzeichnis speichern übernimmt den Originalnamen.

## delete -- Paste zurücknehmen

```sh
python3 "$SKILL_DIR/privatebin" delete "<url oder paste-id>"
python3 "$SKILL_DIR/privatebin" delete <paste-id> --token <deletetoken>
```

Das Delete-Token kommt aus der lokalen History; ist der Eintrag herausgerollt,
muss `--token` es liefern. Nach dem Löschen fällt der History-Eintrag weg.

## history -- was zuletzt geteilt wurde

```sh
python3 "$SKILL_DIR/privatebin" history          # letzte 25
python3 "$SKILL_DIR/privatebin" history -n 5 --json
```

Die History liegt per Default in `~/.claude/privatebin-pastes.log`, ist auf 25
Einträge begrenzt und wird mit Modus `0600` geschrieben. Sie enthält die
**vollständigen URLs samt Schlüssel und die Delete-Tokens** -- das ist der Preis
dafür, dass ein Link nachgereicht und eine Paste zurückgenommen werden kann.
Wer das nicht will, legt einzelne Pastes mit `--no-history` an.

## Fallstricke

- **Rate-Limit.** Instanzen erzwingen typischerweise 10 Sekunden Abstand zwischen
  zwei Pastes derselben IP. Der Skill wartet einmal selbsttätig ab und wiederholt;
  eine Serie von Pastes dauert deshalb entsprechend länger.
- **Größenlimit.** Es gilt für das **Chiffrat**, und ein Anhang wird vor der
  Verschlüsselung Base64-kodiert -- rechne mit rund einem Drittel Aufschlag. Bei
  10 MB Limit passen also ungefähr 7 MB Datei. Der Skill prüft das vorab.
- **Dateiupload kann serverseitig aus sein.** Ein Anhang lässt sich per API auch
  dann anlegen, wenn `fileupload = false` gesetzt ist -- im Browser bleibt er aber
  unerreichbar: das Template rendert den `#attachment`-Container samt Download-Link
  nur bei aktiviertem Upload. Vor dem ersten Anhang die Instanz prüfen.
- **burn-after-reading und Link-Vorschauen.** Ein Messenger, der Links automatisch
  auflöst, verbrennt die Paste, bevor der Empfänger sie sieht. Für Chat-Wege
  lieber kurzer Ablauf statt `--burn`.
- **Format v2 only.** Pastes von Instanzen älter als PrivateBin 1.3 (Format v1,
  AES-CBC/SJCL) kann `read` nicht entschlüsseln.
- **Passwörter gehen nicht im selben Kanal mit.** Sonst ist der Passwortschutz
  reine Dekoration.
