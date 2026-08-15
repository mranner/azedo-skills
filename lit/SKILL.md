---
name: lit
description: >
  Wandelt Dokumente mit dem lokalen CLI `lit` (liteparse) in Markdown, Text oder
  strukturiertes JSON um: PDF und Bilder direkt, Office-Formate (DOCX, XLSX, PPTX)
  über LibreOffice. Schnell, ohne Cloud und ohne ML-Modelle, mit optionalem
  Tesseract-OCR für Scans. Nutze diesen Skill, wenn der User eine Datei nach
  Markdown umwandeln will — "mach aus dem PDF eine MD-Datei", "wandle die Datei
  in Markdown um", "PDF nach Markdown", "konvertier das Dokument zu MD" — oder
  wenn er lit bzw. liteparse ausdrücklich nennt. Enthält auch die Installation
  auf FreeBSD, Linux und macOS. Trigger: /lit.
---

# lit — Dokumente nach Markdown

`lit` ist das CLI von [liteparse](https://github.com/run-llama/liteparse) (Rust,
Apache-2.0). Es extrahiert den Textlayer eines PDFs samt Struktur — Überschriften,
Listen, Tabellen, Links — und gibt Markdown, reinen Text oder JSON mit Bounding
Boxes aus. OCR (Tesseract) ist einkompiliert und wird nur bei Bedarf zugeschaltet.
Alles läuft lokal, es geht kein Dokument an einen Dienst.

**Vor dem ersten Aufruf prüfen, ob das Tool überhaupt da ist:**

```bash
command -v lit || echo "lit fehlt — siehe Abschnitt Installation"
```

Fehlt es und will der User nicht installieren, ist der Rückfallweg `pdftotext -layout`
(liefert Fließtext ohne Struktur) oder bei DOCX `pandoc -t markdown`.

## Der Standardfall

```bash
lit parse --no-ocr --format markdown -o bericht.md bericht.pdf
```

Ohne `-o` geht die Ausgabe nach stdout. Für ein PDF mit intaktem Textlayer dauert
das Millisekunden, nicht Sekunden.

## OCR: die wichtigste Entscheidung

`--no-ocr` ist der richtige Default. Fast jedes am Rechner erzeugte PDF hat einen
Textlayer, den `lit` verlustfrei ausliest; OCR kostet dann nur Zeit und macht das
Ergebnis **schlechter**. Beobachtet an einer bildlastigen Broschüre: ohne OCR
saubere `###`-Überschriften mit Listen darunter, mit OCR dieselbe Passage als
Tabelle mit Aufzählungszeichen-Artefakten (`| ® | Food - ... |`) plus Logo-Rauschen
wie `IMnaker`.

OCR nur zuschalten, wenn die Ausgabe leer oder erkennbar lückenhaft ist — also bei
Scans, bei Text in Grafiken und bei Bilddateien als Input:

```bash
# Sprache immer mitgeben, sonst rät es auf eng

lit parse --ocr-language deu --format markdown -o scan.md scan.pdf
```

**`is-complex` ist als Entscheidungshilfe unzuverlässig.** Bei besagter Broschüre
meldete es „COMPLEX — 14/14 page(s) need OCR", obwohl `--no-ocr` vollständigen Text
lieferte; die großen Bildflächen genügen ihm. Verlässlicher ist der direkte Weg:
erst `--no-ocr`, und nur wenn dabei wenig herauskommt, den OCR-Lauf hinterher.

Beim ersten Lauf einer Sprache **lädt `lit` die `traineddata` aus dem Netz nach**
(`~/.tesseract-rs/tessdata/`). Das erklärt eine erste Laufzeit von Sekunden bei
kaum CPU-Last. Auf Maschinen ohne ausgehendes Internet die Datei vorab ablegen und
`--tessdata-path` setzen. Das Dokument selbst verlässt die Maschine nie.

## Sparsam arbeiten: einmal parsen, dann die Datei durchsuchen

Gilt, wenn nicht die Markdown-Datei das Ziel ist, sondern eine Antwort aus dem
Dokument. `lit parse` extrahiert bei **jedem** Aufruf das ganze Dokument neu, und
jede Zeile, die in die Konversation wandert, wird in jeder weiteren Runde erneut
bezahlt. Also einmal in eine Datei unter `.tmp/` schreiben und alle Suchen dagegen
laufen lassen — nie zum Suchen erneut parsen.

```bash
lit parse --no-ocr --format text -o .tmp/doc.txt bericht.pdf && wc -l .tmp/doc.txt
```

Danach mit `grep -C` arbeiten, damit Fundstelle und Umgebung **in einem** Durchgang
zurückkommen, statt erst zu greppen und dann mit `sed` nachzulesen:

```bash
grep -n -i -C4 "Gesamtsumme" .tmp/doc.txt | head -40
```

Mehrere unabhängige Fragen in einem Befehl bündeln statt eine Runde je Begriff:

```bash
for q in "Rechnungsnummer" "Fälligkeit" "Steuersatz"; do
  echo "=== $q ==="; grep -n -i -C3 "$q" .tmp/doc.txt | head -25
done
```

