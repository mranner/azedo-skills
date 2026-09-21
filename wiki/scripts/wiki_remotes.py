#!/usr/bin/env python3

# stdlib only, no pip dependencies
# version 1.61.2

"""
wiki_remotes.py — Remote-Wiki-Konfiguration lesen und schreiben.

Konfigurationsquellen, in dieser Reihenfolge gemergt (spaetere gewinnen je Key):

1. ~/.claude/wiki-remotes.json          benutzerweit, gilt in jedem Projekt
2. <projekt-root>/.claude/wiki-remotes.json        projektlokal, eingecheckt
3. <projekt-root>/.claude/wiki-remotes.local.json  maschinenlokal

Der Dateiname traegt einen Unterstrich statt des sonst ueblichen Bindestrichs
(lint-wiki.py, audit-wiki.py): lint-wiki.py importiert load_remotes von hier,
und ein Modulname mit Bindestrich laesst sich nicht importieren.

Aufruf: python3 wiki_remotes.py list
        python3 wiki_remotes.py add <name> <host>:<pfad> [--home] [--force]
"""

import json
import os
import sys
from pathlib import Path

HOME_FILE = Path.home() / ".claude" / "wiki-remotes.json"
PROJECT_FILE = Path(".claude/wiki-remotes.json")
PROJECT_LOCAL_FILE = Path(".claude/wiki-remotes.local.json")


def remote_files(project_root):
    """Konfigurationsdateien in Merge-Reihenfolge, als (Herkunft, Pfad)."""
    project_root = Path(project_root)
    return [
        ("home", HOME_FILE),
        ("projekt", project_root / PROJECT_FILE),
        ("local", project_root / PROJECT_LOCAL_FILE),
    ]


def load_remotes(project_root, with_origin=False):
    """Laedt die bekannten Remote-Wikis aus allen drei Quellen.

    Fehlt alles → leeres Dict (dann ist jeder [[x:y]]-Link mit unbekanntem x
    ein toter Link). Kaputtes JSON wird still uebergangen, damit eine defekte
    Datei nicht den ganzen Lint-Lauf kippt.
    Gibt {name: {"host": ..., "path": ...}} zurueck, mit with_origin
    zusaetzlich {name: "home"|"projekt"|"local"}.
    """
    remotes = {}
    origin = {}
    for label, f in remote_files(project_root):
        if not f.exists():
            continue
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(data, dict):
            continue
        remotes.update(data)
        for name in data:
            origin[name] = label
    return (remotes, origin) if with_origin else remotes


def cmd_list(project_root):
    """Bekannte Remotes mit Herkunft ausgeben."""
    remotes, origin = load_remotes(project_root, with_origin=True)

    for label, f in remote_files(project_root):
        print(f"{label:8} {f}{'' if f.exists() else '   (fehlt)'}")
    print()

    if not remotes:
        print("Keine Remote-Wikis konfiguriert.")
        return 0

    width = max(len(n) for n in remotes)
    for name in sorted(remotes):
        conf = remotes[name]
        target = f"{conf.get('host', '?')}:{conf.get('path', '?')}"
        print(f"{name:{width}}  {target}  [{origin[name]}]")
    return 0


def cmd_add(project_root, name, target, home=False, force=False):
    """Einen Remote in die Projekt- oder Home-Datei schreiben."""
    if ":" not in target:
        print(f"FEHLER: Ziel '{target}' ist kein <host>:<pfad>")
        return 2
    host, path = target.split(":", 1)
    if not host or not path:
        print(f"FEHLER: Ziel '{target}' ist kein <host>:<pfad>")
        return 2

    f = HOME_FILE if home else Path(project_root) / PROJECT_FILE
    data = {}
    if f.exists():
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            print(f"FEHLER: {f} ist nicht lesbar ({exc})")
            return 1
        if not isinstance(data, dict):
            print(f"FEHLER: {f} enthaelt kein JSON-Objekt")
            return 1

    if name in data and not force:
        print(f"FEHLER: '{name}' steht schon in {f}: "
              f"{data[name].get('host')}:{data[name].get('path')}")
        print("Mit --force ueberschreiben.")
        return 1

    data[name] = {"host": host, "path": path, "readonly": True}
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                 encoding="utf-8")
    print(f"{name} → {host}:{path}  geschrieben nach {f}")

    # Ein projektlokaler Eintrag verdeckt den gleichnamigen aus dem Home; ein
    # Home-Eintrag umgekehrt nie einen projektlokalen. Beides ist gewollt, aber
    # nur, wenn es jemand weiss.
    others = load_remotes(project_root, with_origin=True)[1].get(name)
    if others and others != ("home" if home else "projekt"):
        print(f"Hinweis: '{name}' wird effektiv aus '{others}' gelesen.")
    return 0


def main():
    args = sys.argv[1:]
    home = "--home" in args
    force = "--force" in args
    args = [a for a in args if a not in ("--home", "--force")]
    project_root = Path(os.getcwd())

    if args and args[0] == "list" and len(args) == 1:
        return cmd_list(project_root)
    if args and args[0] == "add" and len(args) == 3:
        return cmd_add(project_root, args[1], args[2], home=home, force=force)

    print(f"Aufruf: {sys.argv[0]} list")
    print(f"        {sys.argv[0]} add <name> <host>:<pfad> [--home] [--force]")
    print("  --home:  nach ~/.claude/wiki-remotes.json statt ins Projekt")
    print("  --force: bestehenden Eintrag ueberschreiben")
    return 2


if __name__ == "__main__":
    sys.exit(main())
