---
name: google-analytics
description: >
  Google Analytics 4: Accounts, Properties, Traffic-Reports, Realtime-Daten,
  Conversions und Metadaten abfragen. Nutze diesen Skill wenn der User
  GA4-Daten auswerten, Traffic analysieren, Seitenaufrufe pruefen oder
  Conversion-Reports erstellen will. Auch aktiv verwenden wenn der User sagt
  "wie viele Besucher", "Traffic letzte Woche", "Top-Seiten", "Analytics",
  "GA4 Report", o.ae.
  Trigger: /google-analytics, /ga4.
---

# google-analytics -- Google Analytics 4

GA4-Daten (Reports, Realtime, Conversions, Metadaten) werden ueber das gebundelte Script `google-analytics` (Python >=3.11, im Skill-Verzeichnis) abgefragt.

**Aufruf:** `python3 "$SKILL_DIR/google-analytics" <subcommand> [options]`

`$SKILL_DIR` ist das Base Directory dieses Skills (dort wo diese SKILL.md liegt).

## Setup

### Voraussetzungen

- Python-Package `cryptography` (fuer JWT-Signierung)
- Service Account JSON unter `~/.config/ga4-service-account.json`
  (oder Pfad via `GA4_SERVICE_ACCOUNT` Umgebungsvariable)
- Service Account muss als **Betrachter** in den GA4-Properties hinterlegt sein

### Erster Einsatz

```bash
python3 "$SKILL_DIR/google-analytics" setup
```

Das testet die Authentifizierung, listet alle zugaenglichen Accounts/Properties und schreibt `instance.json` ins Skill-Verzeichnis.

Falls `instance.json` nicht existiert, zuerst `setup` ausfuehren.

**Property-ID Lookup:** Zuerst `$SKILL_DIR/instance.json` per grep pruefen — dort stehen alle Properties mit ID und Name. Nur bei unbekannten Properties den `properties` Subcommand nutzen.

## Subcommands

### System

```bash
python3 "$SKILL_DIR/google-analytics" version
python3 "$SKILL_DIR/google-analytics" setup
```

### Accounts & Properties

```bash
# Alle Accounts
python3 "$SKILL_DIR/google-analytics" accounts

# Properties eines Accounts
python3 "$SKILL_DIR/google-analytics" properties --account 123456

# Alle Properties
python3 "$SKILL_DIR/google-analytics" properties
```

### Reports

```bash
# Standard-Report (letzte 7 Tage)
python3 "$SKILL_DIR/google-analytics" report -p 525022788

# Custom Dimensions und Metrics
python3 "$SKILL_DIR/google-analytics" report -p 525022788 \
  -d "pagePath,pageTitle" \
  -m "screenPageViews,averageSessionDuration" \
  -s "30daysAgo" -e "today"

# Top 10 Seiten nach Views, absteigend
python3 "$SKILL_DIR/google-analytics" report -p 525022788 \
  -d "pagePath" -m "screenPageViews" \
  -o "-screenPageViews" -l 10

# Traffic-Quellen
python3 "$SKILL_DIR/google-analytics" report -p 525022788 \
  -d "sessionSource,sessionMedium" -m "sessions,totalUsers"

# Filter: nur organischer Traffic
python3 "$SKILL_DIR/google-analytics" report -p 525022788 \
  -d "pagePath" -m "sessions" \
  -f "sessionMedium==organic"

# JSON-Ausgabe
python3 "$SKILL_DIR/google-analytics" report -p 525022788 --json
```

**Datumsformate:** `today`, `yesterday`, `NdaysAgo` (z.B. `30daysAgo`), oder `YYYY-MM-DD`.

**Haeufige Dimensionen:** `date`, `pagePath`, `pageTitle`, `landingPage`, `sessionSource`, `sessionMedium`, `sessionCampaignName`, `country`, `city`, `deviceCategory`, `browser`.

**Haeufige Metriken:** `sessions`, `totalUsers`, `newUsers`, `activeUsers`, `screenPageViews`, `engagementRate`, `averageSessionDuration`, `conversions`, `eventCount`, `totalRevenue`.

### Realtime

```bash
# Aktive User nach Land
python3 "$SKILL_DIR/google-analytics" realtime -p 525022788

# Custom Realtime
python3 "$SKILL_DIR/google-analytics" realtime -p 525022788 \
  -d "pagePath" -m "activeUsers"
```

### Metadata

```bash
# Alle verfuegbaren Dimensionen und Metriken einer Property
python3 "$SKILL_DIR/google-analytics" metadata -p 525022788

# Nur Metriken
python3 "$SKILL_DIR/google-analytics" metadata -p 525022788 -t metrics

# Suche
python3 "$SKILL_DIR/google-analytics" metadata -p 525022788 -s "page"
```

## Workflow

1. `instance.json` pruefen — falls nicht vorhanden, `setup` ausfuehren
2. Property-ID per grep in `instance.json` nachschlagen
3. Report/Realtime/Metadata Subcommand mit passenden Parametern ausfuehren
4. Bei unbekannten Dimensions/Metriken: `metadata` mit `--search` nutzen

## Hinweise

- Ausgabe ist Tab-separiert (fuer einfaches Weiterverarbeiten)
- `--json` liefert die rohe API-Antwort
- Datumsbereiche: `7daysAgo` bis `today` ist der Default
- Sortierung: `-feld` absteigend, `+feld` aufsteigend
- Filter: einfaches `dimension==wert` Format
- Realtime-Daten umfassen die letzten 30 Minuten
- Neue Properties: Service Account als Betrachter in GA4 hinzufuegen
  (analytics.google.com → Verwaltung → Property-Zugriffsverwaltung)
