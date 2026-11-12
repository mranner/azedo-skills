---
name: sally
description: >
  Sally AI: Meeting-Aufnahmen auflisten, Zusammenfassung und Transkript holen,
  Zusammenfassungen durchsuchen, Review nach einem Call, Aufnahme nach BookStack
  archivieren. Trigger: /sally.
disable-model-invocation: true
argument-hint: "review <aufnahme>, archive <aufnahme>, Frage zu einem Meeting, Aufnahme-Name oder Suchbegriff (optional)"
---

# sally -- Meeting-Aufnahmen aus Sally AI

Alles läuft über das gebündelte Script `sally` (Python >= 3.11, stdlib) gegen
die Sally Public API v1.0. In Sally **liest** der Skill nur: Aufgaben, Tags, Ordner,
Upload und Webhooks sind nicht eingebaut. Geschrieben wird nur mit `archive`, und
zwar nach BookStack.

**Aufruf:** `python3 "$SKILL_DIR/sally" <subcommand> [options]`

`$SKILL_DIR` ist das Base Directory dieses Skills (dort wo diese SKILL.md liegt).

## Konfiguration

`~/.claude/sally.json` (Vorlage `sally.json.example`, Modus 600), anderer Pfad
per `SALLY_CONFIG`:

- `token` - Personal Access Token (Präfix `sally_user_api_`), in der Sally-App
  unter Integrationen erzeugt. Er handelt als dieser Nutzer und sieht genau
  dessen Aufnahmen.
- `directory-id` - das Sally-Firmenkonto; `sally directories` listet die
  Kandidaten, `sally me` prüft den Zugang.
- `archive.books` (optional) - Kunde → Buchname, wo das Buch in BookStack
  anders heißt als der Kunde in Kimai.

Fehlt die Datei oder ein Schlüssel, bricht das Script mit Meldung ab.

## Subcommands

| Aufruf | liefert |
|---|---|
| `recordings [--since D] [--until D] [--limit N]` | Zeit, Dauer, Transkript-Status, ID, Name; neueste zuerst |
| `summary <aufnahme> [--lang de] [--format md\|txt\|pdf\|docx\|odt]` | Zusammenfassung als Dokument, Default Markdown auf stdout |
| `transcript <aufnahme> [--lang de] [--format md\|txt\|pdf\|docx\|xlsx\|vtt\|srt]` | Transkript als Dokument |
| `download <aufnahme> [--to DIR] [--json]` | Zusammenfassung und Transkript (md) als Dateien, Default `./.tmp/` (Modus 700, Dateien 600; warnt, wenn ein bestehendes Verzeichnis offener ist) |
| `search "<text>" [--limit N]` | Treffer in Zusammenfassungen mit Ausschnitt |
| `archive <aufnahme> --kunde <name> [--projekt <name> …] [--titel <text>] [--summary-file f --transcript-file f]` | zwei Seiten in BookStack, gibt beide Links aus |

- `<aufnahme>` ist die ID oder ein eindeutiger Teil des Namens; bei mehreren
  Treffern listet das Script sie auf.
- Datumsangaben sind **lokale** Zeit (`YYYY-MM-DD` oder `YYYY-MM-DDTHH:MM`),
  das Script rechnet nach UTC um und gibt Zeiten lokal aus.
- Eine Zusammenfassung gibt es **je Sprache**. Hat eine Aufnahme mehrere,
  verlangt das Script `--lang`.
- Binärformate (`pdf`, `docx`, `odt`, `xlsx`) nur mit `--out <datei>`.
- `--json` liefert bei `summary` die Abschnitte strukturiert
  (`sectionItems`), bei `transcript` die Segmente mit Sprechern und Zeiten.

## Regeln

- **Eng abfragen.** Meetings enthalten Personenbezogenes und Vertrauliches:
  nur die Aufnahme holen, um die es geht, und nur so viel ausgeben, wie die
  Frage braucht. Downloads landen in `.tmp/` und werden nach dem Task gelöscht.
- **Fragen zu einem Meeting** zuerst über die Zusammenfassung beantworten, das
  Transkript nur holen, wenn sie nicht reicht oder der Wortlaut gefragt ist.
  Ausnahme Review: dort Zusammenfassung und Transkript von Anfang an zusammen.
