---
name: wp-cli
description: >
  WordPress-Administration per WP-CLI in FreeBSD-Jails: Datenbank exportieren
  und importieren, PHP-Code ausführen (wp eval), Plugins, Themes, Users,
  Options, Cache und Cron verwalten, search-replace. Der Basis-Skill für
  WP-CLI-Aufrufe - für Ninja Forms, PixelYourSite oder ein Security-Audit
  gibt es eigene Skills. Auch bei "exportiere die Datenbank", "lösche den
  Cache", "welche Plugins sind installiert", "welche WordPress-Version".
  Trigger: /wp-cli.
allowed-tools: [Bash]
---

# wp-cli — WordPress-Administration via CLI

Referenz fuer die Verwaltung von WordPress-Installationen via `wp` CLI auf FreeBSD-Servern mit Jails.

Ergaenzt den **wordpress-pro** Skill (Entwicklung: Themes, Plugins, Gutenberg) um den **Betrieb** (Administration, DB-Ops, Debugging, Migrationen).

---

## 1. Zugriff auf WordPress in Jails

WordPress-Installationen liegen unter `/www/home/<wwwuser>/<domain>/`.

WP-User haben Shell `/usr/bin/true` — daher `sudo -u <wwwuser>` (jexec) bzw. `iocage exec -U <wwwuser>` verwenden, nicht `su -l`.

> **Nie `--allow-root` / nie als root ausführen.** WP-CLI als root triggert u. a.
> den WPML/WP_Filesystem-FTP-Fatal. Immer als `<wwwuser>`.

### ezjail (jexec)

Jail-ID per `jls` auf dem Server ermitteln. `jexec` braucht die **JID** (numerisch), nicht den Jail-Namen.

```sh
sudo ssh -C root@<server> "jexec <JID> sudo -u <wwwuser> wp --path=/www/home/<wwwuser>/<domain> <command>"
```

Beispiel (webhost1, example.at, JID 2):

```sh
sudo ssh -C root@webhost1.example.at "jexec 2 sudo -u wwwexample wp --path=/www/home/wwwexample/www.example.at plugin list"
```

### iocage (iocage exec)

```sh
sudo ssh -C root@<server> "iocage exec -U <wwwuser> <jailname> -- wp --path=/www/home/<wwwuser>/<domain> <command>"
```

Beispiel (jailer1, apache1.example.com):

```sh
sudo ssh -C root@jailer1.example.at "iocage exec -U wwwexample apache1.example.com -- wp --path=/www/home/wwwexample/www.example.com core version"
```

**Immer `--` nach dem Jail-Namen.** `iocage exec` wertet seine eigenen Optionen auch hinter dem Jail-Namen aus und entfernt sie still: `--force`/`-f`, `-p`, `--help`, und `-U`/`-u` samt Wert - letzteres führt den Befehl sogar als anderer User aus. Ergebnis ist eine wp-cli-Warnung statt der Aktion, oder eine Aktion mit falschen Rechten. Deshalb `iocage exec -U <wwwuser> <jail> -- wp … --force`. `sh -c '…'` nur, wenn im Jail Pipes oder Redirects nötig sind. `-U <wwwuser>` statt `sudo -u`, weil `sudo` im Jail ein Passwort verlangen kann.

### Quoting

SSH → jexec/iocage exec → sudo ergibt drei Quoting-Ebenen. Regeln:

- Aeussere Ebene (SSH): doppelte Anfuehrungszeichen
- Innere Werte: einfache Anfuehrungszeichen oder Escaping mit `\"`
- Komplexe PHP-Ausdruecke: besser in eine Datei schreiben und `wp eval-file` verwenden
- Glob-Argumente in einfache Anfuehrungszeichen: `--search='relevanssi_*'` statt `--search=relevanssi_*`, sonst expandiert die Shell auf dem Jail-Host das Muster, bevor wp-cli es sieht

```sh
# Einfach — keine inneren Quotes noetig
sudo ssh -C root@server "jexec 2 sudo -u wwwuser wp --path=/www/home/wwwuser/domain option get siteurl"

# Mit einfachen Quotes im Wert
sudo ssh -C root@server "jexec 2 sudo -u wwwuser wp --path=/www/home/wwwuser/domain option update blogdescription 'Neue Beschreibung'"

# Glob-Argument — einfach gequotet
sudo ssh -C root@server "jexec 2 sudo -u wwwuser wp --path=/www/home/wwwuser/domain option list --search='relevanssi_*'"
```

### Preflight

Vor dem ersten Befehl pruefen, ob wp-cli erreichbar und WordPress installiert ist:

```sh
sudo ssh -C root@<server> "jexec <JID> sudo -u <wwwuser> wp --path=/www/home/<wwwuser>/<domain> core is-installed && jexec <JID> sudo -u <wwwuser> wp --path=/www/home/<wwwuser>/<domain> core version"
```

---

## 2. Datenbank-Operationen

### wp db (braucht MySQL-Client im Jail)

