# Review nach einem Call

Ablauf für die Auswertung einer Aufnahme: Punkte gruppieren, je Punkt
entscheiden, Ergebnisse in Tasks, Protokoll und Mails überführen. sally liefert
nur die Aufnahme; Tasks laufen über `kanboard`, Mails über `mail-as-me` und
`swaks`, Zeiten über `kimai`. Jeder Schritt endet auf seinem Kriterium
(*Fertig:*), erst dann folgt der nächste.

Inhalt: Rahmen prüfen, Ziel klären, Lesen, Sprecher zuordnen, Gruppieren,
Tasks suchen, Entscheiden, Protokoll und Mails, Kimai, Abschluss, Übergabe an
eine andere Session.

## 1. Rahmen prüfen

Aufnahme per Name finden (`recordings`, bei Bedarf `--since`). Ist ein CR aktiv
oder fällt im Call eine Task-Nummer, ist dieser Task **führend**: alle
Kommentare lesen, die Ergebnisse dort einarbeiten, keine neuen Tasks dazu
anlegen. Gehört der Call zu einem anderen Projekt als die laufende Session
(Arbeitsverzeichnis), das jetzt melden.

*Fertig:* Aufnahme und Zieltask (oder „keiner") stehen fest, die Session passt.

## 2. Ziel klären

Einmal gesammelt fragen:

- Tasks anlegen oder aktualisieren?
- Protokoll: vollständig oder nur der Teil der eigenen Rolle?
- Mails: an wen, und welche Themen?
- Ablage: Chat, Mail oder Datei?

*Fertig:* jede Frage ist beantwortet.

## 3. Lesen

`download` holt Zusammenfassung und Transkript nach `.tmp/`. Das Glossar auf
beide anwenden. Ausgewertet wird **das Transkript**, die Zusammenfassung dient
der Orientierung: sie vermischt Themen, erfindet Namen und meldet geplante
Punkte als erledigt.

*Fertig:* beide Dateien gelesen, Glossar angewendet.

## 4. Sprecher zuordnen

Je `Speaker` eine kurze Textprobe mit Zeitstempel zeigen, die die Person
verrät (Anrede, Rolle, Bezug); der User nennt die Person. Eine Person ist oft
auf mehrere Speaker verteilt, auch der User selbst. Seine eigenen Aussagen
werden als solche gekennzeichnet - sie sind sein Wissen, kein Feedback der
anderen.

*Fertig:* jeder Speaker ist bestätigt oder bleibt als „unbekannt" stehen.

## 5. Gruppieren

- **Chronologisch** bei Ablauf-Calls: Tabelle `Zeit | Thema`.
- **Thematisch** bei Diskussions-Calls, die zwischen Themen springen.

Je Gruppe kurz zusammenfassen und trennen: **bei mir / beim Gegenüber / Info**.
Privates fällt weg. Widersprüche und nicht Entschiedenes kommen als Frage an
den User; offen bleibt offen.

*Fertig:* jede Stelle des Transkripts mit Inhalt gehört zu einer Gruppe.

## 6. Tasks suchen

Je Gruppe gezielt in Kanboard suchen (`search`), mit dem gemeinten Namen und
den Fehlerkennungen aus dem Glossar, nur offene Tasks.

*Fertig:* zu jeder Gruppe steht ein Task oder „keiner".

## 7. Entscheiden

Gruppe für Gruppe eine nummerierte Tabelle `Nr | Punkt | Task | Vorschlag`.
Default-Vorschlag ist **„nichts"**; eine Handlung nur, wenn der Punkt eine
eigene Zusage oder eine offene Aufgabe ist. Wartet ein Punkt auf Termin oder
Feedback Dritter, gehört er ins Protokoll statt in einen Task. Der User
antwortet kompakt („1 ja, 2 nichts, 3 …") und streicht, was nicht ins
Protokoll soll.

Jede Entscheidung **sofort** schreiben: in den Task (Beschreibung, Abschnitt
„Stand Call <wer> (<Datum>)", dazu „Offen" und Handoff) oder in eine
Protokolldatei in `.tmp/`.

*Fertig:* jede Nummer ist entschieden und geschrieben; der abgestimmte Stand
liegt in Task oder Datei.

## 8. Protokoll und Mails

Das Protokoll entsteht aus dem abgestimmten Stand aus Schritt 7, nicht neu aus
dem Transkript. Texten über `mail-as-me`, je Thema eine eigene Mail, auch an
dieselbe Person; zuerst das Protokoll, danach Mails an Dritte. **Versand nur
auf Go.** Fehlt die Adresse eines externen Teilnehmers, geht die Mail an die
Kontaktperson mit der Bitte um Weiterleitung; neue Adressen in die
swaks-Kontakte aufnehmen. Die gesendete Protokoll-Mail als `.eml` aus
„Gesendet" an den Task hängen.

*Fertig:* jede in Schritt 2 vereinbarte Mail ist versendet oder als Entwurf
abgelegt.

## 9. Kimai

Den Call-Beginn beim User erfragen: die Aufnahmezeit in Sally weicht davon ab.
Projekt und Aktivität erfragen, wenn kein früherer Eintrag zum selben Thema
sie vorgibt. Call und Nachbearbeitung als getrennte Einträge.

*Fertig:* beide Einträge gebucht.

## 10. Abschluss

Liste ausgeben:

- **Erledigt** - Tasks, Mails, Buchungen
- **Wartet auf** - wen, mit was
- **Offen** - was der User noch selbst tut

Neue Fehlerkennungen gesammelt als Glossar-Vorschlag; kommt das Wort auch
allgemein vor (ein Vorname, ein Alltagswort), mit `nur bei`. Nach Freigabe
eintragen. Zum Schluss Transkript und Downloads aus `.tmp/` löschen.

*Fertig:* Liste ausgegeben, Glossar entschieden, `.tmp/` ohne Downloads der
Aufnahme.

## Übergabe an eine andere Session

Muss die Review in einer anderen Session weiterlaufen, den abgestimmten Stand
in den Task schreiben und im Handoff je Ergebnis den Stand nennen:
**abgestimmt / Entwurf / versendet**. Offene Schritte als „entwerfen und
abstimmen" formulieren; versendet wird erst auf Go in der Folgesession.
