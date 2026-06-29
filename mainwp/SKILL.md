---
name: mainwp
description: >
  MainWP Dashboard (office.example.at): WordPress-Sites netzwerkuebergreifend
  verwalten. Sites auflisten, Updates pruefen und installieren, Plugins und
  Themes verwalten, Clients und Tags organisieren. Generischer Abilities-
  Executor — kann dynamisch alle verfuegbaren MainWP-Abilities ausfuehren.
  Nutze diesen Skill wenn der User WordPress-Sites uebergreifend verwalten,
  Updates einspielen oder Site-Informationen abrufen will.
  Trigger: /mainwp.
---

# mainwp -- MainWP Dashboard (WordPress-Netzwerk)

WordPress-Sites werden ueber das gebundelte Script `mainwp` (Python >=3.11,
im Skill-Verzeichnis) verwaltet. Das Script nutzt die WP Abilities API
auf dem MainWP Dashboard und kann dynamisch alle verfuegbaren Abilities
ausfuehren.

**Aufruf:** `python3 "$SKILL_DIR/mainwp" <subcommand> [options]`

## Setup

1. WordPress Application Password auf office.example.at erstellen
   (Users → Profile → Application Passwords).

2. Credentials in `.env` eintragen (cwd oder `~/.env`):
   ```
   MAINWP_HOST=https://office.example.at
   MAINWP_USER=<wp-username>
   MAINWP_APP_PASSWORD=<xxxx xxxx xxxx xxxx>
   ```

3. Setup ausfuehren:
   ```bash
   python3 "$SKILL_DIR/mainwp" setup
   ```

## Subcommands

### setup

Verbindung testen, verfuegbare Abilities von der API abrufen und in
`instance.json` cachen.

```bash
python3 "$SKILL_DIR/mainwp" setup
```

### ping

Schneller Verbindungstest zum Dashboard.

```bash
python3 "$SKILL_DIR/mainwp" ping
```

### list

Abilities auflisten (aus Cache). Mit `--category` filtern, mit `--refresh`
direkt von der API laden statt aus dem Cache.

```bash
python3 "$SKILL_DIR/mainwp" list
python3 "$SKILL_DIR/mainwp" list --category sites
python3 "$SKILL_DIR/mainwp" list --category updates
python3 "$SKILL_DIR/mainwp" list --refresh
```

Kategorien (typisch): sites, updates, clients, tags, batch.

### info \<ability-name\>

Schema und Parameter einer Ability anzeigen. Immer zuerst `info` pruefen,
bevor eine unbekannte Ability ausgefuehrt wird.

```bash
python3 "$SKILL_DIR/mainwp" info mainwp/list-sites-v1
python3 "$SKILL_DIR/mainwp" info mainwp/update-plugins-v1
```

### run \<ability-name\> [--param key=value ...] [--confirm] [--dry-run]

Ability ausfuehren. Parameter werden als `--param key=value` uebergeben
(wiederholbar). Werte werden automatisch in den richtigen Typ konvertiert
(int, float, bool, string).

```bash
# Readonly — keine Bestaetigung noetig
python3 "$SKILL_DIR/mainwp" run mainwp/list-sites-v1

# Mit Parametern
python3 "$SKILL_DIR/mainwp" run mainwp/list-sites-v1 --param status=active

# Destruktive Operation — erst Vorschau, dann ausfuehren
python3 "$SKILL_DIR/mainwp" run mainwp/update-plugins-v1 --param site_id=42 --dry-run
python3 "$SKILL_DIR/mainwp" run mainwp/update-plugins-v1 --param site_id=42 --confirm

# Batch mit angepasstem Polling
python3 "$SKILL_DIR/mainwp" run mainwp/update-all-plugins-v1 --confirm --poll-interval 10 --poll-timeout 600
```

