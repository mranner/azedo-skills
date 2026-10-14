---
name: retro
description: >
  Retrospektive einer Session: schlägt Verbesserungen an der Umgebung des
  Agents vor (CLAUDE.md, Memory, Skills, Wiki, Hooks). Trigger: /retro.
disable-model-invocation: true
argument-hint: "Session-ID oder Stichwort (optional, sonst die aktuelle oder die letzte Session)"
---

Der User will eine **Retrospektive**. Du schlägst Verbesserungen an der **Umgebung** des Agents vor, damit künftige Läufe besser werden - nicht am Ergebnis der Session.

## Schritte

1. Skill `writing-for-agents` laden. Er ist der Maßstab für jeden Vorschlag an einem Text, den ein Agent liest.

2. Die Session lesen. Ohne Argument ist es die aktuelle, sofern sie vor `/retro` schon Arbeit enthält - dann steht sie im Kontext. Sonst, oder mit Session-ID oder Stichwort als Argument, die Kurzfassung des Logs holen:

   ```bash
   "$SKILL_DIR/scripts/session-digest" [<session-id> | <stichwort>]
   ```

   `$SKILL_DIR` ist das Base Directory dieses Skills. Ohne Argument nimmt das Script die neueste Session des Arbeitsverzeichnisses außer der laufenden. Es liefert User-Texte, Agent-Texte, Tool-Aufrufe und Tool-Fehler je eine Zeile, gekürzt. Ein Detail daraus mit `jq` im Log nachlesen, dessen Pfad in der ersten Zeile steht.

   Fertig, wenn feststeht, wo der Agent Zeit verlor, wo er korrigiert wurde und wo ein Befehl scheiterte.

3. Kandidaten in jeder Kategorie unter „Kategorien" suchen. Fertig, wenn jede Kategorie geprüft ist und jeder Kandidat eine Belegstelle aus der Session hat.

4. Die Kandidaten nach Schwere geordnet vorlegen, je Kandidat: Beleg, Ort der Änderung, Vorschlag. Nichts davon umsetzen - der User entscheidet.

## Kategorien

- **Navigation:** Wie schnell fand der Agent die richtige Datei, Procedure oder Memory? Gibt es versteckte Abhängigkeiten? Würde ein **Pointer** helfen - eine Zeile in `CLAUDE.md`, im Wiki-Index, in einer Skill-`description`? _Wenn_ der Agent lange nach einer Information suchte, die es schon gab.
- **Automatische Prüfungen:** Hätte ein Check einen Fehler des Agents abgefangen - Lint, PHPStan, Hook, Test? Zuerst nachsehen, was es schon gibt (`lint-skills.py`, `skills-review-guard.py`, die Hooks in `settings.json`, die Prüfung des Projekts): ein vorhandener, aber nicht verdrahteter oder still kaputter Check ist der Befund, keine Neuerfindung. Ein Repo ganz ohne Leitplanke (kein `pre-commit`, kein Hook) ist selbst ein Befund. _Wenn_ der Agent einen Fehler machte, den ein Check hätte finden können.
- **Regeln:** Ist ein Verstoß **mechanisch** (festes Muster, verbotener Aufruf, Dateiort, Syntax), bekommt er einen Check: eine Regel im vorhandenen Lint, einen `pre-commit`-Hook oder einen `PreToolUse`-Hook - was am billigsten ist. Nur echte **Ermessensfragen** werden Text, und dann dort, wo sie erst bei Bedarf geladen werden (Checkliste im Guard, Skill, Procedure). _Wenn_ eine Regel existiert und trotzdem verletzt wurde, oder der User dieselbe Korrektur wiederholt.
- **Ständig geladene Texte:** globale und Projekt-`CLAUDE.md` samt `@`-Includes, `MEMORY.md`, Skill-Descriptions. Gehört etwas davon in einen Check oder hinter einen Pointer? Ist eine Kopie ohne belegtes Versagen des Pointers dabei? _Wenn_ diese Texte groß sind - im Projekt wie global.
- **Korrekturen:** Hat der User den Agent korrigiert, ohne dass die Korrektur danach irgendwo steht (Memory, Skill, Procedure)? Widerspricht eine Memory einem Skill oder der `CLAUDE.md`? _Wenn_ der User eingreifen musste.
- **Tool-Ökonomie:** Teure Aufrufe, die schlanker gingen? Ein Skill-Script oder eine MCP-Ausgabe, die unnötig viele Tokens liefert? Wiederholte Permission-Denials, die eine Freigabe in `settings.json` lösen würde? _Wenn_ ein Aufruf teuer war oder mehrfach scheiterte.
- **No-ops:** Anweisungen in den Steuertexten, die das Verhalten gegenüber dem Default nicht ändern. _Wenn_ die Steuertexte groß und unübersichtlich sind.
- **Informationszugang:** Fehlte dem Agent eine entscheidende Information - ein Log, eine Leseberechtigung, ein Wiki-Eintrag, eine Config? _Wenn_ der Agent raten oder den User fragen musste, obwohl die Information technisch erreichbar wäre.

## Wohin eine Änderung gehört

| Ort | Geladen | Wofür |
|---|---|---|
| globale `CLAUDE.md` | immer, in jedem Projekt | Arbeitsweise, die überall gilt; sparsam |
| Projekt-`CLAUDE.md` | immer, im Projekt | Pointer auf Wiki und Procedures; sparsam |
| `MEMORY.md` + Memory-Datei | Indexzeile immer, Datei bei Bedarf | Vorlieben und Korrekturen des Users |
| Wiki-Procedure | über Pointer | Infrastruktur, Fehlerbilder, Abläufe |
| Skill | Description immer, Rest bei Bedarf | wiederkehrende Aufgaben mit eigenem Werkzeug |
| Lint / Hook | nie im Kontext | alles Mechanische |

Ein Check kostet keinen Kontext und greift jedes Mal. Ein Text greift nur, wenn der Agent ihn liest und befolgt. Im Zweifel den Check vorschlagen.

## Herkunft & Lizenz

Angepasste Übersetzung von `retro` aus [`mattpocock/skills`](https://github.com/mattpocock/skills/tree/main/skills/engineering/retro), Stand Commit `a7d038f6bf7f01b516408e95e2fb56e0b338fa6f`. Lizenz: MIT © 2026 Matt Pocock (siehe `LICENSE`).

azedo-Anpassungen gegenüber dem Upstream:

- Deutsch; Maßstab ist der azedo-Skill `writing-for-agents`
- Dateien auf die azedo-Umgebung umgestellt: kein `AGENTS.md`, kein `CODING_STANDARDS.md` und kein Reviewer-Agent; stattdessen `CLAUDE.md`, Memory, Wiki-Procedures, Skills, Lint und Hooks (Tabelle „Wohin eine Änderung gehört")
- Kategorie „Korrekturen" ergänzt, Permission-Denials unter „Tool-Ökonomie"
- Session-Logs mit konkretem Pfad, Abschlusskriterien je Schritt
- Abschnitt „Implementation vs Review" entfällt mangels Reviewer-Agent
