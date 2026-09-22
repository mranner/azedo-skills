---
name: forgejo
description: >
  Vorhandene Bare-Repos in eine Forgejo-Instanz uebernehmen (Adopt) und den
  HTTPS-Zugang dorthin einrichten und pruefen: Vorpruefung von Bare-Repo,
  Arbeitskopie und Zielplatz, Verschieben samt `chown` und HEAD-Korrektur, der
  Adopt ueber die API mit einem Einweg-Token, dazu Credential-Helper-Scoping
  messen und die Credential-Datei auf Form und Rechte pruefen, ohne sie
  auszugeben. Nutze diesen Skill wenn ein Git-Repo in die eigene Forge soll
  oder ein Push dorthin nicht funktioniert. Auch bei "nimm das Repo in Forgejo
  auf", "adopt", "git.<domain> geht nicht", "could not read Username", "401
  trotz frischem Token", "der Push haengt". Nicht zustaendig fuer GitHub und
  nicht fuer Issues oder Pull Requests - dafuer gibt es `fj` bzw. die
  Weboberflaeche. Trigger: /forgejo.
---

# forgejo -- Repos uebernehmen und den Zugang dorthin

**Aufruf:** `python3 "$SKILL_DIR/forgejo" <subcommand> [optionen]`

`$SKILL_DIR` ist das Verzeichnis dieser SKILL.md. Das Script ist stdlib-only;
auf dem Forgejo-Host werden `curl`, `sqlite3` und `git` gebraucht.

Schreibende Schritte laufen erst mit `--commit`. Ohne das Flag zeigen `adopt`
und `access-setup` nur, was passieren wuerde.

## Config

`~/.claude/forgejo.json`, Vorlage `forgejo.example.json`. Anderer Pfad ueber
`FORGEJO_CONFIG`. Die Werte stehen bewusst nicht im Skill - eine zweite
Instanz braucht nur eine zweite Config.

| Schluessel | Bedeutung |
|---|---|
| `host` | oeffentlicher Name der Forge, z.B. `git.example.org` - **nie** `127.0.0.1:<port>` |
| `forgejo-host` | Rechner, auf dem Forgejo laeuft |
| `ssh` | Befehl als Liste, der dort root wird, z.B. `["sudo","ssh","-C","root@..."]` |
| `api-user` | Forgejo-Benutzer, auf dessen Namen der Einweg-Token ausgestellt wird |
| `owner` | Default-Organisation, je Aufruf mit `--owner` uebersteuerbar |
| `service-user` | Unix-Benutzer des Dienstes (Default `git`) |
| `binary`, `app-ini`, `work-path`, `repo-root`, `db` | Pfade auf dem Forgejo-Host |

**Lokal oder ueber ssh** entscheidet das Script selbst: lokal nur, wenn es auf
`forgejo-host` **und** als root laeuft. Auf dem Host als normaler Benutzer zu
sitzen genuegt nicht - `mv`, `chown` und `su -m` brauchen root, und ein
`sudo <programm>` ist dort oft nicht passwortlos freigegeben. Dann geht der Weg
ueber `ssh`, auch wenn er zum selben Rechner zurueckfuehrt.

## Ablauf einer Uebernahme

```bash
forgejo preflight <repo> --bare /pfad/<repo>.git --user <eigentuemer> \
        --worktree /pfad/arbeitskopie
forgejo adopt <repo> --bare /pfad/<repo>.git --user <eigentuemer>          # Trockenlauf
forgejo adopt <repo> --bare /pfad/<repo>.git --user <eigentuemer> --commit
```

Danach bleiben zwei Schritte beim Menschen (siehe unten): das Remote der
Arbeitskopie und die Treffer in der Projektdoku.

### preflight

Legt drei Dinge nebeneinander und nennt Blocker statt sie zu umgehen:

- **Bare-Repo**: `is-bare`, `HEAD`, Branch-Spitzen. Zeigt `HEAD` auf einen
  Branch, den es nicht gibt, meldet git spaeter "does not have any commits yet",
  obwohl Objekte da sind.
- **Arbeitskopie** (optional): sauber oder nicht, und jede Branch-Spitze gegen
  das Bare-Repo. **Ein Bare-Repo, das hinter der Arbeitskopie zurueckliegt, muss
  vor dem `mv` auffallen** - das ist die einzige Klasse von Datenverlust, die
  dieser Ablauf hat.
