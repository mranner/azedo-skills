# imap - contacts

Alle Adressen eines Threads sammeln - die Vorstufe einer Antwort.

## `contacts` -- Empfaengerkreis eines Threads

Wer auf eine Mail antwortet, braucht den vollstaendigen Empfaengerkreis. Der
steht selten in der zuletzt eingegangenen Mail: eine Adresse aus dem Verteiler
taucht oft nur in einer einzigen aelteren Nachricht auf, und die eigenen
Antworten liegen im "Gesendet" eines ganz anderen Kontos.

```
python3 "$SKILL_DIR/imap" contacts 8841 -a office -f ToDo
python3 "$SKILL_DIR/imap" contacts -m "<abc@example.com>"
python3 "$SKILL_DIR/imap" contacts 8841 --no-thread    # nur diese eine Mail
python3 "$SKILL_DIR/imap" contacts 8841 --json
```

Ausgewertet werden `From`, `Reply-To`, `To` und `Cc` **aller** Mails des
Threads. Die Ausgabe zeigt je Adresse den Anzeigenamen, die Rollen und in wie
vielen Mails sie vorkommt - je haeufiger, desto weiter oben:

```
Re: Angebot ueberarbeitet
6 Adressen aus 5 Mail(s) im Thread

  Max Muster <max@example.com>          from,to,cc    5x
  ...
```

## Wie der Thread bestimmt wird

Aus `References` und `In-Reply-To` der Startmail - dieselbe Kette, die auch das
Threading beim Empfaenger traegt. Jede ID daraus wird gesucht, die gefundenen
Mails werden mit ausgewertet.

**Die Suche laeuft ueber alle konfigurierten Konten.** Zuerst das Konto der
Startmail, dann die uebrigen, und nur so lange, bis nichts mehr offen ist. Das
ist kein Beiwerk: die eigenen Antworten stehen im "Gesendet" des Kontos, mit
dem geantwortet wurde, und ohne sie fehlen genau die Adressen, die man selbst
zuletzt angeschrieben hat.

Mit `-a` oder `-f` bleibt es bei der Angabe - dann wird nur dort gesucht.

Je Ordner geht **ein** SEARCH ueber alle noch offenen Message-IDs (OR-Kette),
nicht einer je ID. Ein Thread mit zehn Vorgaengern kostet damit ein paar
Sekunden statt einer Minute.

## Nicht auffindbare Mails

IDs, zu denen sich keine Mail findet, listet der Befehl auf **stderr** - der
Normalfall bei den Kopien der Gegenseite, die nie in einem der eigenen
Postfaecher lagen. Das ist eine Warnung, kein Fehler: der Exit-Code bleibt `0`,
und die Adressen aus den gefundenen Mails stehen vollstaendig da.

Wenn dort viele Mails der eigenen Seite fehlen, lohnt der Blick, ob das Konto
ueberhaupt konfiguriert ist (`accounts`).

## Weiterverarbeitung

`--json` liefert neben `contacts` auch `mails` (Konto, Ordner, UID, Header je
gefundener Mail) und `missing`:

```
python3 "$SKILL_DIR/imap" contacts 8841 --json \
  | python3 -c 'import json,sys; print(",".join(c["email"] for c in json.load(sys.stdin)["contacts"]))'
```

Die eigene Adresse steht mit in der Liste - beim Bau des Envelope gehoert sie
in der Regel heraus, es sei denn, eine Kopie ins eigene Postfach ist gewollt.

## BODY.PEEK

`contacts` setzt `\Seen` nicht - weder bei der Startmail noch bei den Mails der
Kette.
