---
name: sec-audit-transcripts
description: >
  Prüft die Ablagen von Claude Code auf enthaltene Geheimnisse: Transkripte,
  Prompt-Historie, Datei-Backups, Scratchpads. Sucht die Werte der lokalen
  Credential-Dateien (known-secret matching, ohne Fehlalarme) und zusätzlich
  bekannte Token-Muster fremder Anbieter. Meldet nur Fundstelle und
  HMAC-Kurzhash, nie den Wert. Setzt Datei- und Verzeichnisrechte eng, hakt
  bewertete Funde ab und erzeugt für Löschungen ein Shell-Script, das nach dem
  Beenden von Claude Code aus der Shell läuft.
disable-model-invocation: true
---

# sec-audit-transcripts -- Geheimnisse in den Claude-Code-Ablagen finden

Ein Transkript enthält alles, was in einer Sitzung über den Bildschirm ging --
auch Zugangsdaten, wenn ein Befehl sie versehentlich ausgibt. Eine misslungene
Maskierung genügt, und das Passwort steht im Klartext in einer Datei, die
niemand als Credential-Speicher auf dem Schirm hat.

Dieser Skill deckt die **Erkennung** ab und bietet zwei getrennte Wege der
Bereinigung an. Die **Verhinderung** ist nicht sein Thema -- die läuft über
Deny-Regeln in `settings.json`.

**Aufruf:** `python3 "$SKILL_DIR/sec-audit-transcripts" <subcommand>`

## Der zentrale Grundsatz

**Der Report nennt nie einen Geheimniswert.** Nur Label, Datei, Zeile,
Zeitstempel, Rolle und einen HMAC-Kurzhash. Ein Report, der die Funde im
Klartext enthält, ist die nächste Leckage -- und er bleibt als Datei liegen.
Bei der Mustersuche gibt es höchstens maskierten Kontext (`mi***.`).

Das gilt auch für das erzeugte Bereinigungs-Script: es trägt ausschließlich
Fingerprints, keine Werte.

## Subcommands

| Subcommand | Wirkung |
|---|---|
| `scan` | prüft die Ablagen (Default, wenn kein Subcommand angegeben ist) |
| `sources` | zeigt, welche Quellen geladen wurden -- Label, Länge, `secret_id`, nie den Wert |
| `fix-perms` | setzt die Rechte der Ablagen und Quellen eng (Kategorie A) |
| `ack` / `unack` | bewertete Fundstelle abhaken bzw. wieder öffnen |
| `list` | zeigt die abgehakten Fundstellen |
| `apply` | löscht Fundstellen -- **nur bei beendetem Claude Code** (Kategorie C) |

```bash
python3 "$SKILL_DIR/sec-audit-transcripts" scan
python3 "$SKILL_DIR/sec-audit-transcripts" scan --json --all
python3 "$SKILL_DIR/sec-audit-transcripts" scan --context --limit 0
python3 "$SKILL_DIR/sec-audit-transcripts" scan --emit-cleanup
python3 "$SKILL_DIR/sec-audit-transcripts" ack 9f2c1a4b7e30 --note "Token rotiert"
python3 "$SKILL_DIR/sec-audit-transcripts" fix-perms --dry-run
```

`--limit` kürzt den Textreport auf N Fundstellen je Gruppe (Default 10, `0`
zeigt alle); `--json` ist davon nie betroffen.

## Kurze Treffer bewerten -- `--context`

Ein kurzes Passwort kann in einem großen Korpus auch zufällig stehen. Ob ein
Treffer echt ist, zeigt erst das Umfeld: `set smtp_pass = "[***]"` ist eindeutig,
eine Zeichenfolge mitten in einem Hash nicht. `--context` druckt deshalb ein
Fenster um die Fundstelle, in dem **der Wert selbst geschwärzt** ist (`[***]`,
in jedem Vorkommen). Das gilt für Mustertreffer genauso: ohne `--context`
steht dort nur der maskierte Wert (`ey***M`), der allein nichts entscheidet.

**Der Kontext ist trotzdem Rohtext aus dem Transkript** und kann anderes
Schützenswertes enthalten -- Mailadressen, Hostnamen, Kundendaten. Deshalb ist
er nicht der Default und gehört nicht in einen Report, der weitergereicht wird.

## Erkennung -- zwei Wege

**1. Known-secret matching.** Das Script liest die lokalen Geheimnisquellen und
sucht deren *Werte* in den Ablagen. Das ist präzise und ohne Fehlalarme: was
hier auftaucht, ist tatsächlich ein Geheimnis. Geladen werden `~/.muttrc`,
`~/.env`, `~/.claude/*.json` und `~/.ssh/id_*`; die Werte bleiben im Speicher
und werden nie geschrieben.

