---
name: mainwp
description: >
  MainWP Dashboard: WordPress-Sites netzwerkuebergreifend
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

1. WordPress Application Password auf dem MainWP-Dashboard-Host erstellen
   (Users → Profile → Application Passwords).

2. Credentials in `.env` eintragen (cwd oder `~/.env`):
   ```
   MAINWP_HOST=https://dashboard.example.at
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
python3 "$SKILL_DIR/mainwp" info mainwp/run-updates-v1
```

### run \<ability-name\> [--param key=value ...] [--confirm] [--dry-run]

Ability ausfuehren. Parameter werden als `--param key=value` uebergeben
(wiederholbar). Werte werden automatisch in den richtigen Typ konvertiert
(int, float, bool, string).

```bash
# Readonly — keine Bestaetigung noetig
python3 "$SKILL_DIR/mainwp" run mainwp/list-sites-v1

# Mit Parametern (Werte aus dem Schema, nicht geraten -- vorher `info`)
python3 "$SKILL_DIR/mainwp" run mainwp/list-sites-v1 --param status=connected

# Schreibende Operation -- erst Vorschau, dann ausfuehren
python3 "$SKILL_DIR/mainwp" run mainwp/run-updates-v1 \
  --param 'site_ids_or_domains=[42]' --param 'types=["plugins"]' --dry-run
python3 "$SKILL_DIR/mainwp" run mainwp/run-updates-v1 \
  --param 'site_ids_or_domains=[42]' --param 'types=["plugins"]' --confirm

# Batch mit angepasstem Polling
python3 "$SKILL_DIR/mainwp" run mainwp/sync-sites-v1 --param 'site_ids=[]' \
  --poll-interval 10 --poll-timeout 600
```

**Flags:**
- `--confirm` — Destruktive Operation bestaetigen
- `--dry-run` — Zeigt den Request ohne auszufuehren (fuer **jede** Ability)
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
   - Schreibend: IMMER zuerst `--dry-run`, dann `--confirm` -- auch dann, wenn
     das Script den Aufruf ohne `--confirm` durchliesse (siehe Sicherheitshinweise)

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

