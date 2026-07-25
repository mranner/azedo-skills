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
set imap_user = "mmuster"
set imap_pass = "..."

account-hook imaps://mail.example.at/   'set imap_user="mmuster" imap_pass="..."'
account-hook imaps://office.example.at/ 'set imap_user="mmuster" imap_pass="..."'
```

Ausgewertet wird eine Teilmenge der muttrc-Syntax: `set`, `account-hook`,
`source` (auch `source "cmd |"`) und Backtick-Substitution. Damit funktioniert
auch ein Keystore statt Klartext:

```
account-hook imaps://mail.example.at/ 'set imap_user="mmuster" imap_pass=`pass show mail/azedo`'
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

```
python3 "$SKILL_DIR/imap" list --json                     # beide Konten
python3 "$SKILL_DIR/imap" list -a office --unseen -n 30
python3 "$SKILL_DIR/imap" list -a mail --since 3          # letzte 3 Tage
python3 "$SKILL_DIR/imap" read 8841 -a office --json
```

`--json` gibt es bei jedem Befehl, vor **und** hinter dem Subcommand.
Fuer die eigene Weiterverarbeitung immer `--json` verwenden.

`list` holt nur Envelopes (Von, Betreff, Datum, Flags, Groesse) -- das ist auch
bei mehreren hundert Mails schnell. Bodies erst bei Bedarf per `read`
nachladen, und nur fuer die Mails, die wirklich zusammengefasst werden.

**BODY.PEEK:** `read` setzt `\Seen` nicht. Ein Posteingang ist nach einer
Durchsicht also nicht ploetzlich komplett gelesen.

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

## Triage-Ablauf

Der eigentliche Zweck des Skills. Ablauf bei "geh meine Inbox durch":

1. `list --json` ueber alle Konten
2. Bodies **nur** fuer die inhaltlich relevanten Mails per `read --json`
3. Zusammenfassung ausgeben, dann Vorschlag -- in dieser Reihenfolge:

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

4. **Warten.** Nichts ausfuehren, bevor der User zugestimmt hat.
5. Nach Freigabe: ein `batch`-Aufruf, danach das Ergebnis melden.

**Regeln fuer die Vorschlagsgruppen:**

- Spam, Werbung und Newsletter nach Absender und Betreff einordnen -- dafuer
  reicht der Envelope, kein Body noetig.
- Alles Zweifelhafte kommt in **"Unsicher"** und bleibt liegen. Lieber zu viel
  im Posteingang als eine wichtige Mail weggeraeumt.
- `delete` heisst Papierkorb, nicht weg. Endgueltiges Loeschen gibt es nicht.
- Keine schreibende Aktion ohne ausdrueckliche Zustimmung. "Geh die Inbox
  durch" ist eine Leseaufforderung, keine Freigabe zum Aufraeumen.

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
