---
name: google-analytics
description: >
  Google Analytics 4: Accounts, Properties, Traffic-Reports, Realtime-Daten,
  Conversions und Metadaten abfragen; Properties und Web-Datenstreams anlegen,
  Messungs-IDs auslesen. Nutze diesen Skill wenn der User GA4-Daten auswerten,
  Traffic analysieren, Seitenaufrufe pruefen, Conversion-Reports erstellen oder
  eine neue Site in GA4 einrichten will. Auch aktiv verwenden wenn der User sagt
  "wie viele Besucher", "Traffic letzte Woche", "Top-Seiten", "Analytics",
  "GA4 Report", "leg eine GA4-Property an", "welche Messungs-ID", o.ae.
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

### Property-Details und Datenstreams

```bash
# Anzeigename, Zeitzone, Währung, Branche, Account
python3 "$SKILL_DIR/google-analytics" property-info -p 123123123

# Datenstreams mit Messungs-ID (G-…) und URL
python3 "$SKILL_DIR/google-analytics" list-streams -p 123123123
```

### Property und Web-Stream anlegen

```bash
# Property mit expliziten Werten
python3 "$SKILL_DIR/google-analytics" create-property --account 123456 \
  --display-name "Beispiel" --time-zone Europe/Vienna --currency EUR \
  [--industry NON_PROFIT]

# Zeitzone, Währung und Branche von einer bestehenden Property übernehmen
python3 "$SKILL_DIR/google-analytics" create-property --account 123456 \
  --display-name "Beispiel" --like 123123123

# Web-Stream in der neuen Property, liefert die Messungs-ID
python3 "$SKILL_DIR/google-analytics" create-web-stream -p 123123123 \
  --url https://example.org --display-name "Beispiel"
```

Explizite Angaben gewinnen gegen `--like`. Ohne `--like` sind `--time-zone`
(IANA, z.B. `Europe/Vienna`) und `--currency` (ISO 4217) Pflicht; die Branche
ist ein Enum-Wert der API (`industryCategory`, z.B. `NON_PROFIT`,
`PEOPLE_AND_SOCIETY`) und wird von der API geprüft.

`create-property` prüft vorab auf eine gleichnamige Property im selben Account
und meldet „Bereits vorhanden" samt ID, statt eine zweite anzulegen - GA4 selbst
lässt Duplikate zu. `create-web-stream` prüft das **nicht**: Ein zweiter Aufruf
legt einen zweiten Stream mit eigener Messungs-ID an, vorher `list-streams`.

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

`create-custom-dimension`, `data-retention --set`, `create-property` und
`create-web-stream` fordern den Scope `analytics.edit` an; alle uebrigen
Subcommands bleiben auf `analytics.readonly`. Der Service Account muss dafuer in
der Property als **Bearbeiter** hinterlegt sein — als *Betrachter* quittiert die
API mit `403`. Rolle setzen unter GA4 → Verwaltung → Property-Zugriffsverwaltung.

**`create-property` braucht die Bearbeiter-Rolle auf Ebene des Accounts**
(Verwaltung → Kontozugriffsverwaltung), weil die neue Property noch keine
eigene Zugriffsliste hat. Rechte, die nur je Property vergeben sind, reichen
dafür nicht. Auf die neue Property erbt der Service Account die Kontorolle,
`create-web-stream` geht danach ohne weiteren Schritt.

## Workflow

### Abfragen

1. `instance.json` pruefen — falls nicht vorhanden, `setup` ausfuehren
2. Property-ID per grep in `instance.json` nachschlagen
3. Report/Realtime/Metadata Subcommand mit passenden Parametern ausfuehren
4. Bei unbekannten Dimensions/Metriken: `metadata` mit `--search` nutzen

### Neue Site einrichten

1. `create-property`, mit `--like` auf eine vergleichbare Property
2. `list-streams` auf der neuen Property, dann `create-web-stream` - liefert die
   Messungs-ID (`G-…`) für die Website
3. `data-retention --set 14` - eine neue Property steht auf 2 Monaten
4. Custom Dimensions anlegen, falls die Vorlage welche hat (`list-custom-dimensions`
   auf der Vorlage)
5. `setup`, damit `instance.json` die neue Property kennt

## Hinweise

- Ausgabe ist Tab-separiert (fuer einfaches Weiterverarbeiten)
- `--json` liefert die rohe API-Antwort
- Datumsbereiche: `7daysAgo` bis `today` ist der Default
- Sortierung: `-feld` absteigend, `+feld` aufsteigend
- Filter: einfaches `dimension==wert` Format
- Realtime-Daten umfassen die letzten 30 Minuten
