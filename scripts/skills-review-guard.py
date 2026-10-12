#!/usr/bin/env python3
"""PreToolUse-Guard: vor einem Commit in azedo-skills die Anthropic-Regeln prüfen lassen.

Blockiert `git commit` im Repo azedo-skills, solange geänderte Dateien in einem
Skill-Verzeichnis liegen und der Befehl kein SKILL_REVIEW_OK trägt. Die
Begründung enthält die Checkliste der Regeln, die ein Script nicht prüfen kann;
die mechanischen prüft der pre-commit-Hook (scripts/lint-skills.py).

Ausweg nach erfolgter Prüfung: `# SKILL_REVIEW_OK` an den Befehl hängen.
"""

import json
import os
import re
import subprocess
import sys

CHECKLISTE = """Vor dem Commit die geänderten Skills gegen die Anthropic-Regeln prüfen:

1. description: sagt was der Skill tut und wann er greift, mit wörtlichen Nutzerformulierungen; deckt die Änderung ab
2. Knapp: nur was Claude nicht ohnehin weiß, keine Grundlagen-Erklärungen
3. Ein Standardweg statt mehrerer Optionen; Ausweichweg nur mit Bedingung
4. Begriffe, Schreibweise (echte Umlaute) und Vorlagen einheitlich - im Skill und gegenüber dem Wiki
5. Freiheitsgrad passend: fragile Abläufe als exakte Befehle, sonst Leitlinien
6. Keine zeitabhängigen Angaben, die veralten
7. Beispiele konkret, aber mit Platzhaltern statt Kunden- oder Infrastrukturdaten (Repo ist public)
8. Riskante Schritte mit Prüfschleife (Dry-Run, Backup, Bestätigung)
9. Progressive Disclosure: Details in references/, dort nur eine Ebene tief, Verweis aus SKILL.md

Ergebnis dem User kurz melden (Punkt für Punkt nur Abweichungen), dann den
Commit mit `# SKILL_REVIEW_OK` am Ende des Befehls wiederholen."""

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

if data.get("tool_name") not in (None, "Bash"):
    sys.exit(0)

cmd = (data.get("tool_input") or {}).get("command", "")
norm = re.sub(r"\s+", " ", re.sub(r"\\\s*\n", " ", cmd))

if not re.search(r"\bgit\b[^;&|]*\bcommit\b", norm) or "SKILL_REVIEW_OK" in norm:
    sys.exit(0)

# Arbeitsverzeichnis des Commits: git -C <dir>, sonst ein vorangestelltes cd <dir>, sonst cwd

m = re.search(r"\bgit -C (\S+)[^;&|]*\bcommit\b", norm) or re.search(r"\bcd (\S+) *(?:&&|;)", norm)
ziel = os.path.expanduser(m.group(1).strip("'\"")) if m else data.get("cwd") or os.getcwd()
if not os.path.isabs(ziel):
    ziel = os.path.join(data.get("cwd") or os.getcwd(), ziel)


def git(*args):
    return subprocess.run(["git", "-C", ziel, *args], capture_output=True, text=True).stdout


top = git("rev-parse", "--show-toplevel").strip()
if os.path.basename(top) != "azedo-skills":
    sys.exit(0)

# Alle Änderungen, auch noch nicht gestagte - oft steht das git add im selben Befehl

skills = set()
for zeile in git("status", "--porcelain").splitlines():
    pfad = zeile[3:].split(" -> ")[-1].strip('"')
    erstes = pfad.split("/", 1)[0]
    if "/" in pfad and os.path.isfile(os.path.join(top, erstes, "SKILL.md")):
        skills.add(erstes)

if not skills:
    sys.exit(0)

print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": f"Geänderte Skills: {', '.join(sorted(skills))}\n\n{CHECKLISTE}",
    }
}))
