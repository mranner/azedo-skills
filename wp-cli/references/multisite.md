# wp-cli - Multisite

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

## Optionen liegen bei Multisite in `sitemeta`

Bei einer Multisite liest WordPress eine Reihe von Einstellungen ueber
`get_site_option()`, also aus `wp_sitemeta` statt aus `wp_options` der einzelnen
Site. `wp option get` antwortet dort trotzdem mit einem Wert -- der Aufruf schlaegt
nicht fehl, er antwortet **falsch**. Betroffen sind unter anderem
`auto_update_plugins`, `auto_update_core_major` und `auto_update_core_minor`.

Beide Ebenen koennen gleichzeitig existieren und sich widersprechen. Wer nur
`option get` fragt, dokumentiert den falschen Zustand und aendert anschliessend an
der wirkungslosen Stelle, ohne dass etwas auffaellt.

```sh
# Erst pruefen, ob Multisite (Exit-Code 1, wenn die Konstante fehlt):
wp config get MULTISITE

# FALSCH bei Multisite -- Wert existiert, ist aber wirkungslos:
wp option get auto_update_plugins --format=json

# RICHTIG -- Netzwerk-Ebene:
wp network meta get 1 auto_update_plugins --format=json
wp network meta update 1 auto_update_core_major disabled
```

Die `1` ist die Network-ID; bei einer einzelnen Multisite-Installation ist das immer
`1` (`wp network list` zeigt sie).

**Regel:** Vor jedem `option get`/`option update` auf `MULTISITE` pruefen und bei
einer Multisite auf `network meta get|update 1 <option>` verzweigen. Bei einer
Erhebung ueber mehrere Installationen gilt das ausnahmslos. Ein Plugin mit Status
`active-network` in `wp plugin list` ist ein zuverlaessiges Indiz fuer eine
Multisite.

**Achtung:** `--url` filtert nur auf Standard-WordPress-Tabellen (mit Site-Prefix). Custom-Tabellen wie `wp_*_icl_strings` (WPML) oder andere Plugin-Tabellen ohne Site-Prefix werden von `--url` **nicht** erfasst. Fuer Operationen auf solchen Tabellen `--all-tables` verwenden:

```sh
# FALSCH — findet Custom-Tabellen nicht:
wp search-replace 'alt' 'neu' --url=sub.example.com

# RICHTIG — alle Tabellen einschliessen:
wp search-replace 'alt' 'neu' --all-tables
```

## Sicherung einer Subsite

Die Tabellenliste mit `--all-tables-with-prefix`
bilden, nicht mit `--scope=blog`. `--scope=blog` liefert nur die WP-Kerntabellen
der Subsite und laesst alle Plugin-Tabellen mit ihrem Prefix weg (WPML, Ninja
Forms, Smart Slider, ...) - das Backup sieht vollstaendig aus und ist es nicht.
Bei einer Subsite mit vielen Plugins standen 15 Tabellen gegen 104.

```sh
# FALSCH — nur die 15 Kerntabellen:
wp db tables --url=sub.example.com --scope=blog

# RICHTIG — alle Tabellen mit dem Prefix der Subsite (wp_5_*):
wp db tables --url=sub.example.com --all-tables-with-prefix --format=csv
```

Der Export geht nach stdout und wird auf dem **Host** gepackt. Im Jail braucht es
dann kein beschreibbares Verzeichnis, und die Sicherung liegt nicht im Webroot.
Das Script läuft per STDIN in einem `sh` auf dem Host, damit Tabellenliste und
Pipe keine Quoting-Ebene überwinden müssen (Beispiel iocage, für ezjail `jexec
<JID> sudo -u <wwwuser> wp …`):

```sh
cat <<'SCRIPT' | sudo ssh -C root@<server> sh
set -e
wp="iocage exec -U <wwwuser> <jail> -- wp --path=/www/home/<wwwuser>/<domain> --url=<subsite>"
d=/root/<vorgang>
f=$d/<subsite>-`date +%Y%m%d`.sql.gz
mkdir -p $d
t=`$wp db tables --all-tables-with-prefix --format=csv`
$wp db export - --tables="$t" | gzip > $f
gzip -t $f
echo "Tabellen:     `echo $t | tr , '\n' | wc -l`"
echo "CREATE TABLE: `gzip -dc $f | grep -c '^CREATE TABLE'`"
sha256 -q $f
SCRIPT
```

Fertig ist die Sicherung erst, wenn `gzip -t` durchläuft und die Zahl der
`CREATE TABLE` der Tabellenzahl entspricht. `set -e` greift bei der Pipe nur auf
`gzip` - ein abgebrochener Export fällt erst am Tabellenvergleich auf.

### Aufräumen

Keine Arbeitsdateien und Sicherungen auf dem Server liegen lassen. Nach dem
geprüften Ergebnis:

1. Sicherung ins lokale `.tmp/` des Projekts holen und die sha256 gegen den Wert
   vom Server vergleichen (`sha256 -q` auf FreeBSD, `sha256sum` auf Linux):
   ```sh
   sudo ssh -C root@<server> "cat /root/<vorgang>/<datei>.sql.gz" > .tmp/<datei>.sql.gz
   ```
2. Remote auflisten, was liegt: das Sicherungsverzeichnis auf dem Host und ein
   eventuelles Arbeitsverzeichnis im Jail (`/tmp/<vorgang>/` mit Scripts).
3. Nur die eigenen Dateien löschen. Fremde Reste nicht anfassen, sondern melden.
