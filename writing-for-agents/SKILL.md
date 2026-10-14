---
name: writing-for-agents
description: >
  Regeln für Texte, die ein Agent liest: Skills, CLAUDE.md, Memory-Einträge und
  Wiki-Procedures - was in den Kontext gehört, was hinter einen Verweis, wie
  Trigger, Schritte und Regeln formuliert werden. Nutze diesen Skill, wenn ein
  Skill angelegt oder geändert wird oder eine CLAUDE.md, Memory oder
  Wiki-Procedure entsteht oder überarbeitet wird. Auch bei "der Skill greift
  nicht", "die CLAUDE.md ist zu lang". Trigger: /writing-for-agents.
---

Referenz für jedes Dokument, das ein Agent liest. Ziel ist nicht dieselbe Ausgabe bei jedem Lauf, sondern derselbe **Weg**: Jede Regel unten ist ein Hebel gegen Varianz.

Ist das Dokument ein Skill, zusätzlich [references/skill-mechanik.md](references/skill-mechanik.md) lesen: Aufruf durch Modell oder User, Aufteilen nach Aufruf, Router-Skills. Das Formale (Frontmatter-Notation, Lint, Release) steht in der `CLAUDE.md` des Repos azedo-skills.

## Wo was liegt - und was es kostet

| Ort | Geladen | Kosten |
|---|---|---|
| globale und Projekt-`CLAUDE.md` samt `@`-Includes | immer | jede Zeile in jedem Turn |
| Zeile in `MEMORY.md` | immer | jede Zeile in jedem Turn |
| Skill-`description` | immer | jede Zeile in jedem Turn |
| Memory-Datei, `SKILL.md`, Wiki-Procedure ohne `@` | erst über einen Verweis | nur die Verweiszeile |
| `references/` eines Skills | erst über einen Verweis aus `SKILL.md` | nur die Verweiszeile |

Ein `@`-Include ist **kein** Verweis: Er lädt die ganze Datei immer mit.

## Context Pointer

Ein **Context Pointer** ist alles im Kontext, das auf Material außerhalb zeigt und sagt, wann es zu holen ist: eine Skill-`description`, eine Zeile in `MEMORY.md`, ein Verweis in `CLAUDE.md`. Ob der Agent das Material holt, entscheidet die **Formulierung** des Pointers, nicht das Ziel. Greift ein wichtiges Ziel unzuverlässig, zuerst den Pointer schärfen.

Ein Pointer sagt, was das Material ist, und nennt die **Fälle**, die es auslösen. Ein Fall ist eine eigene Situation, in der das Material einen anderen Weg nimmt.

- **Ein Trigger pro Fall.** Jeder Fall bekommt eine wörtliche Nutzerformulierung, Synonyme für denselben Fall werden zu einer zusammengelegt. Die Formulierungen sichern gegen Untertriggern; die Beschränkung auf eine pro Fall hält die Zeile kurz, die in jedem Turn mitläuft. Festgelegt 2026-10-14, löst das großzügige Triggern mit Synonymlisten ab.
- **Leitbegriff nach vorn**: Am Anfang wirkt er am stärksten als Auslöser.
- **Was der Body ohnehin sagt, gehört nicht in den Pointer.**

## Informationshierarchie

Ein Dokument besteht aus **Schritten** (was der Agent der Reihe nach tut) und **Referenz** (Regeln, Fakten, Definitionen zum Nachschlagen). Jedes Stück sitzt auf einer Stufe:

1. **Schritt in der Datei** - die oberste Stufe.
2. **Referenz in der Datei** - bei Bedarf gelesen. Eine flache Liste gleichrangiger Regeln ist hier in Ordnung.
3. **Ausgelagerte Referenz** - eigene Datei hinter einem Pointer, nur bei Bedarf geladen.

**Faustregel:** Inline, was jeder Fall braucht; hinter einen Pointer, was nur manche Fälle erreichen. Zu wenig ausgelagert, und die Schritte gehen in der Referenz unter; zu viel, und der Agent findet nicht, was er braucht.

**Zusammen ablegen:** Definition, Regeln und Ausnahmen eines Begriffs stehen unter einer Überschrift. Wer einen Teil liest, bekommt die Nachbarn mit.

**Wucherung** ist das Versagensmuster: Ein Dokument ist zu lang, auch wenn jede Zeile stimmt. Die Aufmerksamkeit verteilt sich dünner. Abhilfe ist die Hierarchie: Referenz auslagern, nach Fall oder Ablauf aufteilen.

## Schritte und Abschlusskriterien

Jeder Schritt endet auf einem **Abschlusskriterium**, an dem der Agent erkennt, dass er fertig ist.

