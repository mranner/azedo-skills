---
name: wp-cli
description: >
  WordPress-Administration per WP-CLI in FreeBSD-Jails: Datenbank exportieren
  und importieren, PHP-Code ausführen (wp eval), Plugins, Themes, WP-Benutzer,
  Options, Cache und Cron verwalten, search-replace. Der Basis-Skill für
  WP-CLI-Aufrufe - für Ninja Forms, PixelYourSite oder ein Security-Audit
  gibt es eigene Skills. Auch bei "exportiere die Datenbank", "lösche den
  Cache", "welche Plugins sind installiert", "welche WordPress-Version".
  Trigger: /wp-cli.
allowed-tools: [Bash]
---

# wp-cli — WordPress-Administration via CLI

Referenz für die Verwaltung von WordPress-Installationen via `wp` CLI auf FreeBSD-Servern mit Jails.

Ergänzt den **wordpress-pro** Skill (Entwicklung: Themes, Plugins, Gutenberg) um den **Betrieb** (Administration, DB-Ops, Debugging, Migrationen).

---

## 1. Zugriff auf WordPress in Jails

WordPress-Installationen liegen unter `/www/home/<wwwuser>/<domain>/`.

Die wwwuser haben Shell `/usr/bin/true` — daher `sudo -u <wwwuser>` (jexec) bzw. `iocage exec -U <wwwuser>` verwenden, nicht `su -l`.

> **Nie `--allow-root` / nie als root ausführen.** WP-CLI als root triggert u. a.
> den WPML/WP_Filesystem-FTP-Fatal. Immer als `<wwwuser>`.

### ezjail (jexec)

Jail-Namen per `jls name` auf dem Server ermitteln. `jexec` nimmt den Namen oder die JID; der Name ist stabiler, weil die JID bei jedem Jail-Neustart wechselt.

```sh
sudo ssh -C root@<server> "jexec <jail> sudo -u <wwwuser> wp --path=/www/home/<wwwuser>/<domain> <command>"
```

Beispiel (webhost1, example.at, Jail `apache_example_at`):

```sh
sudo ssh -C root@webhost1.example.at "jexec apache_example_at sudo -u wwwexample wp --path=/www/home/wwwexample/www.example.at plugin list"
```

### iocage (iocage exec)

```sh
sudo ssh -C root@<server> "iocage exec -U <wwwuser> <jailname> -- wp --path=/www/home/<wwwuser>/<domain> <command>"
```

Beispiel (jailer1, apache1.example.com):

```sh
sudo ssh -C root@jailer1.example.at "iocage exec -U wwwexample apache1.example.com -- wp --path=/www/home/wwwexample/www.example.com core version"
```

**Immer `--` nach dem Jail-Namen.** `iocage exec` wertet seine eigenen Optionen auch hinter dem Jail-Namen aus und entfernt sie still: `--force`/`-f`, `-p`, `--help`, und `-U`/`-u` samt Wert - letzteres führt den Befehl sogar als anderer wwwuser aus. Ergebnis ist eine wp-cli-Warnung statt der Aktion, oder eine Aktion mit falschen Rechten. Deshalb `iocage exec -U <wwwuser> <jail> -- wp … --force`. `sh -c '…'` nur, wenn im Jail Pipes oder Redirects nötig sind. `-U <wwwuser>` statt `sudo -u`: ein `sudo -u` direkt hinter dem Jail-Namen fängt `jexec` als eigenes `-u` ab, und der Umweg über `sh -c` bringt eine zusätzliche Quoting-Ebene.

### Quoting

SSH → jexec/iocage exec → sudo ergibt drei Quoting-Ebenen. Regeln:

- Äußere Ebene (SSH): doppelte Anführungszeichen
- Innere Werte: einfache Anführungszeichen oder Escaping mit `\"`
- Komplexe PHP-Ausdrücke: nicht inline per `wp eval`, sondern per stdin an `wp eval-file -` (siehe unten)
- Glob-Argumente in einfache Anführungszeichen: `--search='relevanssi_*'` statt `--search=relevanssi_*`, sonst expandiert die Shell auf dem Jail-Host das Muster, bevor wp-cli es sieht

```sh
# Einfach — keine inneren Quotes nötig
sudo ssh -C root@server "jexec <jail> sudo -u wwwuser wp --path=/www/home/wwwuser/domain option get siteurl"

# Mit einfachen Quotes im Wert
sudo ssh -C root@server "jexec <jail> sudo -u wwwuser wp --path=/www/home/wwwuser/domain option update blogdescription 'Neue Beschreibung'"

# Glob-Argument — einfach gequotet
sudo ssh -C root@server "jexec <jail> sudo -u wwwuser wp --path=/www/home/wwwuser/domain option list --search='relevanssi_*'"
```

### PHP-Snippets per stdin

Das Snippet liegt lokal und geht per stdin an `wp eval-file -`. stdin kommt durch
SSH, `jexec`/`iocage exec` und `sudo` unverändert an:

```sh
# ezjail
sudo ssh -C root@<server> "jexec <jail> sudo -u <wwwuser> wp --path=/www/home/<wwwuser>/<domain> eval-file -" < snippet.php

# iocage
sudo ssh -C root@<server> "iocage exec -U <wwwuser> <jailname> -- wp --path=/www/home/<wwwuser>/<domain> eval-file -" < snippet.php
```

### Preflight

Vor dem ersten Befehl prüfen, ob wp-cli erreichbar und WordPress installiert ist:

```sh
sudo ssh -C root@<server> "jexec <jail> sudo -u <wwwuser> wp --path=/www/home/<wwwuser>/<domain> core is-installed && jexec <jail> sudo -u <wwwuser> wp --path=/www/home/<wwwuser>/<domain> core version"
```

