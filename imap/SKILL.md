---
name: imap
description: >
  IMAP-Zugriff auf mehrere Konten fuer Posteingang-Triage: Mails auflisten und
  zusammenfassen, in Ordner einsortieren, als Spam markieren, in den Papierkorb
  verschieben sowie zwischen zwei Konten kopieren und verschieben. Zugangsdaten
  kommen aus der muttrc (`account-hook`), es gibt keine zweite Credential-Datei.
  Gelesen wird mit BODY.PEEK, der Ungelesen-Status bleibt dabei unangetastet.
  Schreibende Aktionen laufen ausschliesslich gebuendelt ueber `batch` und erst
  nach ausdruecklicher Freigabe durch den Nutzer. stdlib-only Python, kein
  Server-Prozess, lauffaehig auf FreeBSD + macOS. Nutze diesen Skill wenn der
  User seinen Posteingang durchgehen, Mails zusammengefasst haben, aufraeumen,
  Spam aussortieren oder Mails zwischen Konten bewegen will. Auch aktiv
  verwenden bei "geh meine Inbox durch", "was ist heute reingekommen", "raeum
  den Posteingang auf", "gibt es was Wichtiges in der Mail", "verschieb das ins
  Archiv". Trigger: /imap.
---

# imap -- Posteingang-Triage ueber mehrere Konten

Zugriff ueber das gebundelte Script `imap` (Python >=3.11, stdlib only, im
Skill-Verzeichnis). Kein Daemon, kein MCP-Server -- jeder Aufruf oeffnet eine
IMAP-Verbindung und schliesst sie wieder.

**Aufruf:** `python3 "$SKILL_DIR/imap" <subcommand> [options]`

`$SKILL_DIR` ist das Base Directory dieses Skills (dort wo diese SKILL.md liegt).

## Konfiguration (muttrc)

Zugangsdaten stehen in `~/.muttrc` und werden von mutt und diesem Script
gemeinsam genutzt. Es gibt bewusst **keine** zweite Credential-Datei.

```
set folder    = "imaps://mail.example.at/"
set imap_user = "<username>"
set imap_pass = "..."

account-hook imaps://mail.example.at/   'set imap_user="<username>" imap_pass="..."'
account-hook imaps://office.example.at/ 'set imap_user="<username>" imap_pass="..."'
```

Ausgewertet wird eine Teilmenge der muttrc-Syntax: `set`, `account-hook`,
`source` (auch `source "cmd |"`) und Backtick-Substitution. Damit funktioniert
auch ein Keystore statt Klartext:

```
account-hook imaps://mail.example.at/ 'set imap_user="<username>" imap_pass=`pass show mail/example`'
```

Anderer Pfad per `--muttrc /pfad/zur/datei`. Fehlen User oder Passwort fuer ein
Konto, wird es **uebersprungen** statt geraten.

**Kontoname** ist das erste Label des Hostnamens: `mail.example.at` -> `mail`,
`office.example.at` -> `office`. Ohne `--account` gilt das Konto aus `set folder`
als Default; `list` ohne `--account` fragt **alle** Konten ab.

## Lesende Befehle

| Befehl | Zweck |
|---|---|
| `accounts` | konfigurierte Konten (ohne Passwoerter) |
| `folders -a <konto>` | Ordnerliste, Separator, Sonderordner, Server-Capabilities |
| `list [-a <konto>]` | Kopfdaten ohne Body |
| `read <uid> -a <konto>` | Textkoerper einer Mail |
| `read <uid> --headers` | alle Rohheader statt der Kopfzeilen-Auswahl |
| `read <uid> --raw` | komplette unbearbeitete Nachricht (Header + Body) |

```
python3 "$SKILL_DIR/imap" list --json                     # beide Konten
python3 "$SKILL_DIR/imap" list -a office --unseen -n 30
python3 "$SKILL_DIR/imap" list -a mail --since 3          # letzte 3 Tage
python3 "$SKILL_DIR/imap" read 8841 -a office --json
python3 "$SKILL_DIR/imap" read 8841 -a office --headers
python3 "$SKILL_DIR/imap" read 8841 -a office --raw | less
```

`--json` gibt es bei jedem Befehl, vor **und** hinter dem Subcommand.
Fuer die eigene Weiterverarbeitung immer `--json` verwenden.

`list` holt nur Envelopes (Von, Betreff, Datum, Flags, Groesse) -- das ist auch
bei mehreren hundert Mails schnell. Bodies erst bei Bedarf per `read`
nachladen, und nur fuer die Mails, die wirklich zusammengefasst werden.

**BODY.PEEK:** `read` setzt `\Seen` nicht. Ein Posteingang ist nach einer
Durchsicht also nicht ploetzlich komplett gelesen.

### Header lesen (`--headers` / `--raw`)

Die Standardausgabe von `read` zeigt bewusst nur `From`, `To`, `Subject`, `Date`
und Anhaenge -- fuer die Triage ist alles andere Rauschen. Bei Mail-Problemen ist
aber genau der Rest die Aussage:

