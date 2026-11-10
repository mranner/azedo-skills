# Review nach einem Call

Ablauf für die Auswertung einer Aufnahme: Punkte gruppieren, je Punkt
entscheiden, Ergebnisse in Tasks, Protokoll und Mails überführen. sally liefert
nur die Aufnahme; Tasks laufen über `kanboard`, Mails über `mail-as-me` und
`swaks`, Zeiten über `kimai`. Jeder Schritt endet auf seinem Kriterium
(*Fertig:*), erst dann folgt der nächste.

Inhalt: Rahmen prüfen, Lesen, Sprecher zuordnen, Gruppieren, Gruppe
aufbereiten, Entscheiden, Protokoll und Mails, Kimai, Review-Dokument sichern,
Abschluss, Übergabe an eine andere Session.

## 1. Rahmen prüfen

Aufnahme per Name finden (`recordings`, bei Bedarf `--since`). Ein aktiver CR
oder eine im Call genannte Task-Nummer ist ein **Kandidat**: Beschreibung und
alle Kommentare lesen. Ein Call kann mehrere Tasks betreffen oder einen
Folgetask ergeben; wohin ein Punkt gehört, entscheidet Schritt 6 je Gruppe.
Gehört der Call zu einem anderen Projekt als die laufende Session
(Arbeitsverzeichnis), das jetzt melden.

