# imap - Anhänge

Anhänge auflisten, herausschreiben und aus der Mail im Postfach entfernen.

## Anhänge

`attachments` listet, `save-attachment` schreibt heraus:

```
python3 "$SKILL_DIR/imap" attachments 8841 -a office
python3 "$SKILL_DIR/imap" attachments 8841 -a office --json

python3 "$SKILL_DIR/imap" save-attachment 8841 -a office --index 1
python3 "$SKILL_DIR/imap" save-attachment 8841 -a office --name Rechnung.pdf
python3 "$SKILL_DIR/imap" save-attachment 8841 -a office --all -o .tmp/anhänge/
```

Genau eine Auswahl je Aufruf: `--name`, `--index` oder `--all`. Der **Index** ist
1-basiert und folgt der MIME-Reihenfolge; er steht auch im `attachments`-Feld von
`read --json`, sodass eine bereits gelesene Mail nicht erneut aufgelistet werden
muss.

**Ablage:** ohne `--output` landen die Dateien in `.tmp/` des **Arbeits**-
verzeichnisses (nicht im Skill-Verzeichnis). `--output` ist eine Datei bei
einzelnem Anhang, sonst ein Verzeichnis. Eine vorhandene Datei wird **nie**
überschrieben -- es entsteht `Rechnung-1.pdf`. Anhänge heißen oft
`scan.pdf` oder `image001.png`, ein stilles Überschreiben wäre hier der
Normalfall, nicht die Ausnahme.

**Inline-Teile** (Signatur-Logos, eingebettete Bilder mit
`Content-Disposition: inline`) sind standardmäßig **ausgeblendet** -- sonst
besteht die Liste einer normalen Geschäftsmail aus vier Logos und einer
Rechnung. `--include-inline` zeigt bzw. schreibt sie mit. Weil der Index über
**alle** Teile zählt, entstehen dabei Lücken in der Nummerierung; die Ausgabe
sagt, wie viele Teile ausgeblendet sind. Ein per `--name`/`--index`
ausdrücklich benannter Teil wird immer geliefert, auch wenn er inline ist --
der Filter gilt nur für `--all`.

**Dateinamen** kommen aus der Mail und damit vom Absender. Sie werden nach RFC
2231 (`filename*=utf-8''...`) und RFC 2047 (`=?utf-8?B?...?=`) dekodiert, damit
Umlaute stimmen; Pfadanteile und Steuerzeichen fallen weg. Ein Anhang namens
`../../../.ssh/authorized_keys` wird als `authorized_keys` im Zielverzeichnis
abgelegt, nicht anderswo. Teile ohne Namen bekommen `anhang-<index>.<ext>`,
angehängte Mails (`message/rfc822`) werden als `.eml` geschrieben.

Gelesen wird mit `BODY.PEEK` -- auch das Speichern eines Anhangs setzt `\Seen`
**nicht**. Ein zusätzlicher Roundtrip entsteht nicht: `BODY.PEEK[]` holt die
Nachricht ohnehin vollständig, `attachments` schreibt nur ihre Anhänge heraus
(gleiche Argumentation wie bei `--headers`/`--raw`).

## Anhang aus der Mail entfernen

`delete-attachment` entspricht Thunderbirds "Löschen" am Anhang - die Mail
bleibt, der Anhang verschwindet:

```
python3 "$SKILL_DIR/imap" delete-attachment 8841 -a office --index 2 --dry-run
python3 "$SKILL_DIR/imap" delete-attachment 8841 -a office --name Rechnung.pdf
python3 "$SKILL_DIR/imap" delete-attachment 8841 -a office --all --save -o .tmp/x/
```

Auswahl wie bei `save-attachment` (`--name`/`--index`/`--all`, Inline-Teile nur
mit `--include-inline`). `--save` schreibt die Anhänge vorher heraus - das
"Abtrennen" von Thunderbird, ohne Verweis in der Mail.

**Die UID ändert sich.** IMAP kann eine Mail nicht an Ort und Stelle ändern: die
bereinigte Fassung kommt per `APPEND` mit denselben Flags und demselben
INTERNALDATE in den Ordner, erst danach geht das Original in den Papierkorb.
Die Ausgabe nennt die neue UID (`new_uid`); die alte gilt danach nicht mehr.
Scheitert das `APPEND`, bleibt das Original unangetastet. Bis `empty-trash`
lässt sich der Vorgang über das Original im Papierkorb rückgängig machen.

An Stelle des Anhangs steht derselbe Platzhalter wie bei Thunderbird
(`text/x-moz-deleted` mit den ursprünglichen MIME-Headern, dazu
`X-Mozilla-Altered: AttachmentDeleted`); Thunderbird zeigt ihn als gelöschten
Anhang an.

**Abgelehnt** werden signierte und verschlüsselte Mails (S/MIME, PGP/MIME) -
die Signatur wäre danach ungültig. Eine DKIM-Signatur bricht bei jeder Mail;
für die Ablage im eigenen Postfach ist das ohne Belang, für die Weiterleitung
an Dritte als Beleg nicht. Mails im Papierkorb erst herausverschieben.

### Rezept: Anhang aus einer Mail an einen Kanboard-Task

Der häufigste Grund, einen Anhang herauszuschreiben. Der Umweg über ein
selbstgeschriebenes MIME-Parsing entfällt:

```
python3 "$SKILL_DIR/imap" attachments 8841 -a office
python3 "$SKILL_DIR/imap" save-attachment 8841 -a office --index 1 --json
python3 "$KANBOARD_SKILL_DIR/kanboard" attach-file 1234 --file /pfad/aus/dem/json
```

`attach-file` verlangt einen **absoluten** Pfad -- den liefert `--json` im Feld
`saved[].path`. Für ein Jira-Issue ist der zweite Schritt stattdessen
`jira attach <KEY> --file <pfad>`.
