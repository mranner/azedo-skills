---
name: forgejo
description: >
  Bare-Repos in eine Forgejo-Instanz übernehmen (Adopt), neue Repos und
  Organisationen anlegen und den HTTPS-Zugang einrichten und prüfen:
  Vorprüfung, Verschieben samt HEAD-Korrektur, API-Aufrufe mit Einweg-Token,
  Credential-Helper und -Datei prüfen, ohne Werte auszugeben. Nutze diesen
  Skill, wenn ein Git-Repo in die eigene Forge soll oder ein Push dorthin
  scheitert; nicht für GitHub, Issues oder Pull Requests. Auch bei "nimm das
  Repo in Forgejo auf", "leg ein Repo oder eine Org in Forgejo an",
  "could not read Username", "401 trotz frischem Token", "der Push hängt".
  Trigger: /forgejo.
---

# forgejo -- Repos übernehmen oder anlegen und den Zugang dorthin

**Aufruf:** `python3 "$SKILL_DIR/forgejo" <subcommand> [optionen]`

`$SKILL_DIR` ist das Verzeichnis dieser SKILL.md. Das Script ist stdlib-only;
auf dem Forgejo-Host werden `curl`, `sqlite3` und `git` gebraucht.

Schreibende Schritte laufen erst mit `--commit`. Ohne das Flag zeigen `adopt`
und `access-setup` nur, was passieren würde.

## Config

`~/.claude/forgejo.json`, Vorlage `forgejo.example.json`. Anderer Pfad über
`FORGEJO_CONFIG`. Die Werte stehen bewusst nicht im Skill - eine zweite
Instanz braucht nur eine zweite Config.

| Schlüssel | Bedeutung |
|---|---|
| `host` | öffentlicher Name der Forge, z.B. `git.example.org` - **nie** `127.0.0.1:<port>` |
| `forgejo-host` | Rechner, auf dem Forgejo läuft |
| `ssh` | Befehl als Liste, der dort root wird, z.B. `["sudo","ssh","-C","root@..."]` |
| `api-user` | Forgejo-Benutzer, auf dessen Namen der Einweg-Token ausgestellt wird |
| `owner` | Default-Organisation, je Aufruf mit `--owner` übersteuerbar |
| `service-user` | Unix-Benutzer des Dienstes (Default `git`) |
| `binary`, `app-ini`, `work-path`, `repo-root`, `db` | Pfade auf dem Forgejo-Host |

**Lokal oder über ssh** entscheidet das Script selbst: lokal nur, wenn es auf
`forgejo-host` **und** als root läuft. Auf dem Host als normaler Benutzer zu
sitzen genügt nicht - `mv`, `chown` und `su -m` brauchen root, und ein
`sudo <programm>` ist dort oft nicht passwortlos freigegeben. Dann geht der Weg
über `ssh`, auch wenn er zum selben Rechner zurückführt.

## Ablauf einer Übernahme

```bash
forgejo preflight <repo> --bare /pfad/<repo>.git --user <eigentümer> \
        --worktree /pfad/arbeitskopie
forgejo adopt <repo> --bare /pfad/<repo>.git --user <eigentümer>          # Trockenlauf
forgejo adopt <repo> --bare /pfad/<repo>.git --user <eigentümer> --commit
```

Danach bleiben zwei Schritte beim Menschen (siehe unten): das Remote der
Arbeitskopie und die Treffer in der Projektdoku.

### preflight

Legt drei Dinge nebeneinander und nennt Blocker statt sie zu umgehen:

- **Bare-Repo**: `is-bare`, `HEAD`, Branch-Spitzen. Zeigt `HEAD` auf einen
  Branch, den es nicht gibt, meldet git später "does not have any commits yet",
  obwohl Objekte da sind.
- **Arbeitskopie** (optional): sauber oder nicht, und jede Branch-Spitze gegen
  das Bare-Repo. **Ein Bare-Repo, das hinter der Arbeitskopie zurückliegt, muss
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
   ist es physisches Kopieren und ein Abbruch hinterlässt eine Teilkopie
