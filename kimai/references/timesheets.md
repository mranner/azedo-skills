# Timesheets — Subcommand-Referenz

Die Zeitregeln (Anker, Viertelstunden-Raster, Overlap-Guard) stehen in der
SKILL.md, Abschnitt "Zeitregeln" — sie gelten fuer jeden Befehl auf dieser Seite.

```bash
# Auflisten (mit Filtern)
python3 "$SKILL_DIR/kimai" list-timesheets \
  [--user <id>] [--project <id>] [--activity <id>] \
  [--begin <iso-datetime>] [--end <iso-datetime>] \
  [--exported <0|1>] [--size <n>] [--page <n>]

# Einzelnen Eintrag anzeigen
python3 "$SKILL_DIR/kimai" get-timesheet <id>

# Eintrag anlegen (ohne --end wird ein laufender Timer gestartet)
python3 "$SKILL_DIR/kimai" create-timesheet \
  --begin <iso-datetime> [--end <iso-datetime>] \
  --project <id> --activity <id> \
  [--description "<text>"] [--user <id>] \
  [--tags "tag1,tag2"] [--billable <0|1>] [--no-snap]
```

`--begin` wird auf die naechste Viertelstunde aufgerundet, `--end` um dieselbe Differenz
mitverschoben (die Dauer bleibt also erhalten); die Verschiebung wird auf stderr gemeldet.
`--no-snap` bucht die Rohzeiten. Der **Anker** fuer `--begin` ist Sache des Aufrufers —
siehe Zeitregeln in der SKILL.md.

```bash
# Eintrag aendern
python3 "$SKILL_DIR/kimai" update-timesheet <id> \
  [--begin <iso>] [--end <iso>] [--project <id>] [--activity <id>] \
  [--description "<text>"] [--user <id>] [--tags "tag1,tag2"] \
  [--exported <0|1>] [--billable <0|1>]

# Eintrag loeschen
python3 "$SKILL_DIR/kimai" delete-timesheet <id>

# Letzte Eintraege (expandiert, mit User/Projekt-Details)
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
