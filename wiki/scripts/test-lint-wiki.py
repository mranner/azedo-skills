#!/usr/bin/env python3

# stdlib only, no pip dependencies

"""
test-lint-wiki.py — Testfaelle fuer die Praefix-Aufloesung in lint-wiki.py.

Baut ein Wegwerf-Projekt mit zwei Geschwister-Wikis, einem Verzeichnis ohne
wiki/-Unterordner und einer wiki-remotes.json, laesst lint-wiki.py darauf laufen
und vergleicht die Meldungen zu Wikilinks mit der Erwartung.

Aufruf: python3 test-lint-wiki.py
Exit 0 = alle Faelle erfuellt, 1 = Abweichung (wird ausgegeben).
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

LINT = Path(__file__).resolve().parent / "lint-wiki.py"

SCHEMA = {"required_common": ["type"], "types": {"artikel": []}}


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build(root):
    """Legt das Testprojekt an und gibt den Pfad des zu pruefenden Wikis zurueck."""

    # Nachbar-Wiki mit genau einem Artikel
    write(root / "wiki/geschichte/wiki/franzoesische-revolution.md",
          "---\ntype: artikel\n---\n\nText.\n")

    # Zweites Nachbar-Wiki, bewusst NICHT in wiki-remotes.json: nur die lokale
    # Aufloesung kann diesen Link gueltig machen.
    write(root / "wiki/biologie/wiki/zellteilung.md",
          "---\ntype: artikel\n---\n\nText.\n")

    # Verzeichnis ohne wiki/-Unterordner — darf kein Praefix aufloesen
    write(root / "wiki/notizen/README.md", "Kein Wiki.\n")

    # 'geschichte' steht zusaetzlich als Remote drin: lokal muss gewinnen,
    # sonst bliebe der fehlende Slug unbemerkt.
    write(root / ".claude/wiki-remotes.json", json.dumps({
        "fern": {"host": "example.org", "path": "/srv/wiki"},
        "geschichte": {"host": "example.org", "path": "/srv/geschichte"},
    }))

    mathe = root / "wiki/mathe"
    write(mathe / "wiki-schema.json", json.dumps(SCHEMA))
    write(mathe / "wiki/schriftliches-dividieren.md",
          "---\ntype: artikel\n---\n\n"
          "Lokal vorhanden, nicht als Remote bekannt: [[biologie:zellteilung]].\n"
          "Lokal vorhanden, auch als Remote bekannt: [[geschichte:franzoesische-revolution]].\n"
          "Lokal fehlend: [[geschichte:gibt-es-nicht]].\n"
          "Kein Wiki-Verzeichnis: [[notizen:irgendwas]].\n"
          "Unbekanntes Praefix: [[fremd:irgendwas]].\n"
          "Bekannter Remote: [[fern:egal]].\n")
    write(mathe / "index.md", "# Index\n\n- [[schriftliches-dividieren]]\n")
    write(mathe / "log.md", "# Log\n\n- [[geschichte:gibt-es-nicht]]\n")
    return mathe


# (Meldungsteil, muss vorkommen ja/nein)
CASES = [
    ("Toter Wikilink [[biologie:zellteilung]]", False),
    ("Toter Wikilink [[geschichte:franzoesische-revolution]]", False),
    ("Toter Wikilink [[fern:egal]]", False),
    ("schriftliches-dividieren.md: Toter Wikilink [[geschichte:gibt-es-nicht]] — Ziel existiert nicht im Wiki 'geschichte'", True),
    ("schriftliches-dividieren.md: Toter Wikilink [[notizen:irgendwas]] — Ziel existiert nicht", True),
    ("schriftliches-dividieren.md: Toter Wikilink [[fremd:irgendwas]] — Ziel existiert nicht", True),
    ("log.md: Toter Wikilink [[geschichte:gibt-es-nicht]] — Ziel existiert nicht im Wiki 'geschichte'", True),
]


def main():
    with tempfile.TemporaryDirectory() as tmp:
        wiki = build(Path(tmp))
        res = subprocess.run([sys.executable, str(LINT), str(wiki)],
                             capture_output=True, text=True)
        out = res.stdout

    failed = 0
    for needle, expected in CASES:
        found = needle in out
        ok = found == expected
        if not ok:
            failed += 1
        verdict = "OK  " if ok else "FAIL"
        wanted = "erwartet" if expected else "nicht erwartet"
        print(f"{verdict} [{wanted}] {needle}")

    if failed:
        print(f"\n{failed} von {len(CASES)} Faellen abweichend. Lint-Ausgabe:\n{out}")
        return 1

    print(f"\nAlle {len(CASES)} Faelle erfuellt.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