*Fertig:* Aufnahme und Kandidaten (oder „keine") stehen fest, die Session
passt.

## 2. Lesen

`download` holt Zusammenfassung und Transkript nach `.tmp/`. Das Glossar auf
beide anwenden. Ausgewertet wird **das Transkript**, die Zusammenfassung dient
der Orientierung: sie vermischt Themen, erfindet Namen und meldet geplante
Punkte als erledigt. Ihre Teilnehmer- und Aufgabenlisten sind ungeprüft: Namen,
die nur auf dem geteilten Bildschirm stehen (Demo- oder Testdaten), sind keine
Teilnehmer, und eine Begründung ist keine Aufgabe.

*Fertig:* beide Dateien gelesen, Glossar angewendet.

## 3. Sprecher zuordnen

Je `Speaker` eine kurze Textprobe mit Zeitstempel zeigen, die die Person
verrät (Anrede, Rolle, Bezug); der User nennt die Person. Eine Person ist oft
auf mehrere Speaker verteilt, auch der User selbst. Seine eigenen Aussagen
werden als solche gekennzeichnet - sie sind sein Wissen, kein Feedback der
anderen. Nennt sich ein Sprecher in einem Beispiel selbst in der dritten Person
(„wie viele Besuche hat die Karin gestern"), ist das kein Hinweis auf eine
andere Person.

*Fertig:* jeder Speaker ist bestätigt oder bleibt als „unbekannt" stehen.

## 4. Gruppieren

Nur die Gruppenliste, noch ohne Inhalt: Tabelle `Nr | Thema | Zeit`.

- **Chronologisch** bei Ablauf-Calls.
- **Thematisch** bei Diskussions-Calls, die zwischen Themen springen.

Privates fällt weg.

Die **Stand-Datei** in `.tmp/` anlegen: Kopf mit Aufnahme (Name, Datum),
Teilnehmern und Sprecher-Zuordnung aus Schritt 3, darunter die Gruppenliste.

*Fertig:* jede Stelle des Transkripts mit Inhalt gehört zu einer Gruppe, die
Liste ist gezeigt, die Stand-Datei angelegt.

Die Schritte 5 und 6 laufen als **Schleife je Gruppe**, in der Reihenfolge der
Liste.

## 5. Gruppe aufbereiten

Für die aktuelle Gruppe:

- Inhalt kurz zusammenfassen und trennen: **bei mir / beim Gegenüber / Info**.
- Widersprüche und nicht Entschiedenes als Frage an den User; offen bleibt
  offen.
- Die Kandidaten aus Schritt 1 prüfen und zusätzlich gezielt in Kanboard
  suchen (`search`), mit dem gemeinten Namen und den Fehlerkennungen aus dem
  Glossar, nur offene Tasks.

*Fertig:* Rückfragen beantwortet, zur Gruppe steht ein Task oder „keiner".

## 6. Entscheiden

Für die aktuelle Gruppe eine nummerierte Tabelle `Nr | Punkt | Task |
Vorschlag`. Default-Vorschlag ist **„nichts"**; eine Handlung nur, wenn der
Punkt eine eigene Zusage oder eine offene Aufgabe ist. Wartet ein Punkt auf
Termin oder Feedback Dritter, gehört er ins Protokoll statt in einen Task. Der
User antwortet kompakt („1 ja, 2 nichts, 3 …") und streicht, was nicht ins
Protokoll soll.

Jede Entscheidung **sofort** in die Stand-Datei in `.tmp/` schreiben; Kanboard
bleibt in der Schleife unberührt.

Zur nächsten Gruppe (zurück zu Schritt 5) erst nach **Okay des Users**.

Nach der letzten Gruppe je betroffenem Task prüfen, ob der Call viele Punkte
seiner Beschreibung überholt hat. Dann einen **Folgetask** anbieten:
Beschreibung als Checkliste der offenen Punkte, Handoff und Anhänge übernehmen,
den alten Task mit Verweis auf den Folgetask nach „erledigt" verschieben.

Danach je Task den Text gesammelt zeigen:
Beschreibung (Abschnitt „Stand Call <wer> (<Datum>)", dazu „Offen") und
Handoff. In Kanboard geschrieben wird erst nach **Go** des Users.

*Fertig:* jede Gruppe der Liste ist entschieden und steht in der Stand-Datei;
je Task ist der Folgetask entschieden, die Task-Texte sind freigegeben und
geschrieben.

## 7. Protokoll und Mails

Erst hier fragen, und zwar **einzeln**, jede Frage, wenn sie ansteht: Umfang
des Protokolls (vollständig oder nur die eigene Rolle), seine Ablage (Chat,
Mail oder Datei), danach welche Mails an wen gehen.

Das Protokoll entsteht aus dem abgestimmten Stand aus Schritt 6, nicht neu aus
dem Transkript. Texten über `mail-as-me`, je Thema eine eigene Mail, auch an
dieselbe Person; zuerst das Protokoll, danach Mails an Dritte. **Versand nur
auf Go.** Fehlt die Adresse eines externen Teilnehmers, geht die Mail an die
Kontaktperson mit der Bitte um Weiterleitung; neue Adressen in die
swaks-Kontakte aufnehmen. Die gesendete Protokoll-Mail als `.eml` aus
„Gesendet" an den Task hängen.

*Fertig:* Protokoll abgelegt, jede vereinbarte Mail ist versendet oder als
Entwurf abgelegt.

## 8. Kimai

Den Call-Beginn beim User erfragen und die Aufnahmezeit aus Sally einmal als
Vorschlag nennen - sie weicht oft davon ab. Projekt und Aktivität erfragen,
wenn kein früherer Eintrag zum selben Thema sie vorgibt. Call und
Nachbearbeitung als getrennte Einträge; nennt der User eine Gesamtdauer, wird
es eine Buchung.

*Fertig:* die vereinbarten Einträge sind gebucht.

## 9. Review-Dokument sichern

Die Stand-Datei wird zum Review-Dokument: unten einen leeren Abschnitt
„Nachträge" für spätere Präzisierungen anfügen, dann per `kanboard attach-file`
an den Task hängen; betrifft der Call mehrere Tasks, fragen, an welchen.
Spätere Nachträge aktualisieren den Anhang per `replace-file`. Dem User melden,
dass die Aufnahme in Sally jetzt gelöscht werden kann - löschen tut er selbst.

*Fertig:* Review-Dokument hängt am Task.

## 10. Abschluss

Liste ausgeben:

- **Erledigt** - Tasks, Mails, Buchungen
- **Wartet auf** - wen, mit was
- **Offen** - was der User noch selbst tut

Neue Fehlerkennungen gesammelt als Glossar-Vorschlag; kommt das Wort auch
allgemein vor (ein Vorname, ein Alltagswort), mit `nur bei`. Nach Freigabe
eintragen. Zum Schluss Downloads und Stand-Datei aus `.tmp/` löschen.

*Fertig:* Liste ausgegeben, Glossar entschieden, `.tmp/` ohne Downloads und
Stand-Datei der Aufnahme.

## Übergabe an eine andere Session

Muss die Review in einer anderen Session weiterlaufen, den abgestimmten Stand
nach **Go** des Users in den Task schreiben und im Handoff je Ergebnis den
Stand nennen: **abgestimmt / Entwurf / versendet**. Offene Schritte als „entwerfen und
abstimmen" formulieren; versendet wird erst auf Go in der Folgesession.
