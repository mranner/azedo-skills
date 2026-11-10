# compact - Task eindampfen

`/kanboard compact <task_id>` fasst Beschreibung und Handoff eines Tasks knapper
neu. Hat der Task mehr als 5 Kommentare, werden auch die Kommentare
zusammengefasst. Erst kommt der Vorschlag, geschrieben wird nach dem OK des Users.

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
- Kürzen statt umschreiben: keine neuen Inhalte, keine zusätzlichen
  Überschriften, der Ton der Vorlage bleibt.

## 3. Kommentare (nur bei mehr als 5)

Was die Aufgabe oder den Stand betrifft, wandert in Beschreibung bzw. Handoff.
Der Rest wird **ein** Zusammenfassungs-Kommentar, je Punkt mit Autor und Datum
des Originals. Die Original-Kommentare werden danach gelöscht, auch die anderer
User.

## 4. Vorschlag zeigen und warten

- Länge vorher/nachher je Feld
- neue Beschreibung, neuer Handoff, Zusammenfassungs-Kommentar im Wortlaut
- was gestrichen wurde, in Stichworten
- die zu löschenden Kommentare als `K<n> Autor, Datum: "Anfang…" (id)`
- Pfad der Sicherung, mit dem Hinweis, dass gelöschte Kommentare nur dort
  erhalten bleiben

Nichts schreiben ohne OK.

## 5. Schreiben

Jeden Aufruf einzeln absetzen und das Ergebnis prüfen, bevor der nächste folgt:

```bash
python3 "$SKILL_DIR/kanboard" update-task <task_id> --description-file <datei>
python3 "$SKILL_DIR/kanboard" set-handoff <task_id> --file <datei>
python3 "$SKILL_DIR/kanboard" add-comment <task_id> --file <datei>
python3 "$SKILL_DIR/kanboard" remove-comment <comment_id>
```

`remove-comment` kommt zuletzt und nur, wenn der Zusammenfassungs-Kommentar
angelegt ist. Danach Längen, Task-URL und Pfad der Sicherung melden.
