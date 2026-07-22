# azedo-skills – Claude Context

Repo der azedo-Skills für Claude Code (GitHub: `mranner/azedo-skills`). Hier wird
entwickelt und gepusht; die Arbeitsrechner holen den Stand per `git pull`.

## Release-Workflow

Änderungen sind erst dann fertig, wenn sie beim Konsumenten ankommen. Zu jedem
Release gehören drei Dateien gemeinsam:

- `VERSION` — hochzählen (semver)
- `CHANGELOG.md` — neuer Abschnitt oben, absteigend nach Version
- `README.md` — führt nur die *aktuelle* Version, kein Verlauf

Commit-Konvention: `CR<id>: <skill> - <was geändert wurde> (<version>)`
Beispiel: `CR4426: swos - poe-voltage (poe.b i03) + gemeinsame Write-Basis (1.26.1)`

## Neuer Skill

Beim Anlegen eines neuen Skills **`install.sh` mitpflegen**: die Skill-Liste dort ist
hartcodiert. Fehlt der Name, bekommt eine frische Installation keinen Symlink und der
Skill existiert für den Konsumenten nicht — auf einer Maschine, die ihn schon per
Git-Hook verlinkt hat, fällt das nicht auf.

## Konsumenten-Seite (nicht hier, aber davon abhängig)

Auf den Arbeitsrechnern liegt ein Klon unter `~/.claude/azedo-skills/`, die einzelnen
Skills sind nach `~/.claude/skills/<name>` symverlinkt. `install.sh` richtet einen
Git-Hook ein, der neue Skills nach einem `git pull` automatisch verlinkt; Permissions
landen in `~/.claude/settings.json`. Heißt: gepusht wird hier, geholt wird dort per
`git pull` — dort wird nie editiert.

## Temporäre Dateien

`.tmp/` gehört **nicht** ins Repo. Die Skills weisen ihre Nutzer an, temporäre Dateien
ins Projekt-`.tmp/` zu legen; im Repo selbst darf davon nichts landen. Besonders heikel:
SwOS-`.swb`-Sicherungen enthalten das Switch-Passwort im Klartext — solche Dateien
niemals einchecken.