**Welche Felder zurueckkommen:** `id`, `url`, `name`, `status`, `client_id` -- mehr
nicht. Insbesondere **keine** `wp_version` und **keine** `php_version`. Wer die
Versionen braucht, kommt an `get-site-v1` je Site nicht vorbei (siehe
„Site-Details abrufen").

**Parameter immer ueber den Wrapper geben.** Ein direkter Griff auf die
Abilities-API am Script vorbei funktioniert nicht zuverlaessig: die
Query-Parameter kommen dort nicht an. Die Paginierung laeuft dann still ueber
dieselbe Default-Seite und liefert Dubletten statt der naechsten 100 Sites --
ohne Fehlermeldung, die Ausgabe sieht plausibel aus.

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

**Status auslesen — Ausgabe NICHT tailen.** Das Script aggregiert ueber alle
Batches und liefert `total_synced`, `total_errors` sowie die Arrays `synced[]`
und `errors[]` (jeder Fehler mit `identifier`, `code`, `message`). Diese Summen
stehen **oben** im JSON, vor dem langen `synced`-Array — `| tail -N` schneidet
sie ab. Einzelne Sites schlagen oft fehl, deshalb immer `total_errors`/`errors[]`
pruefen. Ausgabe in eine Datei schreiben (stderr = Batch-Fortschritt, getrennt
halten), dann gezielt auswerten:

```bash
# Vollstaendige Ausgabe sichern, stderr getrennt
python3 "$SKILL_DIR/mainwp" run mainwp/sync-sites-v1 --param 'site_ids=[]' \
  >.tmp/mainwp_sync.json 2>.tmp/mainwp_sync.progress

# Zusammenfassung + fehlgeschlagene Sites anzeigen
python3 -c "
import json
d = json.load(open('.tmp/mainwp_sync.json'))
print(f\"synced: {d.get('total_synced')}  errors: {d.get('total_errors')}  batches: {d.get('batches')}\")
for e in d.get('errors', []):
    print(f\"  FAIL {e['identifier']}: [{e['code']}] {e['message']}\")
"
```

### Updates pruefen

```bash
python3 "$SKILL_DIR/mainwp" run mainwp/list-updates-v1 --param per_page=100
```

### Updates einspielen

Zustaendig ist `run-updates-v1` -- eine Ability `update-plugins-v1` gibt es
**nicht**. Die Parameter heissen `site_ids_or_domains` (Array aus IDs oder
Domains), `types` (`core`, `plugins`, `themes`, `translations`) und
`specific_items` (Slugs).

```bash
# Vorschau -- zeigt den Request, ohne etwas zu aendern
python3 "$SKILL_DIR/mainwp" run mainwp/run-updates-v1 \
  --param 'site_ids_or_domains=[42]' --param 'types=["plugins"]' --dry-run

# ein bestimmtes Plugin auf einer Site
python3 "$SKILL_DIR/mainwp" run mainwp/run-updates-v1 \
  --param 'site_ids_or_domains=[42]' --param 'types=["plugins"]' \
  --param 'specific_items=["akismet"]' --confirm
```

**Ein leeres Array bedeutet „alle".** Das gilt fuer jeden der drei Parameter,
und ein weggelassener Parameter ist ein leeres Array. `run mainwp/run-updates-v1`
ohne `--param` spielt also saemtliche verfuegbaren Updates auf **allen** Sites
ein. Die Ziele deshalb immer explizit setzen.

**Der Wrapper haelt hier nichts auf.** `run-updates-v1` traegt
`destructive: false` und enthaelt keines der Verben, an denen die Heuristik des
Scripts greift (`delete`, `remove`, `disconnect`, `deactivate`, `suspend`) -- der
Aufruf laeuft ohne `--confirm` durch. Der Schutz muss hier also vom Aufrufer
kommen: erst `--dry-run`, dann ausfuehren.

Ausgabe: `updated[]`, `errors[]` (je mit `code` und `message`) und `summary`
(`total_updated`, `total_errors`, `sites_updated`). Ab mehr als 200 Sites
schaltet MainWP auf Hintergrundverarbeitung um und liefert stattdessen `queued`,
`job_id` und `status_url`. Einzelne fehlgeschlagene Updates lassen den
Gesamtaufruf erfolgreich aussehen -- `errors[]` immer pruefen.

### Site-Details abrufen

Der Parameter heisst `site_id_or_domain` (nicht `site_id`) und nimmt beides:
Site-ID oder Domain/URL.

```bash
python3 "$SKILL_DIR/mainwp" run mainwp/get-site-v1 --param site_id_or_domain=42
python3 "$SKILL_DIR/mainwp" run mainwp/get-site-v1 --param site_id_or_domain=www.example.at

# mit Statistiken (Update-Zahlen, Health)
python3 "$SKILL_DIR/mainwp" run mainwp/get-site-v1 --param site_id_or_domain=42 --param include_stats=true
```

Geliefert werden `id`, `url`, `name`, `status`, `client_id`, `wp_version`,
`php_version`, `last_sync`, `admin_username`, `child_version`, `notes` und -- mit
`include_stats` -- `stats`.

**Versionen ueber alle Sites erheben.** Das ist ein Aufruf **je Site**; bei einem
Dashboard mit gut hundert Sites also gut hundert Aufrufe. Praktikabel bleibt das
nur parallel:

```bash
# IDs einsammeln (beide Seiten, siehe „Sites auflisten")
python3 "$SKILL_DIR/mainwp" run mainwp/list-sites-v1 --param per_page=100 \
  >.tmp/mainwp_sites_1.json
python3 "$SKILL_DIR/mainwp" run mainwp/list-sites-v1 --param per_page=100 --param page=2 \
  >.tmp/mainwp_sites_2.json

python3 -c "
import json, glob
for f in sorted(glob.glob('.tmp/mainwp_sites_*.json')):
    for it in json.load(open(f)).get('items', []):
        print(it['id'])
" >.tmp/mainwp_ids.txt

# je Site abfragen, 6 parallel -- jede Antwort in eine eigene Datei
export SKILL_DIR
xargs -P 6 -I{} sh -c 'python3 "$SKILL_DIR/mainwp" run mainwp/get-site-v1 --param site_id_or_domain=$1 >.tmp/mainwp_site_$1.json' _ {} \
  <.tmp/mainwp_ids.txt
```

Die Antworten **nicht** parallel in dieselbe Datei schreiben: die Ausgabe des
Wrappers ist mehrzeiliges JSON, bei sechs gleichzeitigen Schreibern vermischen
sich die Bloecke. `export SKILL_DIR` ist noetig, weil die Variable sonst in der
`sh -c`-Subshell leer ist und `python3` still auf einen falschen Pfad zeigt.

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

Abilities-Aufrufe dagegen **nicht** am Script vorbei absetzen: Parameter kommen
bei einem direkten Request nicht an, der Aufruf laeuft dann stillschweigend mit
den Defaults. `--param` gehoert an den Wrapper.

## Sicherheitshinweise

- Vor destruktiven Operationen IMMER zuerst `--dry-run` verwenden.
- Updates: Zuerst `info` pruefen, dann `--dry-run`, dann `--confirm`.
- Batch-Updates: Ergebnis abwarten, Job-Status pruefen.
- Nie mehrere destruktive Operationen blind hintereinander ausfuehren.
- Das Script verweigert eine Ability ohne `--confirm` nur dann, wenn sie
  `destructive: true` traegt oder ihr Name `delete`, `remove`, `disconnect`,
  `deactivate` oder `suspend` enthaelt. **Updates fallen unter keines von
  beidem** und laufen ungebremst durch -- siehe „Updates einspielen".
- Parameterwerte aus dem Schema nehmen (`info`), nicht aus dem Gedaechtnis.
  Enum-Werte prueft die API immerhin selbst und antwortet mit
  `400 ability_invalid_input` samt Liste der zulaessigen Werte (`status=active`
  gibt es z.B. nicht, gemeint ist `connected`). Ein falscher **Ability-Name**
  faellt dagegen erst beim Aufruf mit `404 rest_ability_not_found` auf.

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
