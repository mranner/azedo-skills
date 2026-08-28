# tcsh - FreeBSD-Admin-Patterns

Fertige Befehlsmuster fuer die haeufigen Admin-Aufgaben.

### Service-Management

```sh
# Direkt in tcsh (kein Wrapping noetig)
sudo ssh -C root@server "service apache24 status"
sudo ssh -C root@server "service apache24 restart"
sudo ssh -C root@server "service -e"                    # alle aktivierten Services

# sysrc fuer rc.conf
sudo ssh -C root@server "sysrc nginx_enable=YES"
sudo ssh -C root@server "sysrc -a | grep enable"        # alle enabled-Eintraege
```

### Package-Management (pkg)

```sh
sudo ssh -C root@server "pkg info"                       # installierte Packages
sudo ssh -C root@server "pkg info | grep php"            # filtern
sudo ssh -C root@server "pkg audit -F"                   # Sicherheitsluecken pruefen
sudo ssh -C root@server "pkg version -vIL="              # veraltete Packages

# pkg upgrade NIE automatisch ausfuehren — User macht das selbst
```

### Log-Analyse

```sh
# Einfache Pipes — tcsh nativ
sudo ssh -C root@server "tail -100 /var/log/messages"
sudo ssh -C root@server "tail -500 /var/log/auth.log | grep Failed"

# grep + tail + Pipe — tcsh nativ
sudo ssh -C root@server "grep ERROR /var/log/messages | tail -20"

# Stderr unterdruecken — sh -c wrappen
sudo ssh -C root@server "sh -c 'grep pattern /var/log/messages 2>/dev/null | wc -l'"

# Vom Host aus ins Jail greifen (Dateisystem direkt)
sudo ssh -C root@server "tail -100 /jails/jailname/var/log/httpd-error.log"

# iocage exec fuer Befehle im Jail-Kontext
sudo ssh -C root@server "iocage exec jailname sh -c 'grep ERROR /var/log/httpd-error.log | tail -20'"
```

### Netzwerk-Diagnose

```sh
# tcsh nativ
sudo ssh -C root@server "sockstat -4l"                   # offene Ports
sudo ssh -C root@server "sockstat -4l | grep :80"
sudo ssh -C root@server "netstat -rn"                    # Routing-Tabelle
sudo ssh -C root@server "ifconfig"                       # Interfaces
sudo ssh -C root@server "pfctl -sr"                      # pf Regeln
sudo ssh -C root@server "ipfw list"                      # ipfw Regeln

# Mit Stderr — sh -c
sudo ssh -C root@server "sh -c 'pfctl -sr 2>/dev/null'"
```

### Firewall (ipfw / pf)

```sh
# ipfw — tcsh nativ
sudo ssh -C root@server "ipfw list | tail -20"
sudo ssh -C root@server "ipfw table 1 list"

# pf — tcsh nativ
sudo ssh -C root@server "pfctl -sr"
sudo ssh -C root@server "pfctl -ss | grep 80"

# Regel hinzufuegen (ipfw)
sudo ssh -C root@server "ipfw add 100 deny ip from 1.2.3.4 to any"
```

### Jail-Verwaltung

```sh
# iocage
sudo ssh -C root@server "iocage list"
sudo ssh -C root@server "iocage exec jailname pkg info"

# ezjail (jexec) — JID per jls ermitteln
sudo ssh -C root@server "jls"
sudo ssh -C root@server "jexec 2 pkg info"

# ACHTUNG: JID kann sich nach Jail-Neustart aendern!
# Immer vorher pruefen: jls | grep jailname
```

### Disk / ZFS

```sh
sudo ssh -C root@server "zpool status"
sudo ssh -C root@server "zfs list"
sudo ssh -C root@server "df -h"
sudo ssh -C root@server "du -sh /www/home/*"
```

---
