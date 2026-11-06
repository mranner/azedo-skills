#!/usr/bin/env python3

# stdlib only, no pip dependencies

"""
test-lint-wiki.py — Testfälle für die Präfix-Auflösung, die
Frontmatter-Verweise (references), die Abschnittsverweise, die verwaisten
Seiten, Aussagen zum Patch-Stand, die erlaubten Feldwerte (values), die
Ablösung (supersede), den Schrumpf-Guard (umgehängte Links) und die Sortierung
von log.md in lint-wiki.py.

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
    "types": {"artikel": [], "entscheidung": []},
    "references": {
        "tests": {"pattern": "def {name}\\b", "path": "tests"},
        "config": {"pattern": "\"{name}\"\\s*:", "path": "config/settings.json"},
        "doku": {"pattern": "{name}", "path": "gibt/es/nicht"},
    },
    "values": {"status": ["aktiv", "abgelöst"], "herkunft": ["benutzer", "agent"]},
    "supersede": {"types": ["entscheidung"], "status": "abgelöst", "field": "abgelöst_durch"},
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
    write(mathe / "wiki/patch-offen.md",
          "---\ntype: artikel\n---\n\nFür 7.4 gibt es kein Patch, nur Mitigation.\n")
    write(mathe / "wiki/patch-mit-ablauf.md",
          "---\ntype: artikel\nstale_after: 2099-01-01\n---\n\nKein Patch für 7.4.\n")
    write(mathe / "wiki/kein-update.md",
          "---\ntype: artikel\n---\n\nDer Server liefert kein Update aus, MSI-Tuning ist kein Fix.\n")
    write(mathe / "wiki/entscheidung-alt.md",
          "---\ntype: entscheidung\nstatus: abgelöst\nabgelöst_durch: \"[[entscheidung-neu]]\"\n"
          "herkunft: benutzer\n---\n\nText.\n")
    write(mathe / "wiki/entscheidung-neu.md",
          "---\ntype: entscheidung\nstatus: aktiv\nherkunft: agent\n---\n\nText.\n")
    write(mathe / "wiki/entscheidung-offen.md",
          "---\ntype: entscheidung\nstatus: abgelöst\nherkunft: schaetzung\n---\n\nText.\n")
    write(mathe / "wiki/artikel-abgeloest.md",
          "---\ntype: artikel\nstatus: abgelöst\n---\n\nText.\n")
    write(mathe / "index.md", "# Index\n\n- [[schriftliches-dividieren]]\n- [[grenzwert]]\n")

    # Wiki ohne values/supersede: dieselben Frontmatter-Werte bleiben still
    write(root / "wiki/physik/wiki-schema.json",
          json.dumps({"required_common": ["type"], "types": {"entscheidung": []}}))
    write(root / "wiki/physik/wiki/ohne-schema.md",
          "---\ntype: entscheidung\nstatus: abgelöst\nherkunft: schaetzung\n---\n\nText.\n")
    write(root / "wiki/physik/index.md", "# Index\n\n- [[ohne-schema]]\n")
    write(mathe / "log.md",
          "# Log\n\nNeueste zuerst.\n\n- [[geschichte:gibt-es-nicht]]\n\n"
          "## 2026-11-05\n\nA\n\n## 2026-10-01\n\nB\n\n## 2026-10-19\n\nC\n")
    write(root / "wiki/physik/log.md",
          "# Log\n\nÄlteste zuerst.\n\n## 2026-10-01\n\nA\n\n## 2026-10-19\n\nB\n")
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
    ("schriftliches-dividieren.md: Verwaiste Seite — kein anderer Artikel verlinkt hierher (nur aus index.md)", True),
    ("grenzwert.md: Verwaiste Seite", False),
    ("patch-offen.md: Aussage zum Patch-Stand (\"kein Patch\") ohne stale_after", True),
    ("patch-mit-ablauf.md: Aussage zum Patch-Stand", False),
    ("kein-update.md: Aussage zum Patch-Stand", False),
    ("entscheidung-alt.md: status", False),
    ("entscheidung-alt.md: Feld", False),
    ("entscheidung-neu.md: Feld", False),
    ("entscheidung-offen.md: status 'abgelöst' verlangt 'abgelöst_durch' mit Wikilink auf die Nachfolgerin", True),
    ("entscheidung-offen.md: Feld 'herkunft': Wert 'schaetzung' nicht erlaubt (erlaubt: benutzer, agent)", True),
    ("artikel-abgeloest.md: status", False),
    ("kein-update.md: Feld 'status'", False),
    ("log.md:15: ## 2026-10-19 steht nach ## 2026-10-01, das Log ist neueste zuerst sortiert", True),
    ("log.md:9:", False),
]

# Zweiter Lauf, Wiki ohne values/supersede: keine der neuen Meldungen
CASES_OHNE = [
    ("Artikel gesamt: 1", True),
    ("ohne-schema.md: status", False),
    ("ohne-schema.md: Feld", False),
    ("log.md:", False),
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
        ("log.md: ohne Angabe im Kopf gilt neueste zuerst",
         [n for n, _ in lint.check_log_order("# Log\n\n## 2026-01-01\n\n## 2026-02-01\n")] == [5]),
        ("log.md: aufsteigend laut Kopf, richtig sortiert, still",
         lint.check_log_order("# Log\n\nAufsteigend.\n\n## 2026-01-01\n\n## 2026-02-01\n") == []),
        ("log.md: Tagesüberschrift im Code-Block zählt nicht",
         lint.check_log_order("# Log\n\n## 2026-02-01\n\n```\n## 2026-03-01\n```\n") == []),
    ]


def main():
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp) / "home"
        wiki = build(Path(tmp) / "projekt", home)
        env = dict(os.environ, HOME=str(home))
        res = subprocess.run([sys.executable, str(LINT), str(wiki)],
                             capture_output=True, text=True, env=env)
        out = res.stdout
        res = subprocess.run([sys.executable, str(LINT), str(wiki.parent / "physik")],
                             capture_output=True, text=True, env=env)
        out_ohne = res.stdout

    failed = 0
    runs = [(needle, expected, out) for needle, expected in CASES]
    runs += [(needle, expected, out_ohne) for needle, expected in CASES_OHNE]
    for needle, expected, text in runs:
        found = needle in text
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

    total = len(runs) + len(extra)
    if failed:
        print(f"\n{failed} von {total} Fällen abweichend. Lint-Ausgabe:\n{out}\n{out_ohne}")
        return 1

    print(f"\nAlle {total} Fälle erfüllt.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
