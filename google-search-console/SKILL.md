---
name: google-search-console
description: >
  Google Search Console (GSC): Sites/Properties, Search-Analytics
  (Impressionen, Klicks, CTR, Position nach Query/Seite/Land/Gerät),
  URL-Inspection (Index-Status) und Sitemaps abfragen. Nutze diesen Skill wenn
  der User GSC-Daten auswerten, organische Suchleistung analysieren, den
  Google-Index-Status einer URL prüfen oder Sitemaps kontrollieren will. Auch
  aktiv verwenden wenn der User sagt "wie ranken wir", "organische Klicks",
  "Impressionen in der Google-Suche", "ist die Seite indexiert", "Search
  Console", "GSC Report", o.ae.
  Trigger: /google-search-console, /gsc.
---

# google-search-console -- Google Search Console

GSC-Daten (Sites, Search-Analytics, URL-Inspection, Sitemaps) werden ueber das gebundelte Script `google-search-console` (Python >=3.11, im Skill-Verzeichnis) abgefragt.

**Aufruf:** `python3 "$SKILL_DIR/google-search-console" <subcommand> [options]`

`$SKILL_DIR` ist das Base Directory dieses Skills (dort wo diese SKILL.md liegt).

Read-only (Scope `webmasters.readonly`) — keine schreibenden Operationen (kein Sitemap-Submit, kein Reindex).

## Setup

### Voraussetzungen

- Python-Package `cryptography` (fuer JWT-Signierung)
- Service Account JSON unter `~/.config/ga4-service-account.json`
  (oder Pfad via `GSC_SERVICE_ACCOUNT` Umgebungsvariable) — **derselbe Service
  Account wie beim GA4-Skill**
- Service Account muss als **Nutzer** in der jeweiligen GSC-Property hinterlegt
  sein (search.google.com/search-console → Einstellungen → Nutzer und
  Berechtigungen). Read-only reicht.
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
- Nur lesend — Scope `webmasters.readonly`
- Teilt sich den Service Account mit dem `google-analytics` (GA4) Skill
