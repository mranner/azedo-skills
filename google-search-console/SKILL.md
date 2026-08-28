---
name: google-search-console
description: >
  Google Search Console: organische Suchleistung bei Google - Impressionen,
  Klicks, CTR und Position nach Suchbegriff, Seite, Land und Gerät; dazu
  Index-Status einer URL prüfen und Sitemaps abfragen, einreichen oder
  entfernen. Für das Verhalten der Besucher auf der Website selbst ist
  google-analytics zuständig. Auch bei "wie ranken wir", "organische Klicks",
  "ist die Seite indexiert", "Search Console".
  Trigger: /google-search-console, /gsc.
---

# google-search-console -- Google Search Console

GSC-Daten (Sites, Search-Analytics, URL-Inspection, Sitemaps) werden ueber das gebundelte Script `google-search-console` (Python >=3.11, im Skill-Verzeichnis) abgefragt.

**Aufruf:** `python3 "$SKILL_DIR/google-search-console" <subcommand> [options]`

`$SKILL_DIR` ist das Base Directory dieses Skills (dort wo diese SKILL.md liegt).

**Scope pro Subcommand:** Lesende Subcommands laufen mit `webmasters.readonly`.
Nur die beiden **schreibenden** Subcommands `submit-sitemap` und `delete-sitemap`
fordern den Schreib-Scope `webmasters` an und sind mit einer interaktiven
y/N-Abfrage abgesichert (siehe Abschnitt „Sitemaps — Schreiben"). Reindex/Indexing
gibt es weiterhin nicht (die Search Console API hat dafuer keinen Endpoint).

## Setup

### Voraussetzungen

- Python-Package `cryptography` (fuer JWT-Signierung)
- Service Account JSON unter `~/.config/ga4-service-account.json`
  (oder Pfad via `GSC_SERVICE_ACCOUNT` Umgebungsvariable) — **derselbe Service
  Account wie beim GA4-Skill**
- Service Account muss als **Nutzer** in der jeweiligen GSC-Property hinterlegt
  sein (search.google.com/search-console → Einstellungen → Nutzer und
  Berechtigungen). Fuer die lesenden Subcommands reicht Read-only; fuer
  `submit-sitemap`/`delete-sitemap` braucht der Account **Vollzugriff**
  (`siteFullUser` bzw. `siteOwner`). Den passenden OAuth-Scope waehlt das Script
  je Subcommand selbst.
- Search Console API im zugehoerigen GCP-Projekt aktiviert

### Erster Einsatz

```bash
python3 "$SKILL_DIR/google-search-console" setup
```

Das testet die Authentifizierung, listet alle zugaenglichen Sites/Properties und schreibt `instance.json` ins Skill-Verzeichnis.

Falls `instance.json` nicht existiert, zuerst `setup` ausfuehren.

**Site-Lookup:** Zuerst `$SKILL_DIR/instance.json` per grep pruefen — dort stehen alle Sites mit `siteUrl` und `permissionLevel`. Nur bei unbekannten Sites den `sites` Subcommand nutzen.

**siteUrl-Format:** Domain-Properties sind `sc-domain:example.com`, URL-Praefix-Properties `https://example.com/`. Immer exakt so uebergeben, wie in `sites`/`instance.json` gelistet.

## Subcommands

### System

```bash
python3 "$SKILL_DIR/google-search-console" version
python3 "$SKILL_DIR/google-search-console" setup
```

### Sites

```bash
# Alle zugaenglichen Properties + Berechtigungslevel
python3 "$SKILL_DIR/google-search-console" sites
```

### Search-Analytics

```bash
# Top-Queries der letzten 28 Tage (Default-Zeitraum)
python3 "$SKILL_DIR/google-search-console" search-analytics -S "sc-domain:example.com"

# Top 20 Seiten nach Klicks, letzte 90 Tage
python3 "$SKILL_DIR/google-search-console" search-analytics -S "sc-domain:example.com" \
  -d page -s 90daysAgo -e today -l 20

# Query x Seite, gefiltert auf ein Land
python3 "$SKILL_DIR/google-search-console" search-analytics -S "sc-domain:example.com" \
  -d "query,page" -f "country==aut"

# Zeitreihe nach Tag
python3 "$SKILL_DIR/google-search-console" search-analytics -S "sc-domain:example.com" \
  -d date -s 28daysAgo -e today

# Rohe JSON-Antwort
python3 "$SKILL_DIR/google-search-console" search-analytics -S "sc-domain:example.com" --json
```

**Datumsformate:** `today`, `yesterday`, `NdaysAgo` (z.B. `28daysAgo`) oder `YYYY-MM-DD`. Relative Keywords werden lokal auf ISO-Datumswerte aufgeloest (die GSC-API akzeptiert nur `YYYY-MM-DD`). GSC-Daten haben typischerweise 2-3 Tage Verzoegerung.

**Dimensionen:** `query`, `page`, `country`, `device`, `date`, `searchAppearance` (kombinierbar, komma-separiert).

**Kennzahlen (immer ausgegeben):** `clicks`, `impressions`, `ctr`, `position`.

**Filter:** einfaches `dimension==wert` Format (z.B. `country==aut`, `device==MOBILE`). Werte fuer `country` sind ISO-3166-1-alpha-3 (klein), fuer `device` `DESKTOP`/`MOBILE`/`TABLET`.

### URL-Inspection

```bash
# Echter Google-Index-Status einer konkreten URL
python3 "$SKILL_DIR/google-search-console" url-inspection \
  -S "sc-domain:example.com" \
  -u "https://example.com/eine-seite/"
```

Liefert die Kernfelder aus `indexStatusResult`: `verdict`, `coverageState`, `robotsTxtState`, `indexingState`, `pageFetchState`, `lastCrawlTime`, `googleCanonical`, `userCanonical`, `crawledAs` sowie den `inspectionResultLink`. `--json` liefert die vollstaendige Antwort (inkl. Mobile-Usability, Rich-Results, referring URLs).

### Sitemaps

```bash
python3 "$SKILL_DIR/google-search-console" sitemaps -S "sc-domain:example.com"
```

Listet eingereichte Sitemaps mit `path`, `lastSubmitted`, `pending` sowie den summierten `submitted`/`indexed` URL-Zahlen. `--json` fuer Details je `contents`-Typ.

### Sitemaps — Schreiben (submit / delete)

**Schreibende Operationen** — Scope `webmasters` (nicht `webmasters.readonly`).
Beide zeigen zuerst den aktuellen Zustand des Eintrags an und fragen dann
**interaktiv `[y/N]`** nach, bevor sie schreiben. `--yes`/`-y` ueberspringt die
Abfrage. In **nicht-interaktiven** Kontexten (kein TTY, z.B. Script/Agent) bricht
der Befehl ohne `--yes` bewusst ab (Exit-Code 2) — nichts wird geaendert.

```bash
# Sitemap einreichen (PUT). feedpath ist die volle Sitemap-URL.
python3 "$SKILL_DIR/google-search-console" submit-sitemap \
  -S "sc-domain:example.com" "https://example.com/sitemap.xml"

# Ohne Rueckfrage (z.B. im Script):
python3 "$SKILL_DIR/google-search-console" submit-sitemap \
  -S "sc-domain:example.com" "https://example.com/sitemap.xml" --yes

# Sitemap-Eintrag entfernen (DELETE):
python3 "$SKILL_DIR/google-search-console" delete-sitemap \
  -S "sc-domain:example.com" "https://example.com/sitemap_index.xml" --yes
```

- `feedpath` ist immer die **vollstaendige Sitemap-URL** (kein relativer Pfad);
  `siteUrl` und `feedpath` werden intern voll URL-encodet.
- PUT/DELETE liefern **HTTP 204 ohne Body** — der Skill gibt `[OK] ... (HTTP 204)`
  aus.
- `submit-sitemap` auf einen bereits vorhandenen, gueltigen Eintrag ist
  **idempotent** (aktualisiert nur `lastSubmitted`, setzt `pending=True`).
- `delete-sitemap` auf einen nicht vorhandenen Eintrag meldet „nichts zu loeschen"
  und macht nichts (Exit 0).

## Workflow

1. `instance.json` pruefen — falls nicht vorhanden, `setup` ausfuehren
2. `siteUrl` per grep in `instance.json` nachschlagen (exaktes Format beachten)
3. `search-analytics` / `url-inspection` / `sitemaps` mit passenden Parametern ausfuehren
4. Bei fehlenden Zugriffen: Service Account als Nutzer in der GSC-Property hinterlegen

## Hinweise

- Ausgabe ist Tab-separiert (fuer einfaches Weiterverarbeiten)
- `--json` liefert die rohe API-Antwort
- Default-Zeitraum Search-Analytics: `28daysAgo` bis `today`
- `ctr` wird als Anteil (0..1) mit 4 Nachkommastellen ausgegeben, `position` mit 1
- API-Zeilenlimit Search-Analytics: 25000 (Default hier 1000)
- Scope pro Subcommand: lesend `webmasters.readonly`, schreibend
  (`submit-sitemap`/`delete-sitemap`) `webmasters`. Token werden pro Scope gecacht.
- Schreib-Endpoint liegt unter `www.googleapis.com/webmasters/v3` (nicht
  `searchconsole.googleapis.com`); PUT/DELETE liefern HTTP 204 ohne Body
- Teilt sich den Service Account mit dem `google-analytics` (GA4) Skill
