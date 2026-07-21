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

## Changelog

### 1.26.6

- **swos: die restlichen `fwd.b`-VLAN-Port-Felder als Schreibbefehle — `vlan-mode` (i15),
  `vlan-receive` (i17), `force-vlan-id` (i19) (CR4426).**
  `swos vlan-mode <sw> --port <n> --to disabled|optional|strict`,
  `swos vlan-receive … --to any|tagged|untagged`,
  `swos force-vlan-id … --to on|off` (jeweils `[--force] [--commit]`). Werte aus `engine.js`
  (`i15 u:[disabled,optional,strict]`, `i17 u:[any,only tagged,only untagged]`, `i19 t:D`
  Per-Port-Bitmaske). Gemeinsamer `fwd.b`-Enum-Helfer (`_fwd_enum_write`) plus Bitmasken-Variante
  für `force-vlan-id`; alle drei mit **Link-/Lockout-Schutz** (Änderung an Port mit aktivem Link
  nur mit `--force`, da VLAN-Filterung den Zugriff kappen kann). Live an `.215` verifiziert (Ports
  3/5/7 einzeln + permutiert gegen die UI gegengeprüft). Damit sind alle vier `fwd.b`-Portfelder
  schreibbar (i15/i17/i18=PVID/i19). Zwölf Schreibbefehle gesamt.

### 1.26.5

- **swos: neunter Schreibbefehl `speed` (link.b i05, Forced Speed je Kupferport) — Enum aus der
  UI verifiziert (CR4426).** `swos speed <sw> --port 1..8 --to 10|100|1000 [--force] [--commit]`.
  Die Index→Speed-Enum (`engine.js` `a=[]`, dynamisch je Port) wurde per DevTools-Capture +
  Nutzerangabe der Dropdown-Werte geklärt: `0`=10, `1`=100, `2`=1000 Mbit/s (Kupferports; SFP+ 9/10
  haben andere Werte → abgelehnt). Wirkt nur bei Auto-Neg=off; der Dry-Run weist darauf hin, wenn
  Auto-Neg für den Port noch on ist. Link-/Lockout-Guard wie bei den übrigen link.b-Writes
  (Änderung an Port mit aktivem Link nur mit `--force`). Live an `.215` verifiziert (Port 7
  1000→100→1000; zyklische Permutation der Ports 3/5/7 gegen die UI gegengeprüft).

### 1.26.4

- **swos: `autoneg` (link.b i02) + `duplex` (link.b i03) — Auto Negotiation & Full Duplex je Port
  (CR4426).** `swos autoneg|duplex <sw> --port <n> --to on|off [--force] [--commit]`. Beide sind
  Bitmasken-Writes wie `port-enable`; die drei link.b-Bitmaskenfelder (i01 Enabled / i02 Auto-Neg /
  i03 Full-Duplex) teilen jetzt einen gemeinsamen Helfer `_link_bit_write` mit **Link-/Lockout-
  Schutz**: eine tatsächliche Änderung an einem Port mit aktivem Link (`i06`) verlangt `--force`
  (Enable/Auto-Neg/Duplex-Änderungen können den Link stören). Live an `.215` verifiziert (autoneg
  Port7 off→`i02=0x3bf`→on; duplex Port7 on→`i03=0x7f`→off; Guard greift an Port 2 mit Link).
  **Speed** (link.b i05) bleibt bewusst offen: Index→Speed-Enum ist in `engine.js` dynamisch je Port
  befüllt und nur bei Auto-Neg=off wirksam — erst nach Capture der Dropdown-Werte, nicht geraten.

### 1.26.3