5. `GET admin/unadopted` als Zwischenprüfung; fehlt das Repo dort, stimmt am
   Dateisystem etwas nicht und der POST erübrigt sich
6. `POST admin/unadopted/<owner>/<repo>` - Erfolg ist **HTTP 204**
7. `GET repos/<owner>/<repo>`: `default_branch`, `empty`, `private`

Verschoben wird bewusst, nicht kopiert: ein Push auf den alten Pfad scheitert
danach hörbar, statt still in ein Repo zu laufen, von dem die Forge nichts
mitbekommt. Divergierende Stände sind der teurere Fehler.

**HEAD vor dem Adopt richten, nicht danach.** Bei
`doctor --run synchronize-repo-heads` ist nicht belegt, in welche Richtung
abgeglichen wird; ein falsch eingetragener `default_branch` könnte
festgeschrieben statt korrigiert werden. Der direkte Weg ist nachvollziehbar
und in einer Zeile umkehrbar.

### Was der Skill nicht tut

- **`git remote set-url`** bleibt beim User. Der Aufruf wird in manchen
  Sessions vom Permission-Classifier verweigert und in anderen nicht. Wird er
  verweigert, geht er **zurück an den User** - ausdrücklich nicht an eine
  andere Session: das wäre der Weg, auf dem eine Permission-Entscheidung
  stillschweigend umgangen wird.
- **Suchen-und-Ersetzen für das alte Remote in der Projektdoku.** Ein `grep`
  liefert regelmäßig Treffer, die nichts mit Git zu tun haben (Mailversand,
  Deployment-Ziele). Treffer vorlegen, Mensch entscheidet.

## Repo oder Organisation anlegen

Für ein **neues** Repo ohne Bare-Repo auf der Platte genügt `api`, kein
Adopt. Zuerst den Zielplatz prüfen: **404** heißt frei (siehe HTTP-Merkregel).
`api` kennt kein `--commit` - der POST legt sofort an.

```bash
forgejo api GET  repos/<org>/<repo>      # 404 = Platz frei
forgejo api POST orgs/<org>/repos --data '{"name":"<repo>","private":true,"default_branch":"main"}'   # 201
```

Fehlt die Organisation selbst, vorher anlegen (`visibility`: `public`,
`limited` oder `private`):

```bash
forgejo api GET  orgs/<org>              # 404 = Platz frei
forgejo api POST orgs --data '{"username":"<org>","visibility":"private"}'   # 201
```

Danach in der Arbeitskopie `git remote add` und `git push -u`, beides mit
`GIT_TERMINAL_PROMPT=0` davor.

## Zugang einrichten und prüfen

```bash
forgejo access-check --file ~/.git-credentials-forgejo --remote-check <owner>/<repo>
forgejo access-setup --file ~/.git-credentials-forgejo --commit
forgejo access-setup --file ~/.git-credentials-forgejo --fix-file --commit
```

### Scoping messen, nicht herleiten

Ob der Helper **global** gesetzt werden darf oder **host-geschachtelt** gesetzt
werden muss, hängt daran, ob schon ein Helper aus einer Ebene **oberhalb von
`global`** für alle Hosts gilt (auf macOS typischerweise `osxkeychain`). Die
naheliegende Regel "kommt `osxkeychain` aus `/opt/homebrew/etc/gitconfig`"
trägt **nicht** - auf einem Rechner ohne Homebrew liefert dieselbe
Konfiguration den Pfad aus Xcode, und die Regel hätte dort fälschlich "global
genügt" gesagt.

`access-check` misst deshalb drei Dinge: alle `credential`-Einträge mit ihrer
Herkunft, `--get-urlmatch` für die Forge und `--get-urlmatch` für einen
fremden Host. Der dritte Aufruf ist die **Negativprobe** und gehört dazu - er
belegt, dass die Umstellung die übrigen Hosts nicht angefasst hat.

`--scope` bei `access-setup`: `global-host` (Default, host-geschachtelt),
`global`, `repo`. **Die Ablage ist ein Parameter, kein Muster mit
Ausreißern** - vier Installationen hatten vier Varianten, bis hin zu einem
anderen Unix-Benutzer als Forgejo-Benutzer.

