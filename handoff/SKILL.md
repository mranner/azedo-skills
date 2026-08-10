---
name: handoff
description: Fasst die aktuelle Konversation in ein Übergabedokument zusammen, damit ein neuer Agent nahtlos weiterarbeiten kann. Trigger: /handoff.
argument-hint: "Fokus/Slug der nächsten Session (optional)"
---

Erstelle ein Übergabedokument auf Deutsch, das die aktuelle Konversation zusammenfasst, damit ein neuer Agent die Arbeit fortsetzen kann. Wohin es gehört, entscheidet der Abschnitt „Ablageort bestimmen" — je nach Lage der Task, ein bestehendes Dokument oder eine neue Datei im Projektverzeichnis.

Füge einen Abschnitt „Empfohlene Skills" hinzu, der Skills vorschlägt, die der nächste Agent verwenden sollte.

Dupliziere keine Inhalte, die bereits in anderen Artefakten erfasst sind (PRDs, Pläne, ADRs, Issues, Commits, Diffs). Verweise stattdessen per Pfad oder URL darauf.

Entferne sensible Informationen wie API-Keys, Passwörter oder personenbezogene Daten.

## Aktiver CR-Kontext (Kanboard)

Wenn in der Session ein oder mehrere Kanboard-Tasks als CR-Kontext aktiv sind (geladen via `/kanboard cr <id>` oder weil der User „ich arbeite an CR…" gesagt hat), lege im Handoff einen eigenen, klar markierten Abschnitt „Aktiver CR-Kontext" an. Führe je aktivem CR auf: **CR-ID, Titel, Task-URL und aktuelle Spalte/Status** — aus dem in der Session bekannten Stand, keine Live-Abfrage nötig. Vermerke, dass der nächste Agent den Kontext mit `/kanboard cr <id>` wiederherstellen kann, und nimm `kanboard` in die „Empfohlene Skills" auf.

Ist kein CR aktiv, entfällt der Abschnitt.

## Dateiname und Argument

Gilt für die lokale Ablage (Fälle 2 und 3 unter „Ablageort bestimmen"). Landet der Handoff im Handoff-Feld eines Tasks, dient das Argument nur als Fokusbeschreibung — einen Dateinamen braucht es dort nicht.

Das übergebene Argument bestimmt **sowohl den Fokus** der nächsten Session **als auch den Dateinamen** — so entsteht pro Thema ein eigenes Dokument, und ein bestehendes Handoff wird nicht überschrieben:

- **Kein Argument** → Dateiname `handoff.md`.
- **Argument ohne `.md`-Endung** → dient als Fokusbeschreibung **und** als Slug für den Dateinamen: `handoff-<slug>.md`. Den Slug aus dem Argument ableiten (Kleinschreibung, Leerzeichen und Sonderzeichen zu `-`, Mehrfach-`-` zusammenfassen, führende/abschließende `-` entfernen). Beispiele: `/handoff myacme-appicon` → `docs/handoff-myacme-appicon.md`; `/handoff "Mail-Migration widgetco"` → `docs/handoff-mail-migration-widgetco.md`.
- **Argument mit `.md`-Endung** → wird unverändert als expliziter Dateiname verwendet (z. B. `/handoff uebergabe.md` → `docs/uebergabe.md`).

Verzeichnis in allen drei Fällen: `docs/`, falls vorhanden, sonst der Projektstamm.

## Ablageort bestimmen

Ein Handoff gehört dorthin, wo ihn der nächste Bearbeiter sucht. Das ist **nicht immer** die lokale Datei: Gibt es einen klar umrissenen Task zur Session, ist der Task der Ort — dort steht die Aufgabe, dort schaut der nächste Agent zuerst hin, und eine Datei daneben wäre eine zweite Fassung, die auseinanderdriftet.

Die drei Fälle in dieser Reihenfolge prüfen, der erste passende gewinnt:

**1. Aktiver CR-Kontext → Handoff-Feld des Tasks.** Ist ein Kanboard-Task als CR-Kontext aktiv (siehe „Aktiver CR-Kontext"), geht der volle Handoff-Text in dessen **Handoff-Feld** — ohne Rückfrage, das ist der Normalfall. Es entsteht **keine** lokale `.md`-Datei und **kein** Anhang.

```bash
python3 ~/.claude/skills/kanboard/kanboard set-handoff <task_id> --file <handoff.md>
# oder direkt:
python3 ~/.claude/skills/kanboard/kanboard set-handoff <task_id> --value "<volltext>"
```

Die `task_id` ist die CR-ID. Details zu den Subcommands: kanboard-Skill, Abschnitt „Handoff-Feld (TaskHandoff-Plugin)".

Sind **mehrere** CRs aktiv, ist nicht entscheidbar, welcher Task der richtige ist → den Benutzer fragen, statt zu raten oder in alle zu schreiben.

Liegt bei aktivem CR zusätzlich schon ein thematisch passendes Handoff-Dokument im Projekt, gilt trotzdem dieser Fall — den Benutzer aber auf die Datei hinweisen, damit nicht unbemerkt zwei Fassungen nebeneinander bestehen.

**2. Kein CR, aber ein passendes Dokument existiert → dieses fortschreiben.** Liegt unter `docs/` bzw. im Projektstamm bereits ein thematisch passendes Handoff-Dokument, wird **dieses** aktualisiert statt ein zweites danebenzulegen. Kein neuer Dateiname, keine Rückfrage.

**3. Weder noch → neue lokale Datei** nach der Namenskonvention unten.

**Ausdrückliche Ansage schlägt die Regel.** Sagt der Benutzer, wohin der Handoff soll („leg ihn als Datei ab", „ins Feld von Task 4372"), gilt das — auch gegen die Reihenfolge oben.

**Fallback (Plugin nicht installiert):** Schlägt `set-handoff` mit `API error … "Method not found"` (Code `-32601`) fehl, ist das **TaskHandoff-Plugin** auf dieser Kanboard-Instanz nicht installiert/aktiviert. Dann auf die **lokale `.md`-Datei** zurückfallen (Fall 3) und den Benutzer kurz darüber informieren — nichts geht verloren, der Handoff wird einfach als Datei abgelegt.

## Einlesen eines bestehenden Handoff-Dokuments

Wenn ein Handoff-Dokument (`handoff.md` oder `handoff-<slug>.md`) bereits existiert und du es einliest (z. B. zu Beginn einer neuen Session), gehe wie folgt vor:

1. **Rekapituliere** den Inhalt in einer kurzen Zusammenfassung (max. 5–8 Sätze): Was wurde erarbeitet, was ist der aktuelle Stand, welche nächsten Schritte sind vorgeschlagen.
2. **Frage den Benutzer**, bevor du irgendwelche Aktionen ausführst: „Soll ich mit den vorgeschlagenen nächsten Schritten fortfahren, oder möchtest du etwas anpassen?"
3. **Beginne NIEMALS** eigenständig mit Code-Änderungen, Dateierstellungen oder anderen Aktionen, bevor der Benutzer explizit zugestimmt hat.

Liegt der Handoff **im Handoff-Feld eines Tasks** statt als Datei (der Normalfall bei aktivem CR-Kontext, siehe „Ablageort bestimmen"), lies ihn mit `python3 ~/.claude/skills/kanboard/kanboard get-handoff <task_id>` aus und verfahre dann genauso. Ein leerer Rückgabewert heißt schlicht, dass am Task keiner hinterlegt ist — dann lokal nachsehen.

## Herkunft & Lizenz

Vendorisierter, angepasster Fork von [`mattpocock/skills`](https://github.com/mattpocock/skills/tree/main/skills/productivity/handoff) (Skill-Pfad `skills/productivity/handoff`), Stand Commit `386d4ff719a7c420ad1454232d0436b01f1b8c17`. Lizenz: MIT © 2026 Matt Pocock (siehe `LICENSE`).

azedo-Anpassungen gegenüber dem Upstream:

- Vollständige Übersetzung ins Deutsche
- Ablage im **Projektverzeichnis** (`docs/` bzw. Projektstamm) statt im OS-Temp-Verzeichnis
- Dateinamens-Konvention: Argument dient als Fokus **und** Slug (`handoff-<slug>.md`), damit pro Thema ein eigenes Dokument entsteht und nichts überschrieben wird
- Abschnitt „Einlesen eines bestehenden Handoff-Dokuments" (Rekapitulieren, Rückfragen, nie eigenständig handeln) ergänzt
- Abschnitt „Ablageort bestimmen" ergänzt: bei aktivem Kanboard-CR geht der Handoff in das Handoff-Feld des Tasks (TaskHandoff-Plugin + kanboard-Skill), sonst wird ein vorhandenes lokales Dokument fortgeschrieben, sonst eine neue Datei angelegt
- Frontmatter-Feld `disable-model-invocation: true` entfernt; `Trigger: /handoff.` in der `description` ergänzt

Updates aus dem Upstream werden bei Bedarf **manuell** abgeglichen (kein Auto-Sync).
