---
name: image-optimize
description: >
  Optimiert Bilder fuer Web-Verwendung: Dateigroesse reduzieren (optipng, jpegoptim),
  Aufloesung anpassen (GraphicsMagick), Dateinamen SEO-freundlich umbenennen.
  Nutze diesen Skill wenn der User Bilder optimieren, verkleinern, komprimieren
  oder fuer eine Website aufbereiten will.
  Auch aktiv verwenden wenn der User sagt "Bilder fuer Web optimieren",
  "Bilder komprimieren", "Dateinamen anpassen", o.ae.
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
| `gm`             | `pkg install GraphicsMagick` | Resize/Skalierung |

`optipng` und `jpegoptim` sind Pflicht, `gm` wird nur fuer Resize benoetigt.

## Subcommands

### analyze -- Bilder pruefen

Analysiert Bilder und meldet Optimierungspotenzial (Aufloesung, Dateigroesse, Dateiname).

```bash
python3 "$SKILL_DIR/image-optimize" analyze <files-or-dirs...>
```

**Wichtig:** Wenn die Analyse ergibt, dass die Aufloesung fuer Web-Verwendung zu hoch ist (ueber 1920px), den User fragen ob skaliert werden soll, bevor resize ausgefuehrt wird.

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
| `--dry-run`    | Nur anzeigen, nichts aendern       | -       |

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
| `--rename`   | Dateien auch umbenennen              | -       |
| `--dry-run`  | Nur anzeigen, nichts aendern         | -       |

## Ablauf bei Bildoptimierung

1. Immer zuerst `analyze` ausfuehren, um den Zustand zu pruefen.
2. Wenn Aufloesung zu hoch: **User fragen** ob skaliert werden soll und auf welche Groesse.
3. `optimize` oder `web` ausfuehren.
4. Bei Rename: immer zuerst `--dry-run` zeigen, dann mit `--yes` bestaetigen lassen.
5. Verzeichnisse koennen direkt uebergeben werden — das Script findet alle Bilddateien darin.

## Hinweise

- Alle Subcommands akzeptieren sowohl einzelne Dateien als auch Verzeichnisse.
- JPEG-Optimierung entfernt EXIF-Daten (`--strip-all`).
- PNG-Optimierung ist verlustfrei.
- Resize ueberschreibt standardmaessig das Original (`--output <verzeichnis>/` nutzen, um die Originale zu behalten).
- Unterstuetzte Formate: PNG, JPEG, GIF, WebP, BMP, TIFF.