- **Zielplatz**: `git ls-remote` gegen die Forge. `Repository not found` ist
  hier der **Positivbefund** und ersetzt zwei Einzeltests: der Zugriff war
  authentifiziert, und am Ziel liegt nichts halb da.

### adopt

Mit `--commit` in dieser Reihenfolge:

1. Refs des Quell-Repos notieren
2. `mkdir -p <root>/<owner>`, `mv`, `chown -R <service-user>` auf das
   **Owner-Verzeichnis** (nicht nur auf das Repo - sonst bleibt das
   Elternverzeichnis bei root)
3. `--head-branch <branch>` setzt `symbolic-ref HEAD` **vor** dem Adopt
4. Refs erneut lesen und vergleichen - quert das `mv` eine Dateisystemgrenze,
   ist es physisches Kopieren und ein Abbruch hinterlaesst eine Teilkopie
5. `GET admin/unadopted` als Zwischenpruefung; fehlt das Repo dort, stimmt am
   Dateisystem etwas nicht und der POST eruebrigt sich
6. `POST admin/unadopted/<owner>/<repo>` - Erfolg ist **HTTP 204**
7. `GET repos/<owner>/<repo>`: `default_branch`, `empty`, `private`

Verschoben wird bewusst, nicht kopiert: ein Push auf den alten Pfad scheitert
danach hoerbar, statt still in ein Repo zu laufen, von dem die Forge nichts
mitbekommt. Divergierende Staende sind der teurere Fehler.

**HEAD vor dem Adopt richten, nicht danach.** Bei
`doctor --run synchronize-repo-heads` ist nicht belegt, in welche Richtung
abgeglichen wird; ein falsch eingetragener `default_branch` koennte
festgeschrieben statt korrigiert werden. Der direkte Weg ist nachvollziehbar
und in einer Zeile umkehrbar.

### Was der Skill nicht tut

- **`git remote set-url`** bleibt beim User. Der Aufruf wird in manchen
  Sessions vom Permission-Classifier verweigert und in anderen nicht. Wird er
  verweigert, geht er **zurueck an den User** - ausdruecklich nicht an eine
  andere Session: das waere der Weg, auf dem eine Permission-Entscheidung
  stillschweigend umgangen wird.
- **Suchen-und-Ersetzen fuer das alte Remote in der Projektdoku.** Ein `grep`
  liefert regelmaessig Treffer, die nichts mit Git zu tun haben (Mailversand,
  Deployment-Ziele). Treffer vorlegen, Mensch entscheidet.

## Zugang einrichten und pruefen

```bash
forgejo access-check --file ~/.git-credentials-forgejo --remote-check <owner>/<repo>
forgejo access-setup --file ~/.git-credentials-forgejo --commit
forgejo access-setup --file ~/.git-credentials-forgejo --fix-file --commit
```

### Scoping messen, nicht herleiten

Ob der Helper **global** gesetzt werden darf oder **host-geschachtelt** gesetzt
werden muss, haengt daran, ob schon ein Helper aus einer Ebene **oberhalb von
`global`** fuer alle Hosts gilt (auf macOS typischerweise `osxkeychain`). Die
naheliegende Regel "kommt `osxkeychain` aus `/opt/homebrew/etc/gitconfig`"
traegt **nicht** - auf einem Rechner ohne Homebrew liefert dieselbe
Konfiguration den Pfad aus Xcode, und die Regel haette dort faelschlich "global
genuegt" gesagt.

`access-check` misst deshalb drei Dinge: alle `credential`-Eintraege mit ihrer
Herkunft, `--get-urlmatch` fuer die Forge und `--get-urlmatch` fuer einen
fremden Host. Der dritte Aufruf ist die **Negativprobe** und gehoert dazu - er
belegt, dass die Umstellung die uebrigen Hosts nicht angefasst hat.

`--scope` bei `access-setup`: `global-host` (Default, host-geschachtelt),
`global`, `repo`. **Die Ablage ist ein Parameter, kein Muster mit
Ausreissern** - vier Installationen hatten vier Varianten, bis hin zu einem
anderen Unix-Benutzer als Forgejo-Benutzer.

