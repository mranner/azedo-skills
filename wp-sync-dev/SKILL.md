---
name: wp-sync-dev
description: >
  Synchronisiert WordPress-Plugins und -Themes zwischen Produktions-Installationen
  (in FreeBSD-Jails) und der DEV-Umgebung (dev.example.at) via rsync.
  Bidirektional: Prod → DEV und DEV → Prod.
  Trigger: /wp-sync-dev, "sync plugin", "plugin von prod holen", "theme auf dev kopieren",
  "plugin auf prod deployen"
---

# wp-sync-dev – WordPress Plugin/Theme Sync

Synchronisiert Plugins und Themes zwischen Produktions-WPs (FreeBSD-Jails) und
der DEV-Umgebung auf mom.azedo.at via rsync.

## Pfad-Schema

### DEV (Jail `dev.example.at` auf mom.azedo.at)

`dev.example.at` ist ein **iocage-Jail** auf mom. Fuer den **Datei**-Zugriff (rsync, chmod)
sind die DEV-Vhosts vom mom-Host aus direkt unter dem folgenden Pfad erreichbar — **kein**
Jail-Prefix noetig:

```
/www/virtual/dev.example.at/<site>/wp-content/plugins/<plugin-name>/
/www/virtual/dev.example.at/<site>/wp-content/themes/<theme-name>/
```

> **Nur der Dateizugriff laeuft host-seitig.** Alles Laufzeitartige (wp-cli, WordPress)
> muss **im Jail** laufen:
> `iocage exec dev.example.at sh -c 'sudo -u www wp --path=/www/virtual/dev.example.at/<site> …'`
> — nie `wp` direkt auf dem mom-Host (dort ist `wp` nicht im PATH). Details: Skill `wp-cli`,
> Wiki-Procedure `wp-cli-in-jails`, Server-Entity `mom-azedo-at`.

### Prod (Jail-Host)

Vom Jail-Host aus (nicht aus der Jail heraus) sind die Dateien direkt zugaenglich:

**iocage:**
```
/iocage/jails/<jailname>/root/www/home/<wwwuser>/<domain>/wp-content/plugins/<name>/
/iocage/jails/<jailname>/root/www/home/<wwwuser>/<domain>/wp-content/themes/<name>/
```

**ezjail:**
```
/www/home/<wwwuser>/<domain>/wp-content/plugins/<name>/
/www/home/<wwwuser>/<domain>/wp-content/themes/<name>/
```

## Workflow

### 1. Pfade ermitteln

Quell- und Zielpfade muessen bekannt sein. Wenn nicht angegeben:

- **DEV-Site:** `ls /www/virtual/dev.example.at/` und User fragen
- **Prod-Domain:** Im Jail nachschauen:
  ```sh
  sudo ssh -C root@<jailer> "<jail-exec> ls /www/home/<wwwuser>/"
  ```
  Bei iocage: `iocage exec <jailname> ...`
  Bei ezjail: `jexec <JID> ...` (JID per `jls` ermitteln)
- **Plugin/Theme-Name:** Im jeweiligen `wp-content/plugins/` bzw. `wp-content/themes/` nachschauen

### 2. rsync ausfuehren

Immer von mom.azedo.at aus ausfuehren (als root via `sudo ssh -C root@localhost`).
Trailing Slash bei Quell- und Zielpfad beachten.

**Prod → DEV (pull):**
```sh
sudo ssh -C root@localhost "rsync -a root@<jailer>:<prod-pfad>/ <dev-pfad>/"
```

**DEV → Prod (push):**
```sh
sudo ssh -C root@localhost "rsync -a <dev-pfad>/ root@<jailer>:<prod-pfad>/"
```

### 3. Permissions setzen

**Ziel DEV** — immer gleich:
```sh
sudo ssh -C root@localhost "cd <dev-pfad> && chown -R www:azedo . && find . -type d -exec chmod 775 {} \; && find . -type f -exec chmod 664 {} \;"
```

**Ziel Prod** — an der bestehenden Installation orientieren. Vorher pruefen:
```sh
sudo ssh -C root@<jailer> "<jail-exec> ls -la <domain-pfad>/wp-content/plugins/ | head -5"
```

Owner und Permissions der bestehenden Dateien uebernehmen. Typisch:
```sh
sudo ssh -C root@<jailer> "cd <prod-pfad> && chown -R <wwwuser>:<group> . && find . -type d -exec chmod <dir-mode> {} \; && find . -type f -exec chmod <file-mode> {} \;"
```

### 4. Aufraeumen

macOS- und Finder-Artefakte entfernen (in beiden Richtungen):
```sh
find <zielpfad> \( -name "._*" -or -name ".DS*" \) -print -delete
```

Diesen find-Befehl im selben Kontext wie Schritt 3 ausfuehren (auf dem jeweiligen Ziel-Server).

## Hinweise

- rsync immer von mom.azedo.at aus starten, nie vom Jail-Host zurueck nach mom
- Bei ezjail liegen die Dateien direkt auf dem Host unter `/www/home/...`, kein Jail-Pfad-Prefix noetig
- Bei iocage ist der Prefix `/iocage/jails/<jailname>/root/...`
- Fuer den rsync-Zugriff wird der Jail-Host-Pfad verwendet (nicht der Pfad innerhalb der Jail)
- Nach einem Push auf Prod: Apache-Reload ist fuer Plugins/Themes normalerweise nicht noetig
- `--delete` bei rsync nur verwenden wenn ausdruecklich gewuenscht (entfernt Dateien im Ziel die in der Quelle nicht existieren)