Vor `wp db import` immer zuerst `wp db export` mit Datum im Dateinamen. Die
uebrigen `wp db`-Befehle stehen in `references/befehle.md`.

### Kein MySQL-Client? → wp eval als Workaround

Wenn `wp db` mit "mysql command not found" fehlschlaegt:

```sh
# Query via $wpdb ausfuehren
wp eval 'global $wpdb; $r = $wpdb->get_results("SELECT option_name, option_value FROM $wpdb->options WHERE option_name = \"siteurl\""); print_r($r);'

# Tabellen auflisten
wp eval 'global $wpdb; $tables = $wpdb->get_col("SHOW TABLES"); foreach($tables as $t) echo $t."\n";'

# Update via $wpdb
wp eval 'global $wpdb; $wpdb->update($wpdb->options, ["option_value" => "https://neue-url.at"], ["option_name" => "siteurl"]);'
```

### Search-Replace (Domain-Migrationen)

**Immer** zuerst `--dry-run`, dann nach Bestaetigung ohne:

```sh
# 1. Backup
wp db export /tmp/backup-before-sr.sql

# 2. Dry-Run — zeigt betroffene Tabellen und Anzahl der Ersetzungen
wp search-replace 'https://alte-domain.at' 'https://neue-domain.at' --dry-run --all-tables

# 3. Ausfuehren (erst nach Bestaetigung durch den User)
wp search-replace 'https://alte-domain.at' 'https://neue-domain.at' --all-tables

# 4. Cache leeren
wp cache flush
```

**Wichtig:** `wp search-replace` behandelt serialisierte Daten korrekt — rohe SQL-Queries (`UPDATE ... SET ...`) tun das **nicht**. Immer `wp search-replace` verwenden, nie manuelles SQL fuer URL-Aenderungen.

---

## 3. Code-Ausfuehrung im WordPress-Kontext

`wp eval '<php>'` und `wp eval-file <datei>` laufen mit vollstaendig geladenem
WordPress. Komplexe Ausdruecke als Datei ablegen und per `wp eval-file`
ausfuehren, statt sie durch drei Quoting-Ebenen zu schicken. Beispiele und die
Ausgabe-Flags (`--format`, `--fields`, `--skip-plugins`) stehen in
`references/befehle.md`.

### wp shell — Interaktive REPL

```sh
wp shell
```

**Limitation:** `wp shell` ist interaktiv und funktioniert **nicht** ueber die SSH→jexec/iocage-Pipeline. Nur direkt im Jail nutzbar (via `iocage console`).

---

## 4. Safety

1. **Backup vor destruktiven Operationen** — Immer `wp db export` ausfuehren vor: `wp db import`, `wp search-replace` (ohne --dry-run), `wp core update`, Bulk-Loeschungen
2. **Dry-Run zuerst** — `wp search-replace` immer zuerst mit `--dry-run` ausfuehren, Ergebnis dem User zeigen, erst nach Bestaetigung ohne `--dry-run`
3. **User-Loeschung mit --reassign** — `wp user delete` immer mit `--reassign=<id>` ausfuehren
4. **Serialisierte Daten** — Fuer URL-Aenderungen immer `wp search-replace` verwenden, nie rohes SQL (zerstoert serialisierte Arrays in wp_options)
5. **Core-Updates** — Nie `wp core update` ohne vorheriges Backup und Bestaetigung durch den User

---

## 5. Workflow

1. **Server und Jail ermitteln** — Aus dem Kontext oder beim User nachfragen: Server (z.B. `webhost1.example.at`), Jail-Typ (ezjail/iocage), Jail-ID/Name, wwwuser, Domain/Pfad.
2. **Befehl zusammenbauen** — Mit dem passenden Zugriffs-Template (ezjail/iocage) aus Abschnitt 1
3. **Bei destruktiven Operationen** — Befehl dem User zeigen und Bestaetigung abwarten
4. **Ausfuehren** — Befehl via Bash ausfuehren
5. **Ergebnis melden** — Ausgabe zusammenfassen und dem User praesentieren

---

## 6. Referenzen

Bei Bedarf lesen:

| Datei | Inhalt |
|---|---|
| `references/befehle.md` | Befehle nach Bereich (Datenbank, Plugins, Themes, Users, Options, Cache, Cron, Core, Wartung, Posts), Bulk-Operationen, `wp eval`-Beispiele, Ausgabe-Flags |
| `references/multisite.md` | Multisite: `--url`, Optionen in `sitemeta`, Custom-Tabellen, DB-Export einer Subsite |
| `references/troubleshooting.md` | typische Fehlermeldungen mit Ursache und Loesung |

Bei einer Multisite **vor** dem ersten Befehl `references/multisite.md` lesen: ohne
`--url=<site>` wirkt ein Befehl nur auf die Haupt-Site, und `wp option get` liefert
fuer Netzwerk-Einstellungen einen Wert, der nichts steuert.

Plugin-eigene Subcommands (z.B. `wp ninja-forms`) deckt der Skill [[wp-nf]] ab.
