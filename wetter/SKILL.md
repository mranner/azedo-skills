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
maximale Boeen; dazu 3-stuendliche Zeilen mit Temperatur, Zustand und Wind.
`--tage` steuert die Anzahl Tage (Standard 2).

### Nowcast (~3 h, 15-Minuten-Schritte)

```bash
python3 "$SKILL_DIR/wetter" nowcast <ort> [--json]
```

Nahzeitvorhersage `nowcast-v1-15min-1km` (1 km Raster): naechste ~3 Stunden
in 15-Minuten-Schritten mit Temperatur, Wind/Boeen und Niederschlag.

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
2. Passenden Subcommand waehlen: `forecast` (heute/morgen), `nowcast`
   (naechste Stunden), `warnungen` (Unwetter/Warnlage).
3. Ausgabe dem User lesbar zusammenfassen; bei Bedarf `--json` fuer Weiter-
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
- Warnungen enden mit ihrem Ablaufzeitpunkt; ist nichts aktiv, meldet der
  Skill "Keine aktiven Warnungen".
