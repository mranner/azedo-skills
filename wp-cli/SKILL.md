---
name: wp-cli
description: "WordPress-Administration via WP-CLI in FreeBSD-Jails: Datenbank, Code-Ausfuehrung, Plugins, Themes, Users, Options, Cache, Cron"
trigger:
  - "wp-cli"
  - "wp cli"
  - "WordPress CLI"
  - "wp db"
  - "wp eval"
  - "wp plugin"
  - "wp theme"
  - "wp user"
  - "wp option"
  - "wp search-replace"
  - "exportiere die Datenbank"
  - "loesche den Cache"
  - "installierte Plugins"
  - "WordPress Version"
  - "Datenbank exportieren"
  - "search replace"
---

# wp-cli — WordPress-Administration via CLI

Referenz fuer die Verwaltung von WordPress-Installationen via `wp` CLI auf FreeBSD-Servern mit Jails.

Ergaenzt den **wordpress-pro** Skill (Entwicklung: Themes, Plugins, Gutenberg) um den **Betrieb** (Administration, DB-Ops, Debugging, Migrationen).

---

## 1. Zugriff auf WordPress in Jails

WordPress-Installationen liegen unter `/www/home/<wwwuser>/<domain>/`.

WP-User haben Shell `/usr/bin/true` — daher `sudo -u <wwwuser>` verwenden, nicht `su -l`.

### ezjail (jexec)

Jail-ID per `jls` auf dem Server ermitteln. `jexec` braucht die **JID** (numerisch), nicht den Jail-Namen.

```sh
sudo ssh -C root@<server> "jexec <JID> sudo -u <wwwuser> wp --path=/www/home/<wwwuser>/<domain> <command>"
```

Beispiel (flexo, initech.at, JID 2):

```sh
sudo ssh -C root@webhost1.example.at "jexec 2 sudo -u wwwinitech wp --path=/www/home/wwwinitech/www.initech.at plugin list"
```

### iocage (iocage exec)

```sh
sudo ssh -C root@<server> "iocage exec <jailname> sudo -u <wwwuser> wp --path=/www/home/<wwwuser>/<domain> <command>"
```

Beispiel (jailer.acme.com, apache1.acme.com):

```sh
sudo ssh -C root@jailer.acme.com "iocage exec apache1.acme.com sudo -u wwwacme wp --path=/www/home/wwwacme/www.acme.com core version"
```

### Quoting

SSH → jexec/iocage exec → sudo ergibt drei Quoting-Ebenen. Regeln:

- Aeussere Ebene (SSH): doppelte Anfuehrungszeichen
- Innere Werte: einfache Anfuehrungszeichen oder Escaping mit `\"`
- Komplexe PHP-Ausdruecke: besser in eine Datei schreiben und `wp eval-file` verwenden

```sh
# Einfach — keine inneren Quotes noetig
sudo ssh -C root@server "jexec 2 sudo -u wwwuser wp --path=/www/home/wwwuser/domain option get siteurl"

# Mit einfachen Quotes im Wert
sudo ssh -C root@server "jexec 2 sudo -u wwwuser wp --path=/www/home/wwwuser/domain option update blogdescription 'Neue Beschreibung'"
```

### Preflight

Vor dem ersten Befehl pruefen, ob wp-cli erreichbar und WordPress installiert ist:

```sh
sudo ssh -C root@<server> "jexec <JID> sudo -u <wwwuser> wp --path=/www/home/<wwwuser>/<domain> core is-installed && jexec <JID> sudo -u <wwwuser> wp --path=/www/home/<wwwuser>/<domain> core version"
```

---

## 2. Datenbank-Operationen

### wp db (braucht MySQL-Client im Jail)

```sh
# Export (immer mit Dateiname + Datum)
wp db export /tmp/backup-$(date +%Y%m%d-%H%M%S).sql

# Import
wp db export /tmp/backup-before-import.sql   # IMMER zuerst Backup
wp db import dump.sql

# SQL-Query ausfuehren
wp db query "SELECT option_value FROM wp_options WHERE option_name = 'siteurl'"

# Tabellen anzeigen
wp db tables

# Suche in der Datenbank
wp db search "suchbegriff" --all-tables

# Regex-Suche
wp db search "pattern" --regex

# Datenbank optimieren
wp db optimize

# Datenbank reparieren
wp db repair
```

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

### wp eval — PHP-Einzeiler

WordPress ist vollstaendig geladen (Plugins, Theme, alle Hooks).

