#!/usr/bin/env python3

# stdlib only, no pip dependencies
# version 1.76.25

"""
rotate-log.py — lagert abgeschlossene Monate aus log.md nach log/YYYY-MM.md aus.

In log.md bleiben der Kopf und die Tagesabschnitte (## YYYY-MM-DD) des
laufenden Monats. Jeder ältere Monat wandert in seine eigene Datei unter
<wiki-root>/log/, in der Reihenfolge, die der Kopf von log.md nennt
("älteste zuerst"/"aufsteigend", sonst neueste zuerst). Gibt es die Monatsdatei
schon, kommen die Abschnitte in dieser Richtung dazu.

Aufruf: python3 rotate-log.py <wiki-root>
        z.B. python3 rotate-log.py wiki/azedo/   (relativ zum Projekt-Root)
"""

import re
import sys
from datetime import date
from pathlib import Path

DAY = re.compile(r"^## (\d{4}-\d{2})-\d{2}\b")
ASCENDING = re.compile(r"(?:älteste|aelteste)\s+zuerst|aufsteigend|oldest\s+first", re.I)


def split_log(text):
    """Zerlegt log.md in Kopf und Tagesabschnitte [(monat, text)]."""
    head = []
    sections = []
    in_fence = False
    for line in text.splitlines(keepends=True):
        if line.lstrip().startswith(("```", "~~~")):
            in_fence = not in_fence
        m = None if in_fence else DAY.match(line)
        if m:
            sections.append([m.group(1), line])
        elif sections:
            sections[-1][1] += line
        else:
            head.append(line)
    return "".join(head), sections


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    wiki_root = Path(sys.argv[1])
    log_file = wiki_root / "log.md"
    if not log_file.exists():
        print(f"FEHLER: {log_file} nicht gefunden")
        return 2

    head, sections = split_log(log_file.read_text(encoding="utf-8"))
    current = date.today().strftime("%Y-%m")
    ascending = bool(ASCENDING.search(head))

    keep = [text for month, text in sections if month == current]
    moved = {}
    for month, text in sections:
        if month != current:
            moved.setdefault(month, []).append(text)
    if not moved:
        print("Nichts zu rotieren.")
        return 0

    log_dir = wiki_root / "log"
    log_dir.mkdir(exist_ok=True)
    for month, texts in sorted(moved.items()):
        target = log_dir / f"{month}.md"
        new = "".join(texts).rstrip("\n") + "\n"
        if target.exists():
            old_head, old_sections = split_log(target.read_text(encoding="utf-8"))
            old = "".join(t for _, t in old_sections).rstrip("\n") + "\n"
            body = old + "\n" + new if ascending else new + "\n" + old
        else:
            old_head = f"# Operations Log {month}\n\n"
            body = new
        target.write_text(old_head + body, encoding="utf-8")
        print(f"{target}: {len(texts)} Tagesabschnitte")

    log_file.write_text(head + "".join(keep), encoding="utf-8")
    print(f"{log_file}: {len(keep)} Tagesabschnitte bleiben ({current})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
