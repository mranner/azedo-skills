# compact - Task eindampfen

`/kanboard compact <task_id>` fasst Beschreibung und Handoff eines Tasks knapper
neu. Hat der Task mehr als 5 Kommentare, werden auch die Kommentare
zusammengefasst. Erst kommt der Vorschlag, geschrieben wird nach dem OK des Users;
das Löschen der Original-Kommentare braucht ein zweites, eigenes OK.

## 1. Lesen und sichern

```bash
python3 "$SKILL_DIR/kanboard" cr <task_id> --output .tmp/compact
python3 "$SKILL_DIR/kanboard" get-comments <task_id> > .tmp/compact/cr<task_id>/comments.json
```

`--output` legt Beschreibung und Handoff als `description.md` und `handoff.md`
nach `.tmp/compact/cr<task_id>/`. Das Verzeichnis ist die Sicherung des
Originalstands - nach dem Löschen der Kommentare die einzige Kopie. Erst
aufräumen, wenn der User die neue Fassung gesehen hat.

## 2. Neufassung

- **Beschreibung** = die Aufgabe (Ziel, offene Punkte, Umsetzung),
  **Handoff** = Stand und nächster Schritt. Was in beiden steht, bleibt nur an
  einer Stelle.
- **Raus:** Erledigtes ohne Folgen, überholte Annahmen, Zwischenstände, die ein
  späterer Stand ersetzt, Wiederholungen, Füllsätze.
- **Bleibt:** Entscheidungen mit Begründung, offene Punkte, Verweise (Commits,
  Wiki, Tickets), Zahlen, Namen, Fristen. Erledigte Checkbox-Punkte bleiben als
  `[x]` mit Kurzverweis.
- **Bleibt auch:** Rückfallebenen und Auswege - verworfene oder zurückgestellte
  Alternativen samt Bewertungskriterien, die wieder gebraucht werden, wenn der
  gewählte Weg scheitert. "Nicht gewählt" heißt nicht "überholt".
- **Verweis statt Inhalt** nur, wenn das Ziel (anderer Task, Doku-Datei) den
  gestrichenen Inhalt nachweislich enthält - Abschnitt für Abschnitt prüfen,
  nicht per Stichwort. Ist das Ziel nicht lesbar, bleibt eine Kurzfassung.
- Kürzen statt umschreiben: keine neuen Inhalte, keine zusätzlichen
  Überschriften, der Ton der Vorlage bleibt.

## 3. Kommentare (nur bei mehr als 5)

Was die Aufgabe oder den Stand betrifft, wandert in Beschreibung bzw. Handoff.
Der Rest wird **ein** Zusammenfassungs-Kommentar, je Punkt mit Autor und Datum
des Originals. Die Original-Kommentare werden danach gelöscht, auch die anderer
User - aber erst nach eigener Freigabe (Schritt 6).

## 4. Vorschlag zeigen und warten

- Länge vorher/nachher je Feld
- neue Beschreibung, neuer Handoff, Zusammenfassungs-Kommentar im Wortlaut -
  ab zusammen 3.000 Zeichen stattdessen die Pfade der Dateien in
  `.tmp/compact/cr<task_id>/`, damit der Vorschlag im Chat lesbar bleibt
- was gestrichen wurde, in Stichworten
- die zu löschenden Kommentare als `K<n> Autor, Datum: "Anfang…" (id)`
- Pfad der Sicherung, mit dem Hinweis, dass gelöschte Kommentare nur dort
  erhalten bleiben

Nichts schreiben ohne OK. Dieses OK gilt nur für Schritt 5, nicht für das
Löschen.

## 5. Eindampfen

Jeden Aufruf einzeln absetzen und das Ergebnis prüfen, bevor der nächste folgt:

```bash
python3 "$SKILL_DIR/kanboard" update-task <task_id> --description-file <datei>
python3 "$SKILL_DIR/kanboard" set-handoff <task_id> --file <datei>
python3 "$SKILL_DIR/kanboard" add-comment <task_id> --file <datei>
```

Danach Längen und Task-URL melden. Der User sieht sich die neue Fassung im Task
an, bevor Schritt 6 gefragt wird.

## 6. Kommentare löschen (eigene Freigabe)

Erneut fragen, mit der Liste der zu löschenden Kommentare (`K<n> Autor, Datum:
"Anfang…" (id)`) und dem Pfad der Sicherung - nach dem Löschen die einzige Kopie.
Nur nach ausdrücklichem OK, und nur wenn der Zusammenfassungs-Kommentar aus
Schritt 5 angelegt ist:

```bash
python3 "$SKILL_DIR/kanboard" remove-comment <comment_id>
```

Ohne OK bleiben die Originale stehen; das Eindampfen gilt trotzdem.
