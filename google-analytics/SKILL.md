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
- Service Account muss in den GA4-Properties hinterlegt sein: **Betrachter** genuegt fuer
  alle lesenden Subcommands, die schreibenden brauchen **Bearbeiter**
  (siehe [Schreibende Operationen: Rechte](#schreibende-operationen-rechte))

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
python3 "$SKILL_DIR/google-analytics" report -p 123123123

# Custom Dimensions und Metrics
python3 "$SKILL_DIR/google-analytics" report -p 123123123 \
  -d "pagePath,pageTitle" \
  -m "screenPageViews,averageSessionDuration" \
  -s "30daysAgo" -e "today"

# Top 10 Seiten nach Views, absteigend
python3 "$SKILL_DIR/google-analytics" report -p 123123123 \
  -d "pagePath" -m "screenPageViews" \
  -o "-screenPageViews" -l 10

# Traffic-Quellen
python3 "$SKILL_DIR/google-analytics" report -p 123123123 \
  -d "sessionSource,sessionMedium" -m "sessions,totalUsers"

# Filter: nur organischer Traffic
python3 "$SKILL_DIR/google-analytics" report -p 123123123 \
  -d "pagePath" -m "sessions" \
  -f "sessionMedium==organic"

# JSON-Ausgabe
python3 "$SKILL_DIR/google-analytics" report -p 123123123 --json
```

**Datumsformate:** `today`, `yesterday`, `NdaysAgo` (z.B. `30daysAgo`), oder `YYYY-MM-DD`.

**Haeufige Dimensionen:** `date`, `pagePath`, `pageTitle`, `landingPage`, `sessionSource`, `sessionMedium`, `sessionCampaignName`, `country`, `city`, `deviceCategory`, `browser`.

**Haeufige Metriken:** `sessions`, `totalUsers`, `newUsers`, `activeUsers`, `screenPageViews`, `engagementRate`, `averageSessionDuration`, `conversions`, `eventCount`, `totalRevenue`.

### Realtime

```bash
# Aktive User nach Land
python3 "$SKILL_DIR/google-analytics" realtime -p 123123123

# Custom Realtime
python3 "$SKILL_DIR/google-analytics" realtime -p 123123123 \
  -d "pagePath" -m "activeUsers"
```

### Metadata

```bash
# Alle verfuegbaren Dimensionen und Metriken einer Property
python3 "$SKILL_DIR/google-analytics" metadata -p 123123123

# Nur Metriken
python3 "$SKILL_DIR/google-analytics" metadata -p 123123123 -t metrics

# Suche
python3 "$SKILL_DIR/google-analytics" metadata -p 123123123 -s "page"
```

### Custom Dimensions

Event-Parameter sind ueber die Data API **nur** abfragbar, wenn sie als Custom Dimension
registriert sind — sonst liefert die Property nur Event-Name und Anzahl. Die
Registrierung wirkt **nicht rueckwirkend**: Daten vor der Anlage bleiben `(not set)`.
Abfragen erfolgen anschliessend als `customEvent:<parameter>` bzw. `customUser:<parameter>`.

```bash
# Registrierte Dimensionen anzeigen
python3 "$SKILL_DIR/google-analytics" list-custom-dimensions -p 123123123

# Dimension anlegen (Scope-Default: EVENT)
python3 "$SKILL_DIR/google-analytics" create-custom-dimension -p 123123123 \
  --parameter target_url --display-name "Klick Ziel" \
  [--description "…"] [--scope EVENT|USER|ITEM]
```

**`--display-name` erlaubt keine Bindestriche.** GA4 nimmt nur Buchstaben, Ziffern,
Unterstrich und Leerzeichen; alles andere quittiert die API mit

```
400 INVALID_ARGUMENT
Value for field display_name must only contain alphanumeric, underscore, or space characters.
```

Im Deutschen ist der Bindestrich die naheliegende Schreibweise, der Fehler trifft also
zuverlaessig beim ersten Versuch: „Klick-Ziel" wird abgelehnt, **„Klick Ziel" geht**. Das
Script prueft den Wert vorab und bricht mit einem Hinweis ab, bevor ein API-Aufruf
erfolgt. Betroffen ist nur der Anzeigename — `--parameter` ist davon unberuehrt (dort ist
der Unterstrich ohnehin ueblich).

`create-custom-dimension` prueft ausserdem vorab auf einen gleichnamigen Parameter im
selben Scope und meldet „Bereits vorhanden", statt einen API-Fehler zu produzieren —
mehrfaches Ausfuehren ist damit unschaedlich.

**Limit:** 50 event-scoped und 25 user-scoped Dimensionen pro Property (Standard-GA4).
Nichts registrieren, wofuer GA4 bereits eine Built-in-Dimension hat (`landingPage`,
`hour`, `dayOfWeek`, `month`, Campaign-/UTM-Dimensionen) — das belastet nur das Limit.
Parameter mit hoher Kardinalitaet (IDs, URLs mit Query-String) meiden, sonst greift die
Kardinalitaetsbegrenzung und die Werte landen in `(other)`.

### Datenaufbewahrung

```bash
# Aktuellen Stand anzeigen
python3 "$SKILL_DIR/google-analytics" data-retention -p 123123123

# Auf 14 Monate setzen
python3 "$SKILL_DIR/google-analytics" data-retention -p 123123123 --set 14
```

GA4 steht standardmaessig auf **2 Monate** — Explorations reichen dann nur zwei Monate
zurueck, unabhaengig von den Custom Dimensions. Erlaubte Werte: 2, 14 sowie 26/38/50
(letztere nur mit Analytics 360). Die Umstellung wirkt ebenfalls nur vorwaerts.

### Schreibende Operationen: Rechte

`create-custom-dimension` und `data-retention --set` fordern den Scope
`analytics.edit` an; alle uebrigen Subcommands bleiben auf `analytics.readonly`. Der
Service Account muss dafuer in der Property als **Bearbeiter** hinterlegt sein — als
*Betrachter* quittiert die API mit `403`. Rolle setzen unter GA4 → Verwaltung →
Property-Zugriffsverwaltung.

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
- Neue Properties: Service Account in GA4 hinzufuegen — als Betrachter, fuer schreibende
  Subcommands als Bearbeiter
  (analytics.google.com → Verwaltung → Property-Zugriffsverwaltung)
