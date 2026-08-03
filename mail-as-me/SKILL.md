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
Tanja," — **nie** eine gespiegelte CH/DE-Grussformel wie „Hoi", „Grüezi",
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
3. Entwurf bauen: Anrede/Sign-off/Du-Sie/Dialekt gemaess Profil, Stilmarker
   anwenden. **Immer in der eigenen Stimme des Profils — das Gegenueber niemals
   spiegeln** (weder Sprache, Stil, Register, Region/Dialekt, Anrede noch
   Grussformel; bei einer Reply-`.eml` nicht Ton/Region des Absenders uebernehmen).
   Die Sprache nur wechseln, wenn der Nutzer es **explizit** vorgibt.
4. **Pflicht-Audit via humanizer-de.** Den Skill `humanizer-de` **tatsaechlich
   aufrufen** (Skill-Tool bzw. `/humanizer-de`), Modus **Sachlich**, Zweig **Nur
   Audit**. Ein manueller Abgleich gegen die Anti-Pattern-Liste in `referenz.md`
   ersetzt den Lauf **nicht** und zaehlt nicht als erledigter Schritt 4. Der Lauf
   entfaellt auch bei kurzen Mails, Routinemeldungen oder Zeitdruck nicht.
   Anschliessend die profilspezifischen Anti-Patterns aus `referenz.md` zusaetzlich
   inhaltlich durchgehen: die Linter finden diese Klasse nicht (Zeitkolorit im
   Einstieg, Abstraktum statt konkretem Sachverhalt, Nebenbefunde ohne
   Handlungsrelevanz, doppeltes Hedging, "Rueckfall" fuer Software).
   Beides ist noetig, keines ersetzt das andere.
5. Entwurf zeigen, **immer mit der Ausfuehrungszeile** (siehe unten). Optional
   Versand ueber **swaks** (Text + HTML), Signatur dort; Absender und Bcc kommen
   aus `config.json.send` (siehe Abschnitt Versand).

### rewrite — bestehenden Entwurf in-voice bringen

Nimmt einen Entwurf (eigener oder fremder), gleicht ihn an das Profil an und laeuft
denselben **verbindlichen** humanizer-de-Audit aus Schritt 4 von `draft`, inklusive
Ausfuehrungszeile beim Zeigen. Fuer „mach diese Mail wie ich". Gilt auch hier: **das
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
Schritte: Profil michael · Register sachlich (example.ch) · Beispiele 76421, 76512 · humanizer-de Sachlich/Nur-Audit: Preflight low, keine HIGH-Cluster
```

Vier Felder, immer in dieser Reihenfolge:

| Feld | Inhalt |
|---|---|
| Profil | Name des geladenen Profils |
| Register | bestimmtes Register + Herkunft (Domain aus `register_map`, sonst „nachgefragt") |
| Beispiele | IDs/Dateinamen der geladenen Beispiele aus `corpus/clean/` |
| humanizer-de | Modus/Zweig + Ergebnis in Kurzform (Preflight-Stufe, Cluster-Befund) |

Ist ein Schritt nicht gelaufen, wird das **ausgeschrieben** (`humanizer-de: nicht
gelaufen`), statt das Feld wegzulassen. Ein fehlendes Feld ist genau der Fall, der
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
python3 ~/.claude/skills/swaks/build_mail.py \
  --subject "Betreff" \
  --to "empfaenger@example.com" \
  --from ich@example.org \
  --bcc ich@example.org \
  --text-file .tmp/body.txt \
  --html-file .tmp/body.html \
  > .tmp/mail.eml \
  && test -s .tmp/mail.eml \
  && swaks --server mom.azedo.at \
      --to "empfaenger@example.com,ich@example.org" \
      --from ich@example.org \
      --data @.tmp/mail.eml
```

`--bcc` an `build_mail.py` setzt bewusst **keinen** Header; zugestellt wird die Kopie
allein ueber den Envelope-`--to` von swaks. Fehlt sie dort, kommt trotz `--bcc` nichts
an. Die Signatur bleibt beim eigenen Absender aus `send.from` dran (die globale
Signatur ist die eigene, siehe swaks-Skill) — der Wechsel des Absenders ist **kein**
Ausschlussgrund.

## Anti-Patterns / KI-Tells → humanizer-de

Die sprachlichen Anti-Patterns (Gedankenstrich, Nominalkomposita, elliptische
Antithese, erfundene Zusagen, Anfuehrungszeichen um Paraphrasen, Absolutheit ohne
Hedge, Bestaetigungsfloskeln) sind personenunabhaengig und werden **nicht** hier
dupliziert, sondern ueber einen **Aufruf** des **humanizer-de**-Skills geprueft, nicht
aus dem Gedaechtnis. `referenz.md` fuehrt sie nur als Checkliste mit dem persoenlichen
Bezug; diese Checkliste ist die **Ergaenzung** zum Skill-Lauf, nicht sein Ersatz.

## Integration

- **humanizer-de** - verbindlicher KI-Tell-Audit in Schritt 4 von `draft`/`rewrite`,
  kein optionaler Self-Check; Ergebnis gehoert in die Ausfuehrungszeile.
- **swaks** — Versand (`mail-as-me` schreibt, `swaks` sendet; Signatur kommt aus
  swaks, Absender und Bcc aus `config.json.send` des Profils).
- **kanboard/handoff** — optional CR-Kontext fuer den `learn`-Loop.

## Hinweise

- Profil-Daten liegen **ausserhalb** des Skills (`~/.claude/mail-as-me/`), damit der
  versionierte Skill und die persoenlichen Daten getrennt bleiben.
- Temporaere Dateien ins Projekt-`.tmp/`, nie ins Skill-Verzeichnis.
- Der Auto-Register-/Dialekt-Vorschlag ist bewusst nur ein Vorschlag — im Zweifel
  im Interview bestaetigen lassen (der Auto-Detect kann daneben liegen).