---

## 2. Datenbank-Operationen

### wp db (braucht MySQL-Client im Jail)

Vor `wp db import` immer zuerst `wp db export` mit Datum im Dateinamen. Die
übrigen `wp db`-Befehle stehen in `references/befehle.md`.

### Kein MySQL-Client? → wp eval als Workaround

Wenn `wp db` mit "mysql command not found" fehlschlägt:

```sh
# Query via $wpdb ausführen
wp eval 'global $wpdb; $r = $wpdb->get_results("SELECT option_name, option_value FROM $wpdb->options WHERE option_name = \"siteurl\""); print_r($r);'

# Tabellen auflisten
wp eval 'global $wpdb; $tables = $wpdb->get_col("SHOW TABLES"); foreach($tables as $t) echo $t."\n";'

# Update via $wpdb
wp eval 'global $wpdb; $wpdb->update($wpdb->options, ["option_value" => "https://neue-url.at"], ["option_name" => "siteurl"]);'
```

### Search-Replace (Domain-Migrationen)

**Immer** zuerst `--dry-run`, dann nach Bestätigung ohne:

```sh
# 1. Backup
wp db export /tmp/backup-before-sr.sql

# 2. Dry-Run — zeigt betroffene Tabellen und Anzahl der Ersetzungen
wp search-replace 'https://alte-domain.at' 'https://neue-domain.at' --dry-run --all-tables

# 3. Ausführen (erst nach Bestätigung durch den Nutzer)
wp search-replace 'https://alte-domain.at' 'https://neue-domain.at' --all-tables

# 4. Cache leeren
wp cache flush
```

**Wichtig:** `wp search-replace` behandelt serialisierte Daten korrekt — rohe SQL-Queries (`UPDATE ... SET ...`) tun das **nicht**. Immer `wp search-replace` verwenden, nie manuelles SQL für URL-Änderungen.

---

## 3. Code-Ausführung im WordPress-Kontext

`wp eval '<php>'` und `wp eval-file <datei>` laufen mit vollständig geladenem
WordPress. Alles über einen Einzeiler hinaus lokal als Datei schreiben und per
stdin an `wp eval-file -` geben:

```sh
<zugriff> wp --path=<docroot> eval-file - [<arg1> ...] < snippet.php
```

- Kein Quoting über mehrere Shells - das PHP kommt unverändert an
- Keine Datei auf dem Zielsystem, die abgelegt und wieder gelöscht werden muss
- Argumente nach dem `-` stehen im Snippet in `$args`
- Die Ausgabe lässt sich lokal weiterverarbeiten, z.B. JSON-Snapshots vorher/nachher diffen

Beispiele und die
Ausgabe-Flags (`--format`, `--fields`, `--skip-plugins`) stehen in
`references/befehle.md`.

### wp shell — Interaktive REPL

```sh
wp shell
```

**Limitation:** `wp shell` ist interaktiv und funktioniert **nicht** über die SSH→jexec/iocage-Pipeline. Nur direkt im Jail nutzbar (via `iocage console`).

---

## 4. Safety

1. **Backup vor destruktiven Operationen** — Immer `wp db export` ausführen vor: `wp db import`, `wp search-replace` (ohne --dry-run), `wp core update`, Bulk-Löschungen
2. **Dry-Run zuerst** — `wp search-replace` immer zuerst mit `--dry-run` ausführen, Ergebnis dem Nutzer zeigen, erst nach Bestätigung ohne `--dry-run`
3. **WP-Benutzer nur mit --reassign löschen** — `wp user delete` immer mit `--reassign=<id>` ausführen
4. **Serialisierte Daten** — Für URL-Änderungen immer `wp search-replace` verwenden, nie rohes SQL (zerstört serialisierte Arrays in wp_options)
5. **Core-Updates** — Nie `wp core update` ohne vorheriges Backup und Bestätigung durch den Nutzer

---

## 5. Workflow

1. **Server und Jail ermitteln** — Aus dem Kontext oder beim Nutzer nachfragen: Server (z.B. `webhost1.example.at`), Jail-Typ (ezjail/iocage), Jail-ID/Name, wwwuser, Domain/Pfad.
2. **Befehl zusammenbauen** — Mit dem passenden Zugriffs-Template (ezjail/iocage) aus Abschnitt 1
3. **Bei destruktiven Operationen** — Befehl dem Nutzer zeigen und Bestätigung abwarten
4. **Ausführen** — Befehl via Bash ausführen
5. **Ergebnis melden** — Ausgabe zusammenfassen und dem Nutzer präsentieren

---

## 6. Referenzen

Bei Bedarf lesen:

| Datei | Inhalt |
|---|---|
| `references/befehle.md` | Befehle nach Bereich (Datenbank, Plugins, Themes, WP-Benutzer, Options, Cache, Cron, Core, Wartung, Posts), Bulk-Operationen, `wp eval`-Beispiele, Ausgabe-Flags |
| `references/multisite.md` | Multisite: `--url`, Optionen in `sitemeta`, Custom-Tabellen, Sicherung einer Subsite samt Aufräumen |
| `references/troubleshooting.md` | typische Fehlermeldungen mit Ursache und Lösung |

Bei einer Multisite **vor** dem ersten Befehl `references/multisite.md` lesen: ohne
`--url=<site>` wirkt ein Befehl nur auf die Haupt-Site, und `wp option get` liefert
für Netzwerk-Einstellungen einen Wert, der nichts steuert.

Plugin-eigene Subcommands (z.B. `wp ninja-forms`) deckt der Skill [[wp-nf]] ab.
