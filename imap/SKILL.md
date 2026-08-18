---
name: imap
description: >
  IMAP-Zugriff auf mehrere Konten fuer Posteingang-Triage: Mails auflisten und
  zusammenfassen, in Ordner einsortieren, als Spam markieren, in den Papierkorb
  verschieben sowie zwischen zwei Konten kopieren und verschieben. Anhaenge
  lassen sich auflisten und herausschreiben, etwa um sie an einen Task oder ein
  Ticket zu haengen. Fuer eine Antwort erzeugt `quote` den Zitatblock im
  Thunderbird-Format samt Threading-Headern; `find` loest eine Message-ID zu
  Konto, Ordner und UID auf. Zugangsdaten
  kommen aus der muttrc (`account-hook`), es gibt keine zweite Credential-Datei.
  Gelesen wird mit BODY.PEEK, der Ungelesen-Status bleibt dabei unangetastet.
  Schreibende Aktionen laufen ausschliesslich gebuendelt ueber `batch` und erst
  nach ausdruecklicher Freigabe durch den Nutzer. stdlib-only Python, kein
  Server-Prozess, lauffaehig auf FreeBSD + macOS. Nutze diesen Skill wenn der
  User seinen Posteingang durchgehen, Mails zusammengefasst haben, aufraeumen,
  Spam aussortieren oder Mails zwischen Konten bewegen will. Auch aktiv
  verwenden bei "geh meine Inbox durch", "was ist heute reingekommen", "raeum
  den Posteingang auf", "gibt es was Wichtiges in der Mail", "verschieb das ins
  Archiv", "hol den Anhang aus der Mail", "zitier die Mail fuer meine Antwort",
  "finde die Mail mit dieser Message-ID".
  Trigger: /imap.
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

**Der Kontoname hier ist nicht der aus Thunderbird.** Dort steht ein frei
vergebener Anzeigename ("Arbeit", "privat", der eigene Nachname), hier das erste
Label des Hostnamens -- eine Mail, die aus Thunderbird als Text herauskopiert
wurde, nennt also ein Konto, das dieser Skill nicht kennt. Statt zu raten oder
ein Mapping zu pflegen: `find` fragt ohne `--account` ohnehin alle Konten ab und
liefert den richtigen Namen mit. Wer das Mapping trotzdem festhalten will,
schreibt es in `~/.claude/imap-triage.md` (persoenliche Datei, siehe unten) --
nicht in diesen Skill.

## Lesende Befehle

| Befehl | Zweck |
|---|---|
| `accounts` | konfigurierte Konten (ohne Passwoerter) |
| `folders -a <konto>` | Ordnerliste, Separator, Sonderordner, Server-Capabilities |
| `list [-a <konto>]` | Kopfdaten ohne Body |
| `find -m <message-id>` | Message-ID zu Konto, Ordner und UID aufloesen |
| `read <uid> -a <konto>` | Textkoerper einer Mail |
| `fetch --uids <liste> -a <konto>` | mehrere Mails mit **einem** Login |
| `quote <uid> -a <konto>` | Zitatblock fuer eine Antwort (Text oder HTML) |
| `read <uid> --headers` | alle Rohheader statt der Kopfzeilen-Auswahl |
| `read <uid> --raw` | komplette unbearbeitete Nachricht (Header + Body) |
| `attachments <uid> -a <konto>` | Anhaenge auflisten (Index, Name, Typ, Groesse) |
| `save-attachment <uid> -a <konto>` | Anhang herausschreiben |

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

## `find` -- von der Message-ID zur UID

Der Gegenweg zu `list`: dort ist die UID der Ausgangspunkt, hier die
**Message-ID**. Eine als Text oder Markdown einkopierte Mail nennt Ordner,
Betreff und Message-ID -- aber **nie** die UID, denn die vergibt der Server je
Ordner. Ohne `find` bleibt der Umweg ueber `folders` + `list` und ein
Handabgleich von Betreff und Datum:

```
python3 "$SKILL_DIR/imap" find -m "<abc@example.org>"
python3 "$SKILL_DIR/imap" find -m abc@example.org -a office     # Konto bekannt
python3 "$SKILL_DIR/imap" find -m abc@example.org -a office -f ToDo
python3 "$SKILL_DIR/imap" find -m abc@example.org --all --json  # auch Kopien
```

