---
name: tcsh
description: >
  tcsh-Referenz fuer Remote-Administration auf FreeBSD-Servern.
  Root-Shell auf allen FreeBSD-Servern ist tcsh — Befehle via sudo ssh root@host "..."
  werden in tcsh ausgefuehrt. Dieser Skill hilft, Befehle korrekt zu formulieren und
  typische bash-Gewohnheiten zu vermeiden.
  Wende diesen Skill IMMER automatisch an, wenn du Befehle via SSH auf FreeBSD-Servern
  ausfuehrst — auch ohne expliziten Aufruf.
  Trigger: /tcsh, SSH-Befehle auf FreeBSD, Remote-Administration.
trigger:
  - "tcsh"
  - "csh"
  - "FreeBSD shell"
  - "Remote-Befehl"
---

# tcsh — Remote-Administration auf FreeBSD

Referenz fuer die korrekte Formulierung von Befehlen auf FreeBSD-Servern,
deren Root-Shell `tcsh` ist. Claude denkt in bash/sh — dieser Skill
uebersetzt die gaengigsten Muster.

**Automatische Anwendung:** Gilt fuer jeden Befehl, der via
`sudo ssh root@<host> "..."` auf einem FreeBSD-Server ausgefuehrt wird.

---

## 1. Entscheidungsmatrix: tcsh nativ vs. sh -c

Vor jedem Remote-Befehl entscheiden: kann tcsh das direkt, oder muss ich wrappen?

### tcsh nativ (kein Wrapping noetig)

Einfache Befehle ohne sh-spezifische Syntax:

```sh
# Einzelbefehle
sudo ssh -C root@server "service apache24 restart"
sudo ssh -C root@server "pkg info"
sudo ssh -C root@server "cat /var/log/messages"
sudo ssh -C root@server "ls -la /www/home/"
sudo ssh -C root@server "sysrc nginx_enable=YES"

# Pipes funktionieren in tcsh
sudo ssh -C root@server "pkg info | grep php"
sudo ssh -C root@server "sockstat -4l | grep :80"
sudo ssh -C root@server "tail -100 /var/log/messages | grep error"

# Mehrere Befehle mit Semicolons
sudo ssh -C root@server "cd /tmp ; ls -la"
sudo ssh -C root@server "service apache24 stop ; service apache24 start"

# iocage/jexec — einfache Befehle
sudo ssh -C root@server "iocage exec jailname apachectl graceful"
sudo ssh -C root@server "jexec 2 sudo -u wwwuser wp --path=/www/home/wwwuser/domain core version"
```

### sh -c wrappen (Pflicht)

Sobald eines dieser Merkmale vorkommt:

| Merkmal | Beispiel | Warum tcsh scheitert |
|---------|----------|---------------------|
| Stderr-Redirect | `2>/dev/null`, `2>&1` | tcsh interpretiert `2` als Dateiname |
| `&&` / `||` | `cmd1 && cmd2` | "Invalid null command" |
| `$()` | `$(hostname)` | Nicht unterstuetzt, nur Backticks |
| Variablen-Zuweisung | `VAR=value cmd` | Keine Inline-Zuweisung |
| Funktionen | `f() { ...; }` | "Badly placed ()'s" |
| Bash-Arrays | `arr=(a b c)` | Andere Syntax |
| `[[ ]]` | `[[ -f file ]]` | Nicht unterstuetzt |
| Komplexe Schleifen | `for i in ...; do` | sh-Syntax, nicht tcsh |

```sh
# Stderr unterdruecken
sudo ssh -C root@server "sh -c 'ls /some/path 2>/dev/null'"

# Bedingte Ausfuehrung
sudo ssh -C root@server "sh -c 'test -f /etc/rc.conf && grep nginx /etc/rc.conf'"

# Command Substitution
sudo ssh -C root@server "sh -c 'echo Hostname: \$(hostname)'"

# Variable setzen und verwenden
sudo ssh -C root@server "sh -c 'COUNT=\$(pkg info | wc -l) ; echo \$COUNT Packages'"

# Schleife
sudo ssh -C root@server "sh -c 'for f in /var/log/*.log; do wc -l \$f; done'"

# Pipe + Stderr-Redirect
sudo ssh -C root@server "sh -c 'grep ERROR /var/log/messages 2>/dev/null | tail -20'"
```

