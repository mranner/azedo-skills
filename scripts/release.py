#!/usr/bin/env python3

"""Zieht ein Release in einem Lauf nach: VERSION hochzählen, Eintrag oben in
CHANGELOG.md, Changelog-Abschnitt im README ersetzen, `# version`-Zeilen der
Scripts angleichen.

Aufruf im Repo-Wurzelverzeichnis:
    python3 scripts/release.py --entry <datei> [--minor]

<datei> enthält nur den Text des Eintrags (Aufzählung), ohne Überschrift.
Patch-Bump ist der Default, --minor nur bei wesentlich neuer Fähigkeit."""

import argparse
import os
import re
import sys

TOP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Ganze Zeile als Versionsnummer: ein lockeres `^# version .*` traf auch einen
# Kommentar, der mit dem Wort "version" begann. Kein Filter nach Endung, sonst
# fallen die Scripts ohne Endung (kanboard, imap, ...) durch.

KOPF = re.compile(r"^# version \d+\.\d+\.\d+$", re.M)


def lesen(name):
    with open(os.path.join(TOP, name), encoding="utf-8") as f:
        return f.read()


def schreiben(name, text):
    with open(os.path.join(TOP, name), "w", encoding="utf-8") as f:
        f.write(text)


ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--entry", required=True, help="Datei mit dem Text des Eintrags")
ap.add_argument("--minor", action="store_true", help="Minor- statt Patch-Bump")
args = ap.parse_args()

with open(args.entry, encoding="utf-8") as f:
    text = f.read().strip()

if not text:
    sys.exit("Eintrag ist leer: " + args.entry)

major, minor, patch = map(int, lesen("VERSION").strip().split("."))
neu = "%d.%d.0" % (major, minor + 1) if args.minor else "%d.%d.%d" % (major, minor, patch + 1)
eintrag = "### %s\n\n%s\n\n" % (neu, text)

changelog = lesen("CHANGELOG.md")
i = changelog.find("\n### ")
if i == -1:
    sys.exit("CHANGELOG.md: kein bestehender Abschnitt '### <version>' gefunden")

readme = lesen("README.md")
m = re.search(r"^## Changelog\n.*?\n(### .*?)(?=^## |\Z)", readme, re.S | re.M)
if not m:
    sys.exit("README.md: Abschnitt '## Changelog' mit '### <version>' nicht gefunden")

schreiben("CHANGELOG.md", changelog[:i + 1] + eintrag + changelog[i + 1:])
schreiben("README.md", readme[:m.start(1)] + eintrag.rstrip("\n") + "\n" + ("\n" if readme[m.end(1):] else "") + readme[m.end(1):])
schreiben("VERSION", neu + "\n")

koepfe = []
for wurzel, verzeichnisse, dateien in os.walk(TOP):
    verzeichnisse[:] = [d for d in verzeichnisse if d not in (".git", "__pycache__")]
    for datei in dateien:
        pfad = os.path.join(wurzel, datei)
        try:
            with open(pfad, encoding="utf-8") as f:
                inhalt = f.read()
        except (UnicodeDecodeError, OSError):
            continue

        if KOPF.search(inhalt):
            with open(pfad, "w", encoding="utf-8") as f:
                f.write(KOPF.sub("# version " + neu, inhalt))
            koepfe.append(os.path.relpath(pfad, TOP))

print("Version %s: VERSION, CHANGELOG.md, README.md, %d Script-Köpfe" % (neu, len(koepfe)))
