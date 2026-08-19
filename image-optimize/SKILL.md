---
name: image-optimize
description: >
  Optimiert Bilder fuer Web-Verwendung: Dateigroesse reduzieren (optipng, jpegoptim),
  Aufloesung anpassen (GraphicsMagick), Format umwandeln (PNG/WebP nach JPEG inkl.
  Alpha-Flattening), Dateinamen SEO-freundlich umbenennen.
  Nutze diesen Skill wenn der User Bilder optimieren, verkleinern, komprimieren,
  in ein anderes Format umwandeln oder fuer eine Website aufbereiten will.
  Auch aktiv verwenden wenn der User sagt "Bilder fuer Web optimieren",
  "Bilder komprimieren", "PNG nach JPG umwandeln", "Dateinamen anpassen", o.ae.
  Trigger: /image-optimize.
---

# image-optimize -- Bildoptimierung fuer Web

Bilder werden ueber das gebundelte Script `image-optimize` (Python >=3.11, im Skill-Verzeichnis) optimiert.

**Aufruf:** `python3 "$SKILL_DIR/image-optimize" <subcommand> [options]`

`$SKILL_DIR` ist das Base Directory dieses Skills (dort wo diese SKILL.md liegt).

## Voraussetzungen

| Tool             | Paket (FreeBSD)       | Verwendung         |
|------------------|-----------------------|--------------------|
| `optipng`        | `pkg install optipng` | PNG-Optimierung    |
| `jpegoptim`      | `pkg install jpegoptim` | JPEG-Optimierung |
| `gm`             | `pkg install GraphicsMagick` | Resize, Formatumwandlung, Bildmasse |

`optipng` und `jpegoptim` sind Pflicht. Fuer `resize` und `convert` braucht es
einen Bildwandler: **GraphicsMagick (`gm`)** oder ersatzweise **ImageMagick 7
(`magick`)**. Fehlt beides, brechen diese beiden Subcommands mit klarer Meldung
ab - `analyze`, `optimize` und `rename` laufen weiter.

### Bildmasse: Werkzeug oder eingebauter Parser

Die Abmessungen kommen von `gm identify` bzw. `magick identify`. Ist keines von
beiden da, liest das Script sie **selbst aus dem Datei-Header** (stdlib
`struct`, kein Fremdtool) — unterstuetzt fuer PNG, JPEG, GIF, WebP, BMP und
TIFF. `analyze` schreibt in die erste Zeile, welche der beiden Quellen gerade
gilt.

**Nicht** verwendet wird dafuer `file(1)`: dessen Ausgabe nennt bei
JFIF-JPEGs die Density **vor** der Aufloesung -

```
JPEG image data, JFIF standard 1.01, ..., density 96x96, ..., 1024x768, components 3
```

- und ein Muster ueber die erste Zahlenpaarung liefert deshalb `96x96` statt
`1024x768`. Genau daran haengt aber die Entscheidung, ob skaliert werden muss:
mit `96x96` sieht jedes Bild klein genug aus und ein `resize` taete
stillschweigend nichts. Der Header-Parser liest bei JPEG den SOF-Marker und
ist damit von dieser Verwechslung frei.

Laesst sich die Groesse gar nicht bestimmen, meldet `analyze` `Dimensions:
unknown` samt Hinweis, und `resize`/`web` zaehlen die Datei als Fehlschlag -
statt sie stumm zu ueberspringen.

## Subcommands

### analyze -- Bilder pruefen

Analysiert Bilder und meldet Optimierungspotenzial (Aufloesung, Dateigroesse, Dateiname).

```bash
python3 "$SKILL_DIR/image-optimize" analyze <files-or-dirs...>
```

**Wichtig:** Wenn die Analyse ergibt, dass die Aufloesung fuer Web-Verwendung zu hoch ist (ueber 1920px), den User fragen ob skaliert werden soll, bevor resize ausgefuehrt wird.