### Zeiger und Wert trennen

Den **Helper-Zeiger** darf die Session setzen, er enthaelt kein Geheimnis. Die
**Credential-Datei** schreibt der User in einem eigenen Terminal; `access-setup`
gibt die Zeile dafuer aus. Geprueft werden danach nur Form, Rechte und Existenz:

| Pruefung | Bedeutung |
|---|---|
| Form passend = 1 | die Zeile `https://<user>:<token>@<host>` ist vollstaendig |
| Platzhalter = 0 | eine kopierte Vorlage mit `<token>` scheitert mit derselben Meldung wie ein falscher Token |
| Rechte 600 | mit 644 funktioniert alles und jeder Account auf dem Rechner liest mit |

Nur Zaehler gehen nach stdout, nie Inhalt. `--fix-file` ergaenzt einen fehlenden
URL-Rahmen und setzt 0600 - der Wert laeuft dabei durch keine Ausgabe.

**Zugangsnachweis ueber `git ls-remote`, nicht ueber `curl`.** Beides belegt
Token und Org-Pfad, aber git holt den Wert aus dem Helper, waehrend ein
`-H "Authorization: token ..."` ihn in die Kommandozeile und damit in jede
Prozessliste und jedes Protokoll schreibt.

## Einweg-Token

Jeder API-Aufruf des Skills (`api`, intern auch `adopt`) stellt einen eigenen
Token aus, benutzt ihn und loescht ihn wieder - alles in einem Script auf dem
Forgejo-Host. Der Wert bleibt in einer Shell-Variablen dort und erreicht weder
die lokale Kommandozeile noch das Transcript.

```bash
forgejo api GET admin/unadopted
forgejo api PATCH repos/<owner>/<repo> --data '{"archived": true}'
```

Zwei Dinge, die dabei nicht offensichtlich sind:

- **`-w <work-path>` ist nicht kosmetisch.** Ohne den Work-Path gibt
  `generate-access-token` vor dem Wert eine weitere Zeile aus, die mit in die
  Variable laeuft. Das Ergebnis ist ein **401** - mit einem Token, der in der
  Datenbank korrekt angelegt ist. Das Symptom zeigt auf die Scopes, die Ursache
  liegt im Aufruf.
- **Der Token raeumt sich nicht ueber die API weg.**
  `DELETE /api/v1/users/<user>/tokens/<name>` verlangt Basic Auth und
  beantwortet einen Token-Header mit 401; `forgejo admin user` hat kein
  Gegenstueck zum Anlegen. Bleibt `delete from access_token where name=...`,
  ausgefuehrt als der Dienst-Benutzer und **nicht als root** - sonst gehoeren
  `-wal` und `-shm` danach root.

## HTTP-Merkregel

| Code | Bedeutung |
|---|---|
| **401** | nicht angenommen - kein Token oder ein verstuemmelter |
| **403** | abgelehnt - der Token kam an; anonyme Zugriffe landen bei gesetztem `REQUIRE_SIGNIN_VIEW` immer hier |
| **404** | angenommen **und** Zielplatz frei |

Davor liegen zwei Fehlerbilder, die wie "kein Zugang" aussehen und keins sind:

- **`fatal: could not read Username`** - nackter Tokenwert ohne URL-Rahmen in
  der `store`-Datei. Der Helper kann sie nicht parsen, es ist kein Auth-Fehler.
  Wer das als Scope-Problem liest, stellt einen zweiten Token aus und hat danach
  zwei. `access-check --file` findet es.
- **`git push` haengt stumm** - ohne hinterlegten Zugang wartet git ohne TTY auf
  eine Eingabe, die nie kommt. Der Skill setzt in jedem git-Aufruf
  `GIT_TERMINAL_PROMPT=0`; von Hand gehoert es ebenfalls davor.

## Verwandtes

Was das Forgejo-CLI kann und was nur die API kann, die Fallstricke von `fj` und
die Eigenheiten der Instanz stehen im Infra-Wiki (Skill `wiki`):

```
/wiki query "Forgejo bedienen"
```

`fj` kennt **kein** `adopt` - die Uebernahme bleibt ein API-Aufruf. `gh` ist
unbrauchbar (GitHub-only).
