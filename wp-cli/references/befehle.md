# wp-cli - Befehlsreferenz

Allgemeine WP-CLI-Befehle nach Bereich. Aufruf im Jail immer mit dem Zugriffs-Template aus SKILL.md, Abschnitt 1.

## Datenbank (wp db)

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

## Plugins

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

> **Plugin-eigene CLI-Befehle:** Manche Plugins registrieren eigene WP-CLI-Subcommands.
> Ninja Forms z.B. bringt `wp ninja-forms` mit (`list`/`get`/`form`/`delete`/`info`) —
> Formular-Auslesen/-Aendern, Settings (`element_class`) und Export/Import deckt der
> Skill [[wp-nf]] ab.

## Themes

```sh
wp theme list                               # Alle Themes mit Status
wp theme activate <slug>                    # Theme aktivieren
wp theme install <slug>                     # Theme installieren
wp theme update --all                       # Alle Themes updaten
wp theme delete <slug>                      # Theme loeschen
```

## Users

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

## Options (wp_options)

```sh
wp option get <name>                        # Wert lesen
wp option get <name> --format=json          # Als JSON (fuer Arrays/Objekte)
wp option update <name> <value>             # Wert setzen
wp option update <name> --format=json < data.json  # JSON-Wert setzen
wp option delete <name>                     # Option loeschen
wp option list --search="*woo*"             # Options durchsuchen
```

**Bei Multisite zuerst pruefen, ob die Option ueberhaupt in `wp_options` liegt.**
Eine Reihe von Einstellungen kommt dort aus `wp_sitemeta`; `wp option get` liefert
trotzdem einen Wert, nur steuert der nichts. Siehe [multisite.md](multisite.md), „Optionen liegen bei
Multisite in `sitemeta`".

## Cache

```sh
wp cache flush                              # Object Cache leeren
wp transient delete --all                   # Alle Transients loeschen
wp transient delete --expired               # Nur abgelaufene Transients
wp rewrite flush                            # Rewrite-Rules neu generieren
```

## Cron

```sh
wp cron event list                          # Geplante Events anzeigen
wp cron event run --all                     # Alle faelligen Events ausfuehren
wp cron event run <hook>                    # Einzelnen Event ausfuehren
wp cron event delete <hook>                 # Event loeschen
wp cron schedule list                       # Cron-Intervalle anzeigen
wp cron test                                # WP-Cron-URL testen
```

## Core

```sh
wp core version                             # WordPress-Version
wp core check-update                        # Verfuegbare Updates pruefen
wp core update                              # WordPress updaten (Backup zuerst!)
wp core verify-checksums                    # Core-Integritaet pruefen
```

## Wartung

```sh
wp maintenance-mode activate                # Wartungsmodus ein
wp maintenance-mode deactivate              # Wartungsmodus aus
wp maintenance-mode status                  # Status pruefen
wp config shuffle-salts                     # Neue Salts generieren
```

## Posts und Seiten

```sh
wp post list --post_type=post               # Alle Posts
wp post list --post_type=page               # Alle Seiten
wp post list --post_status=draft            # Entwuerfe
wp post get <id>                            # Post-Details
wp post delete <id>                         # Post in Papierkorb
wp post delete <id> --force                 # Post endgueltig loeschen
```

## Bulk-Operationen

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

## wp eval — PHP-Einzeiler

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

## wp eval-file — PHP-Datei ausfuehren

Fuer komplexere Logik. Die Datei wird mit geladenem WordPress ausgefuehrt.

```sh
# Datei auf den Server uebertragen, dann ausfuehren
wp eval-file /tmp/mein-script.php
```

Typische Anwendung: Daten-Migration, Bulk-Updates, Debugging von Plugin-Problemen.

## Performance-Flags

| Flag | Wirkung |
|---|---|
| `--format=json` | Maschinenlesbare Ausgabe (fuer Weiterverarbeitung mit `jq`) |
| `--format=ids` | Nur IDs ausgeben (fuer Piping) |
| `--format=csv` | CSV-Ausgabe (fuer Export) |
| `--format=table` | Tabelle (Default, gut lesbar) |
| `--fields=ID,user_login` | Nur bestimmte Spalten |
| `--skip-plugins` | Plugins nicht laden (schneller, umgeht fatale Fehler) |
| `--skip-themes` | Themes nicht laden |
| `--quiet` | Keine Info-Ausgabe |