Die Ausgabe beginnt mit `Measuring with: gm` bzw. `Measuring with: built-in
header parser`. Steht dort der Parser, sind `resize` und `convert` in dieser
Umgebung nicht verfuegbar.

### optimize -- Dateigroesse reduzieren

Optimiert PNG (verlustfrei via optipng) und JPEG (quality-basiert via jpegoptim). Veraendert die Aufloesung nicht.

```bash
# Standard (JPEG quality 85, optipng level 2)
python3 "$SKILL_DIR/image-optimize" optimize <files-or-dirs...>

# Mit Optionen
python3 "$SKILL_DIR/image-optimize" optimize <files-or-dirs...> \
  --quality 80 \
  --png-level 4 \
  --dry-run
```

| Option         | Beschreibung                        | Default |
|----------------|-------------------------------------|---------|
| `--quality`    | JPEG-Qualitaet (1-100)             | 85      |
| `--png-level`  | optipng Optimierungslevel (0-7)    | 2       |
| `--baseline`   | Baseline-JPEG statt progressiv     | -       |
| `--dry-run`    | Nur anzeigen, nichts aendern       | -       |

**JPEGs werden progressiv geschrieben** (`jpegoptim --all-progressive`). Bei
Fotos in Webgroesse faellt das Ergebnis damit meist etwas kleiner aus und baut
sich beim Laden angenehmer auf. `--baseline` schaltet zurueck.

Zu beachten: `jpegoptim` ersetzt eine Datei nur, wenn das Ergebnis **kleiner**
ist. Bei einem Bild, das progressiv groesser wuerde, bleibt die Datei deshalb
unveraendert (Meldung `Already optimal`) - und damit baseline. Das ist gewollt:
Bytes sparen geht vor Kodierungsart.

### resize -- Aufloesung anpassen

Skaliert Bilder auf maximale Abmessungen (Seitenverhaeltnis bleibt erhalten). Benoetigt GraphicsMagick (`gm`).

```bash
# Standard (max 1920x1920)
python3 "$SKILL_DIR/image-optimize" resize <files-or-dirs...>

# Eigene Dimensionen
python3 "$SKILL_DIR/image-optimize" resize <files-or-dirs...> \
  --width 1200 --height 800 \
  --quality 90 \
  --dry-run

# In ein Zielverzeichnis schreiben, Originale bleiben unangetastet
python3 "$SKILL_DIR/image-optimize" resize <files-or-dirs...> \
  --width 1200 --output .tmp/mail/
```

| Option       | Beschreibung                          | Default |
|--------------|---------------------------------------|---------|
| `--width`    | Maximale Breite in Pixel             | 1920    |
| `--height`   | Maximale Hoehe in Pixel              | 1920    |
| `--quality`  | Ausgabe-Qualitaet (1-100)            | 85      |
| `--output`   | Zielverzeichnis oder Zieldatei (sonst: Original ueberschreiben) | - |
| `--dry-run`  | Nur anzeigen, nichts aendern         | -       |

#### `--output`: Verzeichnis vs. Datei

`--output` nimmt beides, und die Unterscheidung faellt am Pfad:

- **Verzeichnis**: der Pfad existiert als Verzeichnis oder endet auf `/`. Die
  Ergebnisse landen dort unter ihrem **Originalnamen**; ein noch nicht
  existierendes Verzeichnis wird angelegt. Das ist der Normalfall bei mehreren
  Bildern.
- **Datei**: jeder andere Pfad. Nur mit **genau einer** Eingabedatei sinnvoll;
  bei mehreren bricht das Script mit Exit-Code 2 ab, statt still ein Bild nach
  dem anderen auf denselben Namen zu schreiben.

**Ohne `--output` werden die Originale ueberschrieben.** Bei fremdem Material
(Hersteller- und Kundenbilder) deshalb immer ein Zielverzeichnis angeben.

