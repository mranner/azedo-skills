# Timesheets — Subcommand-Referenz

Die Zeitregeln (Anker, Viertelstunden-Raster, Overlap-Guard) stehen in der
SKILL.md, Abschnitt "Zeitregeln" — sie gelten für jeden Befehl auf dieser Seite.

```bash
# Auflisten (mit Filtern)
python3 "$SKILL_DIR/kimai" list-timesheets \
  [--user <id>] [--project <id>] [--activity <id>] \
  [--begin <iso-datetime>] [--end <iso-datetime>] \
  [--exported <0|1>] [--size <n>] [--page <n>]
# --user all für Auswertungen über alle User; ohne Angabe kommen nur die eigenen Buchungen.

# Einzelnen Eintrag anzeigen
python3 "$SKILL_DIR/kimai" get-timesheet <id>

# Eintrag anlegen (ohne --end wird ein laufender Timer gestartet)
python3 "$SKILL_DIR/kimai" create-timesheet \
  --begin <iso-datetime> [--end <iso-datetime>] \
  --project <id> --activity <id> \
  [--description "<text>"] [--user <id>] \
  [--tags "tag1,tag2"] [--billable <0|1>] [--no-snap]
```

`--begin` wird auf die nächste Viertelstunde aufgerundet, `--end` um dieselbe Differenz
mitverschoben (die Dauer bleibt also erhalten); die Verschiebung wird auf stderr gemeldet.
`--no-snap` bucht die Rohzeiten. Der **Anker** für `--begin` ist Sache des Aufrufers —
siehe Zeitregeln in der SKILL.md.

```bash
# Eintrag ändern
python3 "$SKILL_DIR/kimai" update-timesheet <id> \
  [--begin <iso>] [--end <iso>] [--project <id>] [--activity <id>] \
  [--description "<text>"] [--user <id>] [--tags "tag1,tag2"] \
  [--exported <0|1>] [--billable <0|1>] \
  [--hourly-rate <betrag>] [--fixed-rate <betrag>]

# Hinweis: `--hourly-rate` setzt den Satz dieses Eintrags. Nötig, wenn eine Rate
# erst nach dem Buchen gesetzt wurde - Kimai schreibt den Satz beim Anlegen fest,
# ein Umhängen per --activity zieht ihn nicht nach.

# Eintrag löschen
python3 "$SKILL_DIR/kimai" delete-timesheet <id>

# Letzte Einträge (expandiert, mit User/Projekt-Details)
python3 "$SKILL_DIR/kimai" recent-timesheets [--user <id>] [--begin <iso>] [--size <n>]

# Aktive Timer
python3 "$SKILL_DIR/kimai" active-timesheets

# Timer stoppen
python3 "$SKILL_DIR/kimai" stop-timesheet <id>

# Timer neustarten (erstellt neuen Eintrag basierend auf bestehendem)
python3 "$SKILL_DIR/kimai" restart-timesheet <id>

# Eintrag duplizieren
python3 "$SKILL_DIR/kimai" duplicate-timesheet <id>

# Eintrag als exportiert markieren
python3 "$SKILL_DIR/kimai" export-timesheet <id>
```

## Offene Stunden seit einem Stichtag

"Welche Stunden sind noch nicht verrechnet" heißt: Einträge, die nicht als exportiert
markiert sind. `open-hours` summiert sie je Kunde und Monat, über alle User:

```bash
python3 "$SKILL_DIR/kimai" open-hours --since 2026-01-01 [--until 2026-10-31] \
  [--customer <id|Namensteil>] [--detail] [--json]
```

`--until` fehlt: bis heute. `--detail` teilt nach Projekt und Tätigkeit und nennt den
ersten und letzten Tag. Laufende Timer bleiben außen vor (Hinweis auf stderr).

Für Einzeleinträge statt Summen dieselbe Abfrage mit `list-timesheets`:

```bash
python3 "$SKILL_DIR/kimai" list-timesheets --user all --exported 0 \
  --begin 2026-01-01T00:00:00 --end 2026-10-31T23:59:59 --size 200 --page <n>
```

- `--user all` ist Pflicht, sonst kommen nur die Buchungen des API-Users.
- Seite für Seite abrufen, bis eine Seite weniger als `--size` Einträge hat.
  `API error 404` auf der Folgeseite heißt ebenfalls: keine weiteren Einträge.
- Gegenprobe mit `--exported 1`: beide Abfragen zusammen ergeben alle Einträge des Zeitraums.
- Der Eintrag nennt nur die Projekt-ID. Den Kunden liefert `list-projects` im Feld
  `customer`, dort als Name, nicht als ID.