- **Die API ist Version 1.0 "in development".** Unbekannte Felder und neue
  Enum-Werte sind normal; wirft ein Aufruf einen Validierungsfehler (400) an
  einer Stelle, die laut `--help` stimmt, die Spezifikation unter
  `https://api.sally.io/docs-json` gegenprüfen.
- Ein Transkript-Status ungleich `fertig` (`laeuft`, `noSpokenAudio` …) heißt:
  `transcript` liefert 409, die Zusammenfassung fehlt meist ebenfalls.

## Review nach einem Call

Bei `/sally review <aufnahme>` oder "lass uns den Call durchgehen":
[references/review.md](references/review.md) lesen und Schritt für Schritt
abarbeiten.

## Archiv nach BookStack

Bei `/sally archive <aufnahme>` und in Schritt 9 der Review. `archive` legt im
Kapitel „Besprechungen“ des Kunden-Buchs zwei Seiten an: „JJJJ-MM-TT Titel“
(Datum, Dauer, Link aufs Transkript, Zusammenfassung) und direkt darunter
„… - Transkript“, nur für die Admin-Rolle sichtbar; beide mit den Tags `kunde`,
`datum`, `typ`, `sally-id` und je Projekt `projekt`. Danach sortiert es das
Kapitel nach dem Datum im Seitennamen, die jüngste Besprechung oben.
Es braucht den Skill `bookstack` mit seiner Config.

- **Titel aus den Hauptthemen:** zwei bis vier Hauptthemen der Besprechung als
  Titel vorschlagen, nach Bestätigung per `--titel` übergeben. Er ersetzt im
  Seitennamen und in der Überschrift `# Aufzeichnung: …` den Namen aus Sally.
  Der Titel nennt Themen, keine Personen - den Kunden trägt schon das Buch.
  Beispiel: „Serverumzug, Backup und Druckerfreigabe“.
- `--kunde` und `--projekt` tragen die Namen **wie in Kimai** (`list-customers`,
  `list-projects` im Skill kimai). Betrifft der Call mehrere Projekte, `--projekt`
  je Projekt; ist das Projekt offen, nachfragen statt raten.
- **Mit Glossar archivieren:** die Ersetzungen in den Dateien aus `download`
  vornehmen und sie per `--summary-file`/`--transcript-file` übergeben; ohne die
  Optionen archiviert `archive` den Text frisch aus Sally.
- **Fehlt das Buch des Kunden**, bricht `archive` ab. Ob es angelegt wird,
  entscheidet der User; angelegt wird es dann mit `/bookstack`, mit dem Kapitel
  „Besprechungen“.
- **Schon archiviert** (Seite mit derselben `sally-id`): `archive` bricht mit den
  Links ab - die vorhandenen Seiten melden.

## Glossar (`~/.claude/sally-glossar.md`)

Die Transkription verhört wiederkehrende Eigennamen (Kunden, Produkte, Systeme),
und die Fehler stehen dann auch in der Zusammenfassung. Das Glossar ordnet jeder
bekannten Fehlerkennung den gemeinten Namen zu. Es liegt außerhalb des Repos,
weil es Kundennamen enthält; Vorlage `sally-glossar.md.example`.

- **Vor dem Auswerten** von Zusammenfassung oder Transkript das Glossar lesen,
  falls vorhanden, und die Fehlerkennungen in der Ausgabe durch den gemeinten
  Namen ersetzen. Fehlt die Datei, gilt der Text unverändert.
- Ein Eintrag mit `nur bei` gilt nur, wenn der Call zu diesem Kunden oder
  Kontext gehört. So bleibt ein echter Vorname stehen, der sonst als
  verhörter Kundenname ersetzt würde.
- Ein Name, der im Kontext erkennbar falsch ist, aber nicht im Glossar steht:
  nicht stillschweigend korrigieren, sondern als Vermutung kennzeichnen und die
  Aufnahme ins Glossar vorschlagen.
- **Vor dem Eintragen** den Tabellenkopf gegen die Vorlage prüfen und fehlende
  Spalten ergänzen: eine ältere Datei kann hinter der Vorlage zurückliegen,
  ein `nur bei`-Eintrag hätte dann keine Spalte.
- **Sprecherzuordnung ist unzuverlässig.** Eine Person kann auf mehrere
  `Speaker` verteilt sein, zwei Personen auf einen. Aussagen nur dann einer
  Person zuschreiben, wenn der Inhalt es trägt (Anrede, Rolle, Bezug), sonst
  beim Sprecher-Label bleiben.