Bilder, die ohnehin klein genug sind, werden uebersprungen und dabei **nicht**
ins Zielverzeichnis kopiert. Das Verzeichnis enthaelt danach also nur die
tatsaechlich skalierten Dateien.

Schlaegt `gm` bei einer Datei fehl, laeuft der Rest weiter, am Ende steht die
Zahl der Fehlschlaege und der **Exit-Code ist 1**. Ein Durchlauf ohne Meldung und
mit Exit 0 heisst also wirklich, dass alles geschrieben wurde.

### convert -- Format umwandeln

Wandelt Bilder in ein anderes Format um. Braucht `gm` oder `magick`.

```bash
# PNG nach JPEG (Ergebnis landet neben dem Original)
python3 "$SKILL_DIR/image-optimize" convert <files-or-dirs...> --to jpg

# In ein Zielverzeichnis, mit eigener Qualitaet
python3 "$SKILL_DIR/image-optimize" convert <files-or-dirs...> \
  --to jpg --quality 82 --output .tmp/jpg/

# Original nach erfolgreicher Umwandlung entfernen
python3 "$SKILL_DIR/image-optimize" convert <files-or-dirs...> --to jpg --remove-source
```

| Option            | Beschreibung                                  | Default |
|-------------------|-----------------------------------------------|---------|
| `--to`            | Zielformat: `jpg`, `jpeg`, `png`, `webp`, `gif`, `tiff` | (Pflicht) |
| `--quality`       | Ausgabe-Qualitaet (1-100)                    | 85      |
| `--background`    | Hintergrund beim Flattening                  | white   |
| `--output`        | Zielverzeichnis oder Zieldatei               | neben dem Original |
| `--force`         | Vorhandene Zieldatei ueberschreiben          | -       |
| `--remove-source` | Quelldatei nach Erfolg loeschen              | -       |
| `--dry-run`       | Nur anzeigen, nichts aendern                 | -       |

#### Alpha-Flattening

JPEG kennt keinen Alphakanal. Beim Ziel `jpg`/`jpeg` wird Transparenz deshalb
zuerst auf einen Hintergrund gelegt (`-background white -flatten`). Ohne diesen
Schritt kommt der transparente Bereich **schwarz** heraus - sichtbar an einem
PNG mit freigestelltem Motiv, das sonst auf schwarzem Grund landet. Bei anderen
Zielformaten unterbleibt das Flattening, dort bleibt der Alphakanal erhalten.

#### Schutz vor Datenverlust

- **Quelle == Ziel** wird uebersprungen (z.B. `--to png` bei einer PNG-Datei),
  statt die Datei waehrend der Umwandlung zu ueberschreiben.
- **Vorhandene Zieldateien** werden uebersprungen; erst `--force` ueberschreibt.
- **Namenskollisionen innerhalb eines Laufs** (`foto.png` und `foto.tif` zielen
  beide auf `foto.jpg`) sind ein Fehler, nicht ein Ueberschreiben - auch mit
  `--force`. Die Meldung nennt beide beteiligten Dateien, der Exit-Code ist 1.
  `--force` gilt vorhandenen Dateien, nicht der eigenen Ausgabe des Laufs.
- **Das Original bleibt** standardmaessig liegen - `--remove-source` raeumt es
  weg, aber nur nach erfolgreicher Umwandlung.
- `--output` verhaelt sich wie bei `resize` (Verzeichnis vs. einzelne Datei,
  siehe oben); bei mehreren Bildern und einer Zieldatei bricht das Script mit
  Exit-Code 2 ab.

Schlaegt eine Umwandlung fehl, laeuft der Rest weiter, am Ende steht die Zahl
der Fehlschlaege und der **Exit-Code ist 1**.

### rename -- SEO-freundliche Dateinamen

Benennt Bilddateien um: Kleinschreibung, Umlaute aufloesen, Leerzeichen/Unterstriche zu Bindestrichen, Sonderzeichen entfernen.

