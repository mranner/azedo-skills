#!/bin/sh

# azedo-skills installer
# Legt Symlinks an und traegt Permissions in ~/.claude/settings.json ein.

set -e

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILLS_DIR="$HOME/.claude/skills"
SETTINGS="$HOME/.claude/settings.json"

# Symlinks anlegen
mkdir -p "$SKILLS_DIR"
for skill in envato google-analytics google-search-console handoff humanizer-de image-optimize imap jira kanboard kimai mail-as-me mainwp md2pdf php-formatting pushover ripgrep swaks swos tcsh telegram wetter wiki wp-cli wp-nf wp-pys wp-sync-dev; do
    if [ -d "$REPO_DIR/$skill" ]; then
        target="$SKILLS_DIR/$skill"
        want="$REPO_DIR/$skill"
        if [ -L "$target" ]; then
            # Existierender Symlink: auf das aktuelle Repo-Ziel zeigen lassen
            if [ "$(readlink "$target")" = "$want" ]; then
                echo "  skip  $skill (Symlink aktuell)"
            else
                rm "$target"
                ln -s "$want" "$target"
                echo "  relink  $skill (Symlink neu gesetzt)"
            fi
        elif [ -e "$target" ]; then
            # Echtes Verzeichnis/Datei schattet den Repo-Skill (z.B. alte lokale
            # Kopie vor Aufnahme ins Repo) -> sichern und durch Symlink ersetzen.
            backup="$target.pre-azedo-skills"
            n=1
            while [ -e "$backup" ]; do backup="$target.pre-azedo-skills.$n"; n=$((n + 1)); done
            mv "$target" "$backup"
            ln -s "$want" "$target"
            echo "  replace  $skill (alte Version gesichert nach $(basename "$backup"))"
        else
            ln -s "$want" "$target"
            echo "  link  $skill"
        fi
    fi
done

# Git-Hook installieren: verlinkt neue Skills automatisch nach 'git pull'
# (post-merge fuer 'git pull', post-rewrite fuer 'git pull --rebase').
if git -C "$REPO_DIR" rev-parse --git-dir >/dev/null 2>&1; then
    HOOKS_DIR="$(cd "$REPO_DIR" && git rev-parse --absolute-git-dir)/hooks"
    mkdir -p "$HOOKS_DIR"
    HOOK_BODY="#!/bin/sh
# azedo-skills auto-link hook (erzeugt von install.sh)
# Verlinkt neue Skills automatisch nach 'git pull'.
sh \"$REPO_DIR/install.sh\" >/dev/null 2>&1 || true"
    for hook in post-merge post-rewrite; do
        HOOK_FILE="$HOOKS_DIR/$hook"
        if [ -e "$HOOK_FILE" ] && ! grep -q 'azedo-skills auto-link' "$HOOK_FILE" 2>/dev/null; then
            echo "  warn  $hook Hook existiert bereits (fremd) — nicht ueberschrieben"
        elif [ -e "$HOOK_FILE" ] && [ "$(cat "$HOOK_FILE")" = "$HOOK_BODY" ]; then
            echo "  skip  $hook Hook (aktuell)"
        else
            printf '%s\n' "$HOOK_BODY" > "$HOOK_FILE"
            chmod +x "$HOOK_FILE"
            echo "  hook  $hook installiert"
        fi
    done
fi

# Permissions in settings.json eintragen
if ! command -v python3 >/dev/null 2>&1; then
    echo ""
    echo "WARNUNG: python3 nicht gefunden. Permissions muessen manuell eingetragen werden."
    echo "Folgende Eintraege in $SETTINGS unter permissions.allow ergaenzen:"
    echo "  Read($HOME/.claude/azedo-skills/**)"
    echo "  Read(~/.claude/azedo-skills/**)"
    echo "  Edit($HOME/.claude/azedo-skills/**)"
    echo "  Edit(~/.claude/azedo-skills/**)"
    echo "  Read($HOME/.claude/skills/**)"
    echo "  Read(~/.claude/skills/**)"
    echo "  Edit($HOME/.claude/skills/**)"
    echo "  Edit(~/.claude/skills/**)"
    echo "(Falls noch alte Write(...)-Regeln fuer diese Pfade drinstehen: entfernen —"
    echo " Write(path) wird ignoriert, Edit(path) deckt alle Datei-Tools ab.)"
    exit 0
fi

PYTHON="$(command -v python3)"

"$PYTHON" -c "
import json, os, sys

settings_path = os.path.expanduser('$SETTINGS')
home = os.path.expanduser('~')

needed = [
    'Bash(python3:*)',
    'Read(' + home + '/.claude/azedo-skills/**)',
    'Read(~/.claude/azedo-skills/**)',
    'Edit(' + home + '/.claude/azedo-skills/**)',
    'Edit(~/.claude/azedo-skills/**)',
    'Read(' + home + '/.claude/skills/**)',
    'Read(~/.claude/skills/**)',
    'Edit(' + home + '/.claude/skills/**)',
    'Edit(~/.claude/skills/**)',
]

# Fruehere Versionen trugen fuer diese Pfade Write(...)-Regeln ein. Die File-
# Permission-Checks matchen Write(path) nicht (nur Edit(path) deckt alle
# Datei-Tools ab) -> Claude Code warnt bei jedem Laden. Daher hier mit-entfernen.
obsolete = [
    'Write(' + home + '/.claude/azedo-skills/**)',
    'Write(~/.claude/azedo-skills/**)',
    'Write(' + home + '/.claude/skills/**)',
    'Write(~/.claude/skills/**)',
]

if not os.path.exists(settings_path):
    data = {'permissions': {'allow': []}}
else:
    with open(settings_path) as f:
        data = json.load(f)

allow = data.setdefault('permissions', {}).setdefault('allow', [])

removed = [p for p in allow if p in obsolete]
if removed:
    allow[:] = [p for p in allow if p not in obsolete]

added = []
for perm in needed:
    if perm not in allow:
        allow.append(perm)
        added.append(perm)

if added or removed:
    with open(settings_path, 'w') as f:
        json.dump(data, f, indent=2)
        f.write('\n')
    for p in removed:
        print('  drop  ' + p + ' (obsolet: Write wird ignoriert)')
    for p in added:
        print('  perm  ' + p)
    print('')
    print('Permissions aktualisiert in ' + settings_path)
else:
    print('  Permissions bereits aktuell.')
"

echo ""
echo "Fertig. Jetzt .env anlegen und setup ausfuehren:"
echo "  python3 \"\$SKILL_DIR/kanboard\" setup"
echo "  python3 \"\$SKILL_DIR/kimai\" setup"