### iocage/jexec + sh -c (doppelte Verschachtelung)

Aeussere Anfuehrungszeichen doppelt, innere einfach:

```sh
# iocage + Pipe
sudo ssh -C root@server "iocage exec jailname sh -c 'grep ERROR /var/log/httpd-error.log | tail -20'"

# jexec + Stderr-Redirect
sudo ssh -C root@server "jexec 2 sh -c 'cat /var/log/php-fpm.log 2>/dev/null | grep NOTICE'"
```

**Faustregel:** Im Zweifel wrappen. `sh -c` schadet nie, fehlende Wrapping-Erkennung schon.

---

## 2. tcsh-Syntax-Kurzreferenz

### Variablen

```tcsh
# Shell-Variable (lokal)
set var = "wert"
set liste = (eins zwei drei)

# Umgebungsvariable (vererbt an Kindprozesse)
setenv EDITOR vi
setenv PATH /usr/local/bin:$PATH

# Loeschen
unset var
unsetenv EDITOR

# Pruefen ob gesetzt
echo $?var              # 1=ja, 0=nein

# Listen-Zugriff (1-basiert!)
echo $liste[1]          # → eins
echo $liste[2-3]        # → zwei drei
echo $#liste            # → 3 (Anzahl)
```

**Achtung:** tcsh-Arrays sind 1-basiert (nicht 0-basiert wie bash).

### Arithmetic (@-Operator)

```tcsh
@ i = 5
@ i++
@ i = $i + 3
@ result = ( 10 * $i ) / 2
```

Leerzeichen um Operatoren sind Pflicht. Klammern bei Bitoperationen.

### Redirection

```tcsh
# Stdout
command > datei
command >> datei           # Append

# Stdout + Stderr zusammen
command >& datei
command >>& datei          # Append

# Stdin
command < datei

# KEIN separates Stderr-Redirect moeglich!
# Kein 2>/dev/null, kein 2>&1
# → sh -c wrappen oder >& /dev/null (beide Streams)
```

### Kontrollstrukturen

```tcsh
# if
if ( $status == 0 ) then
    echo "OK"
else if ( $status == 1 ) then
    echo "Fehler"
else
    echo "Unbekannt"
endif

# Einzeiler
if ( -f /etc/rc.conf ) echo "existiert"

# foreach
foreach f ( /var/log/*.log )
    echo $f
end

# while
@ i = 0
while ( $i < 10 )
    echo $i
    @ i++
end

# switch
switch ( $argv[1] )
    case "start":
        echo "Starte..."
        breaksw
    case "stop":
        echo "Stoppe..."
        breaksw
    default:
        echo "Usage: start|stop"
        breaksw
endsw
```

**Wichtig:** `foreach` in Remote-Befehlen (via SSH) bricht oft nach der
1. Iteration ab. Komplexe Schleifen immer als Script per `sh -s` einspeisen
oder in `sh -c` wrappen.

### File-Tests

```tcsh
if ( -e /pfad )    # existiert
if ( -f /pfad )    # regulaere Datei
if ( -d /pfad )    # Verzeichnis
if ( -r /pfad )    # lesbar
if ( -w /pfad )    # schreibbar
if ( -x /pfad )    # ausfuehrbar
if ( -z /pfad )    # leer (0 Bytes)
if ( -l /pfad )    # Symlink
```

### Vergleichsoperatoren

```tcsh
# String
if ( "$var" == "wert" )    # gleich
if ( "$var" != "wert" )    # ungleich
if ( "$var" =~ *.log )     # Glob-Match
if ( "$var" !~ *.log )     # Glob-Nicht-Match

# Numerisch
if ( $i > 5 )
if ( $i >= 10 )
if ( $i < 3 )
if ( $i <= 0 )

# Logisch
if ( $a > 0 && $b > 0 )   # UND (in Expressions erlaubt!)
if ( $a > 0 || $b > 0 )   # ODER
```

