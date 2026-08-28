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
- Tasks löschen (`remove-task`, nicht umkehrbar — ohne `--force` nur Vorschau mit Titel und Abbruch)
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

**Setup:** Eine `.env`-Datei mit `KANBOARD_URL` und `KANBOARD_TOKEN` im Arbeitsverzeichnis anlegen (oder Pfad via `KANBOARD_ENV` setzen; ohne beides gilt `~/.env`, eine Konfiguration für alle Projekte). Vorlage:

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

**Setup:** Eine `.env`-Datei mit `KIMAI_HOST` und `KIMAI_TOKEN` im Arbeitsverzeichnis anlegen (oder Pfad via `KIMAI_ENV` setzen; ohne beides — und bei einem projektlokalen `.env` ohne `KIMAI_*`-Schlüssel — gilt `~/.env`). Vorlage:

```
KIMAI_HOST=https://kimai2.example.com
KIMAI_TOKEN=dein-api-token
```

Dann einmalig `setup` ausfuehren (aus dem Arbeitsverzeichnis mit der `.env`):

```bash
python3 ~/.claude/skills/kimai/kimai setup
```

**Trigger:** `/kimai` oder natürliche Sprache wie "wieviele Stunden habe ich diese Woche", "Zeiteintrag anlegen".

### jira

Jira über die REST API — sowohl selbst-gehostetes **Data Center/Server** (`/rest/api/2/`, PAT-Bearer, Plaintext/Wiki-Markup) als auch **Cloud** (`*.atlassian.net`, `/rest/api/3/`, Basic-Auth `email:token`, ADF-Bodies). Mehrere Instanzen als benannte Profile in `~/.claude/jira.json`, Ziel-Instanz per Projekt-Routing aus dem Issue-Key (die `projects`-Liste der Instanz entscheidet) oder `--instance`:

- Lesen: `search` (JQL, Paginierung DC `--start` / Cloud `--token`), `issue`, `comments` (mit Kommentar-id), `transitions`, `attachments`, `download`, `users` (Nutzersuche → accountId bzw. Username)
- Schreiben: `comment`, `comment-edit` (bestehenden Kommentar überschreiben), `transition` (dry-run, erst mit `--yes`), `assign`, `describe`, `subtask`, `attach`
- `@[<schlüssel>]` im Body wird zur echten Erwähnung: Cloud als ADF-`mention`-Knoten, DC als `[~username]`. Schlüssel ist E-Mail (eindeutig, bevorzugt), accountId/Username oder Anzeigename — bei mehreren Treffern bricht der Skill mit Kandidatenliste ab, statt zu raten
- ADF ↔ Plaintext transparent: beim Lesen verflacht, beim Schreiben aus Plaintext aufgebaut

**Voraussetzungen:** Python ≥ 3.11, DC: Personal Access Token; Cloud: API-Token von id.atlassian.com + Account-E-Mail. Config `~/.claude/jira.json` (Vorlage: `jira/jira.json.example`), alternativ `JIRA_CONFIG=`.

**Trigger:** `/jira` oder natürliche Sprache wie "schau in Jira", "welchen Status hat PROJ-…", "kommentier das Ticket".

### imap

Posteingang-Triage über mehrere IMAP-Konten — das Gegenstück zu `swaks`. Unterstützt:

- Zugangsdaten aus der `~/.muttrc` (`account-hook`), keine zweite Credential-Datei; Backticks und
  `source` werden ausgewertet, also auch `imap_pass=` aus einem Keystore
- Mails auflisten (`list`, ohne Konto über alle Konten, `--unseen`/`--since`) und lesen (`read`)
- `fetch` holt einen Stapel Mails mit **einem** Login (`--uids`/`--uid-file`, `-o` schreibt je UID
  eine Datei) — das lesende Gegenstück zu `batch`
- `quote` erzeugt den Zitatblock für eine Antwort im Thunderbird-Format (`--format text|html`,
  `--width`), löst vorher `format=flowed` auf und liefert per `--json` die Threading-Header
  (`In-Reply-To`, `References`) gleich mit
- `find -m <message-id>` löst eine Message-ID zu Konto, Ordner und UID auf (ohne Konto über alle
  Konten, INBOX zuerst); `quote -m` nimmt dieselbe Angabe direkt statt einer UID — UIDs sind
  ordner-lokal, ein fehlendes `--folder` zitiert sonst still die gleichnamige Mail der INBOX
