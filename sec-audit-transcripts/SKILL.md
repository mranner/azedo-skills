---
name: sec-audit-transcripts
description: >
  Prueft die Ablagen von Claude Code auf enthaltene Geheimnisse: Transkripte,
  Prompt-Historie, Datei-Backups, Scratchpads. Sucht die Werte der lokalen
  Credential-Dateien (known-secret matching, ohne Fehlalarme) und zusaetzlich
  bekannte Token-Muster fremder Anbieter. Meldet nur Fundstelle und
  HMAC-Kurzhash, nie den Wert. Setzt Datei- und Verzeichnisrechte eng, haekelt
  bewertete Funde ab und erzeugt fuer Loeschungen ein Shell-Script, das nach dem
  Beenden von Claude Code aus der Shell laeuft. NUR auf ausdruecklichen Aufruf
  von /sec-audit-transcripts laden. Nicht von selbst laden, auch nicht bei
  Fragen wie "steht ein Passwort im Transkript" oder "Credential-Leck in der
  Session" - dort auf den expliziten Aufruf warten. Trigger: ausschliesslich
  /sec-audit-transcripts.
disable-model-invocation: true
---

# sec-audit-transcripts -- Geheimnisse in den Claude-Code-Ablagen finden

Ein Transkript enthaelt alles, was in einer Sitzung ueber den Bildschirm ging --
auch Zugangsdaten, wenn ein Befehl sie versehentlich ausgibt. Eine misslungene
Maskierung genuegt, und das Passwort steht im Klartext in einer Datei, die
niemand als Credential-Speicher auf dem Schirm hat.

Dieser Skill deckt die **Erkennung** ab und bietet zwei getrennte Wege der
Bereinigung an. Die **Verhinderung** ist nicht sein Thema -- die laeuft ueber
Deny-Regeln in `settings.json`.

**Aufruf:** `python3 "$SKILL_DIR/sec-audit-transcripts" <subcommand>`

## Der zentrale Grundsatz

**Der Report nennt nie einen Geheimniswert.** Nur Label, Datei, Zeile,
Zeitstempel, Rolle und einen HMAC-Kurzhash. Ein Report, der die Funde im
Klartext enthaelt, ist die naechste Leckage -- und er bleibt als Datei liegen.
Bei der Mustersuche gibt es hoechstens maskierten Kontext (`mi***.`).

Das gilt auch fuer das erzeugte Bereinigungs-Script: es traegt ausschliesslich
Fingerprints, keine Werte.

## Subcommands

| Subcommand | Wirkung |
|---|---|
| `scan` | prueft die Ablagen (Default, wenn kein Subcommand angegeben ist) |
| `sources` | zeigt, welche Quellen geladen wurden -- Label, Laenge, `secret_id`, nie den Wert |
| `fix-perms` | setzt die Rechte der Ablagen und Quellen eng (Kategorie A) |
| `ack` / `unack` | bewertete Fundstelle abhaken bzw. wieder oeffnen |
| `list` | zeigt die abgehakten Fundstellen |
| `apply` | loescht Fundstellen -- **nur bei beendetem Claude Code** (Kategorie C) |

```bash
python3 "$SKILL_DIR/sec-audit-transcripts" scan
python3 "$SKILL_DIR/sec-audit-transcripts" scan --json --all
python3 "$SKILL_DIR/sec-audit-transcripts" scan --context --limit 0
python3 "$SKILL_DIR/sec-audit-transcripts" scan --emit-cleanup
python3 "$SKILL_DIR/sec-audit-transcripts" ack 9f2c1a4b7e30 --note "Token rotiert"
python3 "$SKILL_DIR/sec-audit-transcripts" fix-perms --dry-run
```

`--limit` kuerzt den Textreport auf N Fundstellen je Gruppe (Default 10, `0`
zeigt alle); `--json` ist davon nie betroffen.

## Kurze Treffer bewerten -- `--context`

Ein kurzes Passwort kann in einem grossen Korpus auch zufaellig stehen. Ob ein
Treffer echt ist, zeigt erst das Umfeld: `set smtp_pass = "[***]"` ist eindeutig,
eine Zeichenfolge mitten in einem Hash nicht. `--context` druckt deshalb ein
Fenster um die Fundstelle, in dem **der Wert selbst geschwaerzt** ist (`[***]`,
in jedem Vorkommen).

