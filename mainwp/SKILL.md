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
   MAINWP_V2_CONSUMER_KEY=<consumer-key>
   MAINWP_V2_CONSUMER_SECRET=<consumer-secret>
   ```

   - `MAINWP_USER` + `MAINWP_APP_PASSWORD`: WP Application Password fuer die Abilities-API (Sites, Updates, Clients)
   - `MAINWP_V2_CONSUMER_KEY` + `MAINWP_V2_CONSUMER_SECRET`: REST API v2 Key fuer Tag-Verwaltung (in DB-Tabelle `wp_mainwp_api_keys` gespeichert)

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

Die API paginiert (Default: 20 pro Seite). IMMER `per_page=100` verwenden.
**Achtung:** Aktuell 124 Sites — `per_page=100` liefert nicht alle! Immer
auch `page=2` abfragen wenn `total > 100`.

```bash
# Seite 1 (bis 100)
python3 "$SKILL_DIR/mainwp" run mainwp/list-sites-v1 --param per_page=100

# Seite 2 (Rest)
python3 "$SKILL_DIR/mainwp" run mainwp/list-sites-v1 --param per_page=100 --param page=2

# Site nach Name/URL suchen
python3 "$SKILL_DIR/mainwp" run mainwp/list-sites-v1 --param search=globex

# Sites nach Tag filtern (tag_id aus list-tags)
python3 "$SKILL_DIR/mainwp" run mainwp/list-sites-v1 --param tag_id=4 --param per_page=100
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

### Tags verwalten (REST API v2)

Die Abilities-API hat **keine** Tag-Operationen. Tags werden ueber die
MainWP REST API v2 verwaltet, die mit `MAINWP_V2_CONSUMER_KEY` / `MAINWP_V2_CONSUMER_SECRET`
aus `~/.env` authentifiziert.

```bash
# Tags auflisten (inkl. zugewiesener Sites)
python3 -c "
import requests, json, os
host = os.environ['MAINWP_HOST']
r = requests.get(f'{host}/wp-json/mainwp/v2/tags',
    params={'consumer_key': os.environ['MAINWP_V2_CONSUMER_KEY'],
            'consumer_secret': os.environ['MAINWP_V2_CONSUMER_SECRET']},
    timeout=15)
for t in r.json().get('data', {}).values():
    print(f\"  {t['id']:>3}  {t['name']:<20} sites: {t['sites_ids']}\")
"

# Tag erstellen
python3 -c "
import requests, os
host = os.environ['MAINWP_HOST']
r = requests.post(f'{host}/wp-json/mainwp/v2/tags/add',
    params={'consumer_key': os.environ['MAINWP_V2_CONSUMER_KEY'],
            'consumer_secret': os.environ['MAINWP_V2_CONSUMER_SECRET']},
    json={'name': 'NeuerTag'},
    timeout=15)
print(r.json())
"
```

Tag einer Site zuweisen: `update-site-v1` mit `--param tag_ids=[id1,id2]` (Abilities-API).

### Clients verwalten

Clients werden ueber die Abilities-API verwaltet (nicht v2).

```bash
# Clients auflisten
python3 "$SKILL_DIR/mainwp" run mainwp/list-clients-v1

# Client erstellen (mit Sites zuweisen)
python3 "$SKILL_DIR/mainwp" run mainwp/add-client-v1 --param name=Kundenname --param "selected_sites=[169,186]" --confirm

# Client einer Site zuweisen
python3 "$SKILL_DIR/mainwp" run mainwp/update-site-v1 --param site_id_or_domain=169 --param client_id=2 --confirm
```

## API-Architektur

MainWP hat **zwei separate APIs** mit unterschiedlicher Authentifizierung:

| API | Auth | Verwendung |
|-----|------|------------|
| **WP Abilities API** (`wp-abilities/v1`) | WP Application Password | Sites, Updates, Plugins, Themes, Clients |
| **REST API v2** (`mainwp/v2`) | Consumer Key/Secret | Tags (erstellen, loeschen, zuweisen) |

Das `mainwp` Script verwendet die Abilities-API. Fuer Tag-Operationen
direkt die v2 REST API via `requests` aufrufen (siehe Beispiele oben).

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
- v2 REST API Keys werden in der DB-Tabelle `wp_mainwp_api_keys` gespeichert,
  nicht in wp_options. Consumer Secret muss mit `wp_hash_password()` gehasht
  werden (nicht `mainwp_api_hash()`).
- Fuer v2 API Aufrufe `~/.env` sourcen oder Variablen direkt aus `os.environ` lesen.
