---
name: tmux
description: >
  Interaktive Programme über eine tmux-Session fernsteuern: Text und Tasten
  senden, auf eine Ausgabe warten, den Bildschirm lesen - lokal oder per
  `ssh -t` auf einem Server. Für Dialoge ohne Batch-Modus (etcupdate-Konflikte,
  make config, Installer mit Rückfragen, mehrstufige psql/mysql-Sitzungen) und
  für Claude als Hintergrund-Session (ein `/loop` über Nacht). Auch bei
  "starte das in tmux". Trigger: /tmux.
---

# tmux - interaktive Programme fernsteuern

Für Programme, die eine Eingabe im Terminal verlangen und keinen Batch-Modus
haben, und für Claude-Sessions, die ohne offenes Terminal weiterlaufen sollen.
Hat ein Programm einen Batch-Modus (`top -b`, `iftop -t`, `gstat -b`), gilt
dieser als normaler Befehl ohne Session. Configs werden mit `sed -i~` geändert,
nicht über Editor-Tastendrücke.

Alles läuft über `"$SKILL_DIR/tmx"` (`$SKILL_DIR` ist das Verzeichnis dieser
Datei), ohne Argumente zeigt es seine Befehle. Es nutzt einen privaten
tmux-Server unter `/tmp/claude-tmux-<uid>/` (`CLAUDE_TMUX_DIR` übersteuert),
getrennt vom tmux des Users.

## Ablauf

1. **Starten:** `tmx start <name> <befehl…>` - ein Name pro Host oder Zweck
   (`web1`, `loop`). Auf einem Server läuft tmux trotzdem lokal, im Fenster die
   Verbindung: `tmx start web1 sudo ssh -t -C root@<host>`; Jails darin per
   `iocage console` bzw. `jexec`. Die Zeile `Zusehen: …` aus der Ausgabe gibt
   der User weiter, sofort nach dem Start.
2. **Vor jeder Eingabe:** `tmx show <name>` lesen und prüfen, dass der erwartete
   Prompt bzw. der richtige Dialog-Fokus da ist. Die Eingabe im Chat nennen,
   bevor sie gesendet wird - die Freigabe-Regeln sehen nur `tmx`, nicht den
   Befehl, der im Fenster ankommt.
3. **Eingeben:** `tmx send <name> '<zeile>'` für Text mit Enter, `tmx keys
   <name> Tab Space …` für Dialogmasken.
4. **Warten:** `tmx wait <name> '<regex>' [sek]` auf das, was erst **nach** der
   Eingabe erscheint: der nächste Prompt, der Titel des nächsten Dialogs. Bei
   Zeilen-Programmen prüft `wait` nur Ausgabe seit der letzten Eingabe; bei
   Vollbild-Programmen (Dialoge, `top`) den ganzen Bildschirm - dort trifft ein
   Muster, das schon vorher sichtbar war, sofort. Kein `sleep` als Ersatz.
5. **Beenden:** `tmx kill <name>`, danach zeigt `tmx list` keine eigene Session
   mehr. Ausnahme sind Sessions, die bewusst weiterlaufen (ein `/loop` über
   Nacht) - für sie bekommt der User den `attach`-Befehl.

Fertig ist ein Einsatz, wenn das Ergebnis per `show` belegt ist und jede eigene
Session beendet oder bewusst übergeben wurde.

## Regeln

- **Passwörter tippt der User selbst** über den `attach`-Befehl. Per `send`
  landeten sie im Transcript und in der tmux-History.
- Steht `BEENDET` in `tmx list`, hat sich das Programm beendet; die letzte
  Ausgabe bleibt per `show` lesbar, danach `kill`.
- Python-REPL mit `PYTHON_BASIC_REPL=1` starten, die neue REPL verschluckt
  gesendeten Text.

## Claude als Hintergrund-Session

```sh
tmx start loop claude --permission-mode auto "/loop <prompt>"
```

Das Start-Argument kommt als erste Eingabe an, ein `/loop` wird als
Slash-Befehl ausgeführt. Eine fertige Antwort erkennt `wait` an der Zeile
`· done <uhrzeit>` (`tmx wait loop '· done [0-9]' 300`). Ein Muster aus dem
eigenen Prompt trifft dagegen sofort, weil der Prompt oben auf dem Bildschirm
steht. Die Statuszeile zeigt Kontextfüllung und Abo-Limits.

## Herkunft

Idee nach dem Skill `tmux` in
[`mitsuhiko/agent-stuff`](https://github.com/mitsuhiko/agent-stuff/tree/main/skills/tmux),
neu geschrieben in POSIX-sh. Gegenüber der Vorlage: der Socket gilt in jedem
Aufruf (dort fehlte er beim Warten), `wait` prüft nur neue Ausgabe, und eine
beendete Sitzung bleibt mit ihrer letzten Ausgabe stehen.