Ausgabe immer mit `head` begrenzen. Wenn zwei gezielte Greps die Antwort nicht
finden, nicht weiter Stichwortvarianten durchprobieren — dann lieber die betroffene
Seite ansehen (nächster Abschnitt).

## Seiten als Bild — teuer, deshalb gezielt

Ein Seiten-PNG ist das Aufwendigste, was in den Kontext geraten kann. Nur wenn Text
und Tabellen die Frage wirklich nicht beantworten (Diagramme, dichte mehrspaltige
Tabellen, Formulare), und dann **eine** Seite bei moderater DPI:

```bash
lit screenshot --target-pages 13 --dpi 150 -o .tmp/shots/ bericht.pdf
```

Die Option heißt `--target-pages`, nicht `--pages`. Nicht dieselbe Seite nochmal in
höherer Auflösung rendern, solange die erste lesbar ist.

## Formate

| Input | Weg | Voraussetzung |
|---|---|---|
| PDF | direkt über pdfium | — |
| PNG, JPG … | direkt, immer über OCR | — |
| DOCX, XLSX, PPTX | Konvertierung nach PDF | **LibreOffice** |

Ohne LibreOffice bricht ein Office-Input hart ab:

```
Error: Conversion("LibreOffice is not installed. …")
```

Das ist kein Grund, LibreOffice zu installieren: für DOCX nach Markdown ist
`pandoc -t markdown` ohnehin die bessere Wahl, und XLSX gehört in ein
Tabellen-Werkzeug. `lit` lohnt bei Office-Dateien nur, wenn ihr **Layout** zählt.

## Optionen, die zählen

| Option | Zweck |
|---|---|
| `--format markdown\|text\|json` | Ausgabeformat, Default `text` |
| `--no-ocr` | OCR aus — der Normalfall |
| `--ocr-language <iso>` | `deu`, `eng`, … Default `eng` |
| `--target-pages "1-5,10"` | nur bestimmte Seiten |
| `-o <datei>` | Ausgabe in Datei statt stdout |
| `--image-mode off` | Bild-Platzhalter aus dem Markdown werfen |
| `--keep-headers-footers` | Kopf-/Fußzeilen behalten (Default: entfernt) |
| `--no-links` | Links als reinen Text statt `[text](url)` |
| `--password <pw>` | geschütztes PDF |
| `--extract-blocks` | Layout-Blöcke mit Bounding Boxes (nur JSON) |
| `-q` | Fortschrittsmeldungen unterdrücken |

`--format json` nur nehmen, wenn Koordinaten oder Blockstruktur gebraucht werden —
die Ausgabe ist um ein Vielfaches größer und gehört ebenfalls in eine Datei, nicht
in den Kontext.

Für ganze Verzeichnisse gibt es `lit batch-parse <input-dir> <output-dir>`
(`--recursive`, `--extension .pdf`).

## Fallstricke

**`| head` löst einen Panic aus.** `lit` behandelt SIGPIPE nicht und bricht mit
`failed printing to stdout: Broken pipe (os error 32)` ab, sobald der Leser früher
schließt. Die Ausgabe bis dahin stimmt, aber der Exit-Code ist ein Fehler — in
Scripts also `-o <datei>` verwenden und die Datei danach durchsuchen.

**`libpdfium` muss zur Binary-Version passen.** Sie wird per `dlopen` nachgeladen,
steht deshalb in keiner ELF-Abhängigkeit und liegt dem Release-Tarball **nicht** bei.
Fehlt sie, bricht jeder Aufruf ab:

```
failed to load pdfium shared library: … Set PDFIUM_LIB_PATH to the directory containing libpdfium.so
```

Die Builds von `bblanchon/pdfium-binaries` taugen dafür nicht — ab Chromium-Zweig
7999 exportieren sie `FPDFText_GetCharCode` nicht mehr, und der Aufruf scheitert
beim Symbol-Lookup statt beim Laden. Die passende Bibliothek steckt im PyPI-Wheel
derselben `lit`-Version (siehe Installation).

## Installation

Es gibt drei Bausteine: das Binary, die dazu passende pdfium-Bibliothek und einen
Wrapper, der `PDFIUM_LIB_PATH` setzt. Alles landet in `~/bin`, ohne Root.

Auf **Linux und macOS** geht auch `npm i -g @llamaindex/liteparse`, wenn Node 18+
vorhanden ist — dann entfällt der pdfium-Schritt, weil das npm-Paket die Bibliothek
mitbringt. Für **FreeBSD** gibt es kein Paket und keinen Port; dort ist der
Handaufbau unten der einzige Weg.

### Gemeinsam: Version und Plattform-Kürzel

Die Release-Tags tragen ein `node-`-Präfix, das Binary im Tarball heißt nach der
Plattform (`lit-linux-x64`, `lit-darwin-arm64`, …):

```bash
VER=2.13.0          # aktuelle Version: https://github.com/run-llama/liteparse/releases
PLAT=linux-x64      # oder darwin-arm64, darwin-x64, linux-arm64
mkdir -p ~/bin
```

