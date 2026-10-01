# imap - append und Kontowechsel

Versendete Mail ablegen, zwischen Konten kopieren und verschieben.

## `append` -- die versendete Mail in "Gesendet" ablegen

`swaks` spricht SMTP und sonst nichts: es legt **keine Kopie in "Gesendet"** ab.
Die einzige Spur einer versendeten Mail ist die Bcc-Kopie im Posteingang. Wer sie
später sucht, sucht zuerst im falschen Ordner und findet nichts -- der Versand
sieht dann aus, als hätte er nie stattgefunden. `append` schließt die Lücke:

```bash
python3 "$SKILL_DIR/imap" append $M/mail.eml -a <konto>
python3 "$SKILL_DIR/imap" append $M/mail.eml -a <konto> --dry-run --json
```

Abgelegt wird **genau die Datei, die versendet wurde** -- dieselbe, die an
`swaks --data @...` ging. Ein zweiter Bau wäre eine andere Mail: Message-ID und
`Date` entstehen bei jedem Lauf neu.

| Option | Wirkung |
|---|---|
| `-f/--folder` | Zielordner; Default die Sonderrolle `sent`. Auch `drafts`, `archive`, `junk`, `trash` oder ein echter Ordnername |
| `--flags` | IMAP-Flags, leerzeichengetrennt. Default `\Seen` |
| `--date` | `INTERNALDATE`; Default `now` |
| `--allow-duplicate` | auch anlegen, wenn dieselbe Message-ID schon im Ordner liegt |
| `--dry-run` | nur zeigen, was passieren würde |

**Warum `\Seen` der Default ist:** eine selbst versendete Mail ist nicht
ungelesen. Ohne das Flag steht der Eintrag fett im Ordner und sieht nach
eingegangener Post aus.

**Zurückgelesen:** nach dem `APPEND` wird die Mail per Message-ID im Ordner
gesucht; erst der Fund zählt als Erfolg, die UIDs stehen im Feld `uids`. Ein
`OK` des Servers ohne Fund endet mit `ok: false`. swaks ruft `append` so auf
(`--send … --file-sent`, `--draft`), siehe dort.

**Wiederholbar:** liegt im Zielordner bereits eine Mail mit derselben
Message-ID, schreibt `append` **nichts** und meldet `duplicate: true`. Der
Abbruch eines Laufs zwischen Versand und Ablage ist der häufige Fall, ein
doppelter Eintrag in "Gesendet" der lästige.

**Geprüft wird vorher**, ob die Datei überhaupt eine Mail ist: fehlen `From`
und `To` im Kopf, bricht der Aufruf ab. Der typische Fehlgriff ist die
Body-Datei (`body.txt`) statt der fertigen `.eml`; ohne die Prüfung landete sie
als kopfloser Fremdkörper im Ordner.

Der Ordner wird **nicht angelegt**: findet sich keine `sent`-Sonderrolle und kein
Ordner dieses Namens, bricht der Aufruf ab (wie bei `-t/--target`).

## Kontoübergreifend

Innerhalb eines Kontos läuft `MOVE` serverseitig. Zwischen zwei Konten kennt
IMAP keinen solchen Befehl -- die Mail wird geholt und per `APPEND` im Ziel
eingefügt, mit Flags und `INTERNALDATE`. Ablauf:

1. `APPEND` ins Ziel, Erfolg prüfen
2. **erst danach** die Quelle räumen (nur bei `move`)

Schlägt der `APPEND` fehl, bleibt die Quelle unangetastet. Im schlimmsten Fall
entsteht ein Duplikat, nie ein Verlust. Vor dem `APPEND` wird per Message-ID
geprüft, ob die Mail im Ziel schon liegt -- ein abgebrochener Lauf ist damit
gefahrlos wiederholbar.

Bare LF wird vor dem `APPEND` auf CRLF normalisiert (verlustfrei). Cyrus weist
solche Mails sonst mit `NO` zurück, während Dovecot sie klaglos gespeichert
hat -- Richtung Dovecot -> Cyrus ist das der häufigste Fehlerfall.
