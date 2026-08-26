---
name: mail-as-me
description: >
  Entwirft und ueberarbeitet E-Mails im persoenlichen Schreibstil des jeweiligen
  Nutzers (Register, Anrede, Sign-off, Dialekt, Hedging), statt in generischem
  KI-Deutsch. Nutze diesen Skill, wenn ein Mail-Entwurf "nach mir" klingen soll,
  wenn eine Mail in meinem Stil verfasst/umgeschrieben werden soll, oder wenn ein
  Nutzer sein Stilprofil einrichten will. Auch aktiv verwenden bei "schreib eine
  Mail wie ich", "schreib das als Mail wie ich", "in meinem Stil", "klingt zu sehr
  nach KI, mach es wie ich". Bei solchen Auftraegen IMMER zuerst diesen Skill
  aufrufen — auch wenn die Mail danach gleich versendet wird; die Mail NICHT direkt
  in swaks texten (sonst wird der Empfaenger gespiegelt, z.B. CH-Grussformel "Hoi").
  Die universelle Logik lebt im Skill, das persoenliche Profil (Beispiel-Korpus +
  Stilregeln) pro Person unter ~/.claude/mail-as-me/<profil>/.
  Trigger: /mail-as-me.
---

# mail-as-me – Mails im eigenen Schreibstil

Zwei Teile: **universelle Engine** (dieser Skill) + **pro-Person-Profil** (Daten
unter `~/.claude/mail-as-me/<profil>/`). Der Skill liest ein Profil und wendet es an;
`setup` erzeugt/erweitert ein Profil aus echten Mail-Samples.

`$SKILL_DIR` ist das Base Directory dieses Skills (dort wo diese SKILL.md liegt) —
Aufrufe im Text beziehen sich darauf, z.B. `python3 "$SKILL_DIR/extract.py"`.

## Grundregel: eigene Stimme, nie spiegeln

Geschrieben wird **immer** in der Stimme des Profils, nie in der des Gegenuebers —
weder Sprache, Stil, Register, Region/Dialekt, Anrede noch Grussformel werden
uebernommen. Basis von Profil `michael` ist oesterreichisches Deutsch (de-AT),
Anrede „Hallo {Vorname},".

**Konkretes Anti-Beispiel (der wiederkehrende Fehlgriff):** Ein Empfaenger aus der
Schweiz oder Deutschland (z.B. `example.com`, `example.ch`) bekommt trotzdem „Hallo
Karin," — **nie** eine gespiegelte CH/DE-Grussformel wie „Hoi", „Grüezi",
„Grüessech", „Grüess di" oder „Servus". Gilt auch fuer eine Reply-`.eml`: Ton und
Region des Absenders werden **nicht** uebernommen. Sprache/Region nur wechseln, wenn
der Nutzer es **explizit** vorgibt.

## Profil-Ablage

```
~/.claude/mail-as-me/<profil>/
  referenz.md          # das Stilprofil (aus templates/referenz.template.md)
  corpus/clean/*.md    # bereinigte Beispiel-Mails (Frontmatter + Eigentext)
  config.json          # Name, Dialekt, Sign-off (+Sonderfaelle), Anrede,
                        # register_map (Domain->Register), Signatur-Pfade,
                        # send (Absender + Bcc fuer den Versand)
```

Profil-Wahl: `--profile <name>`; ohne Angabe das einzige vorhandene bzw. `default`.
Existiert kein Profil, zuerst `setup` anbieten.

## Subcommands

### setup — Profil bauen/erweitern (Auto + kurzes Interview)

```bash
python3 "$SKILL_DIR/extract.py" --input <ordner|datei> \
  --out ~/.claude/mail-as-me/<profil>/corpus \
  --config ~/.claude/mail-as-me/<profil>/config.json
```