- **Zustellweg** -- die `Received`-Kette: welcher Smarthost war beteiligt, wo
  wurde der Absender umgeschrieben
- **SPF/DKIM/DMARC** -- `Authentication-Results`, wenn Mails im Spam landen
- **Bcc-Verhalten** -- ob ein `Bcc`-Header in der zugestellten Mail stehen blieb
  und die Adresse damit an den To-Empfaenger leakt
- **Newsletter-Triage** -- `List-Id` / `List-Unsubscribe`
- **Dubletten** -- `Message-ID` als Gegenprobe zum kontouebergreifenden `batch`

`--headers` liefert **alle** Header in Originalreihenfolge; Mehrfach-Header wie
`Received` bleiben einzeln stehen, sonst waere die Kette nicht mehr lesbar. Die
Zeilenfaltung wird aufgeloest, der Wert sonst nicht angefasst -- insbesondere
**kein** RFC-2047-Decoding, weil bei einer Header-Analyse der Rohwert zaehlt. Im
`--json` steht das als Feld `headers` (Liste aus `[name, value]`).

`--raw` gibt die Nachricht komplett und ungeparst aus (Header + Body) -- die
Wahl bei MIME-Problemen. In der Textausgabe ersetzt `--raw` die Aufbereitung; per
Pipe an `less`/`grep` ist das der uebliche Weg.

Beides kostet **keinen** zusaetzlichen IMAP-Roundtrip: `BODY.PEEK[]` holt ohnehin
die vollstaendige Rohnachricht, sie wurde bisher nur weggefiltert. `BODY.PEEK`
gilt unveraendert -- auch mit `--headers`/`--raw` bleibt der Ungelesen-Status.

## Schreibende Befehle

| Aktion | Wirkung |
|---|---|
| `move <uid> -t <ziel>` | verschieben |
| `copy <uid> -t <ziel>` | kopieren |
| `spam <uid>` | in den Junk-Ordner |
| `delete <uid>` | in den Papierkorb -- **nie** expunge |
| `seen` / `unseen` | Gelesen-Status |
| `flag` / `unflag` | Markierung |

Als `-t/--target` sind **Sonderrollen** erlaubt: `junk`, `trash`, `archive`,
`sent`, `drafts`. Die werden per SPECIAL-USE beim Server aufgeloest, sonst ueber
eine Namensheuristik. Findet sich nichts, bricht der Aufruf ab, statt einen
Ordner anzulegen.

Jede schreibende Aktion kennt `--dry-run`.

## Batch -- der Normalfall fuer Aktionen

```
echo '[
  {"account":"office","action":"spam",  "uid":8815},
  {"account":"office","action":"move",  "uid":8802, "target":"Archives.2026"},
  {"account":"office","action":"delete","uid":8819},
  {"account":"office","action":"move",  "uid":8790, "target":"Archives.2026", "to_account":"mail"}
]' | python3 "$SKILL_DIR/imap" batch - --json
```

Ein Login je Konto statt eines je Mail. Das ist nicht nur schneller, sondern
vermeidet auch, dass eine Aufraeumsitzung als Login-Serie in den Auth-Logs
landet und dort die Brute-Force-Erkennung streift.

Felder: `account`, `action`, `uid`, optional `folder` (Default `INBOX`),
`target`, `to_account`. `--dry-run` gilt fuer den ganzen Lauf.

## Kontouebergreifend

Innerhalb eines Kontos laeuft `MOVE` serverseitig. Zwischen zwei Konten kennt
IMAP keinen solchen Befehl -- die Mail wird geholt und per `APPEND` im Ziel
eingefuegt, mit Flags und `INTERNALDATE`. Ablauf:

1. `APPEND` ins Ziel, Erfolg pruefen
2. **erst danach** die Quelle raeumen (nur bei `move`)

Schlaegt der `APPEND` fehl, bleibt die Quelle unangetastet. Im schlimmsten Fall
entsteht ein Duplikat, nie ein Verlust. Vor dem `APPEND` wird per Message-ID
geprueft, ob die Mail im Ziel schon liegt -- ein abgebrochener Lauf ist damit
gefahrlos wiederholbar.

Bare LF wird vor dem `APPEND` auf CRLF normalisiert (verlustfrei). Cyrus weist
solche Mails sonst mit `NO` zurueck, waehrend Dovecot sie klaglos gespeichert
hat -- Richtung Dovecot -> Cyrus ist das der haeufigste Fehlerfall.

## Persoenliche Regeldatei (`~/.claude/imap-triage.md`)

Wie eine Inbox einzuordnen ist, ist **persoenlich**: welche Absender Rauschen
sind, was einen Push wert ist, was ohne Rueckfrage weggeraeumt werden darf.
Solche Praeferenzen gehoeren nicht in diesen Skill und nicht in ein Wiki,
sondern in `~/.claude/imap-triage.md`.

**Vor jeder Triage diese Datei lesen, falls vorhanden.** Existiert sie nicht,
gilt der Default-Ablauf unten unveraendert -- kein Grund, sie anzulegen oder
danach zu fragen.

Was sie typischerweise festlegt:

- **Klassifikation je Absender/Muster** (Rauschen, Spam, Push, Kenntnisnahme).
- **Autonomie:** welche Kategorien ohne Rueckfrage in den Papierkorb duerfen.
  Nur was dort ausdruecklich als automatisch markiert ist -- der Default bleibt
  "nichts ohne Zustimmung".
- **Eskalationsschwellen**, z.B. Flapping-Alerts erst ab N Paaren melden.
- **Gegenchecks** vor einem Alarm (siehe naechster Abschnitt).

Widerspricht die Datei einer Regel hier, gewinnt die Datei -- ausser bei den
Sicherheitszusagen des Skripts (`BODY.PEEK`, `delete` = Papierkorb, nie
`expunge`).

## Alert-Mails gegenpruefen, nicht weiterreichen

Monitoring- und Reminder-Mails beschreiben einen **vergangenen** Zustand. Bevor
so eine Mail als Befund gemeldet oder gepusht wird, den Ist-Zustand pruefen:

```
# sshd-Alert -- antwortet der Port jetzt?
nc -z -w 5 <host> 22

# Zertifikats-Reminder -- welches Cert laeuft dort wirklich?
echo | openssl s_client -servername <host> -connect <host>:443 2>/dev/null \
  | openssl x509 -noout -subject -issuer -dates
```

Das aendert die Bewertung regelmaessig: ein "Wildcard laeuft morgen ab" ist
harmlos, wenn der Host laengst ein Let's-Encrypt-Zertifikat ausliefert -- und
ein Alert ohne Recovery-Mail ist erledigt, wenn der Dienst wieder antwortet.
Umgekehrt gilt: **Alert-Paare erst nach einem Monitoring-Intervall bewerten**
(monit schickt die Recovery typisch nach ~2 Minuten), sonst wird jedes
Failed-Alert einmal zu frueh als offener Befund gemeldet.

## Triage-Ablauf

Der eigentliche Zweck des Skills. Ablauf bei "geh meine Inbox durch":

1. `~/.claude/imap-triage.md` lesen, falls vorhanden
2. `list --json` ueber alle Konten
3. Bodies **nur** fuer die inhaltlich relevanten Mails per `read --json`
4. Zusammenfassung ausgeben, dann Vorschlag -- in dieser Reihenfolge:

```
── Antwort noetig ──
• Absender, Zeit [ungelesen]        konto/uid
  Ein bis zwei Zeilen Inhalt.

── Kenntnisnahme ──
• ...

── Unsicher, bleibt liegen ──
• ...

VORSCHLAG
Spam    → office/8815, 8822
Ablage  → office/8802 → Archives.2026
Loeschen → office/8819

ok / einzeln anpassen?
```

5. **Warten.** Nichts ausfuehren, bevor der User zugestimmt hat.
6. Nach Freigabe: ein `batch`-Aufruf, danach das Ergebnis melden.

**Regeln fuer die Vorschlagsgruppen:**

- Spam, Werbung und Newsletter nach Absender und Betreff einordnen -- dafuer
  reicht der Envelope, kein Body noetig.
- Alles Zweifelhafte kommt in **"Unsicher"** und bleibt liegen. Lieber zu viel
  im Posteingang als eine wichtige Mail weggeraeumt.
- `delete` heisst Papierkorb, nicht weg. Endgueltiges Loeschen gibt es nicht.
- Keine schreibende Aktion ohne ausdrueckliche Zustimmung. "Geh die Inbox
  durch" ist eine Leseaufforderung, keine Freigabe zum Aufraeumen. Einzige
  Ausnahme: Kategorien, die `~/.claude/imap-triage.md` **namentlich** als
  automatisch erlaubt kennzeichnet -- die stehende Freigabe des Nutzers. Alles
  andere bleibt im Vorschlag.

## Fallstricke

- **Ordnernamen sind serverspezifisch.** Cyrus mit `altnamespace: yes` hat
  `Spam` ohne `INBOX.`-Praefix und `.` als Separator; Dovecot nutzt hier `/`.
  Nie einen Ordnernamen raten, immer `folders` fragen oder eine Sonderrolle
  verwenden.
- **Capabilities erst nach dem Login pruefen.** Das Greeting listet weniger,
  als der Server nach der Anmeldung kann. Das Script holt `CAPABILITY` deshalb
  erneut; ohne das liefe Dovecot unnoetig in den COPY-Fallback.
- **`UID EXPUNGE` statt `EXPUNGE`** im Fallback ohne `MOVE`. Nacktes `EXPUNGE`
  wuerde alle als geloescht markierten Mails des Ordners mitnehmen.
- **Leerer Posteingang ist kein Fehler.** Wenn serverseitige Sieve-Regeln oder
  ein anderer Client bereits einsortieren, ist die INBOX schlicht leer.

## Verwandte Skills

- [swaks](../swaks/SKILL.md) -- Versand; dieser Skill ist die Lese-Seite dazu
- [mail-as-me](../mail-as-me/SKILL.md) -- Antworten im eigenen Schreibstil
- [pushover](../pushover/SKILL.md) -- Zusammenfassung als Push aufs Handy
