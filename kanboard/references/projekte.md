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
# (markiert moegliche Gruppen-Herkunft als via_group_candidates, siehe Gruppen)
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
- `--user` wird ueber `instance.json` aufgeloest; steht der Name dort nicht
  (z.B. neu angelegt), fragt der Skill im Admin-Pfad `getAllUsers` nach. Statt
  des Namens geht auch die numerische User-ID. Deaktivierte User sind seit
  v1.61.0 in `instance.json` enthalten und mit `"is_active": 0` markiert —
  wichtig, weil `remove-project-user` fast immer Ausgeschiedene betrifft.
- „Gleiche Rechte wie in Projekt X" = Rolle mit `list-project-users --project X`
  ablesen und beim Ziel via `add-project-user --role <rolle>` setzen.

### Gruppen

Auf office.azedo.at kommt der Projektzugriff ueberwiegend aus Gruppen, nicht aus
direkten Mitgliedschaften. Rollen sind dieselben wie bei Projekt-Mitgliedern.

```bash
# Gruppen und ihre Mitglieder anzeigen
python3 "$SKILL_DIR/kanboard" list-groups
python3 "$SKILL_DIR/kanboard" list-group-members --group <name|id>

# Gruppe anlegen, Mitglieder setzen und entfernen
python3 "$SKILL_DIR/kanboard" create-group --name "<name>"
python3 "$SKILL_DIR/kanboard" add-group-member --group <name|id> --user <username|id>
python3 "$SKILL_DIR/kanboard" remove-group-member --group <name|id> --user <username|id>

# Gruppe einem Projekt zuordnen, Rolle aendern, Zuordnung entfernen
python3 "$SKILL_DIR/kanboard" add-project-group --project <name|id> --group <name|id> [--role <rolle>]
python3 "$SKILL_DIR/kanboard" set-project-group-role --project <name|id> --group <name|id> --role <rolle>
python3 "$SKILL_DIR/kanboard" remove-project-group --project <name|id> --group <name|id>
```

**Hinweise:**

- `remove-group-member` wirkt **gruppenweit**: der User verliert den Zugriff auf
  alle Projekte, denen die Gruppe zugeordnet ist. Soll nur ein Projekt entzogen
  werden, stattdessen die Gruppe vom Projekt loesen (`remove-project-group`) oder
  die Gruppe aufteilen.
- `remove-project-user` entfernt nur **direkte** Mitgliedschaften. Kommt der
  Zugriff aus einer Gruppe, liefert der Aufruf `success: false` und aendert
  nichts; die Ausgabe traegt dann einen `hint` mit genau diesem Verdacht. Zum
  Nachsehen `list-groups` / `list-group-members`.
- `getProjectGroupRoles`, `getProjectUserRoles`, `getProjectGroups`,
  `getMemberGroups` und `getGroupsByProject` gibt es in dieser Kanboard-Version
  **nicht** (`Method not found`, geprueft 2026-09-21); die Projekt-Gruppen-
  Zuordnung ist daher nur schreibend erreichbar.
- `list-project-users` naehert die Herkunft deshalb heuristisch an: ist eine
  Gruppe dem Projekt zugeordnet, sind zwingend **alle** ihre Mitglieder
  Projektmitglieder. Jede Gruppe, deren Mitglieder vollstaendig im Projekt
  stehen, erscheint bei diesen Usern als `via_group_candidates`. Die Umkehrung
  gilt nicht — eine Gruppe, deren Mitglieder zufaellig alle direkt im Projekt
  sind, wird mitgemeldet. Das Feld ist ein **Verdacht, kein Nachweis**; die
  Ausgabe sagt das im `hinweis` mit. Verlaesslich ist nur die Gegenprobe: greift
  `remove-project-user` nicht, war es eine Gruppe.
- Eine Gruppe **loeschen** kann der Skill nicht (kein `remove-group`) — das
  bleibt dem Kanboard-UI vorbehalten.