**Beachte:** `&&` und `||` funktionieren innerhalb von `if ( )`-Ausdruecken,
aber NICHT als Command-Chaining zwischen Befehlen.

### Aliases

```tcsh
alias ll 'ls -la'
alias grep 'grep --color=auto'

# Mit Argument-Selektoren
alias h 'history | grep \!*'       # alle Argumente
alias go 'cd \!^ ; ls'             # erstes Argument
alias mcd 'mkdir -p \!^ ; cd \!^'  # erstes Argument (2x)
```

---

## 3. Bash → tcsh Uebersetzungstabelle

| bash/sh | tcsh | Anmerkung |
|---------|------|-----------|
| `export VAR=val` | `setenv VAR val` | Kein `=` bei setenv |
| `VAR=val` | `set var = val` | Leerzeichen um `=` erlaubt |
| `VAR=val command` | `setenv VAR val ; command` | Keine Inline-Zuweisung |
| `$(command)` | `` `command` `` | Backticks, nicht verschachtelbar |
| `cmd1 && cmd2` | `cmd1 ; cmd2` oder `sh -c` | Kein bedingtes Chaining |
| `cmd1 \|\| cmd2` | `sh -c 'cmd1 \|\| cmd2'` | Nicht nativ moeglich |
| `2>/dev/null` | `>& /dev/null` (beide) oder `sh -c` | Kein separater Stderr-Redirect |
| `2>&1 \| grep` | `\|& grep` | Pipe inkl. Stderr |
| `[[ -f file ]]` | `if ( -f file )` | Anderer Syntax |
| `$((1+2))` | `@ r = 1 + 2` | @-Operator |
| `arr=(a b c)` | `set arr = (a b c)` | 1-basiert! |
| `${arr[0]}` | `$arr[1]` | 1-basiert, kein `${}` noetig |
| `${#arr[@]}` | `$#arr` | Listenlaenge |
| `${var:-default}` | nicht moeglich | `$?var` pruefen, dann setzen |
| `function f() {}` | nicht moeglich | Alias oder externes Script |
| `for i in ...; do` | `foreach i ( ... )` ... `end` | Anderer Syntax |
| `while ...; do` | `while ( ... )` ... `end` | Anderer Syntax |
| `case in esac` | `switch endsw` | Mit `breaksw` |
| `echo -n "text"` | `echo -n "text"` | Gleich |
| `printf` | nicht eingebaut | Via `awk` oder `/usr/bin/printf` |
| `read var` | `set var = $<` | Liest Zeile von stdin |

---

## 4. FreeBSD-Admin-Patterns

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

## 5. Quoting-Regeln (SSH → tcsh)

### Grundprinzip

SSH uebergibt den String an die Login-Shell des Ziels (tcsh).
Quoting-Ebenen: Lokal (bash auf mom) → SSH-Transport → tcsh auf Server.

```
Lokal:    sudo ssh root@server "AEUSSERE EBENE"
Server:   tcsh interpretiert: AEUSSERE EBENE
```

### Einfache Befehle — Doppelte Quotes aussen

```sh
sudo ssh -C root@server "service apache24 restart"
sudo ssh -C root@server "cat /etc/rc.conf"
```

### sh -c — Doppelt aussen, einfach innen

```sh
sudo ssh -C root@server "sh -c 'grep pattern /var/log/messages 2>/dev/null'"
```

### Variablen-Escaping

```sh
# Variable auf dem SERVER expandieren — Dollar escapen
sudo ssh -C root@server "echo \$SHELL"

# Variable LOKAL expandieren — kein Escape
LOCAL_PATH="/tmp/test"
sudo ssh -C root@server "cat $LOCAL_PATH"
```

### iocage/jexec + sh -c (3 Ebenen)

```sh
# Einfacher Befehl — kein sh -c
sudo ssh -C root@server "iocage exec jail apachectl graceful"

# Mit Pipe — sh -c, einfache Quotes innen
sudo ssh -C root@server "iocage exec jail sh -c 'grep ERROR /var/log/httpd-error.log | tail -20'"

# Mit Variablen — Dollar escapen
sudo ssh -C root@server "iocage exec jail sh -c 'echo \$USER'"
```

