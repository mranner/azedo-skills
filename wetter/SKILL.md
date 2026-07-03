---
name: wetter
description: >
  GeoSphere Austria Wetterdaten fuer Oesterreich: Kurzfristvorhersage
  (AROME, stuendlich ~60 h), Nowcast (15-Minuten-Schritte, ~3 h) und
  aktive amtliche Wetterwarnungen. Nutze diesen Skill wenn der User
  das Wetter, die Vorhersage, den Regen/Wind oder Wetterwarnungen fuer
  einen Ort in Oesterreich wissen will. Auch aktiv verwenden bei
  "wie wird das Wetter in X", "regnet es morgen in X", "gibt es
  Wetterwarnungen fuer X".
  Trigger: /wetter.
---

# wetter -- GeoSphere Austria Wetter

Vorhersage, Nowcast und Warnungen werden ueber das gebundelte Script `wetter`
(Python >=3.11, stdlib only, im Skill-Verzeichnis) abgefragt.

**Aufruf:** `python3 "$SKILL_DIR/wetter" <subcommand> <ort> [options]`

`$SKILL_DIR` ist das Base Directory dieses Skills (dort wo diese SKILL.md liegt).

Keine Authentifizierung, kein API-Key noetig. Datenquelle: GeoSphere Austria
Data Hub (CC BY 4.0) und die amtliche Warn-API (warnungen.zamg.at).

## Standort

`<ort>` ist entweder ein **Ortsname** (wird via OpenStreetMap/Nominatim auf
Oesterreich beschraenkt geocodiert) oder **Koordinaten** als `lat,lon`:

```bash
python3 "$SKILL_DIR/wetter" forecast Graz
python3 "$SKILL_DIR/wetter" forecast 47.07,15.44
```

Bei mehrdeutigen oder nicht gefundenen Namen: Koordinaten angeben.

## Subcommands

### Stundenvorhersage (AROME, ~60 h)

```bash
python3 "$SKILL_DIR/wetter" forecast <ort> [--tage 1-3] [--json]
```

Stuendliche Werte des Modells `nwp-v1-1h-2500m` (2,5 km Raster), Horizont
ca. 60 Stunden. Ausgabe: pro Tag Min/Max-Temperatur, Niederschlagssumme,
maximale Boeen; dazu 3-stuendliche Zeilen mit Temperatur, relativer Feuchte
(`rF %`), Zustand und Wind. `--tage` steuert die Anzahl Tage (Standard 2).

Oben wird — wie im Nowcast — ein **aktueller Messwert** der naechsten
Favoritenstation angezeigt (echter Stationswert, siehe Nowcast-Abschnitt und
Hinweise). Im `--json` als `messwert`-Block.

### Nowcast (~3 h, 15-Minuten-Schritte)

```bash
python3 "$SKILL_DIR/wetter" nowcast <ort> [--json]
```

Nahzeitvorhersage `nowcast-v1-15min-1km` (1 km Raster): naechste ~3 Stunden
in 15-Minuten-Schritten mit Temperatur, relativer Feuchte (`rF %`),
Wind/Boeen und Niederschlag.

Zusaetzlich wird oben ein **aktueller Messwert** einer TAWES-Station
(`station/current/tawes-v1-10min`) angezeigt — Stationsname, Distanz,
Temperatur, Feuchte, Taupunkt und Wind. Das ist ein echter Messwert im
Gegensatz zu den interpolierten Modellwerten der 15-Minuten-Schritte.

Es werden **ausschliesslich Favoritenstationen** herangezogen (kuratierte
Liste, siehe unten). Von diesen wird die naechstgelegene mit **frischen** Daten
gewaehlt; veraltete Werte (aelter als 2 h) werden uebersprungen. Ist keine
Favoritenstation gesetzt oder liefert keine aktuelle Daten, laeuft der Nowcast
ohne Messwert-Header weiter. Im `--json` steht der Messwert als
`messwert`-Block.

### Stationen (Favoriten-Auswahl)

```bash
python3 "$SKILL_DIR/wetter" stations <ort> [--anzahl N] [--json]
```

