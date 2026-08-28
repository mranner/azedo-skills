# imap - quote

Zitatblock im Thunderbird-Format samt Threading-Headern.

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

Beide `references`-Felder sind **normalisiert**: Kommas zwischen den
Message-IDs werden wie Whitespace behandelt und verschwinden. Nach RFC 5322
gehoert dort keines hin, manche Clients setzen aber trotzdem welche -- und ein
Komma, das in den `References`-Header der Antwort durchrutscht, zerreisst den
Thread beim Empfaenger, ohne dass beim Versand etwas auffaellt. Der Wert aus
`reply.references` kann also unveraendert in den Header.

Message-IDs werden bewusst **nicht** RFC-2047-dekodiert -- sie sind Adressen,
keine anzeigbaren Texte. Die uebrigen Kopffelder sind dekodiert und entfaltet,
ein langer Betreff steht also ohne Zeilenumbruch in einem Feld.
