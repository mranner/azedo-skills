# Stammdaten — Subcommand-Referenz

Projekte, Aktivitaeten, Kunden, Benutzer, Tags und Teams.

## Projekte

```bash
python3 "$SKILL_DIR/kimai" list-projects
python3 "$SKILL_DIR/kimai" get-project <id>
python3 "$SKILL_DIR/kimai" create-project --name "<name>" --customer <id> \
  [--comment "<text>"] [--color "<hex>"] [--visible <0|1>] [--billable <0|1>] \
  [--global-activities <0|1>]
python3 "$SKILL_DIR/kimai" update-project <id> \
  [--name "<name>"] [--customer <id>] [--comment "<text>"] \
  [--color "<hex>"] [--visible <0|1>] [--billable <0|1>] [--global-activities <0|1>]
python3 "$SKILL_DIR/kimai" delete-project <id>
```

`--global-activities` steuert, ob die instanzweiten (globalen) Aktivitaeten
— z.B. *IT-Support (SP90)* — im Projekt buchbar sind. Bei `create-project` ist
der **Default `1`**; ohne globale Aktivitaeten schlaegt `create-timesheet` mit
einer globalen Aktivitaet sonst mit `400 activity … invalid choice` fehl.

## Aktivitaeten

```bash
python3 "$SKILL_DIR/kimai" list-activities [--project <id>]
python3 "$SKILL_DIR/kimai" get-activity <id>
python3 "$SKILL_DIR/kimai" create-activity --name "<name>" \
  [--project <id>] [--comment "<text>"] [--color "<hex>"] \
  [--visible <0|1>] [--billable <0|1>]
python3 "$SKILL_DIR/kimai" update-activity <id> \
  [--name "<name>"] [--project <id>] [--comment "<text>"] \
  [--color "<hex>"] [--visible <0|1>] [--billable <0|1>]
python3 "$SKILL_DIR/kimai" delete-activity <id>
```

## Kunden

```bash
python3 "$SKILL_DIR/kimai" list-customers
python3 "$SKILL_DIR/kimai" get-customer <id>
python3 "$SKILL_DIR/kimai" create-customer --name "<name>" \
  [--country AT] [--currency EUR] [--timezone Europe/Vienna] \
  [--company "<firma>"] [--comment "<text>"] [--color "<hex>"] \
  [--visible <0|1>] [--billable <0|1>]
python3 "$SKILL_DIR/kimai" update-customer <id> \
  [--name "<name>"] [--country <cc>] [--currency <cur>] \
  [--timezone <tz>] [--company "<firma>"] [--comment "<text>"] \
  [--color "<hex>"] [--visible <0|1>] [--billable <0|1>]
python3 "$SKILL_DIR/kimai" delete-customer <id>
```

## Benutzer

```bash
python3 "$SKILL_DIR/kimai" list-users
python3 "$SKILL_DIR/kimai" get-user <id>
```

## Tags

```bash
python3 "$SKILL_DIR/kimai" list-tags
python3 "$SKILL_DIR/kimai" create-tag --name "<name>"
python3 "$SKILL_DIR/kimai" delete-tag <id>
```

## Teams

```bash
python3 "$SKILL_DIR/kimai" list-teams
python3 "$SKILL_DIR/kimai" get-team <id>
python3 "$SKILL_DIR/kimai" create-team --name "<name>" --members "<uid1,uid2,...>" [--color "<hex>"]
python3 "$SKILL_DIR/kimai" update-team <id> [--name "<name>"] [--members "<uid1,uid2,...>"] [--color "<hex>"]
python3 "$SKILL_DIR/kimai" delete-team <id>
```

Der erste User in `--members` wird automatisch Teamlead.
