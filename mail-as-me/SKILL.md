---
name: mail-as-me
description: >
  Entwirft und überarbeitet E-Mails im persönlichen Schreibstil des Nutzers
  (Register, Anrede, Sign-off, Dialekt, Hedging) statt in generischem
  KI-Deutsch; richtet auch das Stilprofil ein. Die fertige Mail geht per
  swaks raus oder landet als Entwurf im Postfach. Auch bei "schreib eine Mail
  wie ich", "in meinem Stil", "klingt zu sehr nach KI, mach es wie ich", "leg es mir als Entwurf ab".
  Soll eine Mail nach dem Nutzer klingen, immer zuerst hier den Text
  erzeugen und erst danach mit swaks versenden - nie direkt in swaks texten,
  sonst wird der Stil des Empfängers gespiegelt.
  Trigger: /mail-as-me.
---

# mail-as-me - Mails im eigenen Schreibstil

Zwei Teile: die **universelle Engine** (dieser Skill) und ein **pro-Person-Profil**
(Daten unter `~/.claude/mail-as-me/<profil>/`). Der Skill liest ein Profil und wendet
es an; `setup` erzeugt oder erweitert ein Profil aus echten Mail-Samples.

`$SKILL_DIR` ist das Base Directory dieses Skills (dort wo diese SKILL.md liegt) -
Aufrufe im Text beziehen sich darauf, z.B. `python3 "$SKILL_DIR/extract.py"`.

## Grundregel: eigene Stimme, das Gegenueber nicht spiegeln

Geschrieben wird in der Stimme des Profils, nicht in der des Gegenuebers: Sprache,
Stil, Register, Region/Dialekt, Anrede und Grussformel kommen aus dem Profil. Der
Grund ist der Zweck des Skills - eine Mail, die den Ton des Empfaengers nachahmt,
klingt nicht mehr nach dem Absender, und genau das faellt dem Empfaenger auf, der
den Absender kennt.

