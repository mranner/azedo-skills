# azedo-skills

Claude Code Skills für das azedo-Team.

## Installation

```bash
git clone https://github.com/mranner/azedo-skills.git ~/.claude/azedo-skills
sh ~/.claude/azedo-skills/install.sh
```

Das Install-Script legt Symlinks an und traegt die nötigen Permissions in `~/.claude/settings.json` ein (Read/Write auf den Skills-Ordner).

## Update

```bash
cd ~/.claude/azedo-skills && git pull
```

`install.sh` richtet beim ersten Lauf einen Git-Hook ein, der neue Skills nach
jedem `git pull` **automatisch** verlinkt — man muss `install.sh` nach einem
Update also nicht erneut aufrufen.

**Aeltere Installationen ohne Hook:** einmalig `sh install.sh` ausfuehren,
danach greift der Automatismus bei jedem weiteren `git pull`.

Nach einem Update ggf. `setup` erneut ausfuehren, damit `instance.json` aktualisiert wird.

**Ab v1.1.0:** `setup` muss nach dem Update einmal ausgefuehrt werden — die `instance.json` enthaelt jetzt die Benutzerrolle (Admin/Non-Admin) fuer die API-Aufrufe.

## Neue Skills hinzufuegen

**Wichtig:** Wird ein neuer Skill angelegt, muss sein Verzeichnisname in die
`for skill in …`-Liste in `install.sh` eingetragen werden. Sonst legt
`install.sh` beim naechsten Lauf keinen Symlink an und der Skill ist nach dem
Update nicht verfuegbar.

Alle Skript-Shebangs verwenden `#!/usr/bin/env python3` (minor-version-
unabhaengig); ein neuer Skill sollte das ebenso halten.

## Skills

### kanboard

Verwaltet Tasks auf einer Kanboard-Instanz via JSON-RPC API. Unterstützt:

- Tasks erstellen, anzeigen, ändern, verschieben, öffnen/schließen
- Kommentare lesen, hinzufügen, ändern, löschen
- Dateien anhängen, auflisten, herunterladen, löschen
- Teilaufgaben erstellen, ändern, löschen
- Task-Verbindungen (interne Links) auflisten, erstellen, löschen
- Projekte, Spalten und User auflisten

**Voraussetzungen:** Python ≥ 3.11

**Setup:** Eine `.env`-Datei mit `KANBOARD_URL` und `KANBOARD_TOKEN` im Arbeitsverzeichnis anlegen (oder Pfad via `KANBOARD_ENV` setzen). Vorlage:

```
KANBOARD_URL=https://example.com/kanboard/jsonrpc.php
KANBOARD_TOKEN=dein-api-token
KANBOARD_USER=dein-username
```

`KANBOARD_USER` ist optional — ohne Angabe wird `jsonrpc` (Admin-API-User) verwendet. Fuer persoenliche API-Tokens den eigenen Kanboard-Usernamen eintragen.

Dann einmalig `setup` ausfuehren (aus dem Arbeitsverzeichnis mit der `.env`):

```bash
python3 ~/.claude/skills/kanboard/kanboard setup --default-user <username>
```

**Trigger:** `/kanboard` oder natürliche Sprache wie "leg mir ein Ticket an", "ins Kanboard eintragen".

### kimai

Zeiterfassung über die Kimai REST API. Unterstützt:

- Zeiteinträge: auflisten, anzeigen, anlegen, ändern, löschen, duplizieren, exportieren
- Laufende Timer: starten, stoppen, neustarten, aktive anzeigen
- Projekte, Aktivitäten, Kunden: CRUD (anlegen, anzeigen, ändern, löschen)
- User und Tags auflisten/verwalten
- Teams: anlegen, ändern, löschen
- Externe Stunden importieren (ersetzt `kimai_stunden.py`)

**Voraussetzungen:** Python ≥ 3.11

**Setup:** Eine `.env`-Datei mit `KIMAI_HOST` und `KIMAI_TOKEN` im Arbeitsverzeichnis anlegen (oder Pfad via `KIMAI_ENV` setzen). Vorlage:

```
KIMAI_HOST=https://kimai2.example.com
KIMAI_TOKEN=dein-api-token
```

Dann einmalig `setup` ausfuehren (aus dem Arbeitsverzeichnis mit der `.env`):

```bash
python3 ~/.claude/skills/kimai/kimai setup
```

**Trigger:** `/kimai` oder natürliche Sprache wie "wieviele Stunden habe ich diese Woche", "Zeiteintrag anlegen".

### swaks

Versendet E-Mails via `swaks` über den lokalen Postfix auf `mom.azedo.at`. Unterstützt:

- Plain-Text und HTML Body
- Dateianhänge (beliebiger MIME-Type)
- Mehrere Anhänge pro Mail
- Kontakt-Shortcuts (`.claude/swaks-contacts.tsv` — Name-zu-Email-Lookup)
- Optionale Default-Signatur (`.claude/swaks-signature.txt`)

**Voraussetzungen:** `swaks` installiert, Zugang zu `mom.azedo.at`

**Trigger:** `/swaks` oder natürliche Sprache wie "schick mir das per Mail", "send this to X".

### envato

Envato Market API (ThemeForest, CodeCanyon). Unterstützt:

- Käufe auflisten und filtern
- Kaufdetails via Purchase-Code abrufen
- Gekaufte Items herunterladen (via Item-ID oder Purchase-Code)
- Items auf dem Marktplatz suchen
- Item-Details anzeigen
- Account-Infos abfragen

**Voraussetzungen:** Python ≥ 3.11

**Setup:** Token auf https://build.envato.com/create-token/ erstellen (Berechtigungen: Download purchased items, List purchases). In `.env` eintragen:

```
ENVATO_TOKEN=dein-personal-token
```

**Trigger:** `/envato` oder natürliche Sprache wie "lade das Theme herunter", "zeig meine Envato-Käufe".

### google-analytics

Google Analytics 4 Datenabfrage via Service Account. Python-Script (stdlib only, keine pip-Dependencies):

- Accounts und Properties auflisten
- Reports: Custom Dimensions, Metrics, Filter, Sortierung, Datumsbereiche
- Realtime: aktive User, aktuelle Seitenaufrufe
- Metadata: verfuegbare Dimensionen und Metriken einer Property
- Tab-separierte oder JSON-Ausgabe

**Voraussetzungen:** Python >= 3.11, Package `cryptography` (fuer JWT-Signierung)

**Setup:** Service Account JSON unter `~/.config/ga4-service-account.json`. Service Account als Betrachter in GA4-Properties hinterlegen. Dann:

```bash
python3 "$SKILL_DIR/google-analytics" setup
```

**Trigger:** `/google-analytics`, `/ga4` oder natuerliche Sprache wie "wie viele Besucher", "Traffic letzte Woche", "GA4 Report".

### image-optimize

Optimiert Bilder für Web-Verwendung. Unterstützt:

- Analyse: Auflösung, Dateigröße und Dateinamen prüfen
- Optimierung: PNG verlustfrei (optipng), JPEG quality-basiert (jpegoptim)
- Resize: Auflösung skalieren via GraphicsMagick (Seitenverhältnis bleibt erhalten)
- Rename: Dateinamen SEO-freundlich umbenennen (Umlaute, Leerzeichen, Sonderzeichen)
- Web-Pipeline: alle Schritte in einem Durchgang

**Voraussetzungen:** Python ≥ 3.11, `optipng`, `jpegoptim`, optional `GraphicsMagick` (für Resize)

**Trigger:** `/image-optimize` oder natürliche Sprache wie "Bilder für Web optimieren", "Bilder komprimieren".

### ripgrep

Referenz-Skill fuer `rg` (ripgrep) — schnelle Textsuche in Dateien und Verzeichnissen. Kein eigenes Script, reine SKILL.md mit:

- Quick Reference: alle wichtigen Flags und Optionen
- Regex-Patterns, Multiline-Matching, File-Filtering
- Common Patterns: Funktionen, Imports, TODOs finden
- Performance-Tipps und haeufige Fehler

