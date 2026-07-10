---
name: handoff
description: Fasst die aktuelle Konversation in ein Übergabedokument zusammen, damit ein neuer Agent nahtlos weiterarbeiten kann. Trigger: /handoff.
argument-hint: "Fokus/Slug der nächsten Session (optional)"
---

Erstelle ein Übergabedokument auf Deutsch, das die aktuelle Konversation zusammenfasst, damit ein neuer Agent die Arbeit fortsetzen kann. Speichere es im Projektverzeichnis — falls ein `docs/`-Verzeichnis existiert, dort ablegen, sonst im Projektstamm.

Füge einen Abschnitt „Empfohlene Skills" hinzu, der Skills vorschlägt, die der nächste Agent verwenden sollte.

Dupliziere keine Inhalte, die bereits in anderen Artefakten erfasst sind (PRDs, Pläne, ADRs, Issues, Commits, Diffs). Verweise stattdessen per Pfad oder URL darauf.

Entferne sensible Informationen wie API-Keys, Passwörter oder personenbezogene Daten.

## Aktiver CR-Kontext (Kanboard)

Wenn in der Session ein oder mehrere Kanboard-Tasks als CR-Kontext aktiv sind (geladen via `/kanboard cr <id>` oder weil der User „ich arbeite an CR…" gesagt hat), lege im Handoff einen eigenen, klar markierten Abschnitt „Aktiver CR-Kontext" an. Führe je aktivem CR auf: **CR-ID, Titel, Task-URL und aktuelle Spalte/Status** — aus dem in der Session bekannten Stand, keine Live-Abfrage nötig. Vermerke, dass der nächste Agent den Kontext mit `/kanboard cr <id>` wiederherstellen kann, und nimm `kanboard` in die „Empfohlene Skills" auf.

Ist kein CR aktiv, entfällt der Abschnitt.

## Dateiname und Argument

Das übergebene Argument bestimmt **sowohl den Fokus** der nächsten Session **als auch den Dateinamen** — so entsteht pro Thema ein eigenes Dokument, und ein bestehendes Handoff wird nicht überschrieben:

- **Kein Argument** → Dateiname `handoff.md`.
- **Argument ohne `.md`-Endung** → dient als Fokusbeschreibung **und** als Slug für den Dateinamen: `handoff-<slug>.md`. Den Slug aus dem Argument ableiten (Kleinschreibung, Leerzeichen und Sonderzeichen zu `-`, Mehrfach-`-` zusammenfassen, führende/abschließende `-` entfernen). Beispiele: `/handoff myacme-appicon` → `docs/handoff-myacme-appicon.md`; `/handoff "Mail-Migration widgetco"` → `docs/handoff-mail-migration-widgetco.md`.
- **Argument mit `.md`-Endung** → wird unverändert als expliziter Dateiname verwendet (z. B. `/handoff uebergabe.md` → `docs/uebergabe.md`).

In allen Fällen entscheidet die Verzeichnisregel oben (`docs/` falls vorhanden, sonst Projektstamm) über den Ablageort.

## Ablage im Kanboard-Handoff-Feld (optional, auf Zuruf)

**Default bleibt die lokale `.md`-Datei** (siehe oben). Kein Automatismus.

Verlangt der Benutzer die Ablage **im Kanboard** ausdrücklich (z. B. „leg den Handoff ins Kanboard-Feld von CR4372"), wird der volle Handoff-Text stattdessen in das **Handoff-Feld des Tasks** geschrieben — eine eigene aufklappbare „Handoff"-Sektion auf der Task-Seite (TaskHandoff-Plugin). Das ist eine **Alternative** zur Datei, kein zusätzlicher Anhang:

```bash
python3 ~/.claude/skills/kanboard/kanboard set-handoff <task_id> --file <handoff.md>
# oder direkt:
python3 ~/.claude/skills/kanboard/kanboard set-handoff <task_id> --value "<volltext>"
```

Wird die Kanboard-Ablage gewählt, ist **keine** lokale `.md`-Datei und **kein** Anhang nötig (entweder-oder). Die `task_id` ergibt sich aus dem aktiven CR-Kontext (siehe „Aktiver CR-Kontext"). Details zu den Subcommands: kanboard-Skill, Abschnitt „Handoff-Feld (TaskHandoff-Plugin)".

**Fallback (Plugin nicht installiert):** Schlägt `set-handoff` mit `API error … "Method not found"` (Code `-32601`) fehl, ist das **TaskHandoff-Plugin** auf dieser Kanboard-Instanz nicht installiert/aktiviert. Dann auf die **lokale `.md`-Datei** zurückfallen (Default-Verhalten) und den User kurz darüber informieren — nichts geht verloren, der Handoff wird einfach als Datei abgelegt.

## Einlesen eines bestehenden Handoff-Dokuments

Wenn ein Handoff-Dokument (`handoff.md` oder `handoff-<slug>.md`) bereits existiert und du es einliest (z. B. zu Beginn einer neuen Session), gehe wie folgt vor:

1. **Rekapituliere** den Inhalt in einer kurzen Zusammenfassung (max. 5–8 Sätze): Was wurde erarbeitet, was ist der aktuelle Stand, welche nächsten Schritte sind vorgeschlagen.
2. **Frage den Benutzer**, bevor du irgendwelche Aktionen ausführst: „Soll ich mit den vorgeschlagenen nächsten Schritten fortfahren, oder möchtest du etwas anpassen?"
3. **Beginne NIEMALS** eigenständig mit Code-Änderungen, Dateierstellungen oder anderen Aktionen, bevor der Benutzer explizit zugestimmt hat.

Liegt der Handoff **im Kanboard-Feld** statt als Datei (siehe oben), lies ihn mit `python3 ~/.claude/skills/kanboard/kanboard get-handoff <task_id>` aus und verfahre dann genauso.

## Herkunft & Lizenz

Vendorisierter, angepasster Fork von [`mattpocock/skills`](https://github.com/mattpocock/skills/tree/main/skills/productivity/handoff) (Skill-Pfad `skills/productivity/handoff`), Stand Commit `386d4ff719a7c420ad1454232d0436b01f1b8c17`. Lizenz: MIT © 2026 Matt Pocock (siehe `LICENSE`).

azedo-Anpassungen gegenüber dem Upstream:

- Vollständige Übersetzung ins Deutsche
- Ablage im **Projektverzeichnis** (`docs/` bzw. Projektstamm) statt im OS-Temp-Verzeichnis
- Dateinamens-Konvention: Argument dient als Fokus **und** Slug (`handoff-<slug>.md`), damit pro Thema ein eigenes Dokument entsteht und nichts überschrieben wird
- Abschnitt „Einlesen eines bestehenden Handoff-Dokuments" (Rekapitulieren, Rückfragen, nie eigenständig handeln) ergänzt
- Abschnitt „Ablage im Kanboard-Handoff-Feld" (optionale Alternative zur Datei, auf Zuruf, via TaskHandoff-Plugin + kanboard-Skill) ergänzt
- Frontmatter-Feld `disable-model-invocation: true` entfernt; `Trigger: /handoff.` in der `description` ergänzt

Updates aus dem Upstream werden bei Bedarf **manuell** abgeglichen (kein Auto-Sync).