**Flags:**
- `--confirm` — Destruktive Operation bestaetigen (Pflicht bei delete, update, etc.)
- `--dry-run` — Zeigt den Request ohne auszufuehren
- `--batch-size N` — site_ids in Gruppen von N aufteilen (Default: 25, 0=aus)
- `--poll-interval N` — Batch-Polling-Intervall in Sekunden (Default: 5)
- `--poll-timeout N` — Batch-Polling-Timeout in Sekunden (Default: 300)

## Workflow

1. Falls `instance.json` nicht existiert: `setup` ausfuehren.

2. Richtige Ability finden:
   - `list` fuer alle Abilities
   - `list --category sites` fuer Site-bezogene Abilities
   - Ability-Namen folgen dem Muster `mainwp/<aktion>-<objekt>-v1`

3. Parameter pruefen: `info <ability-name>` zeigt Schema und Pflichtparameter.

4. Ausfuehren:
   - Readonly: `run <ability-name> [--param ...]`
   - Destruktiv: IMMER zuerst `--dry-run`, dann `--confirm`

5. Ergebnis dem User in lesbarer Form praesentieren (JSON parsen, relevante
   Felder extrahieren).

## Haeufige Workflows

### Sites auflisten

Die API paginiert (Default: 20 pro Seite). IMMER `per_page=100` verwenden,
um alle Sites zu erhalten. Bei >100 Sites zusaetzlich `page=2` etc. abfragen.

```bash
# Alle Sites (bis 100)
python3 "$SKILL_DIR/mainwp" run mainwp/list-sites-v1 --param per_page=100

# Site nach Name/URL suchen
python3 "$SKILL_DIR/mainwp" run mainwp/list-sites-v1 --param search=globex
```

### Alle Sites syncen

Das Script teilt site_ids automatisch in Batches (Default: 25 pro Batch),
um Gateway Timeouts zu vermeiden. Bei leerem Array werden alle Site-IDs
erst via list-sites geholt.

```bash
# Alle Sites syncen (Auto-Batching)
python3 "$SKILL_DIR/mainwp" run mainwp/sync-sites-v1 --param 'site_ids=[]'

# Mit groesseren Batches
python3 "$SKILL_DIR/mainwp" run mainwp/sync-sites-v1 --param 'site_ids=[]' --batch-size 50

# Ohne Batching (nur bei wenigen Sites)
python3 "$SKILL_DIR/mainwp" run mainwp/sync-sites-v1 --param 'site_ids=[]' --batch-size 0
```

### Updates pruefen

```bash
python3 "$SKILL_DIR/mainwp" run mainwp/list-updates-v1 --param per_page=100
```

### Plugin-Update auf einer Site installieren

```bash
# Vorschau
python3 "$SKILL_DIR/mainwp" run mainwp/update-plugins-v1 --param site_id=42 --dry-run
# Ausfuehren
python3 "$SKILL_DIR/mainwp" run mainwp/update-plugins-v1 --param site_id=42 --confirm
```

### Site-Details abrufen

```bash
python3 "$SKILL_DIR/mainwp" run mainwp/get-site-v1 --param site_id=42
```

## Sicherheitshinweise

- Vor destruktiven Operationen IMMER zuerst `--dry-run` verwenden.
- Updates: Zuerst `info` pruefen, dann `--dry-run`, dann `--confirm`.
- Batch-Updates: Ergebnis abwarten, Job-Status pruefen.
- Nie mehrere destruktive Operationen blind hintereinander ausfuehren.
- Das Script verweigert destruktive Operationen ohne `--confirm`.

## Hinweise

- Ability-Namen koennen sich je nach MainWP-Version unterscheiden.
  Bei Unsicherheit: `list` und `info` verwenden.
- `instance.json` ist ein Cache — bei API-Aenderungen `setup` erneut
  ausfuehren oder `list --refresh` verwenden.
- Application Passwords enthalten Leerzeichen — in der `.env` nicht
  in Anfuehrungszeichen setzen oder die Leerzeichen beibehalten.
