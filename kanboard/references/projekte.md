# Projekte und Mitglieder - Subcommands

Projekte anlegen und löschen, Mitglieder und Rollen verwalten, Spalten und User auflisten.
Aufruf durchgehend `python3 "$SKILL_DIR/kanboard" <subcommand>`.

### Projekte, Spalten, User auflisten

```bash
python3 "$SKILL_DIR/kanboard" list-projects
python3 "$SKILL_DIR/kanboard" list-columns --project <name|id>
python3 "$SKILL_DIR/kanboard" list-users
```

### Projekt-Verwaltung (Anlegen, Mitglieder, Owner)

Projekte anlegen und die Projekt-Mitgliedschaften/Rollen verwalten. Rollen sind
`project-manager`, `project-member`, `project-viewer` (Kanboard-Standardrollen).

```bash
# Projekt anlegen (--owner optional: wird Owner UND project-manager-Mitglied)
python3 "$SKILL_DIR/kanboard" create-project --name "<name>" [--owner <username>]

# Projekt loeschen (bricht ab, solange Tasks drin sind; --force loescht sie mit)
python3 "$SKILL_DIR/kanboard" remove-project --project <name|id> [--force]

# Mitglieder eines Projekts mit Rolle + Owner anzeigen
python3 "$SKILL_DIR/kanboard" list-project-users --project <name|id>

# User zum Projekt hinzufuegen (--role Default: project-member)
python3 "$SKILL_DIR/kanboard" add-project-user --project <name|id> --user <username> [--role <rolle>]

# Rolle eines vorhandenen Mitglieds aendern
python3 "$SKILL_DIR/kanboard" set-project-user-role --project <name|id> --user <username> --role <rolle>

# User aus Projekt entfernen
python3 "$SKILL_DIR/kanboard" remove-project-user --project <name|id> --user <username>

# Owner des Projekts setzen (User wird bei Bedarf zuerst als Mitglied ergaenzt)
python3 "$SKILL_DIR/kanboard" set-project-owner --project <name|id> --user <username>
```

**Hinweise:**

- Nach `create-project` einmal `setup` ausfuehren, damit das neue Projekt in
  `instance.json` bekannt ist (sonst schlaegt `--project <name>` fehl; die
  numerische `--project <id>` funktioniert sofort). Dasselbe gilt nach
  `remove-project` — sonst zeigt `instance.json` ein Projekt, das es nicht
  mehr gibt.
- `remove-project` ist **nicht umkehrbar** und nimmt alle Tasks des Projekts mit
  (offene wie geschlossene). Der Befehl zaehlt sie deshalb vorher und bricht mit
  `success: false` und Exit-Code 1 ab, solange welche vorhanden sind; erst
  `--force` fuehrt aus. Bei einem leeren Projekt braucht es kein `--force`.
- `--user` wird ueber `instance.json` aufgeloest — ist ein User dort nicht
  gelistet (z.B. neu angelegt), zuerst `setup` ausfuehren.
- „Gleiche Rechte wie in Projekt X" = Rolle mit `list-project-users --project X`
  ablesen und beim Ziel via `add-project-user --role <rolle>` setzen.