Ausgabe `<konto>/<ordner>/<uid>` plus Absender und Betreff zur Gegenprobe; im
`--json` dieselben Felder wie bei `list`. Die spitzen Klammern sind optional,
ein vorangestelltes `Message-ID:` wird abgeschnitten -- der Wert darf also aus
einem Header-Auszug kopiert sein.

**Gesucht wird ordnerweise**, INBOX zuerst, danach alphabetisch; ohne
`--account` ueber alle konfigurierten Konten. Beim ersten Treffer ist Schluss --
`--all` sucht weiter und findet damit auch Kopien in Archiv oder Zweitkonto. Ein
Sweep ueber ein gewachsenes Postfach dauert dabei durchaus eine Minute (je
Ordner ein SELECT und ein SEARCH); `-a` und `-f` kuerzen das entsprechend ab.

**Kein Treffer ist hier ein Fehler** (Exit-Code 1), anders als bei einer leeren
Inbox: gesucht wird nach einer bestimmten Mail, die es geben soll. Ohne diesen
Exit-Code liefe eine Pipeline still mit fehlendem Zitat weiter.

Nicht durchsucht werden `\Noselect`-Eintraege -- das sind reine Zwischenknoten
der Ordnerhierarchie, keine Mailboxen.

## `fetch` -- ein Stapel Mails, ein Login

`read` oeffnet **je Aufruf** eine eigene Verbindung samt Login. Fuer einen Stapel
ist das dasselbe Problem, das `batch` auf der Schreibseite loest: 200 Mails
waeren 200 Logins in kurzer Folge -- unnoetig langsam und in den Auth-Logs von
einem Brute-Force-Versuch kaum zu unterscheiden. `fetch` holt beliebig viele
UIDs in **einer** Session (und je 50 UIDs mit einem FETCH):

```
python3 "$SKILL_DIR/imap" fetch -a office -f Sent --uids 75433,75436,75430
python3 "$SKILL_DIR/imap" fetch -a office -f Sent --uids "75433 75436" --headers
python3 "$SKILL_DIR/imap" fetch -a office -f Sent --uid-file uids.txt --json
python3 "$SKILL_DIR/imap" fetch -a office -f Sent --uid-file - --raw -o .tmp/eml/
```

Die UID-Liste kommt per `--uids` (Komma oder Leerzeichen) oder aus einer Datei
(`--uid-file`, `-` liest stdin). In der Datei sind Zeilenumbrueche, Kommas und
`#`-Kommentare erlaubt; Dubletten fallen weg, die Reihenfolge bleibt.

Ausgabe wie bei `read`, inklusive `--headers`, `--raw` und `--max-chars`:

- **ohne `-o`** auf stdout, je Mail mit einer Trennzeile `── <konto>/<uid> ──`.
  Fuer eine byte-genaue Rohfassung ist `-o` der Weg, nicht stdout.
- **mit `-o <verzeichnis>`** je UID eine Datei: `<uid>.eml` bei `--raw` (Original-
  bytes, ungetastet), sonst `<uid>.txt` mit der aufbereiteten Fassung.
- **`--json`** liefert ohne `-o` alle Mails als Liste, mit `-o` die
  Schreib-Bilanz (`saved`, `skipped`, `missing`).

**Eine vorhandene Datei wird uebersprungen, nicht ueberschrieben und nicht
durchnummeriert.** Der Dateiname ist die UID, ein zweiter Lauf meint also
dieselbe Mail -- ein abgebrochener Stapelabruf laesst sich damit einfach
wiederholen, ohne einen Korpus mit Dubletten zu fuellen. `--overwrite` erzwingt
das Schreiben. (Bei `save-attachment` ist es umgekehrt: dort kommt der Name vom
Absender, `scan.pdf` meint jedes Mal etwas anderes.)

**Eine unbekannte UID bricht den Lauf nicht ab** -- sie erscheint in `missing`.
Bei einem Stapel ist eine zwischenzeitlich verschobene oder geloeschte Mail der
Normalfall, kein Grund die uebrigen nicht zu holen.

`BODY.PEEK` gilt unveraendert: auch ein Stapelabruf setzt `\Seen` nicht.

Typische Faelle: Korpus-Aufbau fuer [mail-as-me](../mail-as-me/SKILL.md),
Header-Analysen ueber mehrere Mails (Zustellwege, SPF/DKIM), einen Thread am
Stueck lesen, Export vor einer Migration.

