# imap - find und fetch

Message-ID aufloesen, Stapel von Mails mit einem Login holen.

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

Typische Faelle: Korpus-Aufbau fuer [mail-as-me](../../mail-as-me/SKILL.md),
Header-Analysen ueber mehrere Mails (Zustellwege, SPF/DKIM), einen Thread am
Stueck lesen, Export vor einer Migration.