Der wiederkehrende Fehlgriff: ein Empfaenger aus der Schweiz oder Deutschland
(z.B. `example.ch`) bekommt die Anrede des Profils („Hallo Karin,") und keine
gespiegelte Grussformel wie „Hoi", „Grüezi", „Grüessech" oder „Servus". Das gilt
ebenso fuer eine Antwort, bei `rewrite` fuer einen fremden Ausgangston. Sprache oder
Region wechseln nur, wenn der Nutzer es ausdruecklich vorgibt.

## Profil-Ablage

```
~/.claude/mail-as-me/<profil>/
  referenz.md          # das Stilprofil (aus templates/referenz.template.md)
  corpus/clean/*.md    # bereinigte Beispiel-Mails (Frontmatter + Eigentext)
  config.json          # Name, Dialekt, Sign-off (+Sonderfaelle), Anrede,
                        # register_map (Domain->Register), Signatur-Pfade,
                        # send (Absender + Konto fuer Gesendet),
                        # draft (Konto fuer Entwuerfe)
```

Profil-Wahl: `--profile <name>`; ohne Angabe das einzige vorhandene bzw. `default`.
Existiert kein Profil, zuerst `setup` anbieten.

## Subcommands

| Subcommand | Zweck | Details |
|---|---|---|
| `write` | Mail in der eigenen Stimme schreiben | unten |
| `draft` | wie `write`, Ablage in den Entwuerfen statt Versand | [references/versand.md](references/versand.md) |
| `rewrite` | bestehenden Entwurf in die eigene Stimme bringen | unten |
| `setup` | Profil aus echten Mails bauen oder erweitern | [references/profil.md](references/profil.md) |
| `learn` | Korrekturen einer gesendeten Mail ins Profil zurueckspielen | [references/profil.md](references/profil.md) |

### write - Mail in der eigenen Stimme

Eingabe: Empfaenger und Thema, oder eine Mail, auf die geantwortet wird. Ablauf:

1. **Empfaenger aufloesen.** Bevor irgendetwas anderes passiert, steht fest, an
   welche Adresse die Mail geht und woher sie stammt. Bei einer Antwort aus
   `imap quote --json` (siehe [references/antworten.md](references/antworten.md))
   bzw. `imap contacts`, bei einer neuen Mail an einen Namen aus
   `grep -i <name> .claude/swaks-contacts.tsv` (auch `~/.claude/`; die Datei ist
   optional). Kein Treffer, keine Datei oder ein unklarer Kreis: nachfragen. Eine
   aus Domain und Vornamen zusammengebaute Adresse ist geraten, auch wenn sie
   plausibel aussieht - sie faellt weder beim Bau noch beim Versand auf, sondern
   erst beim Bounce oder beim falschen Empfaenger.
2. **Register** aus `config.json.register_map` bestimmen (Domain), sonst nachfragen.
3. **Profil laden:** `referenz.md` und 1-2 Beispiele desselben Registers aus
   `corpus/clean/`.
4. **Faktencheck vor dem Schreiben.** Welche Tatsachenbehauptung und welche
   Machbarkeitszusage soll die Mail enthalten, und ist sie belegt? Belegt heisst
   nachgesehen (Datenbank, Code, Config, Log, Ticket), nicht plausibel. Was sich
   nicht belegen laesst, kommt als Vorbehalt oder als Rueckfrage an den Nutzer in
   den Entwurf, nicht als Zusage. Der Schritt steht vor dem Entwurf, weil eine
   unbelegte Zusage kein Formulierungsfehler ist, den ein Audit hinterher findet -
   sie liest sich sauber und faellt erst beim Empfaenger auf. Typischer Fall: eine
   Datenuebernahme wird zugesagt, ohne dass geprueft ist, ob im Quellsystem
   ueberhaupt Werte stehen (sie standen nicht, das Feld war durchgehend leer).
5. **Entwurf bauen:** Anrede, Sign-off, Du/Sie und Dialekt gemaess Profil,
   Stilmarker anwenden (Grundregel oben).
6. **Audit mit humanizer-de.** Den Skill `humanizer-de` aufrufen (Skill-Tool bzw.
   `/humanizer-de`), Modus Sachlich, Zweig Nur Audit - auch bei kurzen Mails. Ein
   Abgleich aus dem Gedaechtnis ersetzt den Lauf nicht: die Linter finden Muster,
   die beim Gegenlesen des eigenen Textes durchrutschen. Danach die
   profilspezifischen Anti-Patterns aus `referenz.md` inhaltlich durchgehen, denn
   diese Klasse finden die Linter nicht (Zeitkolorit im Einstieg, Abstraktum statt
   konkretem Sachverhalt, Nebenbefunde ohne Handlungsrelevanz, doppeltes Hedging,
   "Rueckfall" fuer Software). Ein Partikel-Befund (`particles_outside_locker`) fuer
   ein Wort, das `referenz.md` als Stilmarker fuehrt (z.B. "eh", "eben",
   "einfach"), wird verworfen, weil Modus Sachlich das Profil nicht kennt; er steht
   dann als `profilkonform verworfen` in der Ausfuehrungszeile. Gehaeuft (mehr als
   einer pro Absatz) oder ausserhalb der Marker bleibt er ein Befund.
7. **Bei einer Antwort: Zitat, Threading, Betreff und Empfaenger aus `imap quote`.**
   Ablauf und Befehle: [references/antworten.md](references/antworten.md), vor
   jeder Antwort lesen. Ohne Antwort-Kontext entfaellt der Schritt.
8. **Entwurf mit Ausfuehrungszeile zeigen** (siehe unten). Versand erst nach dem Go
   des Nutzers, ueber swaks mit Absender und Ablagekonto aus `config.json.send`:
   [references/versand.md](references/versand.md).

### draft - schreiben und als Entwurf ablegen

Wie `write`, Schritte 1 bis 8 unveraendert. Statt des Versands kommt die Mail nach
dem Go in die Entwuerfe des Kontos `config.json.draft.account`; der Nutzer liest
sie dort, aendert bei Bedarf und sendet selbst aus seinem Mailclient
([references/versand.md](references/versand.md), „Als Entwurf ablegen").

### rewrite - bestehenden Entwurf in die eigene Stimme bringen

Fuer „mach diese Mail wie ich": Nimmt einen Entwurf (eigener oder fremder) und
durchlaeuft die Schritte 1 und 4 bis 8 von `write`. Ein uebernommener Entwurf
bringt Adressen, Zusagen und gegebenenfalls ein getipptes Zitat mit - geprueft ist
davon nichts. Die Adresse wird deshalb aufgeloest, die Zusagen kommen in den
Faktencheck, und ein vorhandenes Zitat wird durch das von `imap quote` erzeugte
ersetzt.

## Ausfuehrungszeile (bei write, draft und rewrite)

Jeder gezeigte Entwurf beginnt mit einer Zeile, die belegt, welche Schritte
tatsaechlich gelaufen sind - auch bei kurzen Mails. Sie ist Arbeitsprotokoll fuer
den Nutzer und kein Teil der Mail:

```
Schritte: Profil <name> · Empfaenger: aus contacts.tsv · Register sachlich (example.ch) · Beispiele 76421, 76512 · Faktencheck: Spalte in DB geprueft, keine Werte -> Zusage raus · humanizer-de Sachlich/Nur-Audit: Preflight low, keine HIGH-Cluster · Quote office/ToDo/200
```

Sieben Felder, in dieser Reihenfolge:

| Feld | Inhalt |
|---|---|
| Profil | Name des geladenen Profils |
| Empfaenger | Herkunft der Adresse: `aus contacts.tsv` \| `aus imap contacts` \| `aus quote --json` \| `vom Nutzer genannt` \| `geraten` |
| Register | bestimmtes Register + Herkunft (Domain aus `register_map`, sonst „nachgefragt") |
| Beispiele | IDs/Dateinamen der geladenen Beispiele aus `corpus/clean/` |
| Faktencheck | woran die Behauptung/Zusage geprueft wurde und was dabei herauskam, sonst `keine Zusage` |
| humanizer-de | Modus/Zweig + Ergebnis in Kurzform (Preflight-Stufe, Cluster-Befund) |
| Quote | `<konto>/<ordner>/<uid>` der zitierten Mail, `aus .eml`, sonst `kein Reply` |

Ein Schritt, der nicht gelaufen ist, wird ausgeschrieben (`humanizer-de: nicht
gelaufen`), statt das Feld wegzulassen - ein fehlendes Feld rutscht unbemerkt
durch. Deshalb sind `kein Reply` (es gab nichts zu zitieren) und `nicht gelaufen`
(es gab etwas, der Aufruf unterblieb) zwei verschiedene Aussagen, ebenso
`Faktencheck: keine Zusage` (nichts Pruefbares) und `Faktencheck: nicht gelaufen`.

`Empfaenger: geraten` ist als Auspraegung vorgesehen, obwohl Raten nach Schritt 1
nicht vorkommen soll: die Zeile ist Protokoll, kein Guetesiegel. Steht es da, faellt
der Fall vor dem Versand auf, solange er noch billig zu beheben ist. Eine Quelle
oder ein Schritt, der so nicht stattgefunden hat, macht die Zeile dagegen zur
Falschaussage - schlimmer als gar keine Zeile.

## Integration

- **humanizer-de** - KI-Tell-Audit in Schritt 6. Die sprachlichen Anti-Patterns
  (Gedankenstrich, Nominalkomposita, elliptische Antithese, erfundene Zusagen,
  Anfuehrungszeichen um Paraphrasen, Absolutheit ohne Hedge,
  Bestaetigungsfloskeln) sind personenunabhaengig und stehen deshalb dort, nicht
  hier; `referenz.md` fuehrt sie nur als Checkliste mit persoenlichem Bezug.
- **imap** - `quote` liefert bei einer Antwort Zitat, Threading-Header, Betreff und
  Empfaenger (Schritt 7); `quote -m` bzw. `find -m` loesen eine Message-ID zu Konto,
  Ordner und UID auf.
- **swaks** - Versand und Ablage (`--file-sent`, `--draft`); die Signatur kommt aus
  swaks, Absender und Ablagekonto aus dem Profil. Dessen Schritt 1 (Empfaenger
  aufloesen) und Schritt 11 (Kontakt ergaenzen) gelten mit - sie stehen hier als
  Schritt 1 von `write` und in [references/versand.md](references/versand.md), weil
  die swaks-Schrittliste beim Weg ueber `mail-as-me` nie zu sehen ist.

## Hinweise

- Profil-Daten liegen ausserhalb des Skills (`~/.claude/mail-as-me/`), damit der
  versionierte Skill und die persoenlichen Daten getrennt bleiben.
- Temporaere Dateien ins Projekt-`.tmp/`, nicht ins Skill-Verzeichnis; die Dateien
  eines Versands in ein eigenes Verzeichnis per `mktemp -d` (Grund:
  [references/versand.md](references/versand.md)).
