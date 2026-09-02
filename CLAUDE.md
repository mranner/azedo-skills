# azedo-skills – Claude Context

Repo der azedo-Skills für Claude Code (GitHub: `mranner/azedo-skills`). Hier wird
entwickelt und gepusht; die Arbeitsrechner holen den Stand per `git pull`.

## Das Repo ist public

**Alles hier ist öffentlich lesbar — auch jede frühere Fassung über die
Commit-Historie.** Ein nachträglich entfernter Wert bleibt abrufbar; Löschen im
Arbeitsbaum ist kein Zurücknehmen.

Der Prüfmaßstab sind **Kunden- und Mitarbeiterdaten**. Der eigene Firmenname und
generische Funktionsadressen wie `claude@azedo.at` sind unkritisch und brauchen keine
Bereinigung - wer sie ersetzt, ändert Text ohne Gewinn. Folgendes gehört dagegen **nie**
in Skill-Dateien, Scripts, Beispiele, Kommentare, README oder Changelog:

- **Kunden** — Namen, Domains, Hostnames, Projekt-/Ticket-Keys, wwwuser, Jail-Namen,
  Pfade, Details zu deren Sicherheitsarchitektur (SSO, MFA-Produkt, Zugangswege)
- **Personen** — Klarnamen, Login-Namen, personenbezogene E-Mail-Adressen, accountIds,
  Aliase; eigene wie fremde. Auch Vornamen in Beispieltexten. Rollenadressen ohne
  Personenbezug sind davon nicht betroffen
- **Eigene Infrastruktur** — konkrete Hostnames, Jail- und Pfadstruktur, interne IPs,
  Whitelists, welcher Host welchen Dienst trägt. Nicht gemeint ist der Firmenname als
  solcher
- **Credentials jeder Art** — Tokens, API-Keys, Passwörter, Pushover-User-Keys,
  Backup-Dateien mit eingebetteten Geheimnissen (z.B. SwOS-`.swb`)
- **Konkrete Vorgangs-IDs** — Issue-Nummern, Kommentar-/Attachment-IDs

Stattdessen: Platzhalter (`example.org`, `example.at`, `<username>`, `<dev-host>`)
oder generische Beispiele (`Max Mustermann`, `Karin Musterfrau`). Was ein Skill zur
Laufzeit wirklich braucht, kommt aus einer **Config außerhalb der Repos**
(`~/.claude/<skill>.json`, `.env`) mit einer `*.json.example`-Vorlage im Skill;
Infrastruktur-Details werden aus dem **Infra-Wiki** nachgeschlagen statt dupliziert
(siehe `wp-sync-dev`: `/wiki query "DEV-Webhost"` statt hartkodiertem Hostnamen).

Beim Anlegen einer neuen Config **niemals mit Platzhalterwerten vorbelegen** — ein
Skill, der still an `ich@example.org` sendet, ist schlimmer als einer, der mit
klarer Meldung abbricht. `install.sh` weist nur auf die fehlende Datei hin.

Ein Changelog-Eintrag ist Prosa über einen vergangenen Vorgang: dort reicht kein
Suchen-und-Ersetzen, der Satz muss ohne den Namen weiterhin stimmen („Auslöser:
eine der genutzten Instanzen läuft auf Cloud" statt des Kundennamens).

Vor jedem Push prüfen — die Muster, die in der Praxis durchgerutscht sind:

```bash
git diff --stat @{u}..    # nur die eigenen Aenderungen pruefen, nicht die Historie
rg -n -o '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}' -g '!.git' | grep -Ev 'example|@azedo\.at'
rg -n '\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b' -g '!.git'
rg -n -f ~/.claude/kundendomains.txt -g '!.git'    # Liste liegt ausserhalb des Repos
```

Die Kundendomains stehen bewusst **nicht** hier - eine Liste im Repo waere selbst das
Leck, das sie verhindern soll. Ohne die Datei entfaellt der dritte Lauf; dann die
geaenderten Zeilen von Hand durchsehen. Gegriffen wird der eigene Diff: die Historie
laesst sich ohnehin nicht mehr bereinigen, und ihre Treffer verdecken sonst die neuen.

## Release-Workflow

Änderungen sind erst dann fertig, wenn sie beim Konsumenten ankommen. Zu jedem
Release gehören drei Dateien gemeinsam:

- `VERSION` — hochzählen (semver)
- `CHANGELOG.md` — neuer Abschnitt oben, absteigend nach Version
- `README.md` — führt nur die *aktuelle* Version, kein Verlauf

Commit-Konvention: `CR<id>: <skill> - <was geändert wurde> (<version>)`
Beispiel: `CR4426: swos - poe-voltage (poe.b i03) + gemeinsame Write-Basis (1.26.1)`

## Neuer Skill

Die `description` im Frontmatter gehoert als Block-Scalar notiert:

```yaml
description: >
  Was der Skill tut. Trigger: /beispiel.
```

Unquotiert bricht sie in jedem strikten YAML-Parser ab, sobald ein Doppelpunkt mit
folgendem Leerzeichen im Text steht - und das tut er in jedem `Trigger: /name.`.
Claude Code parst tolerant und zeigt den Fehler nicht; andere Harnesses, die
dieselben Skills ueber `~/.agents/skills/` einbinden, ueberspringen den Skill
stattdessen still und fallen auf eine alte Kopie zurueck. Der Fehler faellt damit
erst dort auf, wo niemand ihn sucht.

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
niemals einchecken (siehe „Das Repo ist public").