- **Klar:** Ein vages Ende („bis das Problem verstanden ist") lädt zum vorzeitigen Abschluss ein - die sichtbaren nächsten Schritte ziehen. Zuerst das Kriterium schärfen. Erst wenn es unscharf bleiben muss und der Agent nachweislich hetzt, die späteren Schritte abtrennen - das wirkt nur über eine echte Kontextgrenze (Subagent, Übergabe).
- **Fordernd:** „Jedes geänderte Modell erfasst" erzwingt gründliche Arbeit, „Liste der Änderungen erstellen" nicht. Das gilt auch für reine Referenz: „jede Regel angewendet".

Am stärksten ist ein Kriterium, das prüfbar und vollständig ist (`lint-skills.py` Exit 0, „jeder Host aus der Liste geprüft").

## Leitbegriffe

Ein **Leitbegriff** ist ein knappes Wort, das das Modell aus dem Training schon kennt und mit dem es beim Ausführen denkt (_Lektion_, _Tracer Bullet_, _rot_ für einen Test, der den Fehler zeigt). Als Wort wiederholt, nie als Satz, bündelt er ein ganzes Verhalten. Ein selbst erfundenes Wort funktioniert, kostet aber die Definition, die ein bekanntes umsonst mitbringt.

Nach Stellen suchen, die ein Leitbegriff ersetzt: eine Dreierreihe an drei Stellen, ein Satz, der um eine Idee herumredet.

## Verbote oder positive Form - nach Textart

Ein Verbot holt das verbotene Verhalten erst in den Kontext. Deshalb entscheidet die Textart:

- **Anweisungen und Regeln** positiv formulieren: das Zielverhalten nennen („in `sh -c` wrappen", „einzeilige Kommentare"). Ein Verbot nur als harte Leitplanke, die sich nicht positiv fassen lässt - dann mit dem Zielverhalten daneben.
- **Fehlerbilder** in Procedures bleiben als FALSCH/RICHTIG-Paar mit der wörtlichen Fehlermeldung. Die Meldung ist der Suchbegriff, und sie zeigt oft auf die falsche Ursache; das FALSCH-Beispiel stellt die Verbindung her.

Festgelegt 2026-10-14.

## Ausdünnen

- **Eine Stelle pro Aussage.** Eine Verhaltensänderung ist dann eine Änderung an einer Stelle. Doppelungen kosten Pflege und Tokens und heben eine Aussage über ihren Rang.
- **Ausnahme nur nach belegtem Versagen:** Eine Kopie zusätzlich zum Pointer ist erlaubt, wenn der geschärfte Pointer nachweislich nicht gegriffen hat. An der Kopie steht, wann und warum (Beispiel: csh-Kurzregeln in der Projekt-`CLAUDE.md` neben dem `@`-Include). Ohne diesen Beleg gilt die eine Stelle. Festgelegt 2026-10-14.
- **Die Umgebung ist auch eine Quelle.** Was Config, Verzeichnis oder `--help` mit einem Befehl liefern, nicht abschreiben - eine Kopie veraltet. Aufschreiben, was niemand nachschlagen kann: die ungeschriebene Konvention, den Grund einer Entscheidung, die Falle, die keine Config verrät. Infrastruktur steht im Wiki, nicht im Skill.
- **Relevanz jeder Zeile prüfen.** Eine Zeile verliert sie, wenn sie nie auf die Aufgabe wirkt oder veraltet ist. Ohne Ausdünnen lagert sich Schicht auf Schicht ab, weil Hinzufügen sicher wirkt und Löschen riskant.
- **No-ops Satz für Satz suchen:** eine Anweisung, die das Modell ohnehin befolgt. Prüffrage: Ändert der Satz das Verhalten gegenüber dem Default? Wenn nein, den ganzen Satz löschen, nicht kürzen. Ein zu schwaches Wort ist auch ein No-op (_gründlich_, wo der Agent schon gründlich ist) - dann ein stärkeres Wort, keine andere Technik.

## Herkunft & Lizenz

Angepasste, gekürzte Übersetzung von `writing-for-agents` aus [`mattpocock/skills`](https://github.com/mattpocock/skills/tree/main/skills/productivity/writing-for-agents), Stand Commit `321658273cb1d20b76026717d027d505790106d4`. Lizenz: MIT © 2026 Matt Pocock (siehe `LICENSE`).

azedo-Anpassungen gegenüber dem Upstream:

- Deutsch, gekürzt; Abschnitt „Wo was liegt" für die azedo-Ablageorte (CLAUDE.md, `@`-Includes, Memory, Wiki, Skills) ergänzt
- Trigger: eine wörtliche Nutzerformulierung pro Fall statt Leitwort allein
- Verbote: FALSCH/RICHTIG-Paare für Fehlerbilder ausdrücklich erlaubt
- Doppelung: Ausnahme nach belegtem Versagen des Pointers, mit Begründung an der Kopie
- Abschnitt „Die zwei Lasten" in die Tabelle „Wo was liegt" überführt; die Merklast des Menschen steht in `references/skill-mechanik.md`

Updates aus dem Upstream werden bei Bedarf **manuell** abgeglichen (kein Auto-Sync).