## `quote` -- Zitatblock fuer eine Antwort

Beim Antworten wird der Originaltext zitiert, so wie es Thunderbird macht. Das
Zitat wird **generiert, nicht formuliert**: sobald die `> `-Praefixe von Hand
getippt werden, weicht das Format bei jeder Mail leicht ab -- mal ein Leerzeichen
zu viel, mal ein anderer Umbruch, mal eine erfundene Attributionszeile.

```
python3 "$SKILL_DIR/imap" quote 8841 -a office -f ToDo
python3 "$SKILL_DIR/imap" quote 8841 -a office -f ToDo --format html
python3 "$SKILL_DIR/imap" quote 8841 -a office -f ToDo --width 0   # kein Umbruch
python3 "$SKILL_DIR/imap" quote 8841 -a office -f ToDo --json
```

**`--folder` gehoert dazu, sobald die Mail nicht in der INBOX liegt.** UIDs sind
**ordner-lokal**: `quote 8841 -a office` zitiert INBOX/8841, und die gibt es dort
sehr wahrscheinlich auch -- nur ist es eine andere Mail. Der Aufruf laeuft dann
ohne Fehlermeldung durch und liefert ein sauber formatiertes Zitat aus einer
fremden Mail. Der Default `INBOX` ist bequem, aber er raet.

Ergebnis auf stdout, fertig zum Anhaengen an die Antwort:

```
Am 18.08.26 um 12:58 schrieb Max Mustermann:
> Hallo,
>
> wie besprochen, hier einmal mein vorlaeufiges Mapping fuer die Spalten
> der Tabelle.
>
>> Das hier war schon zitiert
```

Die Regeln im Einzelnen:

- **Attributionszeile** `Am <dd.mm.yy> um <HH:MM> schrieb <Name>:`, Zeitangabe
  **lokal** (nicht die Zone des Absenders), Name aus `From`, Fallback auf die
  Adresse. Ohne verwertbares `Date` bleibt die Zeitangabe weg (`<Name> schrieb:`)
  statt ein Datum zu raten.
- **Praefix** `> ` je Zeile, Leerzeilen als `>` allein (kein Leerzeichen am
  Zeilenende). Bereits zitierte Zeilen bekommen ein weiteres `>` ohne
  Leerzeichen: `> x` wird zu `>> x`.
- **Umbruch** bei `--width` Zeichen **inklusive** Zitatzeichen (Default 72), die
  Fortsetzung beginnt wieder mit dem Praefix. `--width 0` schaltet den Umbruch
  ab. Bleiben durch tiefe Verschachtelung weniger als 20 nutzbare Zeichen, wird
  die Zeile nicht mehr umgebrochen -- sonst zerfaellt sie in Wortfragmente.
- **Leerzeilen** werden auf hoechstens eine zusammengezogen -- bei jeder Mail,
  nicht nur bei `format=flowed`. Outlook macht aus jeder leeren Tabellenzelle
  eine eigene Leerzeile im `text/plain`-Teil; ohne das Zusammenziehen reisst
  der Zitatblock genau dort auseinander, wo im Original nichts stand.
- **Anhaenge werden nicht zitiert**, `BODY.PEEK` gilt unveraendert.

### `--message-id` statt UID

Ist nur die Message-ID bekannt (einkopierte Mail, Header-Auszug, Log), loest
`quote` sie selbst auf -- Konto, Ordner **und** UID kommen dann aus dem Treffer,
womit der `--folder`-Fehlgriff oben gar nicht erst moeglich ist:

```
python3 "$SKILL_DIR/imap" quote -m "<abc@example.org>" --json
python3 "$SKILL_DIR/imap" quote -m abc@example.org -a office -f ToDo
```

`-a`/`-f` grenzen die Suche nur ein (und beschleunigen sie), noetig sind sie
nicht. Genau eines von UID und `--message-id` muss angegeben sein; findet sich
die Message-ID nirgends, bricht der Aufruf ab, statt eine INBOX-UID zu zitieren.
Der Suchweg ist derselbe wie bei `find` (siehe dort).

### `format=flowed` wird vorher aufgeloest