Listet die naechstgelegenen TAWES-Stationen mit Distanz und aktuellem Messwert
(bzw. "keine aktuellen Daten"/"veraltet"). Dient zum Auswaehlen der Favoriten.
Favoriten sind mit `*` markiert. `--anzahl` steuert die Anzahl (Standard 8).

### Wetterwarnungen

```bash
python3 "$SKILL_DIR/wetter" warnungen <ort> [--json]
# Aliase: warn, warnings
```

Aktive amtliche Warnungen fuer die Gemeinde am angegebenen Punkt. Pro Warnung:
Typ (Sturm, Regen, Schnee, Glatteis, Gewitter, Hitze, Kaelte), Stufe (gelb/
orange/rot), Zeitraum sowie Text, Auswirkungen und Empfehlungen.

## Workflow

1. Ort aus der Anfrage ableiten (Name oder Koordinaten).
2. **Favoriten sicherstellen (nur bei `forecast`/`nowcast`):** Existiert
   `~/.claude/wetter-favorites.json` nicht, zuerst `stations <ort>` aufrufen,
   dem User die naechsten Stationen mit Distanz und Frische-Status zeigen und
   fragen, welche als Favoriten gespeichert werden sollen. Danach die Datei im
   dokumentierten Format anlegen (siehe Hinweise). Erst dann mit dem
   eigentlichen Subcommand fortfahren. Existiert die Datei bereits, diesen
   Schritt ueberspringen. (Bei `warnungen` entfaellt der Schritt — Warnungen
   nutzen keine Favoriten.)
3. Passenden Subcommand waehlen: `forecast` (heute/morgen), `nowcast`
   (naechste Stunden), `warnungen` (Unwetter/Warnlage).
4. Ausgabe dem User lesbar zusammenfassen; bei Bedarf `--json` fuer Weiter-
   verarbeitung.

## Hinweise

- Alle Zeiten werden in lokaler Zeit (Europe/Vienna) ausgegeben.
- Der Wetterzustand (wolkenlos/wolkig/... + Niederschlag) wird aus den
  dokumentierten Feldern **Bewoelkung (tcc)** und **Niederschlag** abgeleitet.
  GeoSphere publiziert keine numerische Legende fuer den rohen Symbol-Code
  `sy`; dieser wird nur im `--json`-Output mitgegeben, nicht interpretiert.
- Modellgebiet-Grenzen (bbox): Oesterreich und angrenzender Alpenraum.
  Koordinaten ausserhalb werden abgelehnt.
- Niederschlags-Summen der Vorhersage werden aus den akkumulierten Feldern
  (`rr_acc`/`rain_acc`/`snow_acc`) pro Intervall differenziert.
- Geocoding nutzt OpenStreetMap/Nominatim (Fair-Use, ein Request pro Ortsname).
  Fuer wiederholte Abfragen desselben Orts besser Koordinaten verwenden.
- **Favoritenstationen** liegen in `~/.claude/wetter-favorites.json`:
  ```json
  { "favorites": [
      { "id": "11238", "name": "Graz/Straßgang" },
      { "id": "11240", "name": "Graz-Thalerhof-Flughafen" } ] }
  ```
  Fehlt die Datei, wird sie beim ersten `forecast`/`nowcast`-Aufruf angelegt
  (siehe Workflow Schritt 2): `stations <ort>` auflisten, den User waehlen
  lassen, Datei schreiben. Bis dahin laeuft der Nowcast ohne Messwert-Header.
  Hintergrund: die naechste Station ist oft eine inoffizielle Messstelle ohne
  aktuelle Daten — deshalb eine kuratierte Liste statt "naechste Station".
- Der Messwert-Header im Nowcast fragt jede Favoritenstation einzeln ab (ein
  HTTP-Request pro Favorit), weil die current-API bei Mehr-Stationen-Requests
  auf einen gemeinsamen Zeitstempel ausrichtet und veraltete Stationen frische
  auf null ziehen wuerden. Die Distanz wird je Station mit ausgegeben.
- Warnungen enden mit ihrem Ablaufzeitpunkt; ist nichts aktiv, meldet der
  Skill "Keine aktiven Warnungen".