Die Untergrenze gegen Fehlalarme ist **nach Quelle gestaffelt**: ein
ausdrückliches Passwortfeld (`*_pass`, `*secret*`) zählt ab 4 Zeichen, ein
generischer Token- oder Key-Eintrag erst ab 8. Eine pauschale Grenze war der
erste Fehler dieses Scripts -- sie hat genau das kurze Passwort verworfen,
wegen dem es gebaut wurde. Werte unter 12 Zeichen bekommen die Confidence
`mittel`, weil eine kurze Zeichenfolge in einem großen Korpus auch zufällig
vorkommt.

`smtp_url` und `imap_url` tragen das Passwort in der Userinfo. Beide werden
zerlegt: das Passwort einzeln und die vollständige URL als eigener Wert.

Nicht geladen werden JSON-Felder auf `*_env` (sie nennen nur die
Umgebungsvariable) und alles unter `skillOverrides` in `settings.json` (der
Skillname `wp-rest-api` traf `api`, der Wert `name-only` lieferte hunderte
Fehlalarme).

**2. Mustersuche.** Für Fremdgeheimnisse, die in keiner lokalen Quelle stehen:
`sk-ant-`, `sk-`, `ghp_`, `AKIA`, `xox…`, `AIza`, JWTs, `BEGIN … PRIVATE KEY`
und Zuweisungen an `password`/`secret`/`token`. Produziert Fehlalarme, wird
deshalb getrennt ausgewiesen und hat einen eigenen Exit-Code. `--no-patterns`
schaltet sie ab. Offensichtliche Platzhalter (`<token>`, `your_…`, `example`,
`***`) werden verworfen, ebenso das `signature`-Feld von Denkschritten - ein
Base64-Blob, in dem `AIza` zufällig vorkommt. Ein JWT direkt hinter einem
Query-Parameter (`?jwt=`, `&m=`) heißt `jwt-link`: meist ein Abmelde- oder
Tracking-Link aus einer eingefügten Mail.

## Umfang

Geprüft wird nicht nur `projects/**/*.jsonl`. Gleiche Bauart, gleiches Problem:

- `~/.claude/projects/` -- die Transkripte
- `~/.claude/history.jsonl` -- die Prompt-Historie (häufigster Fundort, weil
  Zugangsdaten beim Einrichten von Hand eingetippt werden)
- `~/.claude/file-history/` -- **Kopien editierter Dateien**, ganze Inhalte im
  Klartext, nicht nur Diffs
- `shell-snapshots`, `paste-cache`, `session-env`, `sessions`, `plans`,
  `backups`, `cache`, `feedback`, `todos`
- `/tmp/claude-*` -- die Scratchpad-Verzeichnisse

## Fundstelle und Zustand

Jeder Fund bekommt einen stabilen `fingerprint` aus Datei, Locator und
`secret_id`. Der Locator ist die Event-`uuid`, wo es eine gibt, sonst die
Zeilennummer.

Die Rolle wird aus dem **Content-Block** bestimmt, nicht aus `message.role`: ein
`tool_result` steckt in einer `user`-Zeile und wäre sonst falsch als `user`
ausgewiesen.

Die `secret_id` ist ein **HMAC** mit einem lokalen Salt
(`~/.claude/sec-audit-transcripts/salt`, 0600). Ein nackter sha256 eines kurzen
Passworts wäre per Wortliste rückrechenbar -- die Zustandsdatei selbst wäre
dann das Ziel.

Abgehakte Funde stehen in `~/.claude/sec-audit-transcripts/state.json`, damit
der wöchentliche Lauf nicht ewig denselben Altfund meldet. Abgehakt wird per
Fingerprint, nicht per Datei -- ein neuer Fund derselben Art in derselben Datei
bleibt sichtbar.

## Exit-Codes

| Code | Bedeutung |
|---|---|
| 0 | nichts Neues |
| 1 | neue Known-Secret-Funde |
| 2 | nur neue Mustertreffer |
| 3 | Fehler (Quelle unlesbar, Ablage fehlt) |

Damit taugt `scan` als cron-Job, der ab Code 1 eine Push-Meldung auslöst.

## Bereinigung -- drei Kategorien

**A -- sofort, in der Session.** Idempotent und ungefährlich: `fix-perms` setzt
`~/.claude` auf 0700, die Credential-Quellen auf 0600, und rekursiv dieselben
Ablagen, die `scan` durchsucht (Verzeichnisse 0700, Dateien 0600). Eine umask
von `0022` lässt neue Dateien sonst auf 644 landen; geschützt sind sie dann
nur noch durch das Elternverzeichnis.

