---
name: wp-azedo
description: >
  Einstieg für jede WordPress-Aufgabe bei azedo: klärt zuerst, wo die Site liegt
  und wie man sie erreicht, und leitet dann zum zuständigen Skill weiter - für
  Code (Theme, Block-Theme, Blöcke, Patterns, Plugin, REST-Endpunkt, Performance)
  zu den offiziellen WordPress-Skills, für Betrieb und Inhalte zu den azedo-Skills
  (wp-cli, wp-rest, wp-nf, wp-pys, mainwp, novamira). Bringt die azedo-Regeln
  mit, die dort fehlen: Umgebung ohne Docker, Code-Stil, ACF, Abnahme-Checkliste.
  Nutze diesen Skill wenn der User an einer WordPress-Site, einem Theme,
  Plugin oder mu-plugin arbeiten will, bevor ein anderer wp-*-Skill geladen
  wird - auch wenn das Wort WordPress nicht fällt. Auch bei "bau ein Theme",
  "neuer Block", "REST-Endpunkt im mu-plugin", "exportier die DB der Site",
  "Plugins updaten", "ändere den Text auf der Seite", "richte die Seite ein",
  "Go-Live vorbereiten", "prüf das Theme". Trigger: /wp-azedo.
---

# wp-azedo -- Einstieg und Routing für WordPress

Dieser Skill macht selbst keine WordPress-Arbeit. Er klärt zwei Fragen und leitet
weiter: **Wo liegt die Site?** und **Was ist die Aufgabe?** Danach gelten die
azedo-Regeln unten zusätzlich zum Fach-Skill.

## 1. Wo liegt die Site?

Nicht raten und nicht den Host abklopfen: zuerst das Infra-Wiki fragen
(`/wiki query "<site oder domain>"`). Zu klären:

- **Umgebung:** DEV oder Live, welcher Host, welcher Jail, Docroot.
- **Zugang:** WP-CLI im Jail (`wp-cli`), REST mit Application Password (`wp-rest`),
  MainWP (`mainwp`) oder Novamira (`novamira`).
- **Repo:** Liegt Theme oder Plugin in Git, wo ist die Arbeitskopie?

Fehlt etwas davon im Wiki, nachfragen und das Ergebnis danach ins Wiki eintragen.

## 2. Was ist die Aufgabe?

| Aufgabe | Skill |
|---|---|
| Unklar, was für ein Projekt vorliegt | Script von `wp-project-triage` (siehe unten) |
| Block-Theme, `theme.json`, Templates, Template-Parts | `wp-block-themes` |
| Eigene Blöcke, `block.json`, `render.php` | `wp-block-development` |
| Patterns, Block-Markup, Escaping und Übersetzbarkeit in Patterns | `wp-patterns` |
| Plugin oder mu-plugin: Hooks, Sicherheit, Settings | `wp-plugin-development` |
| REST-Endpunkt **bauen** | `wp-rest-api` |
| Performance messen und verbessern | `wp-performance` |
| Betrieb im Jail: DB, Plugins, Cache, Cron, `search-replace` | `wp-cli` |
| Inhalte **pflegen** per REST (Seiten, Medien, Beiträge) | `wp-rest` |
| Ninja Forms | `wp-nf` |
| PixelYourSite, Tracking-Events | `wp-pys` |
| Security-Audit, Backdoor-Suche, Admin-Audit, 2FA | `wp-security` ¹ |
| Ganze Site (Dateien + DB) von Live auf DEV klonen | `wp-clone-dev` ¹ |
| Viele Sites: Updates, Plugins, Clients | `mainwp` |
| Site mit Novamira | `novamira` |
| Plugins/Themes zwischen Live und DEV abgleichen | `/wp-sync-dev` (nur manuell) |

¹ Projekt-Skill, nur im Infra-Projekt verfügbar, nicht Teil dieses Repos.

`wordpress-router` nicht zusätzlich laden - diese Tabelle ersetzt ihn.

**Voraussetzung:** Die offiziellen Skills (`wp-project-triage`, `wp-block-themes`,
`wp-block-development`, `wp-patterns`, `wp-plugin-development`, `wp-rest-api`,
`wp-performance`) installiert `install.sh` nicht. Sie kommen aus
`https://github.com/WordPress/agent-skills`, geklont nach
`~/.claude/vendor/wordpress-agent-skills` und je Skill nach `~/.claude/skills/`
verlinkt. `wordpress-router` wird bewusst nicht verlinkt, die WooCommerce-Skills
ebenso wenig. Fehlt ein Skill aus der Tabelle, ist dieser Schritt nicht gelaufen.

**Scripts der offiziellen Skills:** Deren SKILL.md ruft Scripts relativ zum Repo
auf (`node skills/<skill>/scripts/...`). Hier liegen sie unter
`~/.claude/skills/<skill>/scripts/`. Aufruf im Projektverzeichnis, z. B.:

```bash
node ~/.claude/skills/wp-project-triage/scripts/detect_wp_project.mjs
```

## 3. azedo-Regeln (gelten immer)

- **Keine Docker-Umgebung:** `wp-env` und Playground entfallen. Gearbeitet wird
  direkt auf DEV im Jail.
- **Code-Stil:** PHP nach `php-formatting` (PSR-2 mit Tabs), nicht nach WPCS. Wo
  ein offizieller Skill `phpcs --standard=WordPress` verlangt, gilt das nicht.
- **WP-CLI im Jail:** PHP-Code per `wp eval-file -` über stdin übergeben, nicht
  per `wp eval '…'` - die Root-Shell ist tcsh und bricht das Quoting (`tcsh`).
- **WP-CLI als wwwuser, nie mit `--allow-root`:** `iocage exec -U <wwwuser>` bzw.
  `sudo -u <wwwuser>` (Begründung in `wp-cli`).
- **Sprache vor Core-Updates prüfen:** `wp core update --locale=de_DE` stellt
  eine englische Site auf Deutsch um. Vorher `get_locale()` der Site lesen und
  diesen Wert übergeben; weicht er von `de_DE` ab, nachfragen.
- **Inhalte vs. Code:** Theme, Blöcke, mu-plugin und ACF-JSON gehören in Git.
  Menüs, Seiten, Formulare und Einstellungen sind Inhalt und bleiben in der DB.
- **ACF:** siehe `references/acf.md`.
- **Plan vor Umsetzung:** Bei neuen Themes und größeren Umbauten den Plan gegen
  den Fach-Skill prüfen, bevor er vorgelegt wird.
- **Abnahme:** Vor jeder Abnahme `references/checkliste.md` durchgehen; vor
  einem Go-Live zusätzlich `references/go-live.md`.