Quelle: [ratacat/claude-skills](https://github.com/ratacat/claude-skills/tree/main/skills/ripgrep)

**Trigger:** Wird automatisch als Kontext geladen, kein expliziter Aufruf noetig.

### php-formatting

PHP-Code-Formatierung nach PSR-2 mit azedo-spezifischen Anpassungen. Kein eigenes Script, reine SKILL.md mit:

- PSR-2 Grundregeln als Basis
- Tabs statt Spaces (Ausnahme: bestehende Dateien mit Spaces bleiben bei 4 Spaces)
- Leerzeilen um Kontrollstrukturen (`if`, `for`, `foreach`, etc.)
- Leerzeilen um Kommentarbloecke und DocBlocks
- Leerzeilen nach Methoden-/Funktionsdeklarationen

**Trigger:** `/php-formatting` oder natuerliche Sprache wie "formatiere den PHP Code". Wird automatisch angewendet wenn PHP-Code erstellt oder geaendert wird.

### tcsh

Referenz-Skill fuer tcsh — Remote-Administration auf FreeBSD-Servern. Root-Shell auf allen FreeBSD-Servern ist `tcsh`, Claude denkt aber in bash/sh. Kein eigenes Script, reine SKILL.md mit:

- Entscheidungsmatrix: tcsh nativ vs. `sh -c` Wrapping
- tcsh-Syntax-Kurzreferenz (Variablen, Redirects, Kontrollstrukturen, File-Tests)
- Bash → tcsh Uebersetzungstabelle (die haeufigsten 20 Patterns)
- FreeBSD-Admin-Patterns (service, pkg, jails, logs, firewall, ZFS)
- Quoting-Regeln fuer SSH → tcsh und SSH → jexec/iocage → sh -c
- Bekannte Fallen (Glob-Expansion, History-!, foreach, sed -i, Funktionen)

**Trigger:** Wird automatisch angewendet bei SSH-Befehlen auf FreeBSD-Servern.

### wp-cli

Referenz-Skill fuer `wp` CLI — WordPress-Administration auf FreeBSD-Servern mit Jails. Kein eigenes Script, reine SKILL.md mit:

- Zugriffsmuster fuer ezjail und iocage (SSH → jexec/iocage exec → sudo -u)
- Datenbank-Operationen: Export, Import, Query, Search-Replace (mit Safety-Workflow)
- Code-Ausfuehrung im WordPress-Kontext: `wp eval`, `wp eval-file`, `$wpdb`-Workaround
- Quick Reference: Plugins, Themes, Users, Options, Cache, Cron, Core, Wartung
- Bulk-Operationen, Multisite, Performance-Flags, Troubleshooting

**Trigger:** Wird automatisch geladen bei wp-cli-Befehlen und WordPress-Administrations-Aufgaben.

### wp-sync-dev

Synchronisiert WordPress-Plugins und -Themes zwischen Produktions-Installationen (in FreeBSD-Jails) und der DEV-Umgebung (dev.example.at) via rsync. Bidirektional: Prod → DEV und DEV → Prod. Kein eigenes Script, reine SKILL.md mit:

- Pfad-Schema fuer DEV und Prod (iocage/ezjail)
- rsync-Befehle in beide Richtungen
- Permissions: DEV immer www:azedo 775/664, Prod an bestehender Installation orientieren
- Aufraeumen von macOS-Artefakten (._*, .DS*)

**Trigger:** `/wp-sync-dev` oder natuerliche Sprache wie "sync plugin", "plugin von prod holen", "theme auf dev kopieren".

### mainwp

MainWP Dashboard (office.example.at) — WordPress-Sites netzwerkuebergreifend verwalten.
Generischer Abilities-Executor: 5 Subcommands fuer beliebige MainWP-Abilities.

- Sites auflisten, Details anzeigen
- Updates pruefen und installieren
- Plugins/Themes verwalten (aktivieren, deaktivieren, installieren, loeschen)
- Clients und Tags organisieren
- Batch-Operationen mit Job-Polling

**Voraussetzungen:** Python >= 3.11

**Voraussetzungen:** Python >= 3.11

**Setup:** WordPress Application Password und REST API v2 Key auf office.example.at. In `.env` eintragen:

```
MAINWP_HOST=https://office.example.at
MAINWP_USER=<wp-username>
MAINWP_APP_PASSWORD=<xxxx xxxx xxxx xxxx>
MAINWP_V2_CONSUMER_KEY=<consumer-key>
MAINWP_V2_CONSUMER_SECRET=<consumer-secret>
```

Application Password fuer die Abilities-API (Sites, Updates, Clients). Consumer Key/Secret fuer die REST API v2 (Tags).

Dann einmalig:

```bash
python3 ~/.claude/skills/mainwp/mainwp setup
```

**Trigger:** `/mainwp` oder natuerliche Sprache wie "welche Sites haben Updates", "installiere Updates auf allen Sites".

### wp-pys

Referenz-Skill fuer PixelYourSite Pro Event-Verwaltung in WordPress-(Multi-)Sites per WP-CLI. Kein eigenes Script, reine SKILL.md mit PHP-Snippets:

- Datenmodell: `pys_event` CPT, `wp_{blog}_pys_options`, serialisierte Meta-Felder
- Events auflisten, Plugin-Config lesen, Pixel-Ziele aktivieren
- Events klonen, Trigger aendern (CSS-Click, Ninja Forms)
- Verifizieren (Trigger-Deserialisierung pruefen), Backup/Restore
- Ninja-Form-IDs nachschlagen (site-spezifisch bei Multisite)
- Fallstricke: `wp_slash()` bei Triggers, `$args[]` statt Env-Vars, login-gated Formulare

**Trigger:** `/wp-pys` oder natuerliche Sprache wie "PYS Events auflisten", "GA4 Event einrichten", "PixelYourSite".

### wiki

LLM Wiki-Verwaltung fuer strukturierte Dokumentation. Unterstuetzt **mehrere Wikis** mit je eigenem Entity-Modell (Infra `azedo`: Server/Service/Access/Site/Procedure; Projekt-Wikis abweichend). Kein eigenes Script (bis auf lint-wiki.py), reine SKILL.md mit Subcommands:

- init: neues Wiki-Unterverzeichnis anlegen (inkl. Default-`wiki-schema.json`)
- ingest: Quellen ins Wiki aufnehmen (nach raw/, immutable)
- compile: Quellen zu Wiki-Entities verarbeiten (erlaubte Typen laut Wiki-`CLAUDE.md`)
- query: Fragen gegen das Wiki beantworten
- lint: strukturelle Pruefung (Frontmatter, tote Links, Konnektivitaet, Namenskonventionen)
- status: Ueberblick ueber Wiki-Zustand

Ziel-Wiki per Praefix waehlen: `/wiki cris:query "…"`; ohne Praefix gilt `azedo` (Default). Das Entity-Modell (erlaubte Typen + Pflichtfelder) liest der Linter aus `<wiki-root>/wiki-schema.json`, mit Infra-Default als Fallback.

Referenzen: Frontmatter-Schemas, Compilation-Guide, Cross-Referencing-Regeln.

**Trigger:** `/wiki` oder natuerliche Sprache wie "trag das ins Wiki ein", "was steht im Wiki zu X".

### wetter

GeoSphere Austria Wetterdaten fuer Oesterreich. Python-Script (stdlib only, keine pip-Dependencies, keine Auth):

- forecast: Stundenvorhersage (AROME `nwp-v1-1h-2500m`, ~60 h), pro Tag Min/Max, Niederschlag, Boeen + 3-stuendliche Zeilen
- nowcast: Nahzeitvorhersage (`nowcast-v1-15min-1km`, ~3 h in 15-Minuten-Schritten)
- warnungen: aktive amtliche Warnungen (Typ, Stufe gelb/orange/rot, Zeitraum, Auswirkungen, Empfehlungen)

Standort per Ortsname (Geocoding via OpenStreetMap/Nominatim, auf AT beschraenkt) oder Koordinaten `lat,lon`. Alle Zeiten in Europe/Vienna. `--json` fuer Rohdaten.

**Voraussetzungen:** Python >= 3.11

**Trigger:** `/wetter` oder natuerliche Sprache wie "wie wird das Wetter in X", "regnet es morgen in X", "gibt es Wetterwarnungen fuer X".

### humanizer-de

Deutscher AI-Text-Humanizer: KI-Schreibmuster (KI-Tells) in deutschen Texten auditieren und belegtreu ueberarbeiten. Vendorisierter Fork von [marmbiz/humanizer-de](https://github.com/marmbiz/humanizer-de) (MIT). SKILL.md + Referenzen + Python-Linter (stdlib only):

- 66 Muster in 10 Kategorien (Referenzkatalog `references/patterns.md`)
- Drei Modi: Locker (Blog/Social), Sachlich (Website/Doku/B2B), Formal (Wissenschaft/Recht)
- Fuenf-Pass-Workflow (Triage, Artefakte/Evidenz, Lexik, Struktur, Rhythmus) + optionales QGIR-Gate
- Claim-Lock und Persona-Lock: Quellen, Zahlen, Namen und Aussagen bleiben unveraendert
- Linter: `humanizer_audit.py` (Sammelcheck) plus unicode/rhythm/register/evidence/german-pattern-Checks

**Voraussetzungen:** Python >= 3.11

**Lizenz:** MIT (c) Martin Moeller, mit CC BY-SA 4.0 fuer die aus der deutschen Wikipedia adaptierten Musterbeschreibungen. Basiert auf `blader/humanizer` (MIT). Siehe `humanizer-de/LICENSE`.

**Trigger:** `/humanizer-de` oder natuerliche Sprache wie "humanisiere den Text", "klingt nach KI", "entferne die KI-Tells".

## Changelog

### 1.14.0

- **wiki: Multi-Wiki-Support + konfigurierbares Entity-Modell.** Der Skill ist nicht mehr fest auf das Infra-Wiki `azedo` verdrahtet. Ziel-Wiki per Praefix waehlbar: `/wiki <name>:<subcommand>` (z.B. `/wiki cris:query "…"`), ohne Praefix gilt weiterhin `azedo` (rueckwaertskompatibel). Alle hartkodierten `~/azedo.ai/wiki/azedo/`-Pfade laufen ueber `<WIKI_ROOT>`; vor jeder Operation wird `<WIKI_ROOT>/CLAUDE.md` gelesen (jedes Wiki hat sein eigenes Modell und eigene Konventionen). `lint-wiki.py` laedt erlaubte Typen + Pflichtfelder aus `<wiki-root>/wiki-schema.json` (Format: `required_common` + `types`), mit dem bisherigen Infra-Modell als eingebautem Fallback (`DEFAULT_SCHEMA`) — fehlt die Datei, verhaelt sich der Linter wie bisher. `init` legt neben der Verzeichnisstruktur eine Default-`wiki-schema.json` an. Verifiziert: `azedo`-Lint unveraendert (99 Artikel, 0 Fehler, Default-Fallback), neues Projekt-Wiki `cris` (concept/module/integration/procedure/reference/architecture, Pflichtfeld `projekt`) lintet mit eigenem Schema sauber (10 Artikel, 0 Fehler). Die `wiki-schema.json` der einzelnen Wikis liegt im jeweiligen Wiki, nicht im Skill-Repo

### 1.13.0

- **kanboard: Task-Verbindungen (interne Links):** Vier neue Subcommands zum Verwalten von Task-zu-Task-Verknuepfungen ueber die Kanboard-Link-API. `list-links` listet die instanzweit definierten Link-Typen (id, label, opposite_id) — Discovery, um das richtige Label/die richtige ID zu finden. `list-task-links <task_id>` zeigt bestehende Verbindungen eines Tasks. `create-task-link <task_id> <opposite_task_id> --link "<label|id>"` verknuepft zwei Tasks (Label wird case-insensitiv via `getAllLinks` aufgeloest, oder direkt numerische `link_id`); Kanboard legt die Gegenrichtung automatisch an. `remove-task-link <task_link_id>` loescht eine Verbindung. Damit sind interne Verbindungen (z.B. „relates to", „is a child of", „blocks") jetzt scriptbar. Hinweis: die deutsche UI-Bezeichnung „gehört zu" entspricht dem gespeicherten Label „relates to" (link_id 1)

### 1.12.1

- **humanizer-de: Muster 67 „Business-Anglizismen / Denglisch-Jargon" [MEDIUM] (azedo-Erweiterung):** Neue register- und clustergesteuerte Kategorie erkennt deutschen Business-/Consulting-Jargon und Anglizismen („Bullshit-Bingo") und schlaegt deutsche Entsprechungen vor — abgegrenzt von Muster 45 (harte Transfers) und Muster 64 (deutsche KI-Marker). Kuratiertes Lexikon (Begriff→DE) + fixe Negativliste etablierter Fachbegriffe (MVP, SaaS, CRM, KI, …) in `scripts/german_pattern_lint.py`; case-insensitiver Match mit begrenztem Flexions-Suffix (matcht `R&D`, `Plattform-IP`, `instrumentiert`, ohne `Gate`→`Gateway`/`IP`→`ZIP`-Fehltreffer). Schwellen formal ≥1 / sachlich ≥2 / locker ≥4. `humanizer_audit.py` aggregiert die Kategorie ins Preflight; Muster 67 in `patterns.md` (Pass 2) und `SKILL.md` (Modusmatrix, Carve-outs) dokumentiert. Als klar markierte azedo-Erweiterung gekapselt (kein Upstream-Sync)
- **Wording:** „vendorisiert" statt „vendort/vendorter" in SKILL.md, README und Handoff

### 1.12.0

- **humanizer-de-Skill:** Deutscher AI-Text-Humanizer als vendorisierter Fork von `marmbiz/humanizer-de` (@ `a5084f2`, v5.2.0, MIT). Kuratierter Subset (SKILL.md + 6 Referenzen + 7 Python-Linter, stdlib only); Plugin-/Codex-Manifeste, `tests/`, `docs/` und `assets/` weggelassen, da azedo-skills ueber Symlinks statt Marketplace laeuft. Frontmatter an azedo-Konvention angeglichen, Script-Aufrufe auf `$SKILL_DIR`, Herkunft-/Lizenz-Block ergaenzt. `LICENSE` verbatim erhalten (Attribution an `blader/humanizer` und dt. Wikipedia CC BY-SA 4.0)

### 1.11.5

- **wetter: Favoritendatei bei Fehlen anlegen (Workflow):** Fehlt `~/.claude/wetter-favorites.json`, ist das Anlegen jetzt ein verpflichtender Workflow-Schritt (nur bei `forecast`/`nowcast`): `stations <ort>` auflisten, den User die Favoriten waehlen lassen, Datei schreiben — erst dann die eigentliche Abfrage. Zuvor war das nur ein passiver Hinweis. Bei `warnungen` entfaellt der Schritt (nutzen keine Favoriten)

### 1.11.4

- **wetter: Kuratierte Favoritenstationen fuer den Messwert:** Der Messwert-Header nimmt nicht mehr die geografisch naechste Station (oft inoffiziell/ohne aktuelle Daten), sondern ausschliesslich Stationen aus `~/.claude/wetter-favorites.json`. Von diesen die naechste mit **frischen** Daten (veraltete >2 h werden uebersprungen). Fehlt die Datei/liefert kein Favorit Daten, laeuft es ohne Header weiter
- **wetter: Messwert-Header auch im forecast:** `forecast` zeigt denselben Header (aktueller Favoriten-Messwert) wie der Nowcast, oben in der Ausgabe und als `messwert`-Block im `--json`
- **wetter: Neuer Subcommand `stations <ort>`:** listet die naechstgelegenen TAWES-Stationen mit Distanz und aktuellem Wert (bzw. "veraltet"/"keine Daten"), Favoriten mit `*` markiert — zum Auswaehlen der Favoriten
- **wetter: Robustere Stationsabfrage:** Einzelabfrage pro Station statt Batch — die current-API richtet Mehr-Stationen-Requests auf einen gemeinsamen Zeitstempel aus, wodurch veraltete Stationen frische auf null zogen

### 1.11.3

- **wetter: Feuchte in der Stundenvorhersage:** `forecast` zeigt die relative Feuchte (`rF %`) nun in jeder 3-stuendlichen Zeile (Parameter `rh2m` ergänzt) und im `--json`-Output
- **wetter: Echter Messwert im Nowcast:** `nowcast` zeigt oben einen Header mit dem aktuellen Messwert der naechstgelegenen aktiven TAWES-Station (`station/current/tawes-v1-10min`) — Stationsname, Distanz, Temperatur, Feuchte, Taupunkt, Wind. Echter Messwert statt interpoliertem Modellwert; als `messwert`-Block auch im `--json`. Stationsabfrage ist "best effort" (faellt bei Fehler stillschweigend weg)

### 1.11.2

- **wetter: Luftfeuchtigkeit im Nowcast:** Die relative Feuchte (`rh2m`) wird nun in jeder Nowcast-Zeile ausgegeben (`rF NN%`, zwischen Temperatur und Wind) und im `--json`-Output mitgeliefert. Der Parameter wurde bereits abgefragt, aber bisher nicht angezeigt

### 1.11.1

- **Auto-Verlinkung nach `git pull`:** `install.sh` richtet `post-merge`- und `post-rewrite`-Hooks ein, die neue Skills nach jedem Pull (auch `--rebase`) automatisch verlinken. Fremde Hooks bleiben unangetastet, Installation idempotent. Aeltere Installationen einmalig `sh install.sh` ausfuehren, danach greift der Automatismus

### 1.11.0

- **wetter-Skill:** GeoSphere Austria Wetterdaten fuer Oesterreich (Python, stdlib only, keine Auth). Subcommands: forecast (AROME-Stundenvorhersage ~60 h), nowcast (15-Minuten-Schritte, ~3 h), warnungen (amtliche Warn-API). Standort per Ortsname (Nominatim-Geocoding, AT-beschraenkt) oder Koordinaten. Zustand aus Bewoelkung + Niederschlag abgeleitet (kein `sy`-Raten), Zeiten in Europe/Vienna, `--json`-Ausgabe
- **Versionen vereinheitlicht:** alle Skript-`# version`-Marker und die `VERSION`-Datei auf 1.11.0. `image-optimize` hat nun ebenfalls einen Versions-Marker
- **Minor-Version-Unabhaengigkeit geprueft:** alle Scripts laufen unveraendert auf Python 3.9–3.13 (generischer `#!/usr/bin/env python3`-Shebang, keine entfernten Stdlib-Module, keine ungueltigen Escape-Sequenzen). README-Hinweis fuer neue Skills (`install.sh`-Liste) ergaenzt

### 1.10.0

- **google-analytics-Skill:** GA4-Datenabfrage via Service Account (Python, stdlib only). Subcommands: accounts, properties, report, realtime, metadata, setup. Tab-separierte oder JSON-Ausgabe, Custom Dimensions/Metrics, Filter, Sortierung. instance.json fuer Property-ID Lookup
- **wiki-Skill:** LLM Wiki-Verwaltung fuer Server-Infra-Dokumentation. Subcommands: init, ingest, compile, query, lint, status. Frontmatter-Schemas, Cross-Referencing mit Wikilinks, Backlink-Audit, Compile-Checkliste. Lint-Script (lint-wiki.py) prueft Pflichtfelder, tote Links, Konnektivitaet, Namenskonventionen

### 1.9.8

- **MainWP: REST API v2 dokumentiert:** Tag-Verwaltung ueber `mainwp/v2` Endpoint (Consumer Key/Secret Auth, getrennt von Application Password). Neue Abschnitte: Tags verwalten, Clients verwalten, API-Architektur. Pagination-Warnung (>100 Sites, immer page=2 pruefen). v2 Credentials in `.env` (`MAINWP_V2_CONSUMER_KEY`, `MAINWP_V2_CONSUMER_SECRET`)
- **tcsh: iocage exec + sudo -u Pitfall:** `iocage exec <jail> sudo -u <user>` scheitert, weil jexec den `-u` Flag abfaengt. Fix: in `sh -c` wrappen. Unterschied zu `jexec <JID>` (numerisch) dokumentiert. In Entscheidungsmatrix aufgenommen

### 1.9.6

- **wp-pys-Skill:** Neuer Referenz-Skill fuer PixelYourSite Pro Event-Verwaltung in WordPress-(Multi-)Sites. PHP-Snippets fuer list-events, show-config, enable-target, clone-event, set-trigger, verify, backup/restore, list-forms. Dokumentiert Datenmodell, wp_slash()-Fallstrick und Multisite-Stolpersteine
- **install.sh:** Skill-Liste alphabetisch sortiert, wp-pys ergaenzt

### 1.9.5

- **MainWP Auto-Batching:** `--batch-size N` (Default 25) splittet site_ids-basierte Abilities automatisch in Gruppen, um Gateway Timeouts bei vielen Sites zu vermeiden. Bei leerem Array (= alle Sites) werden IDs erst via list-sites geholt. Ergebnisse (synced/errors) werden aggregiert

### 1.9.4

- **install.sh:** tcsh-Skill in Skill-Liste ergaenzt — kuenftige Installs registrieren den Symlink automatisch

### 1.9.3

- **tcsh-Skill:** Neuer Referenz-Skill fuer tcsh-basierte Remote-Administration auf FreeBSD. Entscheidungsmatrix (tcsh nativ vs. sh -c), Syntax-Kurzreferenz, Bash→tcsh Uebersetzungstabelle, FreeBSD-Admin-Patterns, Quoting-Regeln, bekannte Fallen
- **wp-cli: Custom-Tabellen bei Multisite:** Hinweis ergaenzt — `--url` erfasst nur Standard-Tabellen mit Site-Prefix, Custom-Tabellen (z.B. WPML `wp_*_icl_strings`) erfordern `--all-tables`

### 1.9.2

- **Kanboard: Bessere Fehlerbehandlung:** `rpc_call` und `rpc_try` fangen jetzt HTTP-Fehler und nicht-JSON-Antworten sauber ab (z.B. ModSecurity-Blocks), statt mit einem Traceback abzubrechen. Zeigt HTTP-Statuscode und Response-Body (max 500 Zeichen)

### 1.9.1

- **MainWP Bugfixes:** API-Request-Format korrigiert (input-Envelope, Array-Parameter mit indizierter Notation). `_coerce_value` erkennt jetzt JSON-Arrays/Objects in `--param` Werten. SKILL.md dokumentiert `per_page=100` und `search=` fuer list-sites

### 1.9.0

- **MainWP-Skill:** Neuer Skill fuer MainWP Dashboard (office.example.at) — generischer Abilities-Executor mit 5 Subcommands (setup, ping, list, info, run). Dynamische Erkennung aller verfuegbaren Abilities via WP Abilities API. Destruktive Operationen erfordern --confirm, --dry-run fuer Vorschau

### 1.8.0

- **Swaks: Kontakt-Shortcuts:** Empfaenger-Lookup ueber `.claude/swaks-contacts.tsv` im Arbeitsverzeichnis (TSV: `kurzname<TAB>email`). Namen statt E-Mail-Adressen verwenden, neue Kontakte werden automatisch ergaenzt
- **Swaks: Default-Signatur:** Optionale Signatur aus `.claude/swaks-signature.txt` wird automatisch an den Mail-Body angehaengt (unterdrueckbar per "ohne Signatur" oder bei anderem Absender)

### 1.7.0

- **wp-sync-dev-Skill:** Neuer Referenz-Skill fuer bidirektionalen WordPress-Plugin/Theme-Sync zwischen Prod-Jails und DEV (dev.example.at). Pfad-Schema (iocage/ezjail), rsync, Permissions, Artefakt-Bereinigung

### 1.6.0

- **wp-cli-Skill:** Neuer Referenz-Skill fuer WordPress-Administration via WP-CLI in FreeBSD-Jails. Zugriffsmuster (ezjail/iocage), DB-Operationen (wp db + $wpdb-Workaround), Code-Ausfuehrung (wp eval/eval-file), Quick Reference, Safety-Workflow, Troubleshooting

### 1.5.2

- **Kimai `log` Bugfix:** Timezone-Suffix der API-Antwort (`+0200`, `+02:00`, `Z`) wird jetzt generisch per Regex abgestreift — `fromisoformat()` schlug bei `+0200` (ohne Doppelpunkt) fehl

### 1.5.1

- **Kimai `log` Subcommand:** One-Shot-Buchung — Shortcut-Aufloesung, Zeitberechnung und Timesheet-Anlage in einem Call. Akzeptiert `--shortcut` oder `--project`/`--activity`. Duration-Formate: Dezimalstunden (`0.5`), Minuten (`30m`), gemischt (`1h30m`)
- **Kimai Shortcuts:** Format umgestellt auf flaches JSON (`"key": [pid, aid, "Label"]`, eine Zeile pro Eintrag). Workflow nutzt grep statt Voll-Read. Migrationshinweis fuer bestehende Installationen

### 1.5.0

- **PHP-Formatting-Skill:** Neuer Skill fuer PHP-Code-Formatierung nach PSR-2 mit azedo-Anpassungen (Tabs, Leerzeilen um Kontrollstrukturen/Kommentarbloecke/Methoden)

### 1.4.3

- **Kimai SKILL.md:** Aufbau von `kimai-shortcuts.json` dokumentiert (Keys, Felder, Beispiel) — verhindert Raten auf neuen Installationen

### 1.4.1

- **Kimai Shortcuts:** Pfad von `kimai-shortcuts.json` nach `.claude/kimai-shortcuts.json` verschoben (konsistent mit projektspezifischer `.claude/`-Konfiguration)

### 1.4.0

- **Kimai Shortcuts:** Projekt/Aktivitaets-Lookup ueber `.claude/kimai-shortcuts.json` im Arbeitsverzeichnis statt vollstaendiger `instance.json`. Haeufige Kombinationen werden als kompakte Key-Value-Paare gespeichert, neue Kombinationen automatisch ergaenzt. Fallback auf `instance.json` bei unbekannten Projekten.

### 1.3.2

- **Kanboard SKILL.md:** Hinweis ergaenzt — "erledigt" = move-task in Spalte "erledigt", close-task nur nach Rueckfrage

### 1.3.0

- **Ripgrep-Skill:** Referenz-Skill fuer `rg` uebernommen von [ratacat/claude-skills](https://github.com/ratacat/claude-skills). Quick Reference, Regex-Patterns, Common Patterns, Performance-Tipps.

### 1.2.0

- **Envato-Skill:** Neuer Skill fuer Envato Market (ThemeForest, CodeCanyon) — Kaeufe auflisten, Items herunterladen, suchen, Details anzeigen (8 Subcommands)
- **CR-Kontext:** Kanboard `cr` Subcommand laedt Tasks als aktiven Kontext, Commit-Messages und Kimai-Beschreibungen werden mit `CR{id}: ` prefixed
- **.env Fallback:** Kanboard und Kimai suchen `.env` jetzt auch im Home-Verzeichnis (`~/.env`) als Fallback
- **Kimai:** Neue Eintraege werden zeitlich an den letzten heutigen Eintrag angeschlossen

### 1.1.0

- **Non-Admin-Support:** Kanboard und Kimai funktionieren jetzt mit persoenlichen API-Tokens (ohne Admin-Rechte)
- **Kanboard:** Auth-User konfigurierbar via `KANBOARD_USER` in `.env` (Default: `jsonrpc`)
- **Kanboard:** `setup` erkennt die Benutzerrolle (`getMe`) und speichert sie in `instance.json`
- **Kanboard:** Non-Admins: `getMyProjects` statt `getAllProjects`, Projektmitglieder via `getProjectUsers`
- **Kanboard:** `resolve_user` nutzt `instance.json`-Cache statt Admin-API-Call `getUserByName`
- **Kimai:** `setup` erkennt Admin-Rolle via `/users/me` und speichert `is_admin` in `instance.json`
- **Kimai:** Non-Admins: `GET /users/me` statt `GET /users`
- **Versionierung** eingefuehrt: `VERSION`-Datei im Repo-Root, `# version` Kommentar in Scripts

**Update:** Nach `git pull` einmal `setup` fuer Kanboard und Kimai ausfuehren. Die Setup-Befehle muessen aus dem Arbeitsverzeichnis mit der `.env` ausgefuehrt werden:

```bash
cd ~/.claude/azedo-skills && git pull
cd /pfad/zum/arbeitsverzeichnis   # dort wo die .env liegt
python3 ~/.claude/skills/kanboard/kanboard setup --default-user <username>
python3 ~/.claude/skills/kimai/kimai setup
```

### 1.0.0

Initiale Version mit Kanboard, Kimai, Swaks und Image-Optimize Skills.