**B -- Vorschlag, der Mensch entscheidet.** Alles, was außerhalb der Maschine
wirkt oder nicht umkehrbar ist: ein Token rotieren, eine ganze Session
verwerfen. Der Skill nennt Fundstelle und Begründung und führt nichts aus.

**C -- Script für nach dem Beenden.** Claude Code hält die Transkript-Datei
der laufenden Session offen und schreibt sie fort. Wer sie aus der Session
heraus löscht, bekommt sie beim Beenden überschrieben oder korrumpiert die
aktive Sitzung. Deshalb schreibt `scan --emit-cleanup` ein Shell-Script nach
`~/.claude/sec-audit-transcripts/cleanup-<zeitstempel>.sh` (0700), das **nach**
dem Beenden aus der Shell aufgerufen wird:

```sh
~/.claude/sec-audit-transcripts/cleanup-20260902-2145.sh
```

Das Script prüft selbst, ob Claude Code noch läuft, und bricht sonst ab. Die
Prüfung geht **zwei** Wege, und der erste ist der wichtige: die Umgebung
(`CLAUDECODE`) verrät den Aufruf aus einer Session sofort. `pgrep -f claude`
allein genügt nicht -- FreeBSD schließt die eigenen **Vorfahren** aus der
Trefferliste aus, und genau ein Vorfahr ist Claude Code. Ohne `-a` hätte der
Guard also ausgerechnet im gefährlichsten Fall Entwarnung gegeben. Es ist ein dünner Rahmen -- die Logik bleibt im Python: es ruft
`apply --fingerprint …` auf, das die Werte erneut aus den Quellen lädt und
prüft, ob die Fundstelle überhaupt noch existiert. Ein zwischenzeitlich
geänderter Stand fällt damit auf, statt blind gelöscht zu werden.

`scan --emit-cleanup` erzeugt das Script nur für **known-secret**-Funde -- ein
Mustertreffer braucht immer die menschliche Bewertung aus Kategorie B zuerst
(zu viele Fehlalarme für Automatik). Ist ein Mustertreffer nach dieser
Bewertung ein echtes Geheimnis, nimmt `apply --fingerprint <fp> [<fp> ...]`
seinen Fingerprint trotzdem entgegen -- der manuelle Aufruf prüfte zuvor nur
known-secret-Fingerprints, seit CR4589 (bestätigtes DB-Passwort in einem
`sed`-Rotationsbefehl, kein registrierter known-secret) auch Mustertreffer.
Die Sicherheitsschranke bleibt dieselbe: gelöscht wird ausschließlich, was
per Fingerprint ausdrücklich benannt ist, nie ein automatischer Massenlauf
über alle neuen Mustertreffer.

`apply` entfernt in `history.jsonl` einzelne Zeilen (dort hängt kein `--resume`
dran) und löscht sonst die **ganze Datei**. Eine editierte Session bricht
`--resume` still, eine gelöschte ist sichtbar weg. Erledigte Fundstellen landen
danach als `removed` in der Zustandsdatei.

## Löschen ist kein Zurücknehmen

Snapshots und Backups halten jede gelöschte Datei weiter vor, mitsamt der alten,
womöglich offeneren Rechte. Löschen beseitigt den bequemen Zugriff, nicht das
Geheimnis. **Was wirklich exponiert war, gehört rotiert** -- das Script sagt das
nach jedem `apply` noch einmal.

## Konfiguration

Optional, `~/.claude/sec-audit-transcripts.json`. Ohne die Datei gelten die
Vorgaben oben.

```json
{
  "extra_sources": ["~/projekt/.env"],
  "extra_targets": ["~/eigene-ablage"],
  "extra_perm_files": ["~/projekt/.env"]
}
```

## Zusammenspiel mit den Deny-Regeln

Werden Lesezugriffe auf die Credential-Dateien für das Modell per
`settings.json` gesperrt, muss der Prüfer davon ausgenommen sein -- sonst
blockiert die Regel genau den, der den Fehler finden soll. **Das Script liest
sie, das Modell nicht.** Unter auto mode gehört dafür eine Ausnahme in
`permissions.autoMode.allow`, die den Aufrufpfad des Skills nennt.

## Voraussetzungen

Python >= 3.11, stdlib only. `pgrep` für die Laufzeitprüfung des
Bereinigungs-Scripts (auf BSD und Linux vorhanden).

Laufzeit auf einem Korpus von ~170 MB in 3.800 Dateien: knapp 10 Sekunden ohne,
gut eine Minute mit Mustersuche.
