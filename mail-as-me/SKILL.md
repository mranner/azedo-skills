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
                        # send (Absender + Konto fuer Gesendet),
                        # draft (Konto fuer Entwuerfe)
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
   - Versand-Identitaet: eigene Absenderadresse und die imap-Konten fuer
     Gesendet und Entwuerfe (`send.from`, `send.account`, `draft.account`;
     ohne IMAP-Konto `send.bcc`, siehe unten).
4. **Profil schreiben.** `config.json` aus dem Interview, `referenz.md` aus
   `templates/referenz.template.md` mit den abgeleiteten Markern + Beispiel-Index
   fuellen. Re-Run erweitert den Korpus (bestehende `clean/` bleiben).

Einzelne Datei nur pruefen (nichts schreiben): `extract.py --analyze <datei>`.

### write — Mail in der eigenen Stimme

Eingabe: Empfaenger (+ Thema **oder** eine Reply-`.eml`). Ablauf:
1. **Empfaenger aufloesen -- nicht raten.** Bevor irgendetwas anderes passiert,
   steht fest, an welche Adresse die Mail geht und woher diese Adresse stammt.
   Bei einer **Antwort** kommen die Adressen aus `imap quote --json` bzw.
   `imap contacts` (siehe Abschnitt „Antworten: Zitat und Threading"), bei einer
   **neuen Mail an einen Namen** aus `grep -i <name> .claude/swaks-contacts.tsv`
   (auch `~/.claude/`; die Datei ist optional). Kein Treffer, keine Datei
   oder ein unklarer Kreis: **nachfragen**. Eine aus Domain und Vornamen
   zusammengebaute Adresse ist geraten, auch wenn sie plausibel aussieht -- sie
   faellt weder beim Bau noch beim Versand auf, sondern erst beim Bounce oder
   beim falschen Empfaenger. Herkunft in einem Halbsatz in die Ausfuehrungszeile;
   `geraten` ist eine zulaessige Angabe und genau deshalb vorgesehen, damit der
   Fall sichtbar wird statt unbemerkt zu bleiben.
2. Register aus `config.json.register_map` bestimmen (Domain), sonst nachfragen.
3. `referenz.md` + 1–2 Beispiele desselben Registers aus `corpus/clean/` laden.
4. **Faktencheck vor dem Schreiben.** Bevor der erste Satz steht: welche
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
5. Entwurf bauen: Anrede/Sign-off/Du-Sie/Dialekt gemaess Profil, Stilmarker
   anwenden. **Immer in der eigenen Stimme des Profils — das Gegenueber niemals
   spiegeln** (weder Sprache, Stil, Register, Region/Dialekt, Anrede noch
   Grussformel; bei einer Reply-`.eml` nicht Ton/Region des Absenders uebernehmen).
   Die Sprache nur wechseln, wenn der Nutzer es **explizit** vorgibt.
6. **Pflicht-Audit via humanizer-de.** Den Skill `humanizer-de` **tatsaechlich
   aufrufen** (Skill-Tool bzw. `/humanizer-de`), Modus **Sachlich**, Zweig **Nur
   Audit**. Ein manueller Abgleich gegen die Anti-Pattern-Liste in `referenz.md`
   ersetzt den Lauf **nicht** und zaehlt nicht als erledigter Schritt 6. Der Lauf
   entfaellt auch bei kurzen Mails, Routinemeldungen oder Zeitdruck nicht.
   Anschliessend die profilspezifischen Anti-Patterns aus `referenz.md` zusaetzlich
   inhaltlich durchgehen: die Linter finden diese Klasse nicht (Zeitkolorit im
   Einstieg, Abstraktum statt konkretem Sachverhalt, Nebenbefunde ohne
   Handlungsrelevanz, doppeltes Hedging, "Rueckfall" fuer Software).
   Beides ist noetig, keines ersetzt das andere.
   Ein Partikel-Befund (`particles_outside_locker`) fuer ein Wort, das `referenz.md`
   als Stilmarker fuehrt (z.B. "eh", "eben", "einfach"), wird verworfen: Modus
   Sachlich kennt das Profil nicht. In der Ausfuehrungszeile steht er als
   `profilkonform verworfen`, nicht stillschweigend weg. Gehaeuft (mehr als einer
   pro Absatz) oder ausserhalb der Marker bleibt er ein Befund.
7. **Pflicht-Aufruf `imap quote` bei jedem Reply.** Liegt ein Reply-Kontext vor
   (eine Mail, auf die geantwortet wird -- UID im Postfach oder eine `.eml`), wird
   der Zitatblock **nicht getippt, sondern erzeugt**:
   `imap quote <uid> -a <konto> -f <ordner>` fuer den Text-Part, `--format html`
   fuer den HTML-Part, `--json` fuer die Threading-Header. **`-f` gehoert dazu,
   sobald die Mail nicht in der INBOX liegt** -- UIDs sind ordner-lokal, ohne
   `-f` wird die gleichnamige UID der INBOX zitiert, also eine fremde Mail, und
   zwar ohne Fehlermeldung. Ist nur die Message-ID bekannt, `imap quote
   -m "<message-id>"` verwenden: das loest Konto, Ordner und UID selbst auf.
   Selbst gesetzte `> `-Praefixe zaehlen **nicht** als erledigter
   Schritt 7 -- sie sehen auf den ersten Blick gleich aus, weichen aber bei jeder
   Mail leicht ab und ignorieren `format=flowed` und die Threading-Header. Kein
   Reply-Kontext: der Schritt entfaellt und wird als `kein Reply` ausgewiesen.
8. Entwurf zeigen, **immer mit der Ausfuehrungszeile** (siehe unten). Optional
   Versand ueber **swaks** (Text + HTML), Signatur dort; Absender und Konto fuer
   die Ablage kommen aus `config.json.send` (siehe Abschnitt Versand).

### draft — schreiben und als Entwurf ablegen

Wie `write`, Schritte 1 bis 8 unveraendert. Statt des Versands kommt die Mail nach
dem Go in die Entwuerfe des Kontos `config.json.draft.account`; der Nutzer liest
sie dort, aendert bei Bedarf und sendet selbst aus seinem Mailclient. Umsetzung
siehe Abschnitt Versand, „Als Entwurf ablegen".

### rewrite — bestehenden Entwurf in-voice bringen

Nimmt einen Entwurf (eigener oder fremder), gleicht ihn an das Profil an und laeuft
denselben **verbindlichen** humanizer-de-Audit aus Schritt 6 von `write` sowie -- bei
Reply-Kontext -- den **Pflicht-Aufruf** von `imap quote` aus Schritt 7, inklusive
Ausfuehrungszeile beim Zeigen. Der **Faktencheck** aus Schritt 4 gilt hier genauso:
ein uebernommener Entwurf bringt seine Zusagen mit, geprueft sind sie deswegen nicht.
Dasselbe fuer die **Empfaenger-Aufloesung** aus Schritt 1: die Adresse im uebernommenen
Entwurf ist eine Behauptung wie jede andere und wird aufgeloest, nicht uebernommen. Bringt der Entwurf bereits ein von Hand getipptes Zitat
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

## Ausfuehrungszeile (Pflicht bei write, draft und rewrite)

Jeder gezeigte Entwurf beginnt mit **einer** Zeile, die belegt, welche Schritte
tatsaechlich gelaufen sind. Sie steht vor dem Entwurf, nicht danach, und wird auch bei
kurzen Mails gesetzt:

```
Schritte: Profil michael · Empfaenger: aus contacts.tsv · Register sachlich (example.ch) · Beispiele 76421, 76512 · Faktencheck: Spalte in DB geprueft, keine Werte -> Zusage raus · humanizer-de Sachlich/Nur-Audit: Preflight low, keine HIGH-Cluster · Quote office/ToDo/200
```

Sieben Felder, immer in dieser Reihenfolge:

| Feld | Inhalt |
|---|---|
| Profil | Name des geladenen Profils |
| Empfaenger | Herkunft der Adresse: `aus contacts.tsv` \| `aus imap contacts` \| `aus quote --json` \| `vom Nutzer genannt` \| `geraten` |
| Register | bestimmtes Register + Herkunft (Domain aus `register_map`, sonst „nachgefragt") |
| Beispiele | IDs/Dateinamen der geladenen Beispiele aus `corpus/clean/` |
| Faktencheck | woran die Behauptung/Zusage geprueft wurde und was dabei herauskam, sonst `keine Zusage` |
| humanizer-de | Modus/Zweig + Ergebnis in Kurzform (Preflight-Stufe, Cluster-Befund) |
| Quote | `<konto>/<ordner>/<uid>` der zitierten Mail, sonst `kein Reply` |

`Faktencheck: keine Zusage` heisst: die Mail behauptet nichts Pruefbares (reine
Terminabsprache, Rueckfrage, Dank). `Faktencheck: nicht gelaufen` heisst, es gab
etwas zu pruefen und geprueft wurde nicht -- dieselbe Unterscheidung wie bei
`kein Reply` gegenueber `nicht gelaufen`.

`Empfaenger: geraten` ist bewusst als Auspraegung vorgesehen, obwohl Raten laut
Schritt 1 nicht vorkommen soll: die Zeile ist Protokoll, kein Guetesiegel. Steht
sie da, faellt der Fall vor dem Versand auf -- und das ist der einzige Zeitpunkt,
zu dem er noch billig zu beheben ist. Wer stattdessen eine Quelle hinschreibt, die
es nicht gab, macht dieselbe Falschaussage wie bei einem als gelaufen
ausgewiesenen Audit.

Ist ein Schritt nicht gelaufen, wird das **ausgeschrieben** (`humanizer-de: nicht
gelaufen`, `Quote: nicht gelaufen`), statt das Feld wegzulassen. `kein Reply` und
`nicht gelaufen` sind dabei zwei verschiedene Aussagen: das eine heisst, es gab nichts
zu zitieren, das andere, dass es etwas zu zitieren gab und der Aufruf unterblieb. Ein fehlendes Feld ist genau der Fall, der
unbemerkt durchrutscht; eine Zeile, die einen Schritt als gelaufen ausweist, der nicht
gelaufen ist, ist eine Falschaussage und schlimmer als gar keine Zeile.

Die Zeile ist Arbeitsprotokoll fuer den Nutzer und **kein Teil der Mail**: beim Versand
ueber swaks wird sie nicht mitgeschickt.

## Versand: Absender und Ablage aus dem Profil

Gesendet wird ueber **swaks** — dessen Defaults (`--from claude@azedo.at`) sind aber
die von Claude, nicht die des Profils. Eine Mail, die in der eigenen Stimme verfasst
wurde, aber von `claude@azedo.at` kommt, ist beim Empfaenger schlicht falsch. Damit
das nicht bei jedem Versand haendisch nachgezogen werden muss, steht die
Versand-Identitaet im Profil:

```json
"send":  { "from": "ich@example.org", "account": "<imap-konto>" },
"draft": { "account": "<imap-konto>" }
```

`send.from` ist der Absender (fehlt er, gilt der swaks-Default). `send.account` und
`draft.account` sind Aliase aus `imap accounts`: dort landet die Mail in "Gesendet"
bzw. in den Entwuerfen. Eine Bcc-Kopie an sich selbst gibt es nur noch als
Fallback ohne IMAP-Konto (siehe unten): ob die Mail raus ist, belegt die Queue-ID,
ob sie abgelegt ist, das Zuruecklesen nach der Ablage. Ein Bcc an Dritte,
das der Nutzer im Auftrag nennt, geht weiterhin mit.

Welche Kopie der versendeten Mail entsteht, entscheidet das Profil in dieser
Reihenfolge:

1. **`send.account` gesetzt:** `--file-sent <send.account>`. Steht daneben noch
   `send.bcc` im Profil, wird es nicht verwendet: einmal darauf hinweisen und
   anbieten, den Eintrag zu entfernen. Mitgeschickt landete die Kopie zusaetzlich
   zur Ablage in "Gesendet".
2. **Kein `send.account`, aber `send.bcc`:** Bcc an die Adresse aus `send.bcc`, an
   **beide** Aufrufe (Bau und `--send`), ohne Rueckfrage. Das ist der Weg auf
   Rechnern ohne eingerichtete IMAP-Konten (`imap accounts` leer).
3. **Weder noch:** nicht raten. Liefert `imap accounts` Konten, sie zur Auswahl
   zeigen und die Antwort als `send.account` ins Profil schreiben, damit die Frage
   nur einmal kommt. Ist die Liste leer, nach einer Adresse fuer `send.bcc` fragen.

Fehlt `draft.account`, gilt Schritt 3 sinngemaess; ohne IMAP-Konto gibt es keine
Entwurfsablage.

**Regel:** Wird ein Entwurf aus `write`/`rewrite` versendet, wird `send` aus dem
geladenen Profil gelesen und angewendet — ohne Rueckfrage, wie die Signatur. Eine
Angabe des Nutzers im Auftrag ("schick das von X") hat Vorrang.

Umsetzung: `from` geht an **beide** Aufrufe -- den Bau und den Versand. Gebaut und
geprueft wird in einem Befehl, gesendet und abgelegt im naechsten:

```bash
M=$(mktemp -d .tmp/mail.XXXXXX)
B=~/.claude/skills/swaks/build_mail.py

python3 $B \
  --subject "Betreff" \
  --to "empfaenger@example.com" \
  --from ich@example.org \
  --text-file $M/body.txt \
  --html-file $M/body.html \
  --sha-file $M/mail.sha256 \
  > $M/mail.eml \
  && test -s $M/mail.eml \
  && python3 $B --verify $M/mail.eml \
      --expect-sha256 "$(cat $M/mail.sha256)" \
      --expect-marker "<woertliches Stueck aus dem freigegebenen Entwurf>"
```

```bash
python3 $B --send $M/mail.eml \
  --to "empfaenger@example.com" \
  --from ich@example.org \
  --file-sent <send.account>
```

`--file-sent` legt die versendete Datei nach erfolgreichem Versand in "Gesendet"
und liest sie per Message-ID zurueck. Exit `0` heisst gesendet **und** abgelegt,
`1` nicht gesendet (und nichts abgelegt), `3` gesendet, aber nicht abgelegt. Bei
`3` dem Nutzer genau das sagen und den Befehl aus dem Feld `retry` nennen;
`$M/mail.eml` bleibt dafuer liegen. Details im swaks-Skill, Abschnitt „Ablage".

Ohne `send.account` (Fallback `send.bcc`, siehe oben) statt `--file-sent` an
beide Aufrufe `--bcc <send.bcc>` haengen; Exit `3` gibt es dann nicht.

**Kein fester Pfad wie `.tmp/mail.eml`, und die `--verify`-Zeile gehoert dazu.**
Eine parallel laufende Session schreibt sonst dieselbe Datei, und der Versand
nimmt, was zuletzt drinstand -- mit korrektem Betreff, korrektem Empfaenger und
dem Text einer fremden Mail. Beim Versand faellt das nicht auf: swaks quittiert
die uebertragenen Bytes, nicht die gebauten. Der Marker ist ein woertliches
Stueck aus dem freigegebenen Entwurf; `--verify` dekodiert den Text-Part und
sucht es dort (ein `grep` auf die rohe `.eml` findet es nicht, der Body ist
quoted-printable kodiert). Details im swaks-Skill, Abschnitt "Vor dem Versand
pruefen".

**Kontakt ergaenzen (swaks Schritt 11).** Stand die Adresse nicht in
`.claude/swaks-contacts.tsv` (bzw. `~/.claude/`), wird sie nach dem Versand dort angehaengt -- sonst
ist die naechste Mail an dieselbe Person wieder ein Ratespiel. Nur fuer Adressen,
die ohne Thread wieder gebraucht werden; Thread-Adressen liefert `imap contacts`
jederzeit neu. Details im swaks-Skill.

**Nur Text und kein HTML-Entwurf?** Dann `--html-file` weglassen, nicht die
Textdatei ein zweites Mal angeben. Ein HTML-Part aus rohem Text hat kein
einziges Tag und kommt beim Empfaenger in einer einzigen Zeile an -- Aufzaehlung,
Tabelle und Zugangsdaten inklusive.

Die Signatur bleibt beim eigenen Absender aus `send.from` dran (die globale
Signatur ist die eigene, siehe swaks-Skill) — der Wechsel des Absenders ist **kein**
Ausschlussgrund.

### Als Entwurf ablegen (`draft`)

Gebaut wird wie oben, mit zwei Unterschieden: `--for-draft` beim Bau und statt
`--send` die Ablage in die Entwuerfe. Eine Bcc-Kopie an sich selbst entfaellt
auch hier. Ein Bcc an Dritte steht im Entwurf als Header, sonst kennt der
Mailclient es beim Senden nicht; `--send` verweigert eine solche `.eml` deshalb.

```bash
python3 $B --for-draft --subject "Betreff" --to "empfaenger@example.com" \
  --from ich@example.org --text-file $M/body.txt --html-file $M/body.html \
  --sha-file $M/mail.sha256 > $M/mail.eml \
  && test -s $M/mail.eml \
  && python3 $B --verify $M/mail.eml --expect-sha256 "$(cat $M/mail.sha256)" \
      --expect-marker "<woertliches Stueck aus dem freigegebenen Entwurf>"
```

```bash
python3 $B --draft $M/mail.eml --account <draft.account>
```

Abgelegt wird mit `\Draft` und ungelesen, danach per Message-ID zurueckgelesen;
Exit `0` heisst: liegt in den Entwuerfen, das JSON nennt Ordner und UID. Bei einer
Antwort gehoeren Zitat und Threading-Header genauso dazu wie beim Versand. Der
Kontakt wird erst ergaenzt, wenn der Nutzer den Entwurf abgeschickt hat -- das
sieht dieser Skill nicht, deshalb entfaellt der Schritt hier.

## Antworten: Zitat und Threading

Bei einer Antwort kommen fuenf Dinge nicht aus dem Entwurf, sondern aus `imap quote`:
der **Text-Quote**, der **HTML-Quote**, die beiden **Threading-Header**, der **Betreff**
und die **Empfaenger**. Was das Modell selbst tippt, weicht bei jeder Mail leicht ab.
Antwort oben, Zitat unten; der Entwurf selbst enthaelt **kein** Zitat, das haengt
`build_mail.py` an.

Den vollstaendigen Ablauf mit allen Befehlen, die Regeln fuer Betreff und
Reply-All und den Sonderfall einer Antwort auf eine `.eml` enthaelt
[references/antworten.md](references/antworten.md). **Vor jeder Antwort lesen.**

## Anti-Patterns / KI-Tells → humanizer-de

Die sprachlichen Anti-Patterns (Gedankenstrich, Nominalkomposita, elliptische
Antithese, erfundene Zusagen, Anfuehrungszeichen um Paraphrasen, Absolutheit ohne
Hedge, Bestaetigungsfloskeln) sind personenunabhaengig und werden **nicht** hier
dupliziert, sondern ueber einen **Aufruf** des **humanizer-de**-Skills geprueft, nicht
aus dem Gedaechtnis. `referenz.md` fuehrt sie nur als Checkliste mit dem persoenlichen
Bezug; diese Checkliste ist die **Ergaenzung** zum Skill-Lauf, nicht sein Ersatz.

## Integration

- **humanizer-de** - verbindlicher KI-Tell-Audit in Schritt 6 von `write`/`draft`/`rewrite`,
  kein optionaler Self-Check; Ergebnis gehoert in die Ausfuehrungszeile.
- **imap** - `quote` erzeugt bei jeder Antwort den Zitatblock und die
  Threading-Header (Schritt 7) und liefert Betreff und Empfaenger gleich mit.
  Ebenfalls ein Aufruf, kein Nachbauen; Ergebnis gehoert als letztes Feld in die
  Ausfuehrungszeile. Ist statt der UID nur die Message-ID bekannt (einkopierte
  Mail), loest `imap quote -m` bzw. `imap find -m` sie zu Konto, Ordner und UID
  auf -- der Handabgleich ueber `folders` + `list` entfaellt. Die Ablage in
  "Gesendet" bzw. den Entwuerfen ruft swaks selbst auf (`--file-sent`, `--draft`).
- **swaks** — Versand (`mail-as-me` schreibt, `swaks` sendet; Signatur kommt aus
  swaks, Absender und Ablagekonto aus `config.json.send` des Profils). Dessen Schritt 1
  (Empfaenger aufloesen) und Schritt 11 (Kontakt ergaenzen) gelten mit -- sie sind
  hier als Schritt 1 von `write` und als Absatz im Versand-Abschnitt abgebildet,
  weil die swaks-Schrittliste beim Weg ueber `mail-as-me` nie zu sehen ist.
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