- Gelesen wird mit `BODY.PEEK` — der Ungelesen-Status bleibt unangetastet
- Einsortieren, als Spam markieren, in den Papierkorb (`delete` expunged nie), Flags setzen
- Sonderrollen (`junk`, `trash`, `archive`) statt Ordnernamen, per SPECIAL-USE am Server aufgelöst
- Kopieren und Verschieben **zwischen** zwei Konten (`APPEND` zuerst, Quelle erst danach)
- `batch` führt Aktionen mit einem Login je Konto aus, erst nach Freigabe durch den Nutzer
- `append <datei.eml>` legt eine lokale `.eml` in einen Ordner (Default: Gesendet) — die Ablage, die
  `swaks` selbst nicht vornimmt; `\Seen` als Default-Flag, und eine schon vorhandene Message-ID
  verhindert den zweiten Eintrag
- Anhänge auflisten (`attachments`) und herausschreiben (`save-attachment`, per `--name`/`--index`/`--all`,
  ohne `--output` nach `.tmp/`) — Dateinamen RFC-2231/2047-dekodiert, Pfadanteile gestrippt, nichts wird
  überschrieben; Inline-Teile per Default ausgeblendet

**Voraussetzungen:** `~/.muttrc` mit `account-hook` je Konto (mutt selbst muss nicht installiert sein)

**Trigger:** `/imap` oder natürliche Sprache wie "geh meine Inbox durch", "räum den Posteingang auf".

### swaks

Versendet E-Mails via `swaks` über einen Postfix-Relay. Unterstützt:

- Plain-Text und HTML Body
- Dateianhänge (beliebiger MIME-Type)
- Mehrere Anhänge pro Mail
- Kontakt-Shortcuts (`.claude/swaks-contacts.tsv` — Name-zu-Email-Lookup)
- Optionale Default-Signatur (`.claude/swaks-signature.txt`)
- Versand-Defaults (`to`, `from`, `server`, `message_id_domain`) aus `.claude/swaks.json` — projektlokal vor global, Vorlage `swaks.json.example`
- `--verify` prüft die fertige `.eml` vor dem Versand: Prüfsumme (`--expect-sha256`, gegen die
  `--sha-file` aus dem Bau), Markup im HTML-Part und ein Marker aus dem freigegebenen Entwurf
  (`--expect-marker`, gegen den dekodierten Text-Part)
- `--html-file` ist optional — fehlt es, entsteht der HTML-Part aus dem Text (`<p>`/`<br>`)

**Voraussetzungen:** `swaks` installiert, `.claude/swaks.json` mit erreichbarem `server`

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

Google Analytics 4 Datenabfrage via Service Account. Python-Script (stdlib only, keine pip-Dependencies). Scope pro Subcommand: lesend `analytics.readonly`, schreibend (Custom Dimensions, Datenaufbewahrung) `analytics.edit`:

- Accounts und Properties auflisten
- Reports: Custom Dimensions, Metrics, Filter, Sortierung, Datumsbereiche
- Realtime: aktive User, aktuelle Seitenaufrufe
- Metadata: verfuegbare Dimensionen und Metriken einer Property
- Custom Dimensions auflisten und anlegen — ohne Registrierung sind Event-Parameter ueber die Data API gar nicht abfragbar, und die Registrierung wirkt **nicht rueckwirkend**
- Datenaufbewahrung anzeigen und setzen (GA4-Default sind 2 Monate)
- Tab-separierte oder JSON-Ausgabe

**Voraussetzungen:** Python >= 3.11, Package `cryptography` (fuer JWT-Signierung; Installation plattformabhaengig, das Script nennt den passenden Weg)

**Setup:** Service Account JSON unter `~/.config/ga4-service-account.json`. Service Account in den GA4-Properties hinterlegen: als Betrachter fuer die lesenden Subcommands, als **Bearbeiter** fuer die schreibenden. Dann:

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

**Voraussetzungen:** Python >= 3.11, Package `cryptography` (fuer JWT-Signierung; Installation plattformabhaengig, das Script nennt den passenden Weg)

**Setup:** Service Account JSON unter `~/.config/ga4-service-account.json` (derselbe SA wie GA4, oder Pfad via `GSC_SERVICE_ACCOUNT`). Service Account als Nutzer in der GSC-Property hinterlegen, Search Console API im GCP-Projekt aktivieren. Dann:

```bash
python3 "$SKILL_DIR/google-search-console" setup
```

**Trigger:** `/google-search-console`, `/gsc` oder natuerliche Sprache wie "organische Klicks", "Impressionen in der Google-Suche", "ist die Seite indexiert".