- **swos: sechster Schreibbefehl `port-enable` (link.b i01, „Enabled" je Port) mit Lockout-Schutz
  (CR4426).** `swos port-enable <sw> --port <n> --to on|off [--force] [--commit]` setzt/löscht das
  Enabled-Bit eines Ports in der `link.b`-Bitmaske `i01`. **Lockout-Schutz:** einen Port mit
  aktivem Link (`i06`) zu deaktivieren verlangt `--force` (sonst Abbruch — er könnte den Mgmt-/
  Uplink-Verkehr tragen); Aktivieren ist immer erlaubt, der Dry-Run zeigt die Vorschau auch ohne
  `--force`. Live an `.215` verifiziert (Port 7 off → Read-back `i01=0x3bf` → wieder on → `0x3ff`),
  byte-aligned Hex greift auch hier. Gleiche Guard-Rails wie die übrigen Writes.

### 1.26.2

- **swos: `link.b`/`fwd.b`/`vlan.b`-Writes entsperrt — Ursache des Enabled-Vorfalls gefunden
  (byte-aligned Hex) + `portname`/`pvid`/`vlan-set` zurückgeholt (CR4426).** Root-Cause des
  früheren Vorfalls (ein `link.b`-Write warf die Enabled-Maske auf Ports 1–6 zurück): `_blob_hex`
  serialisierte Werte mit **ungerader** Hex-Breite (`0x3ff`), der SwOS-Parser liest Hex aber
  **bytewise** und interpretierte `0x3ff` als `0x3f` (=63). Fix: byte-aligned (gerade Breite,
  `0x03ff`) wie die SwOS-Web-UI; kontrolliert an `.215` nachgewiesen (Enabled bleibt `0x3ff`,
  nur das Zielfeld ändert sich). `poe.b` war nie betroffen (Werte 0–7 ohnehin 2-stellig). Damit
  sind die drei zurückgestellten Befehle wieder da und live verifiziert: `portname` (link.b i0a),
  `pvid` (fwd.b i18, Default VLAN ID), `vlan-set` (vlan.b Member-Bitmask, legt VLAN an falls neu) —
  jeweils ändern → Read-back → Restore getestet. Gleiche Guard-Rails (writable-Flag, `--dry-run`-
  Default, Snapshot, Read-back-Verify, css610_new/direct). **Weiterhin zurückgestellt:**
  `poe-priority` (Rang/Permutation statt Skalar). SKILL.md-Schreib-Sektion überarbeitet
  (fünf Befehle + zwei Kern-Lehren: byte-aligned Hex; Config-Basis ist der GET, nie der `.swb`).

### 1.26.1

- **swos: zweiter Schreibbefehl `poe-voltage` (poe.b i03) + gemeinsame Write-Basis + harte
  Sicherheits-Lehren aus dem Live-Test (CR4426).** `swos poe-voltage <sw> --port <n> --to
  auto|low|high [--commit]` setzt das PoE „Voltage Level" (`engine.js` `i03 u:[auto,low,high]`).
  Der Write-Pfad wurde auf eine gemeinsame Basis refaktoriert (generischer Blob-Serializer,
  `_write_guard`/`_post_subset`/`_commit_write`, Read-back-Verify) — `poe-out` und `poe-voltage`
  teilen sie, beide live an `.215` verifiziert (Ändern + Read-back + Restore). **Bewusst NICHT
  ausgeliefert** (Format zwar aus einem vollständigen HAR verifiziert, aber der Read-back-Verify
  hat beim Live-Test echte Probleme abgefangen): `poe-priority` — PoE-Priority ist ein **eindeutiger
  Rang/Permutation**, kein Skalar je Port (Switch schichtet um); `portname`/`pvid`/`vlan-set` —
  ein `link.b`-Testwrite hat die **Enabled-Maske umgeworfen** (Ports deaktiviert). **Zentrale
  Lehre, jetzt dokumentiert:** Config-Basis für Writes ist **immer der Live-GET** (nachweislich
  config-treu, Feld-für-Feld deckungsgleich mit der SwOS-Web-UI), **niemals** der `.swb`-Parser
  (lieferte falsche Bitmasken `0x37f/0x3ff` statt `0x37/0x3f`, was einen Fix-POST scheitern ließ).
  Diese vier Befehle kehren erst nach kontrolliertem Nachweis ihres Write-Nebeneffekts zurück.
  Inventory-`writable`-Flag, `--dry-run`-Default, Snapshot-once und Nur-`css610_new`/`direct`
  gelten unverändert. SKILL.md-Schreib-Sektion überarbeitet.

### 1.26.0

- **swos: erster Schreibbefehl `poe-out` (Stufe 2) — PoE Out je Port setzen, Format verifiziert
  statt geraten.** `swos poe-out <switch> --port <n> --to off|on|auto [--commit]`. Das POST-Format
  wurde per Browser-DevTools-Capture an `.215` (CSS610, `css610_new`) plus der `engine.js`-Feldtabelle
  hart abgeleitet, nicht geraten: `POST /poe.b`, `Content-Type: text/plain`, Body als **roher Teil-Blob**
  `{i01,i02,i03,i0a}` mit 8 Kupferport-Elementen (keine SFP/Runtime-Felder). Feldsemantik aus `engine.js`:
  `i01`=**PoE Out** (`u:[off,on,auto]` → `0/1/2`), `i02`=PoE Priority, `i03`=Voltage Level, `i0a`=global.
  **Wichtig:** der Config-Modus steht in `i01` — der bisherige read-only `ports`-View liest faelschlich
  `i04` (= Runtime-Status), das bleibt ein offener Read-only-Bug. **Guard-Rails:** Inventory-Flag
  `"writable": true` ist Pflicht (nur die 3 Buero-Sandkasten-Switches; Seiersberg bleibt read-only);
  `--dry-run` ist Default (zeigt Ist-/Soll-`i01` + exakten POST-Body, sendet nichts), erst `--commit`
  postet; vor der **ersten** Aenderung zieht das Tool automatisch einen `.swb`-Snapshot nach `.tmp/`
  als Rollback-Punkt; nach jedem Commit **Read-back-Verify** (nur `i01[port]` darf sich geaendert haben,
  sonst Abbruch mit Snapshot-Hinweis); Write bisher nur `css610_new` (andere Dialekte abgelehnt, bis
  separat gecaptured), nur `direct`-Transport (nicht ssh-curl). Live gegen `css610test` (.215)
  verifiziert: Port 8 `on`→`auto` zurueckgesetzt, Read-back + unabhaengige Gegenprobe bestaetigt. (CR4426)

### 1.25.3

- **swos: Dialekt-Bug gefixt — `.swb`-Backups verlieren nicht mehr die echten Portnamen.**
  `.swb`-Backups jeder CSS610-Generation tragen in `sys.b` sowohl `F`- als auch `J`-Keys, egal ob
  das Geraet live `css610_new` oder `css610_old` meldet — `detect_dialect()` erkennt Backups
  deshalb immer als `css610_old`. VLAN/PVID/PoE waren davon nicht betroffen (korrekt unter den
  `css610_old`-Buchstaben-Keys dekodiert), aber `portnames` stand faelschlich auf `None` und fiel
  immer auf die generischen `ether1..8`/`SFP+1/2`-Fallbacks zurueck, obwohl `link.b` unter Key `K`
  die echten Namen (`Port1..8`/`SFP+1`/`SFP+2`) enthaelt. Fix: `css610_old.portnames = "K"`.
  Gegenprobe an zwei unabhaengigen `.swb`-Quellen: dem echten Alt-FW-Fixture `swvspoe1.swb`
  (site1-Nightly) und einem frischen Neu-FW-Backup von `swbs02poe` (CR4369, per `backup`
  gezogen) — beide liefern jetzt die realen Portnamen. Modell/Version/MAC/Serial bleiben `?`:
  das ist keine Dialekt-Verwechslung mehr, sondern fehlt in **beiden** Referenz-Backups
  gleichermassen und damit vermutlich grundsaetzlich im `.swb`-Format (Config-Backup ohne
  Identitaets-/Hardware-Daten) — dokumentiert statt geraten.

### 1.25.2

- **swos: neuer Subcommand `backup` (Live-Backup ziehen, GET `/backup.swb`).** Referenz-Fund:
  `/root/bin/swos-backup.sh` auf `gatekeeper.example.com` zeigte den bisher unbekannten
  Backup-Endpoint (Digest-Auth, gleiches Passwort wie die `.b`-Endpoints), der denselben
  `.swb`-Container liefert wie der SwOS-Web-UI-Backup-Knopf und den `--swb` bereits offline
  dekodiert. Roher Byte-Dump (keine Blob-Parse) ueber `direct`/`ssh-curl`; funktioniert mit
  Inventory-Namen, `--ip/--mode` oder Ad-hoc-Zielen, nicht mit `--swb`. Bleibt Stufe 1
  (read-only) — reines GET, keine Config-Aenderung am Switch. Live gegen `swbs02poe` (CSS610,
  CR4369) verifiziert: bytegenau identisch zum manuellen curl-Download. **Nebenbefund
  dokumentiert, nicht gefixt:** ein frisches `.swb` desselben Switches wird vom bestehenden
  Dialekt-Detector faelschlich als `css610_old` statt `css610_new` erkannt (Backup-`sys.b`
  traegt sowohl `F`- als auch `J`-Keys) — Modell/Version/MAC/Serial/Portnamen fallen dann auf
  Fallback-Werte zurueck, VLAN/PVID/PoE bleiben korrekt. Neue Erkenntnis (Backup-Passwort
  hex-kodiert in `.pwd.b`) zusaetzlich in `reference_swos_lite_endpoints`-Memory festgehalten.

### 1.25.1

- **humanizer-de: zwei neue Leitplanken fuer explizite Nutzer-Stilvorgaben.** (1) Hat der Nutzer hinterlegt, dass er generell (ausser in Word) keine echten Gedankenstriche verwendet, geht das der Standard-Cluster-Regel vor: `—`/`–` werden dann durchgaengig durch den einfachen Bindestrich `-` ersetzt, ohne Satzumbau. (2) Nutzerspezifische Stilpraeferenzen jenseits der Muster-Kataloge (z. B. keine erklaerenden Nebensaetze fuer Offensichtliches, sparsames Bold in Aufzaehlungen, kurze sachliche Ueberschriften) werden auf Wunsch angewendet, auch wenn Preflight/Lint dafuer kein Muster findet — solche expliziten Vorgaben stehen ueber der reinen Cluster-Regel. Anlass: Abgleich eines E-Mail-Entwurfs mit der vom Nutzer final versendeten Fassung (CR4369) zeigte genau diese beiden Abweichungen, obwohl der Preflight-Audit selbst „low risk" meldete. Reiner SKILL.md-Doku-Change, keine Script-Aenderung.

### 1.25.0

- **kanboard: `search` findet Text auch in Beschreibung/Kommentar (`--anywhere` / `--in`) + Doku der Feld-Filter.** Kanboards `searchTasks` matcht ein **unqualifiziertes** Stichwort nur gegen den **Titel** — steht der String nur in Beschreibung oder Kommentar, lieferte `search "printsrv"` faelschlich nichts (real erlebt: der Pfad `Print_and_Follow` in der Beschreibung von CR4271 blieb ueber bloße Wortsuche unauffindbar, obwohl Kanboard `description:`/`comment:` nativ, case-insensitiv und als Teilstring durchsucht). Neu: `--anywhere` (Kurzform fuer `--in title,description,comment`) und `--in <felder>` behandeln die `query` als reinen Begriff, wickeln sie in jeden Feld-Filter (Phrasen mit Leerzeichen werden gequotet) und unionieren die Treffer nach `id`; jeder Treffer bekommt `matched_in` (Liste der Fundfelder). Der klassische Query-Modus (Operatoren `status:`/`assignee:`/`title:` …) bleibt unveraendert. SKILL.md-Abschnitt „Tasks suchen" um die Titel-Falle, die nativen Feld-Filter (`title:`/`description:`/`comment:`), die AND/ODER-Semantik (verschiedene Felder = UND, gleiches Feld doppelt = ODER) und die neuen Flags erweitert. Live gegen die azedo-Instanz verifiziert.
- **install.sh: `Edit(...)`- statt `Write(...)`-Permissions (+ Alt-Regeln aufraeumen).** Claude Code matcht `Write(path)`-Allow-Regeln nicht mehr — nur `Edit(path)` deckt die datei-schreibenden Tools ab —, weshalb `install.sh` bei jedem Update (der post-merge/post-rewrite-Hook ruft es nach jedem `git pull`) vier „Write(...) is not matched … use Edit(...) instead"-Warnungen ausloeste. `install.sh` traegt jetzt `Edit(~/.claude/azedo-skills/**)` bzw. `Edit(~/.claude/skills/**)` (je HOME-absolut und `~`) ein **und entfernt** die frueher gesetzten `Write(...)`-Altregeln fuer dieselben Pfade aus `permissions.allow` (fremde Regeln bleiben unberuehrt, idempotent). Ein einziger `git pull` heilt beide Maschinen selbst, da der Hook danach die neue `install.sh` faehrt. Auch der python3-Fallback-Hinweis nennt jetzt `Edit(...)`.

### 1.24.0

- **Neuer Skill `swos` (MikroTik SwOS read-only Abfrage).** Python-Script (stdlib only, `urllib` HTTP-Digest, kein `requests`), lauffaehig auf FreeBSD und Linux. **Ein Decoder, drei Transporte:** `direct` (urllib direkt auf die Switch-IP), `ssh-curl` (curl --digest auf einem Jump-Host — Passwoerter mit `$` werden korrekt via STDIN-Pipe an `sh` behandelt, kein `!`-Escaping noetig) und `swb` (offline aus `.swb`-Backup via `strings`). Dekodiert die SwOS-Blobs (kein valides JSON: unquoted Keys, Hex-Ints, Single-Quote-Hex-Strings) mit einem recursive-descent-Parser in lesbare Tabellen: `sys` (Modell/IP/MAC/Serial/Temp), `vlan` (Mitglieder), `ports` (PVID + PoE-Modus), `hosts` (FDB MAC→Port), `all`, `raw`. **Vier Feld-Dialekte autodetektiert** (`css326`, `css610_new`, `css610_old`, `swos_lite`) — Detektion an charakteristischen Keys, nicht am ersten sys.b-Key (Live-Reihenfolge weicht vom Backup ab). Gegenueber dem urspruenglichen `.swb`-Parser drei Bugs vermieden: VLAN-Namen werden pro Geraet aus `vlan.b nm` gelesen (nicht hardcoded), Modell aus `brd`/`i07` (nicht aus dem Dialekt geraten), und per-Endpoint-Parsing statt Whole-Text-Regex (keine Kreuzkontamination von `fwd.b`-`{B:,C:}` in die VLAN-Liste — der Original-Parser meldete dadurch eine Phantom-VLAN 1022). Inventory-Config `inventory.json` (gitignored) mit Credential-Refs (`password`/`password_env`/`password_file`) und Modus/Jump je Switch; `inventory.example.json` als Vorlage. read-only (Stufe 1); Schreibzugriff (Stufe 2) erst nach `engine.js`-Verifikation. Live verifiziert an 3 Buero-Switches (direct: CSS610/CSS326/CSS106) und site1 (ssh-curl via gatekeeper), Decoder-Gegenprobe Live == `.swb` identisch. `install.sh`-Liste ergaenzt. (CR4426)

### 1.23.1

- **kimai: Shortcut-Lookup findet `.claude/kimai-shortcuts.json` jetzt per Aufwaertssuche.** Bisher wurde die Datei nur unter `os.getcwd()/.claude/` gesucht; lief `kimai` aus einem Unterverzeichnis (z.B. `.tmp/`), kam `load_shortcuts()` leer zurueck und `log --shortcut <key>` scheiterte mit „shortcut not found" (obwohl der Key existiert). Neu: `_find_shortcuts_file()` laeuft die Elternverzeichnisse hoch bis `.claude/kimai-shortcuts.json` gefunden wird (analog git/.git), sodass der Lookup aus jedem Projekt-Unterverzeichnis funktioniert. Die `.env`-Config hatte bereits einen `~/.env`-Fallback. (CR4369)

### 1.23.0

- **Neuer Skill `telegram` (Telegram-Bot, outbound-first).** Python-Script (stdlib only, `urllib`, kein `requests`), lauffaehig auf macOS **und** FreeBSD, **kein Server-Prozess** — jeder Aufruf ein einzelner HTTPS-Call an `api.telegram.org` (auch aus cron). Kernbefehl `send` (sendMessage; Text aus Argument/`--file`/STDIN, `--parse-mode` Default Klartext, `--silent`, `--no-preview`, `--json`), Monitoring-Vorlagen `alert`/`recovery`/`digest` (HTML + Emoji, dynamische Werte HTML-geescaped), Setup-Helfer `setup` (chat_id via `getUpdates`, optional `--write` in die .env) und `me` (getMe/Token-Check). **Interaktiver Empfang** `wait` (blockiert einmalig per Long-Poll bis eine Nachricht kommt, gibt den Text aus; Exit 2 = Timeout) und `ask` (Frage senden **und** auf die Antwort warten) — beide drainen den Backlog vorab (nur Nachrichten NACH Start zaehlen) und akzeptieren per Default nur den eigenen Chat; damit kann Claude Code auf eine Telegram-Anweisung warten und danach handeln. Zusaetzlich Dauer-Empfang als Scaffold: `get-updates` (roh) und `poll` (Long-Poll im Vordergrund, fuehrt `offset` mit, loest vorab `deleteWebhook`) — kein Daemon, reine Ausbaubasis. Credentials in `.env` (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`; Auffindung wie kimai/kanboard, Env-Variablen haben Vorrang), FreeBSD-TLS-Escape-Hatch `TELEGRAM_CA_BUNDLE`. `install.sh`-Liste ergaenzt. (CR4420)

### 1.22.4

- **mainwp: Hinweis zum Auslesen des Sync-Status (Ausgabe nicht tailen).** Beim `sync-sites-v1` schlagen einzelne Sites oft fehl; das Script aggregiert ueber alle Batches und liefert `total_synced`/`total_errors` sowie `errors[]` (mit `identifier`, `code`, `message`). Diese Summen stehen **oben** im JSON, vor dem langen `synced`-Array — `| tail -N` schneidet sie ab. SKILL.md-Abschnitt „Alle Sites syncen" um eine Warnung plus fertiges Auswerte-Snippet ergaenzt (Ausgabe in Datei, stderr getrennt, dann `total_errors`/`errors[]` gezielt ausgeben).

### 1.22.3

- **wp-sync-dev: Scope-Grenze Host-Dateizugriff vs. Jail-Laufzeit klargestellt.** Der Skill beschrieb die DEV-Pfade als host-seitig (korrekt fuer rsync/chmod), sagte aber nicht, dass `dev.example.at` ein iocage-Jail ist und alles Laufzeitartige (`wp`-CLI, WordPress) **im Jail** laufen muss (`iocage exec dev.example.at … sudo -u www wp …`). Fuehrte in dieser Session zur Fehlannahme, `wp` liefe direkt auf dem mom-Host (`command not found`). DEV-Abschnitt umbenannt + Notiz mit Verweis auf Skill `wp-cli` / Wiki `wp-cli-in-jails` / `mom-azedo-at`.

### 1.22.2

- **wp-nf: Export-Snippet faengt Schreibfehler ab.** `nf-export-form.php` pruefte den Rueckgabewert von `file_put_contents()` nicht und meldete „OK … Bytes" auch dann, wenn die Datei gar nicht geschrieben wurde (aufgefallen beim Live-Test auf dev.example.at, als `wp` als `www` nicht ins Jail-`/tmp` schreiben durfte). Jetzt: bei `false` Abbruch mit Fehlermeldung und Exit 1. §5-Write und §8-Import wurden dabei end-to-end gegen NF 3.14.9 verifiziert (Export→Import→`element_class`-Write→Cache-Rebuild, Meta↔Cache konsistent). (CR4409)

### 1.22.1

- **wp-cli: Hinweis auf plugin-eigene CLI-Befehle (Cross-Link zu `wp-nf`).** Kurze Notiz unter der Plugins-Quick-Reference: manche Plugins registrieren eigene WP-CLI-Subcommands; Ninja Forms bringt `wp ninja-forms` mit, Details (Settings/`element_class`/Export/Import) deckt der Skill `wp-nf` ab. (CR4409)

### 1.22.0

- **Neuer Skill `wp-nf` (Ninja-Forms-Administration).** Reiner Referenz-Skill (nur SKILL.md, PHP-Snippets fuer `wp eval-file` im FreeBSD-Jail), verifiziert am Plugin-Quellcode von **Ninja Forms 3.14.8** auf apache1.acme.com. Anlass: das bei CR4266 (customer, GA4-CSS-Click-Events) entstandene, bisher nur im Handoff lebende NF-Wissen reproduzierbar kodieren. Inhalt: Datenmodell + Footguns (`element_class` liegt in `nf3_field_meta`, **keine** `settings`-Spalte in 3.14.8 — die aeltere Annahme ist damit widerlegt; Render-Quelle ist der Form-Cache `nf3_upgrades`, `WPN_Helper::use_cache()` liefert hart `true`), Formulare auflisten + Titel→ID-Mapping, Felder+Settings dumpen (Model-API), `element_class`-Write nach dem Muster Backup→Write→**Cache invalidieren**→Verify, **Export/Import** (`.nff`, Backend-identisch, ueber `export_form()`/`import_form()`; Import legt immer ein neues Formular an), Settings-Preflight (Meta↔Cache-Drift), Diagnose-Muster PYS-CSS-Click ↔ `element_class`, sowie eine Uebersicht der nativen `wp ninja-forms`-Extension und ihrer Grenzen (kein Export/Import, keine Settings-Details). `install.sh`-Liste ergaenzt. (CR4409)
- **wp-pys: NF-ID-Wissen nach `wp-nf` migriert.** Abschnitt „3.8 Ninja-Form-IDs ermitteln" enthielt das Roh-Snippet zur Formular-Auflistung; das gesamte NF-Datenmodell gehoert nun in den neuen Skill `wp-nf`. `wp-pys` verweist jetzt nur noch darauf (Titel-Mapping-Prinzip + Cross-Link) und ergaenzt den reziproken Hinweis, dass `css_click` auch an der NF-Feld-Klasse `element_class` haengt. Keine Duplizierung mehr zwischen den beiden Skills. (CR4409)

### 1.21.0

- **kanboard: `cr` laedt den Task-Inhalt vollstaendig.** Der `cr`-Kontext hat bisher die **Beschreibung verworfen** (Whitelist ohne `description`) — bei leerem Handoff sah ein voller Task faelschlich leer aus (Anlass: CR4377, dessen Kostenanalyse komplett in der Beschreibung stand und uebersehen wurde). `cr` liefert jetzt: `description` (immer, Volltext), `modified` (Aenderungszeitpunkt lesbar), `tags` inkl. herausgehobenem `kimai`-Feld, sowie `comments`/`attachments`-Zaehler (nur > 0). Description und Handoff sind bewusst beide dabei (Aufgabe vs. Uebergabestand). Kommentar-Volltext, Teilaufgaben, Task-Links und Anhang-Details bleiben eigene Befehle. Nebenbei schlanker: der in `cr` ungenutzte Swimlane-RPC entfaellt, `project_name` kommt aus dem `instance.json`-Cache. Feldauswahl in der SKILL.md dokumentiert. (CR4411)
- **kanboard: Tags + Kimai-Verknuepfung.** Neue Subcommands `get-tags`, `set-tags` (ersetzt alle), `add-tag`/`remove-tag` (read-merge-write, ohne Clobbern) und `set-kimai <task_id> --shortcut <key>`. Ein Tag `kimai:<shortcut>` verknuepft den Task mit einem Kimai-Shortcut (`.claude/kimai-shortcuts.json`); `cr` hebt ihn als Feld `kimai` heraus. Write-back-Regel dokumentiert (kanboard- **und** kimai-SKILL.md): nach einer Kimai-Buchung unter aktivem CR wird der Shortcut automatisch am Task getaggt, sodass er beim naechsten `cr` bereitsteht. Genau ein Kimai-Shortcut pro Task (`set-kimai` ersetzt einen vorhandenen). (CR4411)
- **kanboard: `list-tasks`-Bugfix.** `getAllTasks` liefert `column_name`/`owner_username` **nicht** mit — beide waren in jeder Auflistung leer. Werden jetzt aus `column_id` (via `getColumns`) bzw. `owner_id` (via `instance.json`) aufgeloest; `date_due` wird lesbar formatiert. (CR4411)
- **kanboard: `search` + `my-tasks`.** `search "<text>" [--project] [--all]` findet Tasks per Stichwort/Query projektuebergreifend (nutzt `searchTasks`, versteht UI-Operatoren wie `status:open`/`assignee:…`; Default nur offene Tasks). `my-tasks [--user]` listet offene Tasks eines Users (Default `default_user`) ueber alle Projekte. Beide ziehen Spalte/Owner direkt aus `searchTasks` (keine Extra-Lookups). (CR4415)
- **kanboard: `create-task` faellt ohne `--owner` auf `default_user` zurueck** (wie `add-comment`) — neue Tasks landen standardmaessig beim eingestellten User statt unassigned; ist kein `default_user` gesetzt, bleibt der Task ohne Zuweisung.
- **kanboard: internes Refactoring.** `rpc_call`/`rpc_try` teilten ~40 Zeilen Duplikat (Payload/Auth/HTTP/JSON-Parse) und wurden auf einen gemeinsamen Kern `_rpc(method, params, strict)` zusammengefuehrt — `strict=True` exit-on-error, `strict=False` liefert `None`. Kein Verhaltenswechsel. Ausserdem neuer `format_ts()`-Helper fuer lesbare Zeitstempel. (CR4416)

### 1.20.1

- **google-search-console: schreibende Sitemap-Operationen `submit-sitemap`/`delete-sitemap`.** Der Skill war bisher rein lesend (Scope `webmasters.readonly`). Neu: `submit-sitemap <-S siteUrl> <feedpath>` (`PUT`) und `delete-sitemap <-S siteUrl> <feedpath>` (`DELETE`). Der Scope wird jetzt **pro Subcommand** gewaehlt — lesende Befehle behalten `webmasters.readonly`, nur die beiden Schreib-Befehle fordern `webmasters` an (Token-Cache pro Scope). Schreib-Endpoint liegt unter `www.googleapis.com/webmasters/v3` (nicht `searchconsole.googleapis.com`); `PUT`/`DELETE` liefern HTTP 204 ohne Body, was `api_call` jetzt abfaengt (leerer Body → `{}`). `siteUrl` und `feedpath` werden voll URL-encodet. Absicherung: beide Befehle zeigen den Vorher-Zustand und fragen interaktiv `[y/N]`; `--yes`/`-y` ueberspringt, ohne TTY (Agent/Script) wird ohne `--yes` mit Exit 2 abgebrochen (kein versehentlicher Write). Verifiziert gegen `sc-domain:globex.com` (siteFullUser): idempotenter Re-Submit liefert HTTP 204 und aktualisiert `lastSubmitted`. Anlass: die in CR4400 noch per Ad-hoc-Script erledigten Sitemap-Writes reproduzierbar machen. (CR4408)

### 1.20.0

- **Neuer Skill `google-search-console` (GSC).** Read-only Datenabfrage der Google Search Console via Service Account (derselbe SA wie GA4, Scope `webmasters.readonly`). Python-Script (stdlib + `cryptography`, JWT-Flow 1:1 aus dem GA4-Skill uebernommen). Subcommands: `setup` (Auth testen, Sites cachen), `sites` (Properties + permissionLevel), `search-analytics` (Klicks/Impressionen/CTR/Position nach query/page/country/device/date/searchAppearance, Zeitraum + `dimension==value`-Filter; relative Datums-Keywords wie `28daysAgo` werden lokal auf ISO-Daten aufgeloest, da die GSC-API nur `YYYY-MM-DD` akzeptiert), `url-inspection` (echter Google-Index-Status je URL: verdict/coverageState/robots/lastCrawlTime/canonical), `sitemaps` (eingereichte Sitemaps + submitted/indexed URL-Zahlen). Trigger `/google-search-console`, `/gsc`. Anlass: empirischer Index-/Ranking-Nachweis fuer duenne Landingpages (CR4403, im Kontext CR4400). (CR4403)

### 1.19.3

- **kimai: `create-project`/`update-project` steuern jetzt `globalActivities`.** Neues Flag `--global-activities 0|1`. Bislang legte `create-project` Projekte implizit mit `globalActivities=false` an — dadurch waren instanzweite (globale) Aktivitaeten wie *IT-Support (SP90)* nicht buchbar und `create-timesheet` schlug mit `400 activity … invalid choice` fehl, was ein manueller Raw-API-PATCH nachziehen musste. `create-project` setzt jetzt **Default `1`** (globale Aktivitaeten erlaubt); `update-project` patcht das Feld nur bei explizitem Flag. (CR4397)

- **swaks: robuster Interpreter-Aufruf + Test-Mail-Footgun geschlossen.** `build_mail.py` wurde in SKILL.md und im Shebang von `python3.11` auf `python3` umgestellt — auf Maschinen ohne `python3.11` (z. B. mom mit `python3` 3.12) schlug der Aufruf sonst mit „command not found" fehl. Kritischer: Das bisher dokumentierte `build_mail.py | swaks --data @-` ist ein Footgun — schlägt der Bau fehl (Exit ≠ 0 oder Interpreter fehlt), läuft `swaks` trotzdem auf leerem STDIN und verschickt seine eingebaute **Default-Test-Mail** (genau so passiert). `set -o pipefail` verhindert das **nicht**, da `swaks` in der Pipe ohnehin startet. Der Standard-Ablauf baut die MIME-DATA jetzt erst in eine Datei und sendet per `&& test -s <datei> && swaks … --data @<datei>` — die `&&`-Kette stoppt vor `swaks`, sobald der Bau fehlschlägt oder die Datei leer ist. Verifiziert: erfolgreicher Bau erzeugt valide Multipart-MIME und passiert den Guard; fehlende Body-Datei (Exit 1) und `python3.11`-not-found (Exit 127, 0-Byte-Datei) stoppen die Kette beide vor `swaks`.

### 1.19.1

- **kanboard: `move-project` erhaelt jetzt den Offen/Geschlossen-Status.** `moveTaskToProject` oeffnet einen geschlossenen Task beim Projektwechsel automatisch wieder (is_active 0 → 1). `move-project` merkt sich den Status vor dem Move und schliesst einen zuvor geschlossenen Task danach wieder (`closeTask`), Rueckgabefeld `reclosed: true`. Ein reines Verschieben aendert damit den Erledigt-Status nicht mehr. Verifiziert: geschlossener Task bleibt nach dem Move geschlossen (richtige Spalte), offener Task bleibt offen.

### 1.19.0

- **kanboard: Projekt-Verwaltung — Projekte anlegen und Mitglieder/Rollen/Owner scriptbar.** Sechs neue Subcommands schliessen die Luecke, dass bisher nur Tasks, aber keine Projekte und keine Projekt-Rechte verwaltet werden konnten: `create-project --name <name> [--owner <username>]` (`createProject`; mit `--owner` wird der User Owner **und** `project-manager`-Mitglied), `list-project-users --project <p>` (`getProjectUsers` + `getProjectUserRole` je User, inkl. Owner), `add-project-user --project <p> --user <u> [--role <rolle>]` (`addProjectUser`, Default-Rolle `project-member`), `set-project-user-role` (`changeProjectUserRole`), `remove-project-user` (`removeProjectUser`) und `set-project-owner` (`updateProject`; ergaenzt den User bei Bedarf zuerst als Mitglied). Rollen validiert gegen `project-manager`/`project-member`/`project-viewer`. Damit ist „Projekt X anlegen, User Y mit gleicher Rolle wie in Projekt Z" ein Einzeiler statt Inline-Python. **API-Stolperfalle dokumentiert:** `updateProject` erwartet den Key `project_id` (nicht `id`) — mit `id` kommt „Missing argument: project_id", mit `name`/`id` ein stummes `False`; und ein Owner muss erst Projektmitglied sein, bevor er gesetzt werden kann. Verifiziert: alle sechs Subcommands live gegen die azedo-Instanz getestet (add/rollenwechsel/remove reversibel, Wegwerf-Projekt angelegt + wieder entfernt), Rollen-Validierung bricht bei ungueltiger Rolle mit Exit ≠ 0 ab.

### 1.18.2

- **swaks/build_mail.py: `--cc`/`--bcc` und Hart-Abbruch bei leerem Body.** `--cc` setzt einen sichtbaren `Cc:`-Header (Adresse zusätzlich in den swaks-Envelope `--to` aufnehmen). `--bcc` setzt **bewusst keinen** Header (sonst wären die Empfänger sichtbar) — die Adresse gehört nur in den swaks-Envelope; ein stderr-Hinweis erinnert daran. Neu: bricht mit Exit ≠ 0 ab, wenn Text *und* HTML leer sind (bzw. die Ausgabe leer wäre), damit swaks nie auf seine eingebaute Default-Test-Mail zurückfällt. SKILL.md um Cc/Bcc/Leer-Body-Hinweise ergänzt. (Enthält außerdem die zuvor lokal offene Multipart-Dokumentation zu `build_mail.py`.)

### 1.18.1

- **kanboard/handoff: robusteres Verhalten, wenn das TaskHandoff-Plugin fehlt.** Ist das Plugin auf der Kanboard-Instanz nicht installiert/aktiviert, liefern `set-handoff`/`get-handoff`/`remove-handoff` den JSON-RPC-Fehler `-32601` „Method not found". Der kanboard-Skill ergänzt bei diesem Code jetzt einen erklärenden Hinweis (Methode wird evtl. von einem nicht installierten Plugin bereitgestellt, z. B. TaskHandoff). Der handoff-Skill dokumentiert den Fallback: schlägt `set-handoff` mit `-32601` fehl, auf die lokale `.md`-Datei zurückfallen und den User informieren.

### 1.18.0

- **kanboard: Handoff-Feld pro Task (`set-handoff` / `get-handoff` / `remove-handoff`).** Ergaenzt das serverseitige Kanboard-Plugin **TaskHandoff** (eigenes Repo/Deployment), das pro Task ein Handoff-Dokument als Volltext-Markdown in einer aufklappbaren „Handoff"-Sektion der Task-Seite speichert (Spalte `content` als `LONGTEXT` — keine Laengengrenze, anders als Task-Metadata mit `VARCHAR(255)`; Bearbeiten per Modal wie „Aufgabe bearbeiten"). Drei neue Subcommands ueber die Plugin-JSON-RPC-Prozeduren `saveTaskHandoff`/`getTaskHandoff`/`removeTaskHandoff`: `set-handoff <task_id> (--file <pfad> | --value <text>)`, `get-handoff <task_id> [--output <pfad>]` (roher Markdown auf stdout oder in Datei), `remove-handoff <task_id>`. Ein Handoff pro Task (Upsert). Verifiziert: API-Round-Trip mit 24 KB Payload (inkl. Umlaute/Emoji) ohne Trunkierung, Skill-Subcommands live getestet. Der handoff-Skill nutzt die Kanboard-Ablage als bewusste **Alternative** zur lokalen `.md`-Datei (Default bleibt die Datei)

### 1.17.0

- **md2pdf-Skill aufgenommen.** Neuer Skill (SKILL.md + gebundeltes bash-Script `md2pdf`) rendert Markdown zu einem "schönen" PDF im Typora-nahen Look. Pipeline: `pandoc` → self-contained HTML (CSS + SVG inline) → headless Chrome `--print-to-pdf` — kein LaTeX nötig, weil Typora selbst über eine Browser-Engine rendert und Chrome praktisch denselben Look samt nativem SVG liefert. Cross-Platform generalisiert (macOS/Linux/FreeBSD): Chrome/Chromium-Discovery je OS mit `MD2PDF_CHROME`-Override, `--headless=new` mit Fallback auf `--headless`, auf Linux/FreeBSD `--no-sandbox --disable-dev-shm-usage` (root/Jail-tauglich), plattformübergreifender Font-Stack (Noto/DejaVu/Liberation). Mermaid-Blöcke (```mermaid) werden via `mmdc` zu SVG gerendert (Puppeteer-Config mit `--no-sandbox` automatisch übergeben); fehlt `mmdc`, bleibt der Block als Code und es gibt eine Warnung (graceful degradation). Optionen `--css <file>` und `--no-mermaid`. `install.sh`-Liste ergänzt

### 1.16.2

- **wp-cli: expliziter Negativ-Hinweis „nie `--allow-root`".** Der Skill zeigte durchgaengig das `sudo -u <wwwuser>`-Muster, sagte aber nirgends ausdruecklich, dass WP-CLI **nicht** als root laufen darf. Warnkasten in Abschnitt „1. Zugriff auf WordPress in Jails" ergaenzt: `--allow-root` vermeiden — triggert u. a. den WPML/WP_Filesystem-FTP-Fatal; immer `sudo -u <wwwuser>`

### 1.16.1

- **handoff + kanboard: aktiver CR-Kontext wird ins Handoff uebernommen.** Ist beim Erstellen eines Uebergabedokuments ein Kanboard-Task als CR-Kontext aktiv (`/kanboard cr <id>`), legt der handoff-Skill jetzt einen eigenen Abschnitt „Aktiver CR-Kontext" an (CR-ID, Titel, Task-URL, aktuelle Spalte/Status; konventionsbasiert aus dem Session-Stand, keine Live-Abfrage) und nimmt `kanboard` in die empfohlenen Skills auf. Der kanboard-Skill verweist im Abschnitt „CR-Kontext" gegenlaeufig darauf. Damit weiss der naechste Agent, an welchem Task gearbeitet wird, und kann ihn mit `/kanboard cr <id>` wiederherstellen
- **install.sh: alte Skill-Verzeichnisse werden beim Update ersetzt.** Bisher uebersprang `install.sh` jeden Skill, dessen Ziel unter `~/.claude/skills/` bereits existierte — eine alte lokale Kopie (echtes Verzeichnis, z.B. das fruehere `handoff/`) blieb so nach einem `git pull` bestehen. Jetzt: bestehende Symlinks werden aufs aktuelle Repo-Ziel umgesetzt; ein echtes Verzeichnis/Datei, das einen Repo-Skill schattet, wird nach `<skill>.pre-azedo-skills` gesichert und durch den Symlink ersetzt (nicht geloescht)

### 1.16.0

- **handoff-Skill aufgenommen.** Reiner Referenz-Skill (nur SKILL.md, kein Script) zum Erstellen von Uebergabedokumenten. Vendorisierter, angepasster Fork von [mattpocock/skills](https://github.com/mattpocock/skills/tree/main/skills/productivity/handoff) @ `386d4ff` (MIT (c) 2026 Matt Pocock, `LICENSE` mitgefuehrt). azedo-Anpassungen gegenueber dem Upstream: Uebersetzung ins Deutsche, Ablage im Projektverzeichnis (`docs/`/Projektstamm) statt OS-Temp, Abschnitt „Einlesen eines bestehenden Handoff-Dokuments", `disable-model-invocation` entfernt. **Neu:** Dateinamens-Konvention — das Argument dient als Fokus **und** Slug (`handoff-<slug>.md`), Argument mit `.md`-Endung als expliziter Dateiname; damit entsteht pro Thema ein eigenes Dokument statt ein stets ueberschriebenes `handoff.md`. `install.sh`-Liste ergaenzt

### 1.15.2

- **kanboard: Neuer Subcommand `move-project` (Task in anderes Projekt verschieben).** `move-task` arbeitet nur projektintern (`moveTaskPosition`) und schlaegt bei einem Projektwechsel fehl. `move-project <task_id> --project <name|id> [--column <name>] [--swimlane <name>]` nutzt `moveTaskToProject` und setzt danach optional Spalte/Swimlane im Zielprojekt (ohne `--column` Kanboard-Standardspalte, ohne `--swimlane` erste aktive Swimlane). Verifiziert: Live-Verschiebung eines realen Tasks ins Zielprojekt/-spalte (`success: true`)

### 1.15.1

- **php-formatting: Leerzeilen um Kontrollstrukturen an Blockgrenzen praezisiert.** Die Ausnahmen-Liste in Abschnitt 2 sagte bisher pauschal „am Anfang/Ende eines Blocks (direkt nach `{` / direkt vor `}`) keine ueberfluessige Leerzeile" — das widersprach der Grundregel, wenn das erste bzw. letzte Statement selbst eine Kontrollstruktur ist. Klargestellt: Regel 2 hat Vorrang, die Leerzeile vor/nach einer Kontrollstruktur gilt konsequent auch an Blockgrenzen (auch direkt nach dem oeffnenden `{` und direkt vor dem schliessenden `}`). Einzige verbleibende Ausnahme bleibt `}`↔`else`/`elseif`/`catch`/`finally`. Beispiel mit verschachtelter Kontrollstruktur als erstes/letztes Statement ergaenzt

### 1.15.0

- **wiki: Read-only-Zugriff auf Wikis anderer Hosts (SSH).** Ein Projekt kann die Wikis eines anderen Hosts nutzen, ohne Sync und ohne je remote ins Wiki zu schreiben. Drei Bausteine: **(1) Remote-Query** — Remotes werden aus `<projekt>/.claude/wiki-remotes.json` (`{name: {host, path, readonly}}`) aufgeloest; `query`/`status` lesen die Dateien per `ssh <host> "cat/grep …"` (User-Shell ist bash, normales Quoting), `ingest`/`compile`/`init` sind fuer Remotes gesperrt (read-only by construction). **(2) Remote-Hints** — Wikilinks `[[<remote>:<slug>]]` gelten im Linter als gueltig, wenn `<remote>` in `.claude/wiki-remotes.json` steht (kein toter Link, keine Waisen-Folgefehler); Default offline-sicher, Flag `--check-remotes` verifiziert die Ziele on demand per SSH-`find`. **(3) Handoff-Note** — Subcommand `<remote>:handoff` liest das Zielschema + `index.md` per SSH, erkennt new-vs-update und erzeugt eine ingest-fertige Note unter `.claude/wiki-outbox/<remote>-<slug>.md`; Transport (Kanboard/scp/Mail) und Ingest auf dem Zielhost sind user-ausgeloest. `lint-wiki.py`: neue `load_remotes()`/`parse_remote_target()`/`check_remote_target()`, `--check-remotes`-Flag. Verifiziert: Regression azedo 99/0 + cris 27/0 unveraendert; SSH-Read + Remote-Pointer + Handoff-Format gegen die reale cris-Wiki getestet

### 1.14.1

- **wiki: Wiki-Basis projekt-relativ (Portabilitaet).** Die Wiki-Root wird nicht mehr home-verankert (`~/azedo.ai/wiki/<name>/`) aufgeloest, sondern **relativ zum Projekt-Root** (`wiki/<name>/`) — konsistent mit der Projekt-`CLAUDE.md` (`wiki/azedo/…`) und portabel fuer Mac, andere Mitarbeiter und abweichende Checkout-Orte. Kein Home-Fallback (waere bei anderem Checkout-Pfad kontraproduktiv). Nur SKILL.md-Anleitung + Hilfetexte im Linter betroffen; `lint-wiki.py` war bereits vollstaendig parametrisch (nimmt die Wiki-Root als Argument). Verifiziert: azedo + cris linten sauber sowohl aus dem Projekt-Root als auch aus einem anderen Verzeichnis (0 Fehler)

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