### Zeiger und Wert trennen

Den **Helper-Zeiger** darf die Session setzen, er enthält kein Geheimnis. Die
**Credential-Datei** schreibt der User in einem eigenen Terminal; `access-setup`
gibt die Zeile dafür aus. Geprüft werden danach nur Form, Rechte und Existenz:

| Prüfung | Bedeutung |
|---|---|
| Form passend = 1 | die Zeile `https://<user>:<token>@<host>` ist vollständig |
| Platzhalter = 0 | eine kopierte Vorlage mit `<token>` scheitert mit derselben Meldung wie ein falscher Token |
| Rechte 600 | mit 644 funktioniert alles und jeder Account auf dem Rechner liest mit |

Nur Zähler gehen nach stdout, nie Inhalt. `--fix-file` ergänzt einen fehlenden
URL-Rahmen und setzt 0600 - der Wert läuft dabei durch keine Ausgabe.

**Zugangsnachweis über `git ls-remote`, nicht über `curl`.** Beides belegt
Token und Org-Pfad, aber git holt den Wert aus dem Helper, während ein
`-H "Authorization: token ..."` ihn in die Kommandozeile und damit in jede
Prozessliste und jedes Protokoll schreibt.

## Einweg-Token

Jeder API-Aufruf des Skills (`api`, intern auch `adopt`) stellt einen eigenen
Token aus, benutzt ihn und löscht ihn wieder - alles in einem Script auf dem
Forgejo-Host. Der Wert bleibt in einer Shell-Variablen dort und erreicht weder
die lokale Kommandozeile noch das Transcript.

```bash
forgejo api GET admin/unadopted
forgejo api PATCH repos/<owner>/<repo> --data '{"archived": true}'
```

Zwei Dinge, die dabei nicht offensichtlich sind:

- **`-w <work-path>` ist nicht kosmetisch.** Ohne den Work-Path gibt
  `generate-access-token` vor dem Wert eine weitere Zeile aus, die mit in die
  Variable läuft. Das Ergebnis ist ein **401** - mit einem Token, der in der
  Datenbank korrekt angelegt ist. Das Symptom zeigt auf die Scopes, die Ursache
  liegt im Aufruf.
- **Der Token räumt sich nicht über die API weg.**
  `DELETE /api/v1/users/<user>/tokens/<name>` verlangt Basic Auth und
  beantwortet einen Token-Header mit 401; `forgejo admin user` hat kein
  Gegenstück zum Anlegen. Bleibt `delete from access_token where name=...`,
  ausgeführt als der Dienst-Benutzer und **nicht als root** - sonst gehören
  `-wal` und `-shm` danach root.

## HTTP-Merkregel

| Code | Bedeutung |
|---|---|
| **401** | nicht angenommen - kein Token oder ein verstümmelter |
| **403** | abgelehnt - der Token kam an; anonyme Zugriffe landen bei gesetztem `REQUIRE_SIGNIN_VIEW` immer hier |
| **404** | angenommen **und** Zielplatz frei |

Davor liegen zwei Fehlerbilder, die wie "kein Zugang" aussehen und keins sind:

- **`fatal: could not read Username`** - nackter Tokenwert ohne URL-Rahmen in
  der `store`-Datei. Der Helper kann sie nicht parsen, es ist kein Auth-Fehler.
  Wer das als Scope-Problem liest, stellt einen zweiten Token aus und hat danach
  zwei. `access-check --file` findet es.
- **`git push` hängt stumm** - ohne hinterlegten Zugang wartet git ohne TTY auf
  eine Eingabe, die nie kommt. Der Skill setzt in jedem git-Aufruf
  `GIT_TERMINAL_PROMPT=0`; von Hand gehört es ebenfalls davor.

## Verwandtes

Was das Forgejo-CLI kann und was nur die API kann, die Fallstricke von `fj` und
die Eigenheiten der Instanz stehen im Infra-Wiki (Skill `wiki`):

```
/wiki query "Forgejo bedienen"
```

`fj` kennt **kein** `adopt` - die Übernahme bleibt ein API-Aufruf. `gh` ist
unbrauchbar (GitHub-only).