### image-optimize

Optimiert Bilder für Web-Verwendung. Unterstützt:

- Analyse: Auflösung, Dateigröße und Dateinamen prüfen
- Optimierung: PNG verlustfrei (optipng), JPEG quality-basiert (jpegoptim), progressiv als Default
- Resize: Auflösung skalieren via GraphicsMagick (Seitenverhältnis bleibt erhalten)
- Convert: Format umwandeln inkl. Alpha-Flattening, damit Transparenz im JPEG nicht schwarz wird
- Rename: Dateinamen SEO-freundlich umbenennen (Umlaute, Leerzeichen, Sonderzeichen)
- Web-Pipeline: alle Schritte in einem Durchgang

Bildmaße kommen von `gm`/`magick`; fehlt beides, liest ein eingebauter Header-Parser
(PNG, JPEG, GIF, WebP, BMP, TIFF) sie direkt aus der Datei. `analyze` nennt die
verwendete Quelle.

**Voraussetzungen:** Python ≥ 3.11, `optipng`, `jpegoptim`, für Resize und Convert
`GraphicsMagick` (oder ImageMagick 7)

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

### lit

Die Gegenrichtung zu `md2pdf`: wandelt Dokumente über das CLI [liteparse](https://github.com/run-llama/liteparse) (Rust, Apache-2.0) nach Markdown, Text oder JSON. PDFs und Bilder direkt, Office-Formate über LibreOffice. Lokal, ohne Cloud, ohne ML-Modelle, Tesseract-OCR einkompiliert — ein PDF mit intaktem Textlayer dauert Millisekunden.

- `--no-ocr` als Default; OCR verschlechtert bei Textlayer-PDFs die Struktur, und `is-complex` ist als Entscheidungshilfe unzuverlässig
- Kontext-Disziplin: einmal in eine Datei parsen und diese durchsuchen, statt je Suche neu zu extrahieren
- Installation für FreeBSD (Linux-Binary über den Linuxulator, kein Port vorhanden), Linux und macOS — inklusive der passenden `libpdfium`, die per `dlopen` nachgeladen wird und dem Release-Tarball nicht beiliegt
- Fallstricke dokumentiert: SIGPIPE-Panic bei `| head`, Nachladen der `traineddata` beim ersten OCR-Lauf, harter Abbruch bei Office ohne LibreOffice

**Voraussetzungen:** `lit` im PATH (Installationsanleitung im Skill); optional LibreOffice für DOCX/XLSX/PPTX

**Aufruf:** `lit parse --no-ocr --format markdown -o <out.md> <datei>`

**Trigger:** `/lit` oder natürliche Sprache wie "mach aus dem PDF eine Markdown-Datei", "wandle die Datei in MD um". Bewusst **kein** Trigger auf bloßes Lesen eines PDFs.

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

Synchronisiert WordPress-Plugins und -Themes zwischen Produktions-Installationen (in FreeBSD-Jails) und der DEV-Umgebung via rsync. Bidirektional: Prod → DEV und DEV → Prod. Kein eigenes Script, reine SKILL.md mit:

- Pfad-Schema fuer DEV und Prod (iocage/ezjail); DEV-Host und Jail-Name kommen aus dem Infra-Wiki, nicht aus dem Skill
- rsync-Befehle in beide Richtungen
- Permissions: DEV immer `www:<gruppe>` 775/664, Prod an bestehender Installation orientieren
- Aufraeumen von macOS-Artefakten (._*, .DS*)

**Trigger:** `/wp-sync-dev` oder natuerliche Sprache wie "sync plugin", "plugin von prod holen", "theme auf dev kopieren".

### mainwp

MainWP Dashboard — WordPress-Sites netzwerkuebergreifend verwalten.
Generischer Abilities-Executor: 5 Subcommands fuer beliebige MainWP-Abilities.

- Sites auflisten, Details anzeigen
- Updates pruefen und installieren
- Plugins/Themes verwalten (aktivieren, deaktivieren, installieren, loeschen)
- Clients und Tags organisieren
- Batch-Operationen mit Job-Polling

**Voraussetzungen:** Python >= 3.11

**Voraussetzungen:** Python >= 3.11

**Setup:** WordPress Application Password und REST API v2 Key auf dem Dashboard-Host. In `.env` eintragen:

```
MAINWP_HOST=https://dashboard.example.at
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

LLM Wiki-Verwaltung fuer strukturierte Dokumentation. Unterstuetzt **mehrere Wikis** mit je eigenem Entity-Modell (Infra `azedo`: Server/Service/Access/Site/Procedure; Projekt-Wikis abweichend). Zwei Scripts (`lint-wiki.py`, `audit-wiki.py`), sonst reine SKILL.md mit Subcommands:

- init: neues Wiki-Unterverzeichnis anlegen (inkl. Default-`wiki-schema.json`)
- ingest: Quellen ins Wiki aufnehmen (nach raw/, immutable)
- compile: Quellen zu Wiki-Entities verarbeiten (erlaubte Typen laut Wiki-`CLAUDE.md`)
- harvest: Erkenntnisse der Sitzung durch den Aufnahmefilter schicken und als Vorlage zeigen (inkl. der verworfenen mit Grund); schreibt erst nach Freigabe
- query: Fragen gegen das Wiki beantworten
- lint: strukturelle Pruefung (Frontmatter, tote Links, Konnektivitaet, Namenskonventionen, Datum in Ueberschriften); `--check-remotes` verifiziert Remote-Pointer per SSH
- audit: aufgeblaehte und historienlastige Artikel finden (Zeilen relativ zum p90 des eigenen Entity-Typs, Historie-Dichte, prozeduraler Inhalt in erzaehlenden Entities); bewertet statt zu pruefen, Exit immer 0
- refactor: eine Entity abschnittsweise einordnen (bleibt / gehoert in eine Procedure / ueberholte Historie / Duplikat) und einen Umbauvorschlag vorlegen; schreibt nichts ohne Freigabe
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

Die Kontaktadresse in der User-Agent-Zeile (von Nominatim gewuenscht) kommt aus `WETTER_CONTACT` oder `contact` in `~/.claude/wetter.json` (Vorlage: `wetter/wetter.json.example`); ohne beides laeuft der Skill ohne Kontaktangabe.

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

### einfache-sprache

Deutsche Texte in Einfache Sprache bringen und auf Verstaendlichkeit pruefen - messend statt nach Gefuehl. Orientiert an DIN 8581-1 (Einfache Sprache) und DIN ISO 24495-1 (Grundsaetze verstaendlicher Sprache). SKILL.md + fuenf Referenzen + Python-Linter (stdlib only):

- Drei Zielstufen mit eigenen Zielwerten: `PLAIN` (Fachpublikum), `B1` (Standard), `A2` (Formulare, Merkblaetter)
- Lesbarkeitsindizes: Wiener Sachtextformel 1-4, LIX, Flesch in der deutschen Fassung nach Amstad, je mit Ampel gegen die Stufe
- Regel-Linter: Satzlaenge/Nebensaetze/Passiv/Konjunktiv/Genitivketten/Verbklammer (`sentence_lint.py`), Nominalstil/Funktionsverbgefuege/Amtsdeutsch/Fremdwoerter/Begriffsvarianten (`lexicon_lint.py`), Absaetze/Ueberschriften/Listenkandidaten/Anrede/Datumsformate (`structure_lint.py`)
- Sammelcheck `einfache_sprache_audit.py` mit Ampel, priorisierten Hebeln und `--vergleich` fuer Vorher/Nachher
- Inhaltstreue als Leitplanke: Zahlen, Fristen, Bedingungen und Rechtsfolgen bleiben unveraendert; Rechtsbegriffe werden erklaert statt ersetzt
- Abgrenzung zur Leichten Sprache (A1, DIN SPEC 33429) ist Teil des Skills - die verlangt eine Pruefgruppe aus der Zielgruppe und ist kein Werkzeugergebnis

**Voraussetzungen:** Python >= 3.11

**Trigger:** `/einfache-sprache` oder natuerliche Sprache wie "schreib das einfacher", "in Einfacher Sprache", "das versteht kein Mensch", "Amtsdeutsch aufloesen", "Lesbarkeit pruefen".

### handoff

Fasst die aktuelle Konversation in ein Uebergabedokument zusammen, damit ein neuer Agent nahtlos weiterarbeiten kann. Reiner Referenz-Skill (nur SKILL.md, kein Script). Vendorisierter, angepasster Fork von [mattpocock/skills](https://github.com/mattpocock/skills/tree/main/skills/productivity/handoff) (MIT):

- Ablage im Projektverzeichnis (`docs/` falls vorhanden, sonst Projektstamm)
- Dateiname aus dem Argument: kein Argument → `handoff.md`; Argument ohne `.md` → Fokus **und** Slug (`handoff-<slug>.md`, nichts wird ueberschrieben); Argument mit `.md` → expliziter Dateiname
- Abschnitt „Empfohlene Skills" im Dokument, keine Duplikate zu bestehenden Artefakten, Redaktion sensibler Daten
- Einlese-Workflow: bestehendes Handoff rekapitulieren, rueckfragen, nie eigenstaendig handeln

**Lizenz:** MIT (c) 2026 Matt Pocock. Siehe `handoff/LICENSE`. azedo-Anpassungen (Deutsch, Ablageort, Dateinamens-Konvention, Einlese-Sektion) in der SKILL.md unter „Herkunft & Lizenz" dokumentiert.

**Trigger:** `/handoff` oder natuerliche Sprache wie "erstell eine Uebergabe", "fass die Session fuer den naechsten Agent zusammen".

### wie-bitte

Erklaert die zuletzt gegebene Antwort noch einmal, in Einfacher Sprache. Fuer den Moment, in dem eine Antwort nicht angekommen ist - auf Nachfrage wird sie sonst meist nur laenger, nicht verstaendlicher. Reiner Referenz-Skill (nur SKILL.md, kein Script). Angelehnt an `wait-what` aus [mattpocock/skills](https://github.com/mattpocock/skills/tree/main/skills/productivity/wait-what) (MIT):

- Fester Aufbau: ein Satz Kontext, die Aussage, die Folge fuer den Nutzer - hoechstens acht Saetze
- Sprachregeln auf Stufe `B1` von `einfache-sprache`, aber ohne dessen Messapparat (keine Kennwerte, keine Linter, keine Befundliste)
- Fachbegriffe bleiben stehen und bekommen einen Halbsatz Erklaerung, statt ersetzt zu werden
- Gilt immer der **letzten eigenen Antwort**, nie einem mitgeschickten Text; ein Argument benennt nur die Stelle, die nicht getragen hat
- `disable-model-invocation: true` - nur ueber `/wie-bitte`, sonst kollidiert der Trigger mit `einfache-sprache`

**Lizenz:** MIT (c) 2026 Matt Pocock. Siehe `wie-bitte/LICENSE`. azedo-Anpassungen (Deutsch, B1 statt ASD-STE100, kein Repo-Anker, fester Dreiteiler, Abgrenzung zu `einfache-sprache`) in der SKILL.md unter „Herkunft & Lizenz" dokumentiert.

**Trigger:** nur `/wie-bitte`.

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

### privatebin

PrivateBin-Anbindung — teilt Text, Logausschnitte, Configs und ganze Dateien als Ende-zu-Ende-verschluesselte Paste und gibt den Link zurueck. Die Verschluesselung passiert lokal im Skill (Format v2: AES-256-GCM, PBKDF2-HMAC-SHA256, raw deflate); der Base58-Schluessel steht nur im URL-Fragment und erreicht den Server nie:

- create: Inhalt aus `--text`/`--file`/STDIN, Datei per `--attach` (`--name` benennt um), `--expire` (5min…never), `--burn`, `--password`, `--discussion`, `--format` (plaintext/markdown/syntaxhighlighting), `--json`. Ausgabe ist genau eine Zeile: die fertige URL
- read: entschluesselt eine Paste-URL samt `#`-Fragment — auch von fremden Instanzen; `--save-attachment` schreibt den Anhang, `--password` fuer geschuetzte Pastes
- delete: nimmt eine Paste zurueck, Token aus der History oder per `--token`
- history: die letzten 25 geteilten Links (`~/.claude/privatebin-pastes.log`, Modus 0600, enthaelt Schluessel und Delete-Tokens; `--no-history` schaltet das Mitschreiben ab)

Instanz-URL und optionale Basic-Auth-Zugangsdaten in `~/.claude/privatebin.json` (Vorlage `privatebin/privatebin.json.example`), mehrere Instanzen moeglich.

**Voraussetzungen:** Python >= 3.9 und `cryptography` (AES-256-GCM gibt es in der stdlib nicht). FreeBSD: `pkg install py3XY-cryptography` passend zur laufenden Python-Version; macOS: `python3 -m pip install --user cryptography`, bei Homebrew-Python stattdessen ein venv (`python3 -m venv ~/.claude/venv`). Fehlt das Modul, nennt das Script den passenden Weg.

**Trigger:** `/privatebin` oder natuerliche Sprache wie "teil das per PrivateBin", "mach einen Paste draus", "schick mir das als Link", "gib mir den Inhalt von dieser Paste-URL".

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

### 1.47.0

- **Skill-Descriptions auf ihre Aufgabe zurückgeschnitten.** Die Description ist
  der einzige Text, der dauerhaft im Kontext steht - sie entscheidet nur, *ob*
  ein Skill geladen wird. Alles, was erst *danach* gebraucht wird, gehört in den
  Body. Aus zwölf Descriptions sind deshalb Implementierungsdetails
  (Krypto-Verfahren, API-Hostnames, Kernbefehle, stdlib-only, unterstützte
  Betriebssysteme), Config-Pfade und mehrfach umformulierte Trigger-Sätze
  entfernt worden: `imap`, `jira`, `wiki`, `privatebin`, `pushover`, `telegram`,
  `mail-as-me`, `swaks`, `google-search-console`, `einfache-sprache`, `lit`,
  `image-optimize`. Summe über alle Skills 15.527 -> 12.449 Bytes, rund 770
  Token weniger pro Request.
- **Verwechselbare Paare grenzen sich jetzt gegenseitig ab.** Wo zwei Skills
  dieselben Wörter benutzten, nennt jede Description den Nachbarn beim Namen:
  `pushover` (nur ausgehend) gegen `telegram` (kann auf eine Antwort warten),
  `mail-as-me` (formulieren, immer zuerst) gegen `swaks` (versenden),
  `google-search-console` (Weg zur Website) gegen `google-analytics` (Verhalten
  auf der Website), `wp-cli` (Basis) gegen die Spezial-Skills daneben. Auslöser
  war die Beobachtung, dass eine Mail direkt in `swaks` getextet den Stil des
  Empfängers spiegelt - genau das, was die Engine-Regel in `mail-as-me`
  verhindern soll.
- **`swos` und `ripgrep` haben erstmals Frontmatter.** Beide hatten keinen
  YAML-Block; Name und Beschreibung wurden aus der ersten Überschrift
  abgeleitet, steuerbar war daran nichts. `swos` lädt sich jetzt nur bei
  eindeutiger SwOS-Identität von selbst (SwOS, SwOS-Lite, CSS106/326/610,
  RB260) und ausdrücklich *nicht* bei den mehrdeutigen Nachbarbegriffen
  MikroTik, Switch, VLAN, PoE - die meinen genauso oft RouterOS.
- **`ripgrep`: neuer Abschnitt „Verfügbarkeit prüfen".** `rg` gehört auf FreeBSD
  nicht zum Basissystem. Der Skill prüft jetzt erst `which rg`, fragt auf
  Systemen ohne `rg` nach, bevor ein Paket nachinstalliert wird, und weicht bis
  dahin auf `grep` aus - mit einer Übersetzungstabelle für die gängigen
  Optionen. Bisher stand dort nur „use it instead of grep", was auf einem Host
  ohne `rg` ins Leere lief.
- **Die `trigger:`-Arrays sind aufgelöst.** Vier Skills (`wp-cli`, `wp-nf`,
  `wp-pys`, `tcsh`) führten im Frontmatter eine Liste von Auslöse-Phrasen.
  Claude Code liest das Feld nicht - es ist kein Teil der Spezifikation, die
  Phrasen kamen also nirgends an. Sichtbar wurde der Schaden an `wp-cli`: 129
  Bytes Description, während 16 brauchbare Phrasen im toten Feld lagen. Die
  verwertbaren sind in die jeweilige Description gewandert, die Arrays sind
  weg. `wp-cli` und `wp-pys` sind dadurch bewusst *länger* geworden - dafür
  greifen sie überhaupt.
- **Kunden-Projekt-Keys aus dem Arbeitsbaum entfernt.** In `jira/` und
  `kanboard/` standen echte Jira-Projekt-Keys und Vorgangs-IDs in Beispielen,
  Hilfetexten und der Beispiel-Config - 49 Stellen in sieben Dateien, entgegen
  der eigenen Regel für dieses öffentliche Repo. Ersetzt durch sprechende
  Platzhalter (PROJ für die DC-Instanz, OPS/SUPPORT/WEB für die Cloud-Instanz),
  sodass das Instanz-Routing im Beispiel erkennbar bleibt. Zwei
  Changelog-Sätze, die eine Vorgangs-ID als Beleg trugen, sind umformuliert
  statt ersetzt. **Die Historie bleibt öffentlich einsehbar** - das hier
  verhindert nur, dass es weiter wächst.
