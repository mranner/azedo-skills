---
name: wie-bitte
description: "Stopp - die letzte Antwort ist nicht angekommen. Sie wird noch einmal erklärt, in Einfacher Sprache. Trigger: /wie-bitte."
allowed-tools: []
disable-model-invocation: true
metadata:
  display_name: Wie bitte?
  version: 1.46.0
---

# Wie bitte?

Die letzte Antwort ist nicht angekommen. Erkläre sie noch einmal - nicht lauter,
sondern einfacher.

Gemeint ist **immer die letzte eigene Antwort** in dieser Konversation, nie ein
Text, den der Nutzer mitgeschickt hat. Kam mit dem Aufruf ein Argument, ist das
der Hinweis, **welche Stelle** nicht getragen hat („der Teil mit dem Jail"), kein
neuer Gegenstand.

## Aufbau

Drei Teile, in dieser Reihenfolge:

1. **Worum es geht** - ein Satz Kontext. Die vorige Antwort setzte etwas voraus,
   das nicht gesagt war; hier steht es.
2. **Die Aussage** - der Kern, ohne Vorrede.
3. **Was das heißt** - die Folge für den Nutzer: was zu tun ist, was sich
   ändert, oder ausdrücklich, dass nichts zu tun ist.

Höchstens acht Sätze insgesamt. Wird es länger, war der erste Teil zu breit.

## Sprache

Einfache Sprache, Stufe B1 im Sinne des Skills `einfache-sprache`:

- Sätze im Mittel unter 15 Wörtern, höchstens ein Nebensatz je Satz.
- Ein Gedanke pro Absatz.
- Verben statt Nominalstil: „prüfen" statt „einer Prüfung unterziehen".
- Kein Passiv ohne handelnde Person. Steht nicht fest, wer handelt, gehört das
  gesagt statt umschrieben.
- Keine Ausrufezeichen, kein munterer Ton. Wer nachfragt, ist nicht begriffsstutzig.

**Fachbegriffe bleiben stehen** und bekommen bei der ersten Nennung einen
Halbsatz Erklärung: „im Jail (der abgeschottete Bereich, in dem die Website
läuft)". Ersetzt man den Begriff, kann der Nutzer später nicht danach fragen
oder suchen.

## Grenzen

- **Keine neuen Fakten.** Nur die vorige Antwort wird verständlich gemacht.
  Fehlt darin etwas, wird die Lücke benannt, nicht gefüllt.
- **Zahlen, Pfade, Hostnamen, Befehle und Fristen bleiben wörtlich.** Genau
  daran hängt die Aussage.
- **Keine Messung, keine Befundliste.** Für Kennwerte, Linter und
  Vorher/Nachher-Vergleiche ist `einfache-sprache` zuständig, und dessen eigene
  Warnung gilt: bei Texten unter ~10 Sätzen sind die Kennwerte ohnehin nicht
  belastbar.
- **War die Antwort schlicht falsch**, ist das der Befund. Dann wird das gesagt
  und korrigiert, statt eine falsche Aussage verständlich zu verpacken.

## Abgrenzung zu `einfache-sprache`

| | `wie-bitte` | `einfache-sprache` |
|---|---|---|
| Gegenstand | die letzte eigene Antwort | ein Text oder eine Datei des Nutzers |
| Ergebnis | die Antwort noch einmal | Messung, Befunde, Übertragung |
| Auslöser | nur `/wie-bitte` | auch selbsttätig |

Der Skill wird **nicht selbsttätig** ausgelöst (`disable-model-invocation`).
Sonst griffe er bei Sätzen wie „das versteht kein Mensch", die zu
`einfache-sprache` gehören.

## Herkunft & Lizenz

Angelehnt an [`mattpocock/skills`](https://github.com/mattpocock/skills/tree/main/skills/productivity/wait-what)
(Skill-Pfad `skills/productivity/wait-what`), Stand Commit
`5c89081d4bbeb3d039a42093653f90bb698d780e`. Lizenz: MIT (c) 2026 Matt Pocock
(siehe `LICENSE`).

azedo-Anpassungen gegenüber dem Upstream:

- Deutsch, und Einfache Sprache nach DIN-Stufe B1 statt ASD-STE100 (Simplified
  Technical English) - die Antworten hier sind deutsch
- Kein Repo-Anker: der Upstream zieht die Begriffe aus `CONTEXT.md` /
  `CONTEXT-MAP.md`, dieser Skill kommt ohne aus und funktioniert in jedem Projekt
- Fester Aufbau in drei Teilen (Kontext, Aussage, Folge) statt „give me a little
  bit of context"
- Regel „Fachbegriff behalten und erklären" sowie die Leitplanken zu Zahlen,
  neuen Fakten und falschen Antworten ergänzt
- Abgrenzung zu `einfache-sprache` ergänzt, damit die Trigger nicht kollidieren

Updates aus dem Upstream werden bei Bedarf **manuell** abgeglichen (kein Auto-Sync).