### Quoting zu komplex? → Script einspeisen

```sh
# Lokales Script per stdin an den Server schicken
sudo ssh -C root@server "sh -s" < /pfad/zum/lokalen/script.sh

# In ein Jail per jexec
sudo ssh -C root@server "jexec 2 sh -s" < /pfad/zum/lokalen/script.sh

# In ein Jail per iocage
sudo ssh -C root@server "iocage exec jailname sh -s" < /pfad/zum/lokalen/script.sh
```

Das umgeht tcsh-Eigenheiten und Quoting-Hoelle komplett — das Script
laeuft in `sh`, nicht in `tcsh`.

---

## 6. Bekannte Fallen

### Glob-Expansion / "No match"

tcsh expandiert `*` in Argumenten als Datei-Glob. Wenn kein File matcht:
`No match.`

```sh
# FALSCH — tcsh expandiert wp_*
sudo ssh -C root@server "jexec 2 sudo -u wwwuser wp db export --tables=wp_*options"
# → No match.

# RICHTIG — in sh -c wrappen (sh expandiert * nicht ohne Treffer)
sudo ssh -C root@server "sh -c 'jexec 2 sudo -u wwwuser wp db export --tables=wp_*options'"

# RICHTIG — Glob escapen
sudo ssh -C root@server "jexec 2 sudo -u wwwuser wp db export --tables=wp_\*options"
```

### History-Expansion mit !

tcsh interpretiert `!` auch in doppelten Anfuehrungszeichen als
History-Expansion:

```sh
# FALSCH — ! loest History-Expansion aus
sudo ssh -C root@server "echo Hello!"
# → Unrecognized history modifier

# RICHTIG — Backslash oder einfache Quotes
sudo ssh -C root@server "echo Hello\!"
sudo ssh -C root@server 'echo Hello!'
```

### ${var} und History-Modifier

tcsh interpretiert `${var}` gefolgt von `:` als Variable mit Modifier
(`:h`, `:t`, `:r` usw.). Das kollidiert mit Pfaden:

```sh
# FALSCH — tcsh sieht :/ als Modifier
sudo ssh -C root@server "echo ${HOME}:/usr/local"
# → Bad : modifier in $ ($)

# RICHTIG — Escapen oder sh -c
sudo ssh -C root@server "sh -c 'echo \${HOME}:/usr/local'"
```

### foreach bricht nach 1. Iteration ab

tcsh-`foreach` in Remote-Befehlen (via SSH) gibt oft nur die erste Iteration
aus. Ursache: die Shell sieht das `end` nicht korrekt.

```sh
# FALSCH — bricht nach erstem Element ab
sudo ssh -C root@server "foreach f (a b c)
echo $f
end"

# RICHTIG — sh -c mit for-Schleife
sudo ssh -C root@server "sh -c 'for f in a b c; do echo \$f; done'"

# RICHTIG — Script per stdin
sudo ssh -C root@server "sh -s" <<'EOF'
for f in a b c; do
    echo $f
done
EOF
```

### sed -i (BSD vs. GNU)

BSD-`sed` verlangt ein Backup-Suffix als Argument fuer `-i`:

```sh
# FALSCH — BSD-sed braucht Suffix
sudo ssh -C root@server "sed -i 's/alt/neu/' /etc/config.conf"
# → sed: 1: "/etc/config.conf": invalid command code

# RICHTIG — mit Backup-Suffix (Konvention: immer -i~)
sudo ssh -C root@server "sed -i~ 's/alt/neu/' /etc/config.conf"
```

### Keine Funktionen

tcsh kennt keine Shell-Funktionen. `f() { ...; }` ergibt "Badly placed ()'s":

```sh
# FALSCH
sudo ssh -C root@server "myfunc() { echo test; }"
# → Badly placed ()'s

# RICHTIG — Alias (fuer Einzeiler)
sudo ssh -C root@server "alias myfunc 'echo test' ; myfunc"

# RICHTIG — sh -c (fuer alles Komplexe)
sudo ssh -C root@server "sh -c 'myfunc() { echo test; }; myfunc'"
```
