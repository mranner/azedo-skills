# tcsh - Syntax-Kurzreferenz

Was in tcsh anders geschrieben wird als in bash.

## tcsh-Syntax-Kurzreferenz

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

**Beachte:** `&&` und `||` funktionieren sowohl innerhalb von `if ( )`-Ausdruecken
als auch als Command-Chaining zwischen Befehlen, samt Kurzschluss-Semantik.

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

## Bash → tcsh Uebersetzungstabelle

| bash/sh | tcsh | Anmerkung |
|---------|------|-----------|
| `export VAR=val` | `setenv VAR val` | Kein `=` bei setenv |
| `VAR=val` | `set var = val` | Leerzeichen um `=` erlaubt |
| `VAR=val command` | `setenv VAR val ; command` | Keine Inline-Zuweisung |
| `$(command)` | `` `command` `` | Backticks, nicht verschachtelbar |
| `cmd1 && cmd2` | `cmd1 && cmd2` | Gleich, auch der Kurzschluss |
| `cmd1 \|\| cmd2` | `cmd1 \|\| cmd2` | Gleich |
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
