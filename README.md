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

- Tasks erstellen, anzeigen, ändern, verschieben (auch projektübergreifend), öffnen/schließen
- Kommentare lesen, hinzufügen, ändern, löschen
- Dateien anhängen, auflisten, herunterladen, löschen
- Teilaufgaben erstellen, ändern, löschen
- Task-Verbindungen (interne Links) auflisten, erstellen, löschen
- Tags verwalten (`get-tags`/`set-tags`/`add-tag`/`remove-tag`) inkl. Kimai-Verknüpfung (`set-kimai`)
- Handoff-Feld setzen/auslesen/entfernen (TaskHandoff-Plugin, Volltext-Markdown pro Task)
- Projekte, Spalten und User auflisten
- Projekt-Verwaltung: Projekte anlegen, Mitglieder/Rollen verwalten, Owner setzen
- Tasks suchen (`search`, Stichwort/Query projektübergreifend) und eigene offene Tasks (`my-tasks`)
- `get-task` liefert zusätzlich Klarnamen (Spalte, Owner, Swimlane) neben den IDs
- `cr` lädt Beschreibung, Änderungszeitpunkt, Handoff, Tags/Kimai-Kontext und Kommentar-/Anhang-Zähler
- Neue Tasks fallen ohne `--owner` auf den `default_user` zurück

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

### google-search-console

Google Search Console (GSC) Datenabfrage via Service Account. Python-Script (stdlib + `cryptography`). Scope pro Subcommand: lesend `webmasters.readonly`, schreibend (submit/delete-sitemap) `webmasters`:

- Sites/Properties + Berechtigungslevel auflisten
- Search-Analytics: Klicks, Impressionen, CTR, Position nach query/page/country/device/date/searchAppearance, mit Zeitraum und Filter
- URL-Inspection: echter Google-Index-Status je URL (verdict, coverageState, robots, lastCrawlTime, canonical)
- Sitemaps: eingereichte Sitemaps + submitted/indexed URL-Zahlen (`sitemaps`); einreichen (`submit-sitemap`) und entfernen (`delete-sitemap`) mit y/N-Abfrage bzw. `--yes`
- Tab-separierte oder JSON-Ausgabe

**Voraussetzungen:** Python >= 3.11, Package `cryptography` (fuer JWT-Signierung)

**Setup:** Service Account JSON unter `~/.config/ga4-service-account.json` (derselbe SA wie GA4, oder Pfad via `GSC_SERVICE_ACCOUNT`). Service Account als Nutzer in der GSC-Property hinterlegen, Search Console API im GCP-Projekt aktivieren. Dann:

```bash
python3 "$SKILL_DIR/google-search-console" setup
```

**Trigger:** `/google-search-console`, `/gsc` oder natuerliche Sprache wie "organische Klicks", "Impressionen in der Google-Suche", "ist die Seite indexiert".

### image-optimize

Optimiert Bilder für Web-Verwendung. Unterstützt:

- Analyse: Auflösung, Dateigröße und Dateinamen prüfen
- Optimierung: PNG verlustfrei (optipng), JPEG quality-basiert (jpegoptim)
- Resize: Auflösung skalieren via GraphicsMagick (Seitenverhältnis bleibt erhalten)
- Rename: Dateinamen SEO-freundlich umbenennen (Umlaute, Leerzeichen, Sonderzeichen)
- Web-Pipeline: alle Schritte in einem Durchgang

**Voraussetzungen:** Python ≥ 3.11, `optipng`, `jpegoptim`, optional `GraphicsMagick` (für Resize)

**Trigger:** `/image-optimize` oder natürliche Sprache wie "Bilder für Web optimieren", "Bilder komprimieren".

### md2pdf

Rendert Markdown zu einem "schönen" PDF (Typora-naher Look). Pipeline: `pandoc` → self-contained HTML (CSS + SVG inline) → headless Chrome `--print-to-pdf`. Kein LaTeX nötig. Läuft unter macOS, Linux und FreeBSD (Chrome/Chromium-Discovery je OS, Override per `MD2PDF_CHROME`). Unterstützt:

- Tabellen, Code-Blöcke, Blockquotes im GitHub/Typora-Look
- Inline-SVG (z.B. eingebettete ER-Diagramme) scharf im PDF
- Mermaid-Blöcke (```mermaid) via `mmdc` als SVG gerendert (optional, degradiert sauber wenn `mmdc` fehlt)
- Optionen `--css <file>` (eigenes Stylesheet) und `--no-mermaid`

**Voraussetzungen:** `pandoc` (Pflicht), Chrome/Chromium (Pflicht), `bash`; optional `mmdc` (`@mermaid-js/mermaid-cli`) für Mermaid

**Aufruf:** `"$SKILL_DIR/md2pdf" <input.md> [output.pdf]`

**Trigger:** `/md2pdf` oder natürliche Sprache wie "mach ein PDF draus", "Markdown zu PDF", "Doku als PDF exportieren".

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

### wp-nf

Referenz-Skill fuer Ninja-Forms-Administration in WordPress-(Multi-)Sites per WP-CLI (FreeBSD-Jail). Kein eigenes Script, reine SKILL.md mit PHP-Snippets, verifiziert an NF 3.14.8:

- Datenmodell + Footguns: `nf3_forms`/`nf3_fields`/`nf3_field_meta`, `element_class` liegt in der Meta-Tabelle (keine `settings`-Spalte); Render-Quelle ist der Form-Cache (`nf3_upgrades`), `use_cache()` hart `true`
- Formulare auflisten + Titel→ID-Mapping (native `wp ninja-forms list` oder Snippet), Felder + Settings dumpen (Model-API)
- `element_class`/HTML-Link-Klasse setzen — Backup (Form-Export) → Write → Cache invalidieren → Verify
- Export/Import (`.nff`, Backend-identisch): Backup und Klonen zwischen Subsites; Import legt immer ein neues Formular an
- Settings-Preflight: Meta↔Cache-Drift pruefen (Signatur des stillen „geaendert, aendert sich nichts"-Fehlers)
- Diagnose-Muster PYS-CSS-Click ↔ NF-`element_class` (Cross-Link zu wp-pys)
- Uebersicht der nativen `wp ninja-forms`-Extension und ihrer Grenzen (kein Export/Import, keine Settings-Details)

**Trigger:** `/wp-nf` oder natuerliche Sprache wie "Ninja Forms Feld", "element_class setzen", "Formular exportieren/importieren".

### wiki

LLM Wiki-Verwaltung fuer strukturierte Dokumentation. Unterstuetzt **mehrere Wikis** mit je eigenem Entity-Modell (Infra `azedo`: Server/Service/Access/Site/Procedure; Projekt-Wikis abweichend). Kein eigenes Script (bis auf lint-wiki.py), reine SKILL.md mit Subcommands:

- init: neues Wiki-Unterverzeichnis anlegen (inkl. Default-`wiki-schema.json`)
- ingest: Quellen ins Wiki aufnehmen (nach raw/, immutable)
- compile: Quellen zu Wiki-Entities verarbeiten (erlaubte Typen laut Wiki-`CLAUDE.md`)
- query: Fragen gegen das Wiki beantworten
- lint: strukturelle Pruefung (Frontmatter, tote Links, Konnektivitaet, Namenskonventionen); `--check-remotes` verifiziert Remote-Pointer per SSH
- status: Ueberblick ueber Wiki-Zustand
- handoff: aus lokalen Erkenntnissen eine ingest-fertige Note fuer ein Remote-Wiki erzeugen (manueller Ingest auf dem Zielhost)

Ziel-Wiki per Praefix waehlen: `/wiki cris:query "…"`; ohne Praefix gilt `azedo` (Default). Die Wiki-Root wird projekt-relativ aufgeloest (`wiki/<name>/` relativ zum Projekt-Root), nicht ueber einen absoluten Home-Pfad — portabel ueber Maschinen/Checkout-Orte. Das Entity-Modell (erlaubte Typen + Pflichtfelder) liest der Linter aus `<wiki-root>/wiki-schema.json`, mit Infra-Default als Fallback.

**Remote-Wikis (read-only):** Ein Wiki auf einem anderen Host kann per SSH read-only abgefragt werden — ohne lokale Kopie, ohne Sync. Definiert in `.claude/wiki-remotes.json` (`{name: {host, path}}`); `query`/`status` lesen dann per `ssh <host> "cat/grep …"`, schreibende Subcommands sind fuer Remotes gesperrt. Aus einem lokalen Wiki auf eine Remote-Entity verweisen: `[[<remote>:<slug>]]` (gueltiger Pointer, kein toter Link, wenn `<remote>` bekannt). Neue Erkenntnisse fuer ein Remote-Wiki liefert `<remote>:handoff` als Outbox-Note (`.claude/wiki-outbox/`) zum manuellen Ingest auf dem Zielhost — kein Remote-Write.

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

### handoff

Fasst die aktuelle Konversation in ein Uebergabedokument zusammen, damit ein neuer Agent nahtlos weiterarbeiten kann. Reiner Referenz-Skill (nur SKILL.md, kein Script). Vendorisierter, angepasster Fork von [mattpocock/skills](https://github.com/mattpocock/skills/tree/main/skills/productivity/handoff) (MIT):

- Ablage im Projektverzeichnis (`docs/` falls vorhanden, sonst Projektstamm)
- Dateiname aus dem Argument: kein Argument → `handoff.md`; Argument ohne `.md` → Fokus **und** Slug (`handoff-<slug>.md`, nichts wird ueberschrieben); Argument mit `.md` → expliziter Dateiname
- Abschnitt „Empfohlene Skills" im Dokument, keine Duplikate zu bestehenden Artefakten, Redaktion sensibler Daten
- Einlese-Workflow: bestehendes Handoff rekapitulieren, rueckfragen, nie eigenstaendig handeln

**Lizenz:** MIT (c) 2026 Matt Pocock. Siehe `handoff/LICENSE`. azedo-Anpassungen (Deutsch, Ablageort, Dateinamens-Konvention, Einlese-Sektion) in der SKILL.md unter „Herkunft & Lizenz" dokumentiert.

**Trigger:** `/handoff` oder natuerliche Sprache wie "erstell eine Uebergabe", "fass die Session fuer den naechsten Agent zusammen".

### telegram

Telegram-Bot-Anbindung (outbound-first). Python-Script (stdlib only, keine pip-Dependencies), lauffaehig auf macOS + FreeBSD, **kein Server-Prozess** — jeder Aufruf ist ein einzelner HTTPS-Call an `api.telegram.org` und laeuft auch aus cron:

- send: Kernbefehl (sendMessage), Text aus Argument/`--file`/STDIN, `--parse-mode`, `--silent`, `--no-preview`, `--json`
- Vorlagen: alert (rot), recovery (gruen), digest (Titel + Bullets) — HTML mit Emoji, dynamische Werte geescaped
- setup: chat_id via `getUpdates` ermitteln (optional `--write` in die .env)
- Interaktiv warten: `wait` (blockiert bis Nachricht kommt, gibt Text aus) und `ask` (Frage senden **und** auf Antwort warten) — drainen Backlog vorab, akzeptieren per Default nur den eigenen Chat, Exit 2 bei Timeout
- Dauer-Empfangs-Scaffold: `get-updates` (roh) und `poll` (Long-Poll `getUpdates?timeout=50` im Vordergrund, fuehrt `offset` mit) — optional, kein Daemon

Credentials in `.env`: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` (Auffindung wie kimai/kanboard: cwd/.env → ~/.env, Env-Variablen haben Vorrang). FreeBSD-TLS-Escape-Hatch `TELEGRAM_CA_BUNDLE`.

**Voraussetzungen:** Python >= 3.11, Bot-Token von BotFather. FreeBSD: `pkg install python311 ca_root_nss`.

**Trigger:** `/telegram` oder natuerliche Sprache wie "schick mir das per Telegram", "Alert nach Telegram", "Post-Update-Status per Telegram melden".

### pushover

Pushover-Anbindung (outbound-only) — Push-Notifications aufs Handy (iOS/Android/Desktop). Python-Script (stdlib only, keine pip-Dependencies), lauffaehig auf macOS + FreeBSD, **kein Server-Prozess** — jeder Aufruf ist ein einzelner HTTPS-Call an `api.pushover.net` und laeuft auch aus cron:

- send: Kernbefehl, Text aus Argument/`--file`/STDIN, `--title`, `--priority -2..1` (Emergency=2 bewusst nicht), `--sound`, `--user`/`--device` (komma-faehig), `--url`/`--url-title`, `--html`|`--monospace`, `--ttl`, `--attachment` (Bild <=5 MB), `--silent`, `--json`
- Vorlagen: alert (rot, Prio 1), recovery (gruen, Prio 0), digest (Titel + Bullets, Prio -1) — html mit Emoji, dynamische Werte geescaped, `--host`-Fusszeile
- validate: Token + User/Group-Key pruefen (zeigt aktive Geraete); sounds: verfuegbare Sound-Kennungen
- Empfaenger-Verzeichnis (Adressbuch): `recipients add/list` mappt Alias-Namen auf Keys, `--user kollege` statt Roh-Key; Default ist der Alias `me`. Ein Alias kann auch ein Delivery-Group-Key sein (ein `send` an alle). Datei `~/.pushover-recipients` (bzw. cwd)

Credentials in `.env`: `PUSHOVER_TOKEN` (Auffindung wie kimai/kanboard: cwd/.env → ~/.env, Env-Variablen haben Vorrang); Empfaenger im Verzeichnis (`me` = Default) oder `PUSHOVER_USER` als Fallback, optional `PUSHOVER_DEVICE`. FreeBSD-TLS-Escape-Hatch `PUSHOVER_CA_BUNDLE`.

**Voraussetzungen:** Python >= 3.11, App-Token + User-Key von pushover.net. FreeBSD: `pkg install python311 ca_root_nss`.

**Trigger:** `/pushover` (Slash-Kommando; `/push` gibt es als Slash nicht — der Name des Skills ist `pushover`) oder natuerliche Sprache wie "push mir eine Nachricht", "push kollege eine Nachricht", "schick mir das per Pushover", "Alert nach Pushover".

## Changelog

Vollstaendiger Verlauf: **[CHANGELOG.md](CHANGELOG.md)**. Hier nur die aktuelle Version.

### 1.31.0

- **`swaks`: Signatur-Auto-Resolve + `--no-sig`.** `build_mail.py` loest die Signatur selbst auf —
  projektlokal `.claude/swaks-signature.{txt,html}` (Vorrang) → global `~/.claude/swaks-signature.*`
  → sonst keine. Explizite `--sig-*-file` ueberschreiben (muessen dann existieren); `--no-sig`
  schaltet auch die Standard-Signatur ab. Behebt den Doku-Footgun (relativer Beispielpfad →
  `FileNotFoundError`). SKILL.md: Beispiel ohne `--sig-*`-Zeilen, Standard = global.