```sh
# Option abfragen
wp eval 'echo get_option("siteurl");'

# Aktives Theme
wp eval 'echo wp_get_theme()->get("Name");'

# Anzahl veroeffentlichter Posts
wp eval 'echo wp_count_posts()->publish;'

# Transient loeschen
wp eval 'delete_transient("mein_transient");'

# Alle User mit Rolle administrator auflisten
wp eval '$users = get_users(["role" => "administrator"]); foreach($users as $u) echo $u->user_login . " - " . $u->user_email . "\n";'
```

### wp eval-file — PHP-Datei ausfuehren

Fuer komplexere Logik. Die Datei wird mit geladenem WordPress ausgefuehrt.

```sh
# Datei auf den Server uebertragen, dann ausfuehren
wp eval-file /tmp/mein-script.php
```

Typische Anwendung: Daten-Migration, Bulk-Updates, Debugging von Plugin-Problemen.

### wp shell — Interaktive REPL

```sh
wp shell
```

**Limitation:** `wp shell` ist interaktiv und funktioniert **nicht** ueber die SSH→jexec/iocage-Pipeline. Nur direkt im Jail nutzbar (via `iocage console`).

---

## 4. Quick Reference

### Plugins

```sh
wp plugin list                              # Alle Plugins mit Status
wp plugin list --status=active              # Nur aktive
wp plugin list --format=json                # JSON-Ausgabe
wp plugin install <slug> --activate         # Installieren + aktivieren
wp plugin activate <slug>                   # Aktivieren
wp plugin deactivate <slug>                 # Deaktivieren
wp plugin update <slug>                     # Einzelnes Plugin updaten
wp plugin update --all                      # Alle Plugins updaten
wp plugin delete <slug>                     # Plugin loeschen
wp plugin search <term>                     # Im Repository suchen
wp plugin verify-checksums --all            # Integritaet pruefen
```

### Themes

```sh
wp theme list                               # Alle Themes mit Status
wp theme activate <slug>                    # Theme aktivieren
wp theme install <slug>                     # Theme installieren
wp theme update --all                       # Alle Themes updaten
wp theme delete <slug>                      # Theme loeschen
```

### Users

```sh
wp user list                                # Alle User
wp user list --role=administrator           # Nur Admins
wp user get <id|login|email>                # User-Details
wp user create <login> <email> --role=editor  # User erstellen
wp user update <id> --user_pass=<pw>        # Passwort aendern
wp user delete <id> --reassign=<other_id>   # User loeschen (Posts umhaengen!)
wp user add-role <id> <role>                # Rolle hinzufuegen
wp user remove-role <id> <role>             # Rolle entfernen
```

**Wichtig:** Bei `wp user delete` immer `--reassign=<id>` angeben, um Posts einem anderen User zuzuweisen. Ohne `--reassign` werden alle Posts geloescht.

### Options (wp_options)

```sh
wp option get <name>                        # Wert lesen
wp option get <name> --format=json          # Als JSON (fuer Arrays/Objekte)
wp option update <name> <value>             # Wert setzen
wp option update <name> --format=json < data.json  # JSON-Wert setzen
wp option delete <name>                     # Option loeschen
wp option list --search="*woo*"             # Options durchsuchen
```

### Cache

```sh
wp cache flush                              # Object Cache leeren
wp transient delete --all                   # Alle Transients loeschen
wp transient delete --expired               # Nur abgelaufene Transients
wp rewrite flush                            # Rewrite-Rules neu generieren
```

### Cron

```sh
wp cron event list                          # Geplante Events anzeigen
wp cron event run --all                     # Alle faelligen Events ausfuehren
wp cron event run <hook>                    # Einzelnen Event ausfuehren
wp cron event delete <hook>                 # Event loeschen
wp cron schedule list                       # Cron-Intervalle anzeigen
wp cron test                                # WP-Cron-URL testen
```

### Core

```sh
wp core version                             # WordPress-Version
wp core check-update                        # Verfuegbare Updates pruefen
wp core update                              # WordPress updaten (Backup zuerst!)
wp core verify-checksums                    # Core-Integritaet pruefen
```

### Wartung

```sh
wp maintenance-mode activate                # Wartungsmodus ein
wp maintenance-mode deactivate              # Wartungsmodus aus
wp maintenance-mode status                  # Status pruefen
wp config shuffle-salts                     # Neue Salts generieren
```

### Posts und Seiten

