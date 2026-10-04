#!/usr/bin/env python3

# stdlib only, no pip dependencies

"""
test-lint-wiki.py — Testfälle für die Präfix-Auflösung, die
Frontmatter-Verweise (references), die Abschnittsverweise und den
Schrumpf-Guard (umgehängte Links) in lint-wiki.py.

Baut ein Wegwerf-Projekt mit zwei Geschwister-Wikis, einem Verzeichnis ohne
wiki/-Unterordner und einer wiki-remotes.json, lässt lint-wiki.py darauf laufen
und vergleicht die Meldungen zu Wikilinks mit der Erwartung. Das Home wird auf
ein Wegwerf-Verzeichnis umgebogen: so wird der benutzerweite Fallback
(~/.claude/wiki-remotes.json) mitgeprüft, ohne dass die echte Datei des
Entwicklers in den Lauf hineinwirkt.

Aufruf: python3 test-lint-wiki.py
Exit 0 = alle Fälle erfüllt, 1 = Abweichung (wird ausgegeben).
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

LINT = Path(__file__).resolve().parent / "lint-wiki.py"

SCHEMA = {
    "required_common": ["type"],
    "types": {"artikel": []},
    "references": {
        "tests": {"pattern": "def {name}\\b", "path": "tests"},
        "config": {"pattern": "\"{name}\"\\s*:", "path": "config/settings.json"},
        "doku": {"pattern": "{name}", "path": "gibt/es/nicht"},
    },
}


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build(root, home):
    """Legt Testprojekt und Wegwerf-Home an, gibt das zu prüfende Wiki zurück."""

    # Nur im Home bekannt — prüft den benutzerweiten Fallback
    write(home / ".claude/wiki-remotes.json", json.dumps({
        "heim": {"host": "example.org", "path": "/srv/heim"},
    }))

    # Nachbar-Wiki mit genau einem Artikel
    write(root / "wiki/geschichte/wiki/franzoesische-revolution.md",
          "---\ntype: artikel\n---\n\nText.\n")

    # Zweites Nachbar-Wiki, bewusst NICHT in wiki-remotes.json: nur die lokale
    # Auflösung kann diesen Link gültig machen.
    write(root / "wiki/biologie/wiki/zellteilung.md",
          "---\ntype: artikel\n---\n\nText.\n")

    # Verzeichnis ohne wiki/-Unterordner — darf kein Präfix auflösen
    write(root / "wiki/notizen/README.md", "Kein Wiki.\n")

    # 'geschichte' steht zusätzlich als Remote drin: lokal muss gewinnen,
    # sonst bliebe der fehlende Slug unbemerkt.
    write(root / ".claude/wiki-remotes.json", json.dumps({
        "fern": {"host": "example.org", "path": "/srv/wiki"},
        "geschichte": {"host": "example.org", "path": "/srv/geschichte"},
    }))

    # Prüfqüllen für die Frontmatter-Verweise
    write(root / "tests/test_regeln.py",
          "def test_grenzwert():\n    pass\n\ndef test_grenzwert_hoch():\n    pass\n")
    write(root / "config/settings.json",
          json.dumps({"limits": {"grenzwert": 5.1}}))

    mathe = root / "wiki/mathe"
    write(mathe / "wiki-schema.json", json.dumps(SCHEMA))
    write(mathe / "wiki/schriftliches-dividieren.md",
          "---\ntype: artikel\n---\n\n"
          "Lokal vorhanden, nicht als Remote bekannt: [[biologie:zellteilung]].\n"
          "Lokal vorhanden, auch als Remote bekannt: [[geschichte:franzoesische-revolution]].\n"
          "Lokal fehlend: [[geschichte:gibt-es-nicht]].\n"
          "Kein Wiki-Verzeichnis: [[notizen:irgendwas]].\n"
          "Unbekanntes Präfix: [[fremd:irgendwas]].\n"
          "Bekannter Remote: [[fern:egal]].\n"
          "Remote nur aus dem Home: [[heim:egal]].\n"
          "Kurzform eines Abschnitts: [[grenzwert]], Abschnitt Epsilon.\n"
          "Umbrochener Name: [[grenzwert]], Abschnitt „Folgen\nund Reihen\".\n"
          "Nachgestellte Form: [[grenzwert]] (Delta-Abschnitt).\n"
          "Beschreibend, nicht geprüft: [[grenzwert]], Abschnitt zu `lim` in Folgen.\n")
    write(mathe / "wiki/grenzwert.md",
          "---\ntype: artikel\n"
          "tests: [test_grenzwert, test_umbenannt]\n"
          "config:\n  - grenzwert\n  - entfernt\n"
          "---\n\nText.\n\n## Epsilon-Umgebung\n\nText.\n")
    write(mathe / "index.md", "# Index\n\n- [[schriftliches-dividieren]]\n- [[grenzwert]]\n")
    write(mathe / "log.md", "# Log\n\n- [[geschichte:gibt-es-nicht]]\n")
    return mathe


# (Meldungsteil, muss vorkommen ja/nein)
CASES = [
    ("Toter Wikilink [[biologie:zellteilung]]", False),
    ("Toter Wikilink [[geschichte:franzoesische-revolution]]", False),
    ("Toter Wikilink [[fern:egal]]", False),
    ("Toter Wikilink [[heim:egal]]", False),
    ("schriftliches-dividieren.md: Toter Wikilink [[geschichte:gibt-es-nicht]] — Ziel existiert nicht im Wiki 'geschichte'", True),
    ("schriftliches-dividieren.md: Toter Wikilink [[notizen:irgendwas]] — Ziel existiert nicht", True),
    ("schriftliches-dividieren.md: Toter Wikilink [[fremd:irgendwas]] — Ziel existiert nicht", True),
    ("log.md: Toter Wikilink [[geschichte:gibt-es-nicht]] — Ziel existiert nicht im Wiki 'geschichte'", True),
    ("tests-Eintrag 'test_grenzwert' nicht gefunden", False),
    ("grenzwert.md: tests-Eintrag 'test_umbenannt' nicht gefunden in tests", True),
    ("config-Eintrag 'grenzwert' nicht gefunden", False),
    ("grenzwert.md: config-Eintrag 'entfernt' nicht gefunden in config/settings.json", True),
    ("wiki-schema.json: Prüfqülle für 'doku' fehlt: gibt/es/nicht", True),
    ("Abschnittsverweis [[grenzwert]] \"Epsilon\"", False),
    ("schriftliches-dividieren.md: Abschnittsverweis [[grenzwert]] \"Folgen und Reihen\"", True),
    ("schriftliches-dividieren.md: Abschnittsverweis [[grenzwert]] \"Delta\"", True),
    ("Abschnittsverweis [[grenzwert]] \"zu", False),
]


def shrink_cases():
    """Schrumpf-Guard direkt: umgehängter Link still, gelöschter gemeldet."""
    sys.path.insert(0, str(LINT.parent))
    import importlib.util
    spec = importlib.util.spec_from_file_location("lint_wiki", LINT)
    lint = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(lint)

    old = "---\ntype: artikel\n---\n\nSiehe [[alt]].\n\nAuch [[weg]].\n"
    new = "---\ntype: artikel\n---\n\nSiehe [[neu]].\n\nAuch nichts.\n"
    out = " ".join(lint.check_shrink(old, new))
    return [
        ("Schrumpf-Guard: umgehängter Link [[alt]] -> [[neu]] nicht gemeldet", "[[alt]]" not in out),
        ("Schrumpf-Guard: ersatzlos entfernter Link [[weg]] gemeldet", "[[weg]]" in out),
    ]


def main():
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp) / "home"
        wiki = build(Path(tmp) / "projekt", home)
        env = dict(os.environ, HOME=str(home))
        res = subprocess.run([sys.executable, str(LINT), str(wiki)],
                             capture_output=True, text=True, env=env)
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

    extra = shrink_cases()
    for label, ok in extra:
        if not ok:
            failed += 1
        print(f"{'OK  ' if ok else 'FAIL'} {label}")

    total = len(CASES) + len(extra)
    if failed:
        print(f"\n{failed} von {total} Fällen abweichend. Lint-Ausgabe:\n{out}")
        return 1

    print(f"\nAlle {total} Fälle erfüllt.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