**Der Kontext ist trotzdem Rohtext aus dem Transkript** und kann anderes
Schuetzenswertes enthalten -- Mailadressen, Hostnamen, Kundendaten. Deshalb ist
er nicht der Default und gehoert nicht in einen Report, der weitergereicht wird.

## Erkennung -- zwei Wege

**1. Known-secret matching.** Das Script liest die lokalen Geheimnisquellen und
sucht deren *Werte* in den Ablagen. Das ist praezise und ohne Fehlalarme: was
hier auftaucht, ist tatsaechlich ein Geheimnis. Geladen werden `~/.muttrc`,
`~/.env`, `~/.claude/*.json` und `~/.ssh/id_*`; die Werte bleiben im Speicher
und werden nie geschrieben.

Die Untergrenze gegen Fehlalarme ist **nach Quelle gestaffelt**: ein
ausdrueckliches Passwortfeld (`*_pass`, `*secret*`) zaehlt ab 4 Zeichen, ein
generischer Token- oder Key-Eintrag erst ab 8. Eine pauschale Grenze war der
erste Fehler dieses Scripts -- sie hat genau das kurze Passwort verworfen,
wegen dem es gebaut wurde. Werte unter 12 Zeichen bekommen die Confidence
`mittel`, weil eine kurze Zeichenfolge in einem grossen Korpus auch zufaellig
vorkommt.

`smtp_url` und `imap_url` tragen das Passwort in der Userinfo. Beide werden
zerlegt: das Passwort einzeln und die vollstaendige URL als eigener Wert.

**2. Mustersuche.** Fuer Fremdgeheimnisse, die in keiner lokalen Quelle stehen:
`sk-ant-`, `sk-`, `ghp_`, `AKIA`, `xox…`, `AIza`, JWTs, `BEGIN … PRIVATE KEY`
und Zuweisungen an `password`/`secret`/`token`. Produziert Fehlalarme, wird
deshalb getrennt ausgewiesen und hat einen eigenen Exit-Code. `--no-patterns`
schaltet sie ab. Offensichtliche Platzhalter (`<token>`, `your_…`, `example`,
`***`) werden verworfen.

## Umfang

Geprueft wird nicht nur `projects/**/*.jsonl`. Gleiche Bauart, gleiches Problem:

- `~/.claude/projects/` -- die Transkripte
- `~/.claude/history.jsonl` -- die Prompt-Historie (haeufigster Fundort, weil
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
`tool_result` steckt in einer `user`-Zeile und waere sonst falsch als `user`
ausgewiesen.

Die `secret_id` ist ein **HMAC** mit einem lokalen Salt
(`~/.claude/sec-audit-transcripts/salt`, 0600). Ein nackter sha256 eines kurzen
Passworts waere per Wortliste rueckrechenbar -- die Zustandsdatei selbst waere
dann das Ziel.

Abgehakte Funde stehen in `~/.claude/sec-audit-transcripts/state.json`, damit
der woechentliche Lauf nicht ewig denselben Altfund meldet. Abgehakt wird per
Fingerprint, nicht per Datei -- ein neuer Fund derselben Art in derselben Datei
bleibt sichtbar.

## Exit-Codes

| Code | Bedeutung |
|---|---|
| 0 | nichts Neues |
| 1 | neue Known-Secret-Funde |
| 2 | nur neue Mustertreffer |
| 3 | Fehler (Quelle unlesbar, Ablage fehlt) |

Damit taugt `scan` als cron-Job, der ab Code 1 eine Push-Meldung ausloest.

## Bereinigung -- drei Kategorien

**A -- sofort, in der Session.** Idempotent und ungefaehrlich: `fix-perms` setzt
`~/.claude` auf 0700, die Credential-Quellen auf 0600, und rekursiv dieselben
Ablagen, die `scan` durchsucht (Verzeichnisse 0700, Dateien 0600). Eine umask
von `0022` laesst neue Dateien sonst auf 644 landen; geschuetzt sind sie dann
nur noch durch das Elternverzeichnis.

**B -- Vorschlag, der Mensch entscheidet.** Alles, was ausserhalb der Maschine
wirkt oder nicht umkehrbar ist: ein Token rotieren, eine ganze Session
verwerfen. Der Skill nennt Fundstelle und Begruendung und fuehrt nichts aus.

**C -- Script fuer nach dem Beenden.** Claude Code haelt die Transkript-Datei
der laufenden Session offen und schreibt sie fort. Wer sie aus der Session
heraus loescht, bekommt sie beim Beenden ueberschrieben oder korrumpiert die
aktive Sitzung. Deshalb schreibt `scan --emit-cleanup` ein Shell-Script nach
`~/.claude/sec-audit-transcripts/cleanup-<zeitstempel>.sh` (0700), das **nach**
dem Beenden aus der Shell aufgerufen wird:

```sh
~/.claude/sec-audit-transcripts/cleanup-20260902-2145.sh
```

Das Script prueft selbst, ob Claude Code noch laeuft, und bricht sonst ab. Die
Pruefung geht **zwei** Wege, und der erste ist der wichtige: die Umgebung
(`CLAUDECODE`) verraet den Aufruf aus einer Session sofort. `pgrep -f claude`
allein genuegt nicht -- FreeBSD schliesst die eigenen **Vorfahren** aus der
Trefferliste aus, und genau ein Vorfahr ist Claude Code. Ohne `-a` haette der
Guard also ausgerechnet im gefaehrlichsten Fall Entwarnung gegeben. Es ist ein duenner Rahmen -- die Logik bleibt im Python: es ruft
`apply --fingerprint …` auf, das die Werte erneut aus den Quellen laedt und
prueft, ob die Fundstelle ueberhaupt noch existiert. Ein zwischenzeitlich
geaenderter Stand faellt damit auf, statt blind geloescht zu werden.

`scan --emit-cleanup` erzeugt das Script nur fuer **known-secret**-Funde -- ein
Mustertreffer braucht immer die menschliche Bewertung aus Kategorie B zuerst
(zu viele Fehlalarme fuer Automatik). Ist ein Mustertreffer nach dieser
Bewertung ein echtes Geheimnis, nimmt `apply --fingerprint <fp> [<fp> ...]`
seinen Fingerprint trotzdem entgegen -- der manuelle Aufruf pruefte zuvor nur
known-secret-Fingerprints, seit CR4589 (bestaetigtes DB-Passwort in einem
`sed`-Rotationsbefehl, kein registrierter known-secret) auch Mustertreffer.
Die Sicherheitsschranke bleibt dieselbe: geloescht wird ausschliesslich, was
per Fingerprint ausdruecklich benannt ist, nie ein automatischer Massenlauf
ueber alle neuen Mustertreffer.

`apply` entfernt in `history.jsonl` einzelne Zeilen (dort haengt kein `--resume`
dran) und loescht sonst die **ganze Datei**. Eine editierte Session bricht
`--resume` still, eine geloeschte ist sichtbar weg. Erledigte Fundstellen landen
danach als `removed` in der Zustandsdatei.

## Loeschen ist kein Zuruecknehmen

Snapshots und Backups halten jede geloeschte Datei weiter vor, mitsamt der alten,
womoeglich offeneren Rechte. Loeschen beseitigt den bequemen Zugriff, nicht das
Geheimnis. **Was wirklich exponiert war, gehoert rotiert** -- das Script sagt das
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

Werden Lesezugriffe auf die Credential-Dateien fuer das Modell per
`settings.json` gesperrt, muss der Pruefer davon ausgenommen sein -- sonst
blockiert die Regel genau den, der den Fehler finden soll. **Das Script liest
sie, das Modell nicht.** Unter auto mode gehoert dafuer eine Ausnahme in
`permissions.autoMode.allow`, die den Aufrufpfad des Skills nennt.

## Voraussetzungen

Python >= 3.11, stdlib only. `pgrep` fuer die Laufzeitpruefung des
Bereinigungs-Scripts (auf BSD und Linux vorhanden).

Laufzeit auf einem Korpus von ~170 MB in 3.800 Dateien: knapp 10 Sekunden ohne,
gut eine Minute mit Mustersuche.