```bash
# Vorschau (zeigt geplante Umbenennungen)
python3 "$SKILL_DIR/image-optimize" rename <files-or-dirs...> --dry-run

# Mit Praefix (z.B. fuer Kunden-/Projektbezug)
python3 "$SKILL_DIR/image-optimize" rename <files-or-dirs...> \
  --prefix "hotel-alpenblick" --dry-run

# Ausfuehren
python3 "$SKILL_DIR/image-optimize" rename <files-or-dirs...> --yes
```

| Option       | Beschreibung                          |
|--------------|---------------------------------------|
| `--prefix`   | Praefix fuer alle Dateinamen         |
| `--dry-run`  | Nur anzeigen, nicht umbenennen       |
| `--yes`      | Umbenennung ohne Rueckfrage          |

**Beispiele:**
- `Foto Büro (1).JPG` -> `foto-buero-1.jpg`
- `IMG_20240315_142233.jpg` -> `img-20240315-142233.jpg`
- Mit `--prefix hotel`: `IMG_001.jpg` -> `hotel-img-001.jpg`

### web -- Komplette Pipeline

Fuehrt alle Schritte in einem Durchgang aus: Resize (falls noetig) + Optimize + Rename-Vorschlag.

```bash
# Vorschau
python3 "$SKILL_DIR/image-optimize" web <files-or-dirs...> --dry-run

# Ausfuehren (ohne Rename)
python3 "$SKILL_DIR/image-optimize" web <files-or-dirs...>

# Ausfuehren mit Rename
python3 "$SKILL_DIR/image-optimize" web <files-or-dirs...> --rename

# Mit eigenen Dimensionen
python3 "$SKILL_DIR/image-optimize" web <files-or-dirs...> \
  --width 1200 --height 800 --quality 80 --rename
```

| Option       | Beschreibung                          | Default |
|--------------|---------------------------------------|---------|
| `--width`    | Maximale Breite                      | 1920    |
| `--height`   | Maximale Hoehe                       | 1920    |
| `--quality`  | JPEG-Qualitaet                       | 85      |
| `--baseline` | Baseline-JPEG statt progressiv       | -       |
| `--rename`   | Dateien auch umbenennen              | -       |
| `--dry-run`  | Nur anzeigen, nichts aendern         | -       |

Muesste ein Bild skaliert werden, es fehlt aber der Bildwandler, **bricht `web`
mit Exit-Code 1 ab** statt nur zu warnen. Sonst liefe die Pipeline scheinbar
erfolgreich durch und liesse ein zu grosses Bild zurueck.

## Ablauf bei Bildoptimierung

1. Immer zuerst `analyze` ausfuehren, um den Zustand zu pruefen.
2. Wenn Aufloesung zu hoch: **User fragen** ob skaliert werden soll und auf welche Groesse.
3. `optimize` oder `web` ausfuehren.
4. Bei Rename: immer zuerst `--dry-run` zeigen, dann mit `--yes` bestaetigen lassen.
5. Verzeichnisse koennen direkt uebergeben werden — das Script findet alle Bilddateien darin.
6. Soll ein einheitlicher Formatsatz entstehen (z.B. ein Foto-Export, in dem eine
   einzelne PNG steckt): erst `convert --to jpg`, dann `resize`/`optimize`.

## Hinweise

- Alle Subcommands akzeptieren sowohl einzelne Dateien als auch Verzeichnisse.
- JPEG-Optimierung entfernt EXIF-Daten (`--strip-all`).
- PNG-Optimierung ist verlustfrei.
- Resize ueberschreibt standardmaessig das Original (`--output <verzeichnis>/` nutzen, um die Originale zu behalten).
- `convert` legt das Ergebnis dagegen **neben** das Original und laesst dieses stehen.
- Unterstuetzte Formate: PNG, JPEG, GIF, WebP, BMP, TIFF.
- Von ImageMagick wird `magick` angesprochen, nie das in Version 7 abgekuendigte
  `convert` — letzteres warnt bei jedem Aufruf.