Mailclients wie Thunderbird verschicken Text als `format=flowed` (RFC 3676): die
Absaetze sind **weich** umgebrochen, jede Fortsetzungszeile endet auf ein
Leerzeichen. Wer diese Umbrueche fuer echt haelt und darauf den eigenen setzt,
erzeugt einen Saegezahn -- aus einer 71 Zeichen langen Quellzeile wird bei
Breite 70 eine volle Zeile plus ein einzelnes Restwort:

```
> Stimmt, ich muss auch auf dieser Seite vorsichtiger vorgehen und die
> AI
> nicht einfach machen lassen.
```

`quote` fuehrt die weichen Umbrueche deshalb zuerst zu Absaetzen zusammen
(inkl. `delsp`, Space-Stuffing und Zitatebene) und bricht danach neu um. Der
Signatur-Trenner `-- ` endet ebenfalls auf ein Leerzeichen, ist laut RFC aber
ausdruecklich kein weicher Umbruch und bleibt stehen.

### `--format html`

Der HTML-Part der Originalmail wird uebernommen und in
`<blockquote type="cite">` gewickelt -- Formatierung, Links und Listen bleiben
damit erhalten, verschachtelte Zitate der Vorgeschichte ebenso. Genommen wird
nur der Inhalt von `<body>`; `<head>`, Skripte und Stylesheets fallen weg, sie
gehoeren zur Darstellung der Originalmail und nicht zum zitierten Inhalt.

Eine Ausnahme braucht dabei Outlook: es setzt jede Zeile -- und jede
Tabellenzelle -- als eigenes `<p class="MsoNormal">` und laesst den Abstand
von einer Regel im `<head>` auf null setzen. Faellt das Stylesheet weg, greift
die Browser-Vorgabe `margin: 1em 0` und der Zitatblock geht weit auseinander.
Elemente mit einer `Mso*`-Klasse bekommen deshalb `margin:0` inline nachgetragen;
ein vorhandenes `style` bleibt erhalten und gewinnt. Hat
die Mail **keinen** HTML-Part, wird der Textkoerper escaped und mit `<br>`
nachgebaut.

### `--json` -- Threading faellt mit ab

Neben `attribution` und `quote` (dem kompletten Block inkl. Attributionszeile)
stehen die Kopfdaten der Originalmail und ein fertiges `reply`-Objekt:

```json
{
  "message_id": "<abc@example.org>",
  "in_reply_to": "<vorher@example.org>",
  "references": ["<wurzel@example.org>", "<vorher@example.org>"],
  "reply": {
    "in_reply_to": "<abc@example.org>",
    "references": "<wurzel@example.org> <vorher@example.org> <abc@example.org>"
  }
}
```

`message_id`, `in_reply_to` und `references` sind die Header der **Originalmail**;
`reply` enthaelt die Werte fuer die **Antwort** -- `In-Reply-To` ist deren
`Message-ID`, `References` die bestehende Kette plus diese `Message-ID`
(RFC 5322 3.6.4). Ohne diese beiden Header haengt die Antwort im Mailclient des
Empfaengers nicht am Thread, sondern startet einen neuen.

Message-IDs werden bewusst **nicht** RFC-2047-dekodiert -- sie sind Adressen,
keine anzeigbaren Texte. Die uebrigen Kopffelder sind dekodiert und entfaltet,
ein langer Betreff steht also ohne Zeilenumbruch in einem Feld.

## Anhaenge

`attachments` listet, `save-attachment` schreibt heraus:

```
python3 "$SKILL_DIR/imap" attachments 8841 -a office
python3 "$SKILL_DIR/imap" attachments 8841 -a office --json

python3 "$SKILL_DIR/imap" save-attachment 8841 -a office --index 1
python3 "$SKILL_DIR/imap" save-attachment 8841 -a office --name Rechnung.pdf
python3 "$SKILL_DIR/imap" save-attachment 8841 -a office --all -o .tmp/anhaenge/
```

Genau eine Auswahl je Aufruf: `--name`, `--index` oder `--all`. Der **Index** ist
1-basiert und folgt der MIME-Reihenfolge; er steht auch im `attachments`-Feld von
`read --json`, sodass eine bereits gelesene Mail nicht erneut aufgelistet werden
muss.

