---
name: bang
description: >
  Ersetzt einen Befehl für `!` durch einen Einzeiler (max. 80 Zeichen), der
  ein selbstlöschendes Script in `.tmp/` aufruft. Selbsttätig nutzen, bevor
  ein `!`-Befehl über 80 Zeichen, mit Heredoc oder mehrzeilig an den User
  geht. Auch bei "gib mir einen Einzeiler". Trigger: /bang.
---

# bang - kurzer `!`-Einzeiler mit Wegwerf-Script

Muss der User einen Befehl selbst per `!` ausführen, bekommt er statt eines
langen oder mehrzeiligen Blocks nur:

```
! sh ~/<projekt>/.tmp/bang-<slug>-<hex>.sh
```

Der eigentliche Inhalt steht im Script.

## Wann

- Der `!`-Befehl wäre **länger als 80 Zeichen**, enthält ein **Heredoc** oder
  hat **mehrere Zeilen**.
- Kürzere Einzelbefehle gehen weiter direkt als `! <befehl>` an den User.
- `/bang` ohne Argument: den zuletzt ausgegebenen langen `!`-Befehl nachträglich
  in diese Form bringen.

**Kein Umweg um Freigaben.** Der Skill gilt nur für Befehle, die ohnehin per `!`
an den User gehen sollen. Er ersetzt nicht die Rückfrage nach einem
Permission-Denial; wird ein Weg blockiert, entscheidet der User, ob er ihn per
`!` selbst geht.

## Ablage

- Pfad: `.tmp/bang-<slug>-<hex>.sh` im Projekt-Arbeitsverzeichnis, im Aufruf
  und in der `rm`-Zeile **absolut**, mit `~/` gekürzt. Das Arbeitsverzeichnis
  der Shell wandert mit jedem `cd` im Bash-Tool; ein relativer Pfad greift dann
  ins Leere (`No such file or directory`).
  - `<slug>`: 1-3 Wörter kebab-case, was das Script tut (`cron-update`,
    `dev-artikel-loeschen`).
  - `<hex>`: 4 zufällige Hex-Zeichen, damit parallele Sessions sich nicht
    überschreiben.
- Fehlt `.tmp/`: `mkdir -m 700 .tmp`. Nie `/tmp`.
- Der ganze Aufruf `! sh ~/<projekt>/.tmp/bang-….sh` bleibt unter 80 Zeichen;
  sonst den Slug kürzen.

## Aufbau

Erste Zeile ist immer das Selbstlöschen. `sh` hat die Datei da schon geöffnet und
liest sie zu Ende; das Script läuft vollständig, die Datei ist trotzdem sofort
weg - auch bei Fehler oder Ctrl-C. Der Exit-Code des Scripts kommt beim User an.
Den eigenen Pfad wörtlich eintragen: den Positionsparameter für den
Scriptnamen ersetzt Claude Code beim Laden dieser Datei durch das
Skill-Argument.

```sh
rm -f -- ~/<projekt>/.tmp/bang-<slug>-<hex>.sh
sudo ssh -C root@host.example.org sh <<'SCRIPT'
set -e
sed -i~ 's/^daily_clean_tmps_enable=.*/daily_clean_tmps_enable="YES"/' /etc/periodic.conf
grep daily_clean_tmps /etc/periodic.conf
SCRIPT
```

- **Remote immer per STDIN-Heredoc an `sh`**, mit `'SCRIPT'` in Quotes: keine
  lokale Expansion, kein Quoting über mehrere
  Ebenen. Gateway-Hops: `"ssh -T root@<intern> sh"` als Remote-Befehl.
- Lokale Befehle direkt ins Script, ohne Heredoc.
- `set -e` dort, wo ein späterer Schritt nur nach Erfolg des vorigen laufen darf.
- Am Ende eine Kontrollausgabe (geänderte Zeile, Dienststatus), damit das Ergebnis
  im Chat sichtbar ist.

## Vor dem Aufruf

Der User führt das Script blind aus. Deshalb **vor** der Ausgabe des Einzeilers
den Inhalt im Chat zeigen: den Volltext, bei längeren Scripts eine knappe Liste
der Schritte mit allen zustandsändernden Befehlen wörtlich.

## Fehlschlag

Das Script ist nach dem Aufruf weg, auch wenn es fehlgeschlagen ist. Vor einem
neuen Versuch **den Zustand prüfen** - ein abgebrochenes Script ist oft zum Teil
gelaufen (ein zweites `sed -i~` überschreibt das Backup mit der schon geänderten
Datei). Dann ein **neues** Script mit neuem `<hex>` schreiben, das nur die
fehlenden Schritte enthält.

## Mehrfach benötigt

Soll dasselbe Script mehrmals laufen (Wiederholung nach einer Prüfung,
Schleife über Hosts per Argument), entfällt die `rm`-Zeile. Dann im Chat sagen,
dass es liegen bleibt, und es beim Abschluss des Tasks selbst löschen.
