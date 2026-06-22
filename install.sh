#!/bin/sh

# azedo-skills installer
# Legt Symlinks an und traegt Permissions in ~/.claude/settings.json ein.

set -e

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILLS_DIR="$HOME/.claude/skills"
SETTINGS="$HOME/.claude/settings.json"

# Symlinks anlegen
mkdir -p "$SKILLS_DIR"
for skill in kanboard kimai swaks image-optimize envato ripgrep php-formatting; do
    if [ -d "$REPO_DIR/$skill" ]; then
        if [ -e "$SKILLS_DIR/$skill" ]; then
            echo "  skip  $skill (existiert bereits)"
        else
            ln -s "$REPO_DIR/$skill" "$SKILLS_DIR/$skill"
            echo "  link  $skill"
        fi
    fi
done

# Permissions in settings.json eintragen
if ! command -v python3 >/dev/null 2>&1 && ! command -v python3.11 >/dev/null 2>&1; then
    echo ""
    echo "WARNUNG: python3 nicht gefunden. Permissions muessen manuell eingetragen werden."
    echo "Folgende Eintraege in $SETTINGS unter permissions.allow ergaenzen:"
    echo "  Read($HOME/.claude/azedo-skills/**)"
    echo "  Read(~/.claude/azedo-skills/**)"
    echo "  Write($HOME/.claude/azedo-skills/**)"
    echo "  Write(~/.claude/azedo-skills/**)"
    echo "  Read($HOME/.claude/skills/**)"
    echo "  Read(~/.claude/skills/**)"
    echo "  Write($HOME/.claude/skills/**)"
    echo "  Write(~/.claude/skills/**)"
    exit 0
fi

PYTHON="$(command -v python3.11 2>/dev/null || command -v python3)"

"$PYTHON" -c "
import json, os, sys

settings_path = os.path.expanduser('$SETTINGS')
home = os.path.expanduser('~')

needed = [
    'Bash(python3:*)',
    'Read(' + home + '/.claude/azedo-skills/**)',
    'Read(~/.claude/azedo-skills/**)',
    'Write(' + home + '/.claude/azedo-skills/**)',
    'Write(~/.claude/azedo-skills/**)',
    'Read(' + home + '/.claude/skills/**)',
    'Read(~/.claude/skills/**)',
    'Write(' + home + '/.claude/skills/**)',
    'Write(~/.claude/skills/**)',
]

if not os.path.exists(settings_path):
    data = {'permissions': {'allow': []}}
else:
    with open(settings_path) as f:
        data = json.load(f)

allow = data.setdefault('permissions', {}).setdefault('allow', [])

added = []
for perm in needed:
    if perm not in allow:
        allow.append(perm)
        added.append(perm)

if added:
    with open(settings_path, 'w') as f:
        json.dump(data, f, indent=2)
        f.write('\n')
    for p in added:
        print('  perm  ' + p)
    print('')
    print('Permissions eingetragen in ' + settings_path)
else:
    print('  Permissions bereits vorhanden.')
"

echo ""
echo "Fertig. Jetzt .env anlegen und setup ausfuehren:"
echo "  python3 \"\$SKILL_DIR/kanboard\" setup"
echo "  python3 \"\$SKILL_DIR/kimai\" setup"