**Ablage:** ohne `--output` landen die Dateien in `.tmp/` des **Arbeits**-
verzeichnisses (nicht im Skill-Verzeichnis). `--output` ist eine Datei bei
einzelnem Anhang, sonst ein Verzeichnis. Eine vorhandene Datei wird **nie**
ueberschrieben -- es entsteht `Rechnung-1.pdf`. Anhaenge heissen oft
`scan.pdf` oder `image001.png`, ein stilles Ueberschreiben waere hier der
Normalfall, nicht die Ausnahme.

**Inline-Teile** (Signatur-Logos, eingebettete Bilder mit
`Content-Disposition: inline`) sind standardmaessig **ausgeblendet** -- sonst
besteht die Liste einer normalen Geschaeftsmail aus vier Logos und einer
Rechnung. `--include-inline` zeigt bzw. schreibt sie mit. Weil der Index ueber
**alle** Teile zaehlt, entstehen dabei Luecken in der Nummerierung; die Ausgabe
sagt, wie viele Teile ausgeblendet sind. Ein per `--name`/`--index`
ausdruecklich benannter Teil wird immer geliefert, auch wenn er inline ist --
der Filter gilt nur fuer `--all`.

**Dateinamen** kommen aus der Mail und damit vom Absender. Sie werden nach RFC
2231 (`filename*=utf-8''...`) und RFC 2047 (`=?utf-8?B?...?=`) dekodiert, damit
Umlaute stimmen; Pfadanteile und Steuerzeichen fallen weg. Ein Anhang namens
`../../../.ssh/authorized_keys` wird als `authorized_keys` im Zielverzeichnis
abgelegt, nicht anderswo. Teile ohne Namen bekommen `anhang-<index>.<ext>`,
angehaengte Mails (`message/rfc822`) werden als `.eml` geschrieben.

Gelesen wird mit `BODY.PEEK` -- auch das Speichern eines Anhangs setzt `\Seen`
**nicht**. Ein zusaetzlicher Roundtrip entsteht nicht: `BODY.PEEK[]` holt die
Nachricht ohnehin vollstaendig, die Anhaenge wurden bisher nur weggefiltert
(gleiche Argumentation wie bei `--headers`/`--raw`).

### Rezept: Anhang aus einer Mail an einen Kanboard-Task

Der haeufigste Grund, einen Anhang herauszuschreiben. Der Umweg ueber ein
selbstgeschriebenes MIME-Parsing entfaellt:

```
python3 "$SKILL_DIR/imap" attachments 8841 -a office
python3 "$SKILL_DIR/imap" save-attachment 8841 -a office --index 1 --json
python3 "$KANBOARD_SKILL_DIR/kanboard" attach-file 1234 --file /pfad/aus/dem/json
```

`attach-file` verlangt einen **absoluten** Pfad -- den liefert `--json` im Feld
`saved[].path`. Fuer ein Jira-Issue ist der zweite Schritt stattdessen
`jira attach <KEY> --file <pfad>`.

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
- **UIDs sind ordner-lokal.** Dieselbe Nummer existiert in jedem Ordner und
  meint dort eine andere Mail. Zu jeder UID gehoert deshalb `-f <ordner>`,
  sobald sie nicht aus der INBOX stammt -- ein fehlendes `-f` liefert keinen
  Fehler, sondern die falsche Mail. Wo nur die Message-ID bekannt ist, `find`
  bzw. `quote --message-id` verwenden, statt die UID zu suchen.
- **Zitate nie selbst tippen.** Fuer eine Antwort immer `quote` aufrufen. Ein
  von Hand gesetztes `> ` sieht auf den ersten Blick gleich aus, weicht aber bei
  jeder Mail leicht ab und ignoriert `format=flowed` und die Threading-Header.
- **Leerer Posteingang ist kein Fehler.** Wenn serverseitige Sieve-Regeln oder
  ein anderer Client bereits einsortieren, ist die INBOX schlicht leer.

## Verwandte Skills

- [swaks](../swaks/SKILL.md) -- Versand; dieser Skill ist die Lese-Seite dazu
- [mail-as-me](../mail-as-me/SKILL.md) -- Antworten im eigenen Schreibstil
- [pushover](../pushover/SKILL.md) -- Zusammenfassung als Push aufs Handy
- [kanboard](../kanboard/SKILL.md) / [jira](../jira/SKILL.md) -- Ziel fuer
  Anhaenge aus einer Mail (`attach-file` bzw. `attach`)
