# wp-cli - Troubleshooting

| Problem | Ursache | Loesung |
|---------|---------|---------|
| `wp db` schlaegt fehl: "mysql: not found" | MySQL-Client nicht im Jail installiert | `wp eval` mit `$wpdb` als Workaround (siehe SKILL.md, Abschnitt 2) |
| "Error: This does not appear to be a WordPress install" | Falscher `--path` | Pfad pruefen: `ls /www/home/<wwwuser>/<domain>/wp-config.php` |
| Permission denied | Falscher wwwuser | `ls -la /www/home/` im Jail pruefen, korrekten wwwuser verwenden |
| Quoting-Fehler | Verschachtelte Anfuehrungszeichen | Quoting vereinfachen oder `wp eval-file` mit externer Datei verwenden |
| Timeout bei grossen Operationen | Lange DB-Queries oder Bulk-Ops | `--quiet` verwenden, bei Search-Replace einzelne Tabellen angeben |
| Plugin-Fehler beim Laden | Fehlerhaftes Plugin | `--skip-plugins` verwenden, dann gezielt debuggen |
| Premium-Plugin: `update: none`, obwohl eine neuere Version existiert | Hersteller-Updater nicht registriert: Plugin inaktiv, Updater nur bei `manage_options` oder nur in `admin_init`; dasselbe Symptom zeigt eine fehlende Lizenzaktivierung der Domain | `wp transient delete update_plugins`, dann mit `--user=<admin>`; inaktives Plugin vorher aktivieren; `admin_init`-Updater per `--require` auf `init` ziehen (Beispiel im Skill [[wp-pys]]) |
