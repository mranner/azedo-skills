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
allowed-tools: [Bash]
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

# ACHTUNG: iocage exec + sudo -u — NICHT direkt moeglich!
# iocage exec leitet an jexec weiter, jexec faengt -u als eigenen Flag ab.
# jexec <JID> (numerisch) hat dieses Problem NICHT.
# → Bei iocage exec immer sh -c wrappen:
sudo ssh -C root@server "iocage exec jailname sh -c 'sudo -u wwwuser wp --path=/www/home/wwwuser/domain core version'"
```

### sh -c wrappen (Pflicht)

Sobald eines dieser Merkmale vorkommt:

| Merkmal | Beispiel | Warum tcsh scheitert |
|---------|----------|---------------------|
| `iocage exec` + `sudo -u` | `iocage exec jail sudo -u user ...` | jexec faengt `-u` als eigenen Flag ab |
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

## 2. Quoting-Regeln (SSH → tcsh)

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

## 3. Bekannte Fallen

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

## 4. Nachschlagen

Was zum Formulieren eines konkreten Befehls gebraucht wird, liegt daneben:

| Datei | Inhalt |
|---|---|
| `references/syntax.md` | Variablen, Arithmetik, Redirection, Kontrollstrukturen, File-Tests, Vergleichsoperatoren, Aliases, Bash-nach-tcsh-Uebersetzungstabelle |
| `references/admin-patterns.md` | Service- und Package-Management, Log-Analyse, Netzwerk-Diagnose, Firewall, Jails, Disk/ZFS |