1. **Samples einsammeln.** No-privilege-Weg fuer Mitarbeiter: in Thunderbird Mails
   markieren → „Speichern als" bzw. herausziehen → `.eml` in einen Ordner. Auch
   `.mbox` (ganzer Ordner-Export) oder ein Maildir/Cyrus-Verzeichnis moeglich.
   **Auswahl-Regel:** nur selbstverfasste Mails mit substanziellem Eigentext,
   Register gestreut (formell + locker), moeglichst >4 Wochen alt (keine
   KI-generierten Fassungen). Anhaenge egal — werden ignoriert.
2. **Auto-Extraktion.** `extract.py` strippt Zitat + Signatur, schlaegt je Mail
   `bucket` (Register) und `dialekt_auto` vor.
3. **Kurzes Interview** — nur was Samples nicht sicher hergeben; Auto-Vorschlag
   zeigen, Mensch bestaetigt/korrigiert:
   - Sign-off je Register **+ Sonderfaelle** (z.B. „Mike nur bei Empfaengern, die
     mich selbst so nennen").
   - Du/Sie-Zuordnung.
   - Dialekt (Auto-Detect bestaetigen; z.B. de-AT: „eh", „Jänner", „schlimmster
     Fall"). Achtung Fehlgriffe des Auto-Detects hier wegklicken.
   - Empfaenger/Domain → Register (`register_map`).
   - Versand-Adressen: eigene Absenderadresse und — falls gewuenscht — eine
     Bcc-Kopie an sich selbst (`send.from`, `send.bcc`, siehe unten).
4. **Profil schreiben.** `config.json` aus dem Interview, `referenz.md` aus
   `templates/referenz.template.md` mit den abgeleiteten Markern + Beispiel-Index
   fuellen. Re-Run erweitert den Korpus (bestehende `clean/` bleiben).

Einzelne Datei nur pruefen (nichts schreiben): `extract.py --analyze <datei>`.

### draft — Entwurf in der eigenen Stimme

Eingabe: Empfaenger (+ Thema **oder** eine Reply-`.eml`). Ablauf:
1. Register aus `config.json.register_map` bestimmen (Domain), sonst nachfragen.
2. `referenz.md` + 1–2 Beispiele desselben Registers aus `corpus/clean/` laden.
3. **Faktencheck vor dem Schreiben.** Bevor der erste Satz steht: welche
   **Tatsachenbehauptung** und welche **Machbarkeitszusage** soll die Mail
   enthalten -- und ist sie belegt? Belegt heisst nachgesehen (Datenbank, Code,
   Config, Log, Ticket), nicht plausibel. Was sich nicht belegen laesst, kommt
   nicht als Zusage in den Entwurf, sondern als Vorbehalt oder als Rueckfrage an
   den Nutzer. Der Schritt steht bewusst **vor** dem Entwurf: eine unbelegte
   Zusage ist kein Formulierungsfehler, den ein Audit hinterher findet -- sie
   liest sich sauber und faellt erst beim Empfaenger auf.
   Typischer Fall: eine Datenuebernahme wird zugesagt, ohne dass geprueft ist,
   ob im Quellsystem ueberhaupt Werte stehen (sie standen nicht, das Feld war
   durchgehend leer). Ergebnis in einem Halbsatz in die Ausfuehrungszeile.
4. Entwurf bauen: Anrede/Sign-off/Du-Sie/Dialekt gemaess Profil, Stilmarker
   anwenden. **Immer in der eigenen Stimme des Profils — das Gegenueber niemals
   spiegeln** (weder Sprache, Stil, Register, Region/Dialekt, Anrede noch
   Grussformel; bei einer Reply-`.eml` nicht Ton/Region des Absenders uebernehmen).
   Die Sprache nur wechseln, wenn der Nutzer es **explizit** vorgibt.
5. **Pflicht-Audit via humanizer-de.** Den Skill `humanizer-de` **tatsaechlich
   aufrufen** (Skill-Tool bzw. `/humanizer-de`), Modus **Sachlich**, Zweig **Nur
   Audit**. Ein manueller Abgleich gegen die Anti-Pattern-Liste in `referenz.md`
   ersetzt den Lauf **nicht** und zaehlt nicht als erledigter Schritt 5. Der Lauf
   entfaellt auch bei kurzen Mails, Routinemeldungen oder Zeitdruck nicht.
   Anschliessend die profilspezifischen Anti-Patterns aus `referenz.md` zusaetzlich
   inhaltlich durchgehen: die Linter finden diese Klasse nicht (Zeitkolorit im
   Einstieg, Abstraktum statt konkretem Sachverhalt, Nebenbefunde ohne
   Handlungsrelevanz, doppeltes Hedging, "Rueckfall" fuer Software).
   Beides ist noetig, keines ersetzt das andere.
6. **Pflicht-Aufruf `imap quote` bei jedem Reply.** Liegt ein Reply-Kontext vor
   (eine Mail, auf die geantwortet wird -- UID im Postfach oder eine `.eml`), wird
   der Zitatblock **nicht getippt, sondern erzeugt**:
   `imap quote <uid> -a <konto> -f <ordner>` fuer den Text-Part, `--format html`
   fuer den HTML-Part, `--json` fuer die Threading-Header. **`-f` gehoert dazu,
   sobald die Mail nicht in der INBOX liegt** -- UIDs sind ordner-lokal, ohne
   `-f` wird die gleichnamige UID der INBOX zitiert, also eine fremde Mail, und
   zwar ohne Fehlermeldung. Ist nur die Message-ID bekannt, `imap quote
   -m "<message-id>"` verwenden: das loest Konto, Ordner und UID selbst auf.
   Selbst gesetzte `> `-Praefixe zaehlen **nicht** als erledigter
   Schritt 6 -- sie sehen auf den ersten Blick gleich aus, weichen aber bei jeder
   Mail leicht ab und ignorieren `format=flowed` und die Threading-Header. Kein
   Reply-Kontext: der Schritt entfaellt und wird als `kein Reply` ausgewiesen.
7. Entwurf zeigen, **immer mit der Ausfuehrungszeile** (siehe unten). Optional
   Versand ueber **swaks** (Text + HTML), Signatur dort; Absender und Bcc kommen
   aus `config.json.send` (siehe Abschnitt Versand).

### rewrite — bestehenden Entwurf in-voice bringen

Nimmt einen Entwurf (eigener oder fremder), gleicht ihn an das Profil an und laeuft
denselben **verbindlichen** humanizer-de-Audit aus Schritt 5 von `draft` sowie -- bei
Reply-Kontext -- den **Pflicht-Aufruf** von `imap quote` aus Schritt 6, inklusive
Ausfuehrungszeile beim Zeigen. Der **Faktencheck** aus Schritt 3 gilt hier genauso:
ein uebernommener Entwurf bringt seine Zusagen mit, geprueft sind sie deswegen nicht. Bringt der Entwurf bereits ein von Hand getipptes Zitat
mit, wird es **ersetzt**, nicht uebernommen. Fuer „mach diese Mail wie ich". Gilt auch hier: **das
Gegenueber nie spiegeln** (Sprache/Stil/Region), ein fremder Ausgangston wird auf die
eigene Stimme gezogen, nicht beibehalten.

### learn — Feedback-Loop (Konvergenz)

```
--draft <entwurf> --sent <tatsaechlich_gesendet>
```
Beide Fassungen kommen typischerweise als Dateien aus einem vom Nutzer genannten
**Projektordner** (Entwurf + tatsaechlich gesendete Fassung nebeneinander). Diff der
beiden bilden, die Korrekturen als neue Anti-Patterns/Beispiele an `referenz.md`
anhaengen — dabei generelle Stilregeln von inhaltlichen Einzelfall-Aenderungen trennen.
So wird jede korrigierte Mail zum Trainingssignal; die Korrekturen pro Mail nehmen mit
der Zeit ab.

## Ausfuehrungszeile (Pflicht bei draft und rewrite)

Jeder gezeigte Entwurf beginnt mit **einer** Zeile, die belegt, welche Schritte
tatsaechlich gelaufen sind. Sie steht vor dem Entwurf, nicht danach, und wird auch bei
kurzen Mails gesetzt:

```
Schritte: Profil michael · Register sachlich (example.ch) · Beispiele 76421, 76512 · Faktencheck: Spalte in DB geprueft, keine Werte -> Zusage raus · humanizer-de Sachlich/Nur-Audit: Preflight low, keine HIGH-Cluster · Quote office/ToDo/200
```

Sechs Felder, immer in dieser Reihenfolge:

| Feld | Inhalt |
|---|---|
| Profil | Name des geladenen Profils |
| Register | bestimmtes Register + Herkunft (Domain aus `register_map`, sonst „nachgefragt") |
| Beispiele | IDs/Dateinamen der geladenen Beispiele aus `corpus/clean/` |
| Faktencheck | woran die Behauptung/Zusage geprueft wurde und was dabei herauskam, sonst `keine Zusage` |
| humanizer-de | Modus/Zweig + Ergebnis in Kurzform (Preflight-Stufe, Cluster-Befund) |
| Quote | `<konto>/<ordner>/<uid>` der zitierten Mail, sonst `kein Reply` |

`Faktencheck: keine Zusage` heisst: die Mail behauptet nichts Pruefbares (reine
Terminabsprache, Rueckfrage, Dank). `Faktencheck: nicht gelaufen` heisst, es gab
etwas zu pruefen und geprueft wurde nicht -- dieselbe Unterscheidung wie bei
`kein Reply` gegenueber `nicht gelaufen`.

Ist ein Schritt nicht gelaufen, wird das **ausgeschrieben** (`humanizer-de: nicht
gelaufen`, `Quote: nicht gelaufen`), statt das Feld wegzulassen. `kein Reply` und
`nicht gelaufen` sind dabei zwei verschiedene Aussagen: das eine heisst, es gab nichts
zu zitieren, das andere, dass es etwas zu zitieren gab und der Aufruf unterblieb. Ein fehlendes Feld ist genau der Fall, der
unbemerkt durchrutscht; eine Zeile, die einen Schritt als gelaufen ausweist, der nicht
gelaufen ist, ist eine Falschaussage und schlimmer als gar keine Zeile.

Die Zeile ist Arbeitsprotokoll fuer den Nutzer und **kein Teil der Mail**: beim Versand
ueber swaks wird sie nicht mitgeschickt.

## Versand: Absender und Bcc aus dem Profil

Gesendet wird ueber **swaks** — dessen Defaults (`--from claude@azedo.at`) sind aber
die von Claude, nicht die des Profils. Eine Mail, die in der eigenen Stimme verfasst
wurde, aber von `claude@azedo.at` kommt, ist beim Empfaenger schlicht falsch. Damit
das nicht bei jedem Versand haendisch nachgezogen werden muss, steht die
Versand-Identitaet im Profil:

```json
"send": {
  "from": "ich@example.org",
  "bcc": "ich@example.org"
}
```

Beide Felder sind optional: fehlt `from`, gilt der swaks-Default; fehlt `bcc` (oder
ist es leer), geht keine Kopie raus. Mehrere Bcc-Adressen kommasepariert.

**Regel:** Wird ein Entwurf aus `draft`/`rewrite` versendet, wird `send` aus dem
geladenen Profil gelesen und angewendet — ohne Rueckfrage, wie die Signatur. Eine
Angabe des Nutzers im Auftrag ("schick das von X") hat Vorrang.

Umsetzung im swaks-Aufruf — `from` geht an **beide** Seiten (Header und Envelope),
`bcc` **nur** in den Envelope, sonst wird die Kopie fuer die Empfaenger sichtbar:

```bash
M=$(mktemp -d .tmp/mail.XXXXXX)
B=~/.claude/skills/swaks/build_mail.py

python3 $B \
  --subject "Betreff" \
  --to "empfaenger@example.com" \
  --from ich@example.org \
  --bcc ich@example.org \
  --text-file $M/body.txt \
  --html-file $M/body.html \
  --sha-file $M/mail.sha256 \
  > $M/mail.eml \
  && test -s $M/mail.eml \
  && python3 $B --verify $M/mail.eml \
      --expect-sha256 "$(cat $M/mail.sha256)" \
      --expect-marker "<woertliches Stueck aus dem freigegebenen Entwurf>" \
  && swaks --server <server> \
      --to "empfaenger@example.com,ich@example.org" \
      --from ich@example.org \
      --data @$M/mail.eml
```

**Kein fester Pfad wie `.tmp/mail.eml`, und die `--verify`-Zeile gehoert dazu.**
Eine parallel laufende Session schreibt sonst dieselbe Datei, und der Versand
nimmt, was zuletzt drinstand -- mit korrektem Betreff, korrektem Empfaenger und
dem Text einer fremden Mail. Beim Versand faellt das nicht auf: swaks quittiert
die uebertragenen Bytes, nicht die gebauten. Der Marker ist ein woertliches
Stueck aus dem freigegebenen Entwurf; `--verify` dekodiert den Text-Part und
sucht es dort (ein `grep` auf die rohe `.eml` findet es nicht, der Body ist
quoted-printable kodiert). Details im swaks-Skill, Abschnitt "Vor dem Versand
pruefen".

**Nach dem Versand ablegen.** swaks legt keine Kopie in "Gesendet" ab; das holt
`imap append` nach, mit genau der Datei, die versendet wurde:

```bash
python3 ~/.claude/skills/imap/imap append $M/mail.eml -a <konto>
```

Erst nach dem erfolgreichen Versand, nie davor -- eine Kopie in "Gesendet" zu
einer abgewiesenen Mail ist eine Falschaussage im Postfach. Ein wiederholter
Lauf legt keinen zweiten Eintrag an (gleiche Message-ID).

**Nur Text und kein HTML-Entwurf?** Dann `--html-file` weglassen, nicht die
Textdatei ein zweites Mal angeben. Ein HTML-Part aus rohem Text hat kein
einziges Tag und kommt beim Empfaenger in einer einzigen Zeile an -- Aufzaehlung,
Tabelle und Zugangsdaten inklusive.

`--bcc` an `build_mail.py` setzt bewusst **keinen** Header; zugestellt wird die Kopie
allein ueber den Envelope-`--to` von swaks. Fehlt sie dort, kommt trotz `--bcc` nichts
an. Die Signatur bleibt beim eigenen Absender aus `send.from` dran (die globale
Signatur ist die eigene, siehe swaks-Skill) — der Wechsel des Absenders ist **kein**
Ausschlussgrund.

## Antworten: Zitat und Threading

Bei einer Antwort kommen fuenf Dinge nicht aus dem Entwurf, sondern aus `imap quote`:
der **Text-Quote**, der **HTML-Quote**, die beiden **Threading-Header**, der **Betreff**
und die **Empfaenger**. Der Grund ist derselbe wie beim humanizer-de-Audit: was das
Modell selbst tippt, weicht bei jeder Mail leicht ab. Das alles ist Formatarbeit, keine
Formulierungsarbeit.

**Betreff und Empfaenger stehen in `quote --json` bereits drin** (`subject`, `from`,
`to`, `cc`) -- sie werden von dort uebernommen, nicht abgeschrieben und nicht aus dem
Auftrag rekonstruiert:

- **Betreff** = `subject` plus ein vorangestelltes `Re: `. Ein abgetippter Betreff
  verliert genau die Zeichen, an denen der Mailclient den Thread erkennt: eine
  Ticketnummer in eckigen Klammern, ein `AW:` der Gegenseite, ein Umlaut aus einer
  RFC-2047-Kodierung.
- **Empfaenger** = `from`; bei Reply-All zusaetzlich `to` und `cc`, **abzueglich der
  eigenen Adressen** aus `config.json.send`. Aus dem Auftrag kommt hoechstens eine
  ausdrueckliche Abweichung ("nur an X"), nicht die Standardbesetzung.

Wer die Empfaenger aus dem Auftrag statt aus den Kopfdaten nimmt, verliert still den
Mitleser im `Cc` -- fuer den Absender sieht die Antwort vollstaendig aus.

**Position: Antwort oben, Zitat unten** (Top-Posting). Die Reihenfolge im fertigen
Text-Part ist Antwort -> Signatur -> Zitat; `build_mail.py` setzt sie so zusammen,
solange der Quote ueber `--quote-text-file`/`--quote-html-file` hereinkommt. Der Entwurf
selbst enthaelt also **kein** Zitat.

```bash
Q=$(mktemp -d .tmp/reply.XXXXXX)
IMAP=~/.claude/skills/imap/imap
B=~/.claude/skills/swaks/build_mail.py

# 1. Zitat und Threading erzeugen -- nicht tippen.
#    -f gehoert dazu, sobald die Mail nicht in der INBOX liegt (UIDs sind
#    ordner-lokal); alternativ -m "<message-id>" statt uid/-a/-f.
python3 $IMAP quote <uid> -a <konto> -f <ordner> > $Q/quote.txt
python3 $IMAP quote <uid> -a <konto> -f <ordner> --format html > $Q/quote.html
python3 $IMAP quote <uid> -a <konto> -f <ordner> --json > $Q/quote.json

# 2. Threading-Header abgreifen (Feld `reply`, nicht die Header der Originalmail)
IRT=$(python3 -c "import json;print(json.load(open('$Q/quote.json'))['reply']['in_reply_to'])")
REF=$(python3 -c "import json;print(json.load(open('$Q/quote.json'))['reply']['references'])")

# 3. Betreff und Empfaenger aus denselben Kopfdaten -- nicht abschreiben.
#    Re: nur, wenn nicht schon ein Re:/AW: dransteht; Reply-All ist
#    from + to + cc minus der eigenen Adressen aus config.json.send.
SUBJ=$(python3 -c "
import json,re
s=json.load(open('$Q/quote.json'))['subject']
print(s if re.match(r'^(re|aw|wg|fwd)\s*:', s, re.I) else 'Re: '+s)")
TO=$(python3 -c "
import json,email.utils
q=json.load(open('$Q/quote.json'))
mine={'ich@example.org'}
addrs=email.utils.getaddresses([q['from'], q['to'], q['cc']])
seen=[]
for _,a in addrs:
    if a and a.lower() not in mine and a.lower() not in seen: seen.append(a.lower())
print(','.join(seen))")

# 4. Mail bauen -- Body ohne Zitat, der Helper haengt es unter die Signatur
python3 $B \
  --subject "$SUBJ" \
  --to "$TO" \
  --from ich@example.org \
  --text-file $Q/body.txt \
  --html-file $Q/body.html \
  --quote-text-file $Q/quote.txt \
  --quote-html-file $Q/quote.html \
  --in-reply-to "$IRT" \
  --references "$REF" \
  --sha-file $Q/mail.sha256 \
  > $Q/mail.eml \
  && test -s $Q/mail.eml \
  && python3 $B --verify $Q/mail.eml \
      --expect-sha256 "$(cat $Q/mail.sha256)" \
      --expect-marker "<woertliches Stueck aus dem Entwurf>" \
  && swaks --server <server> --to "$TO" \
      --from ich@example.org --data @$Q/mail.eml
```

Zum Betreff: `Re: ` wird **einmal** vorangestellt. Traegt der Originalbetreff bereits
ein `Re:` (oder das deutsche `AW:`), bleibt es bei dem vorhandenen Praefix -- `Re: AW:
Re: ...` ist ein sicheres Zeichen dafuer, dass der Betreff zusammengetippt statt
uebernommen wurde. Die Fallunterscheidung steckt deshalb im Snippet oben und nicht im
Kopf des Modells.

**Warum die Threading-Header nicht optional sind:** ohne `In-Reply-To` und `References`
startet die Antwort im Mailclient des Empfaengers einen **neuen** Thread. Das faellt
beim Versand nicht auf, sondern erst beim Gegenueber -- und dort auch nur als
diffuses "die Antwort ist irgendwo untergegangen". Es ist genau der Fehler, der zuletzt
nachtraeglich in die fertige `.eml` gepatcht werden musste.

**Liegt die Mail als `.eml` statt im Postfach**, gibt es keine UID -- dann bleibt nur
der handgebaute Weg (Betreff und Empfaenger kommen dort aus den Kopfzeilen der `.eml`,
ebenfalls nicht aus dem Auftrag). Das ist der einzige Fall, in dem das Zitat nicht aus `imap quote`
kommt; in der Ausfuehrungszeile steht dann `Quote: aus .eml` statt einer UID.

## Anti-Patterns / KI-Tells → humanizer-de

Die sprachlichen Anti-Patterns (Gedankenstrich, Nominalkomposita, elliptische
Antithese, erfundene Zusagen, Anfuehrungszeichen um Paraphrasen, Absolutheit ohne
Hedge, Bestaetigungsfloskeln) sind personenunabhaengig und werden **nicht** hier
dupliziert, sondern ueber einen **Aufruf** des **humanizer-de**-Skills geprueft, nicht
aus dem Gedaechtnis. `referenz.md` fuehrt sie nur als Checkliste mit dem persoenlichen
Bezug; diese Checkliste ist die **Ergaenzung** zum Skill-Lauf, nicht sein Ersatz.

## Integration

- **humanizer-de** - verbindlicher KI-Tell-Audit in Schritt 5 von `draft`/`rewrite`,
  kein optionaler Self-Check; Ergebnis gehoert in die Ausfuehrungszeile.
- **imap** - `quote` erzeugt bei jeder Antwort den Zitatblock und die
  Threading-Header (Schritt 6) und liefert Betreff und Empfaenger gleich mit.
  Ebenfalls ein Aufruf, kein Nachbauen; Ergebnis gehoert als letztes Feld in die
  Ausfuehrungszeile. Ist statt der UID nur die Message-ID bekannt (einkopierte
  Mail), loest `imap quote -m` bzw. `imap find -m` sie zu Konto, Ordner und UID
  auf -- der Handabgleich ueber `folders` + `list` entfaellt.
- **swaks** — Versand (`mail-as-me` schreibt, `swaks` sendet; Signatur kommt aus
  swaks, Absender und Bcc aus `config.json.send` des Profils).
- **imap** — `quote` fuer Zitat und Threading vor dem Versand, `append` fuer die
  Ablage in "Gesendet" danach.
- **kanboard/handoff** — optional CR-Kontext fuer den `learn`-Loop.

## Hinweise

- Profil-Daten liegen **ausserhalb** des Skills (`~/.claude/mail-as-me/`), damit der
  versionierte Skill und die persoenlichen Daten getrennt bleiben.
- Temporaere Dateien ins Projekt-`.tmp/`, nie ins Skill-Verzeichnis. Die Dateien
  eines Versands (Body, `.eml`, Quote) aber in ein **eigenes** Verzeichnis pro
  Versand (`mktemp -d` unter `.tmp/`): feste Pfade kollidieren mit parallel
  laufenden Sessions, siehe Abschnitt Versand.
- Der Auto-Register-/Dialekt-Vorschlag ist bewusst nur ein Vorschlag — im Zweifel
  im Interview bestaetigen lassen (der Auto-Detect kann daneben liegen).
