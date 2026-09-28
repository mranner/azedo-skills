# wp-cli - Troubleshooting

| Problem | Ursache | Loesung |
|---------|---------|---------|
| `wp db` schlaegt fehl: "mysql: not found" | MySQL-Client nicht im Jail installiert | `wp eval` mit `$wpdb` als Workaround (siehe SKILL.md, Abschnitt 2) |
| "Error: This does not appear to be a WordPress install" | Falscher `--path` | Pfad pruefen: `ls /www/home/<wwwuser>/<domain>/wp-config.php` |
| Permission denied | Falscher wwwuser | `ls -la /www/home/` im Jail pruefen, korrekten User verwenden |
| Quoting-Fehler | Verschachtelte Anfuehrungszeichen | Quoting vereinfachen oder `wp eval-file` mit externer Datei verwenden |
| Timeout bei grossen Operationen | Lange DB-Queries oder Bulk-Ops | `--quiet` verwenden, bei Search-Replace einzelne Tabellen angeben |
| Plugin-Fehler beim Laden | Fehlerhaftes Plugin | `--skip-plugins` verwenden, dann gezielt debuggen |