```sh
wp post list --post_type=post               # Alle Posts
wp post list --post_type=page               # Alle Seiten
wp post list --post_status=draft            # Entwuerfe
wp post get <id>                            # Post-Details
wp post delete <id>                         # Post in Papierkorb
wp post delete <id> --force                 # Post endgueltig loeschen
```

---

## 5. Bulk-Operationen

```sh
# Alle Plugins + Themes updaten
wp plugin update --all && wp theme update --all

# Alle User als CSV exportieren
wp user list --format=csv > users.csv

# Posts eines Typs als IDs (zum Weiterverarbeiten)
wp post list --post_type=product --format=ids

# Alle Spam-Kommentare loeschen
wp comment delete $(wp comment list --status=spam --format=ids) --force

# Alle Transients loeschen (Performance-Probleme)
wp transient delete --all
```

---

## 6. Multisite

```sh
# Alle Sites im Netzwerk
wp site list

# Befehl auf bestimmter Site ausfuehren
wp --url=sub.example.com plugin list

# Super-Admins verwalten
wp super-admin list
wp super-admin add <user>
wp super-admin remove <user>

# Plugin netzwerkweit aktivieren
wp plugin activate <slug> --network
```

Bei Multisite-Installationen **immer** `--url=<site>` angeben, sonst wirkt der Befehl nur auf die Haupt-Site.

---

## 7. Performance-Flags

| Flag | Wirkung |
|------|---------|
| `--format=json` | Maschinenlesbare Ausgabe (fuer Weiterverarbeitung mit `jq`) |
| `--format=ids` | Nur IDs ausgeben (fuer Piping) |
| `--format=csv` | CSV-Ausgabe (fuer Export) |
| `--format=table` | Tabelle (Default, gut lesbar) |
| `--fields=ID,user_login` | Nur bestimmte Spalten |
| `--skip-plugins` | Plugins nicht laden (schneller, umgeht fatale Fehler) |
| `--skip-themes` | Themes nicht laden |
| `--quiet` | Keine Info-Ausgabe |

---

## 8. Safety

1. **Backup vor destruktiven Operationen** — Immer `wp db export` ausfuehren vor: `wp db import`, `wp search-replace` (ohne --dry-run), `wp core update`, Bulk-Loeschungen
2. **Dry-Run zuerst** — `wp search-replace` immer zuerst mit `--dry-run` ausfuehren, Ergebnis dem User zeigen, erst nach Bestaetigung ohne `--dry-run`
3. **User-Loeschung mit --reassign** — `wp user delete` immer mit `--reassign=<id>` ausfuehren
4. **Serialisierte Daten** — Fuer URL-Aenderungen immer `wp search-replace` verwenden, nie rohes SQL (zerstoert serialisierte Arrays in wp_options)
5. **Core-Updates** — Nie `wp core update` ohne vorheriges Backup und Bestaetigung durch den User

---

## 9. Workflow

1. **Server und Jail ermitteln** — Aus dem Kontext oder beim User nachfragen: Server (z.B. webhost1.example.at), Jail-Typ (ezjail/iocage), Jail-ID/Name, wwwuser, Domain/Pfad. Siehe `server/overview.md` fuer Details
2. **Befehl zusammenbauen** — Mit dem passenden Zugriffs-Template (ezjail/iocage) aus Abschnitt 1
3. **Bei destruktiven Operationen** — Befehl dem User zeigen und Bestaetigung abwarten
4. **Ausfuehren** — Befehl via Bash ausfuehren
5. **Ergebnis melden** — Ausgabe zusammenfassen und dem User praesentieren

---

## 10. Troubleshooting

| Problem | Ursache | Loesung |
|---------|---------|---------|
| `wp db` schlaegt fehl: "mysql: not found" | MySQL-Client nicht im Jail installiert | `wp eval` mit `$wpdb` als Workaround (siehe Abschnitt 2) |
| "Error: This does not appear to be a WordPress install" | Falscher `--path` | Pfad pruefen: `ls /www/home/<wwwuser>/<domain>/wp-config.php` |
| Permission denied | Falscher wwwuser | `ls -la /www/home/` im Jail pruefen, korrekten User verwenden |
| Quoting-Fehler | Verschachtelte Anfuehrungszeichen | Quoting vereinfachen oder `wp eval-file` mit externer Datei verwenden |
| Timeout bei grossen Operationen | Lange DB-Queries oder Bulk-Ops | `--quiet` verwenden, bei Search-Replace einzelne Tabellen angeben |
| Plugin-Fehler beim Laden | Fehlerhaftes Plugin | `--skip-plugins` verwenden, dann gezielt debuggen |