### FreeBSD

Es gibt kein FreeBSD-Binary — das Linux-Binary läuft über den **Linuxulator**. Es ist
ein dynamisch gelinktes PIE gegen glibc, braucht also eine Linux-Basis; die üblichen
sieben Bibliotheken (`libc`, `libstdc++`, `libgcc_s`, `libm`, `libpthread`, `libdl`,
`ld-linux`) deckt `linux_base-rl9` ab. Tesseract wird **nicht** gebraucht, die
Engine ist einkompiliert.

```bash
# Linuxulator einmalig aktivieren

sudo pkg install linux_base-rl9
sudo sysrc linux_enable=YES
sudo service linux start
```

Danach der gemeinsame Teil:

```bash
fetch -o /tmp/lit.tgz \
  https://github.com/run-llama/liteparse/releases/download/node-v$VER/lit-$PLAT.tar.gz
tar xzf /tmp/lit.tgz -C /tmp
install -m 755 /tmp/lit-$PLAT ~/bin/lit.bin
```

### Linux

Identisch, nur mit `curl` statt `fetch`:

```bash
curl -sL -o /tmp/lit.tgz \
  https://github.com/run-llama/liteparse/releases/download/node-v$VER/lit-$PLAT.tar.gz
tar xzf /tmp/lit.tgz -C /tmp
install -m 755 /tmp/lit-$PLAT ~/bin/lit.bin
```

### macOS

Zusätzlich muss die Gatekeeper-Quarantäne weg, sonst weigert sich das Binary:

```bash
curl -sL -o /tmp/lit.tgz \
  https://github.com/run-llama/liteparse/releases/download/node-v$VER/lit-$PLAT.tar.gz
tar xzf /tmp/lit.tgz -C /tmp
install -m 755 /tmp/lit-$PLAT ~/bin/lit.bin
xattr -d com.apple.quarantine ~/bin/lit.bin
```

### pdfium aus dem Wheel holen (alle Plattformen)

Die Datei heißt `libpdfium.so` (FreeBSD/Linux) bzw. `libpdfium.dylib` (macOS) und
kommt aus dem PyPI-Wheel derselben Version. Die Wheel-URL ermittelt dieses Snippet,
damit man keinen Hash-Pfad abtippt:

```bash
# WHEELPLAT: manylinux_2_28_x86_64 | macosx_11_0_arm64 | macosx_10_12_x86_64

WHEELPLAT=manylinux_2_28_x86_64
python3 - "$VER" "$WHEELPLAT" <<'PY' > /tmp/wheel.url
import json, sys, urllib.request
ver, plat = sys.argv[1], sys.argv[2]
d = json.load(urllib.request.urlopen(f"https://pypi.org/pypi/liteparse/{ver}/json"))
print(next(f["url"] for f in d["urls"] if plat in f["filename"]))
PY

fetch -o /tmp/lp.whl "$(cat /tmp/wheel.url)"        # macOS/Linux: curl -sL -o
python3 -c "
import zipfile
z = zipfile.ZipFile('/tmp/lp.whl')
n = [x for x in z.namelist() if 'libpdfium' in x][0]
open('/tmp/' + n.split('/')[-1], 'wb').write(z.read(n))
print(n)
"
install -m 755 /tmp/libpdfium.* ~/bin/
```

Auf macOS auch hier `xattr -d com.apple.quarantine ~/bin/libpdfium.dylib`.

### Wrapper

Ohne ihn müsste bei jedem Aufruf `PDFIUM_LIB_PATH` gesetzt werden. Er leitet den
Pfad aus seinem eigenen Verzeichnis ab, das Verschieben von `~/bin` bleibt also
möglich:

```bash
cat > ~/bin/lit <<'EOF'
#!/usr/bin/env sh

# Wrapper für liteparse: libpdfium wird per dlopen nachgeladen und steht
# deshalb in keiner Abhängigkeit - ohne PDFIUM_LIB_PATH bricht jeder Aufruf ab.

BINDIR=$(cd "$(dirname "$0")" && pwd)

PDFIUM_LIB_PATH="$BINDIR"
export PDFIUM_LIB_PATH

exec "$BINDIR/lit.bin" "$@"
EOF
chmod 755 ~/bin/lit
lit --version
```

Liegt `~/bin` nicht im PATH, gehört es dort hinein — auf FreeBSD steht es meist
schon in der `default`-Klasse von `/etc/login.conf`.

### Update

Binary **und** pdfium gemeinsam ziehen, immer aus derselben Version. Driften sie
auseinander, scheitert der Symbol-Lookup — genau der Fehler, den die
bblanchon-Bibliothek auslöst.

## Quellen

- liteparse: <https://github.com/run-llama/liteparse> (Apache-2.0)
- Die Abschnitte zur Kontext-Disziplin folgen dem Upstream-Skill
  `run-llama/llamaparse-agent-skills`, `skills/liteparse/SKILL.md` (MIT).
