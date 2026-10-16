---
name: sally
description: >
  Sally AI (Meeting-Aufnahmen): Aufnahmen auflisten, Zusammenfassung und
  Transkript einer Aufnahme holen oder ablegen, Zusammenfassungen
  durchsuchen - nur lesend über die Sally-API. Nutze diesen Skill, wenn der
  User nach einem aufgezeichneten Meeting fragt. Auch bei "welche Aufnahmen
  gibt es in Sally", "hol die Zusammenfassung vom Meeting", "ich brauch das
  Transkript", "in welchem Meeting ging es um X".
  Trigger: /sally.
---

# sally -- Meeting-Aufnahmen aus Sally AI

Alles läuft über das gebündelte Script `sally` (Python >= 3.11, stdlib) gegen
die Sally Public API v1.0. Der Skill **liest nur**: Aufgaben, Tags, Ordner,
Upload und Webhooks sind nicht eingebaut.

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

Fehlt die Datei oder ein Schlüssel, bricht das Script mit Meldung ab.

## Subcommands

| Aufruf | liefert |
|---|---|
| `recordings [--since D] [--until D] [--limit N]` | Zeit, Dauer, Transkript-Status, ID, Name; neueste zuerst |
| `summary <aufnahme> [--lang de] [--format md\|txt\|pdf\|docx\|odt]` | Zusammenfassung als Dokument, Default Markdown auf stdout |
| `transcript <aufnahme> [--lang de] [--format md\|txt\|pdf\|docx\|xlsx\|vtt\|srt]` | Transkript als Dokument |
| `download <aufnahme> [--to DIR] [--json]` | Zusammenfassung und Transkript (md) als Dateien, Default `./.tmp/` (Modus 700) |
| `search "<text>" [--limit N]` | Treffer in Zusammenfassungen mit Ausschnitt |

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
- **Die API ist Version 1.0 "in development".** Unbekannte Felder und neue
  Enum-Werte sind normal; wirft ein Aufruf einen Validierungsfehler (400) an
  einer Stelle, die laut `--help` stimmt, die Spezifikation unter
  `https://api.sally.io/docs-json` gegenprüfen.
- Ein Transkript-Status ungleich `fertig` (`laeuft`, `noSpokenAudio` …) heißt:
  `transcript` liefert 409, die Zusammenfassung fehlt meist ebenfalls.
