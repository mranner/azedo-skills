---
name: wp-sync-dev
description: >
  Synchronisiert WordPress-Plugins und -Themes zwischen Produktions-Installationen
  (in FreeBSD-Jails) und der DEV-Umgebung via rsync.
  Bidirektional: Prod → DEV und DEV → Prod.
  Trigger: /wp-sync-dev, "sync plugin", "plugin von prod holen", "theme auf dev kopieren",
  "plugin auf prod deployen"
---

# wp-sync-dev – WordPress Plugin/Theme Sync

Synchronisiert Plugins und Themes zwischen Produktions-WPs (FreeBSD-Jails) und
der DEV-Umgebung via rsync.

## DEV-Umgebung ermitteln

Host und Jail-Name der DEV-Umgebung stehen bewusst **nicht** in diesem Skill,
sondern im Infra-Wiki — dort sind sie samt Jail-IP, Pfaden und Zugang gepflegt.
Vor dem ersten Schritt nachschlagen (Skill `wiki`):

```
/wiki query "DEV-Webhost"
```

Die Server-Entity mit der Rolle `jailer`, die den DEV-Webhost betreibt, liefert
die drei Platzhalter dieser Anleitung:

| Platzhalter   | Bedeutung                                                      |
|---------------|----------------------------------------------------------------|
| `<dev-host>`  | Host, auf dem das DEV-Jail laeuft — von dort laeuft **jedes** rsync |
| `<dev-jail>`  | Name des iocage-Jails der DEV-Umgebung                          |
| `<dev-group>` | Gruppe der Datei-Owner auf den DEV-Vhosts (Web-User ist `www`)  |

## Pfad-Schema

### DEV (Jail `<dev-jail>` auf `<dev-host>`)

Das DEV-Jail ist ein **iocage-Jail**. Fuer den **Datei**-Zugriff (rsync, chmod)
sind die DEV-Vhosts vom Host aus direkt unter dem folgenden Pfad erreichbar — **kein**
Jail-Prefix noetig:

```
/www/virtual/<dev-jail>/<site>/wp-content/plugins/<plugin-name>/
/www/virtual/<dev-jail>/<site>/wp-content/themes/<theme-name>/
```

> **Nur der Dateizugriff laeuft host-seitig.** Alles Laufzeitartige (wp-cli, WordPress)
> muss **im Jail** laufen:
> `iocage exec <dev-jail> sh -c 'sudo -u www wp --path=/www/virtual/<dev-jail>/<site> …'`
> — nie `wp` direkt auf dem Jail-Host (dort ist `wp` nicht im PATH). Details: Skill `wp-cli`,
> Wiki-Procedure `wp-cli-in-jails`, Server-Entity des DEV-Hosts.

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

- **DEV-Site:** `ls /www/virtual/<dev-jail>/` und User fragen
- **Prod-Domain:** Im Jail nachschauen:
  ```sh
  sudo ssh -C root@<jailer> "<jail-exec> ls /www/home/<wwwuser>/"
  ```
  Bei iocage: `iocage exec <jailname> ...`
  Bei ezjail: `jexec <JID> ...` (JID per `jls` ermitteln)
- **Plugin/Theme-Name:** Im jeweiligen `wp-content/plugins/` bzw. `wp-content/themes/` nachschauen

### 2. rsync ausfuehren

Immer von `<dev-host>` aus ausfuehren (als root; arbeitet man bereits dort, via `sudo ssh -C root@localhost`).
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

**Ziel DEV** — immer gleich (`<dev-group>` aus der Server-Entity, s.o.):
```sh
sudo ssh -C root@localhost "cd <dev-pfad> && chown -R www:<dev-group> . && find . -type d -exec chmod 775 {} \; && find . -type f -exec chmod 664 {} \;"
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

- rsync immer von `<dev-host>` aus starten, nie vom Prod-Jail-Host zurueck
- Bei ezjail liegen die Dateien direkt auf dem Host unter `/www/home/...`, kein Jail-Pfad-Prefix noetig
- Bei iocage ist der Prefix `/iocage/jails/<jailname>/root/...`
- Fuer den rsync-Zugriff wird der Jail-Host-Pfad verwendet (nicht der Pfad innerhalb der Jail)
- Nach einem Push auf Prod: Apache-Reload ist fuer Plugins/Themes normalerweise nicht noetig
- `--delete` bei rsync nur verwenden wenn ausdruecklich gewuenscht (entfernt Dateien im Ziel die in der Quelle nicht existieren)
