# Compilation Guide

Regeln fuer das Kompilieren von Quellen zu Wiki-Entities.

## Grundprinzipien

1. **Source-first**: Jede Aussage im Wiki muss auf eine Quelle in `raw/` zurueckfuehrbar sein
2. **Keine Erfindungen**: Was nicht in der Quelle steht, wird nicht ins Wiki geschrieben
3. **Secrets filtern**: Passwoerter, Private Keys, API-Tokens durch `[siehe Passwortmanager]` ersetzen
4. **Immutable raw/**: Quelldateien in `raw/` werden nie veraendert

## Entity-Extraktion

Beim Lesen einer Quelle diese Entity-Typen identifizieren:

| Signal in der Quelle | Entity-Typ |
|----------------------|------------|
| Hostname, IP, OS-Version, Rollen | **server** |
| Dienst-Name, Port, Config-Pfad, Version | **service** |
| SSH-Befehl, sudo-Regel, Jail-Zugriff | **access** |
| Standort, VLAN, Subnetz, Netzwerk-Topologie | **site** |
| Schritt-fuer-Schritt-Anleitung, Workflow | **procedure** |

Eine Quelldatei kann mehrere Entities erzeugen. Typisch:
- Ein Server-Doc → 1 Server + 1-3 Services + 1 Access
- Ein Gateway-Doc → 1 Server + 3-5 Services + 1 Access + 1 Site

## Duplikat-Pruefung

Vor dem Anlegen eines neuen Entities:

1. Dateiname pruefen: `ls wiki/servers/<slug>.md`
2. Hostname/Service-Name im Index suchen
3. Wenn Entity existiert: bestehenden Artikel lesen, dann gezielt aktualisieren
4. Wenn Entity nicht existiert: neuen Artikel mit Template anlegen

## Cross-Referencing

### Wikilinks setzen

- Format: `[[slug]]` (ohne `.md`, ohne Pfad-Praefix)
- Minimum 3 Wikilinks pro Artikel
- Beim ersten Vorkommen eines referenzierten Entity im Text verlinken
- Nicht jeden Vorkommen verlinken — nur das erste

### Backlink-Audit (nach jedem neuen Artikel)

1. Dateiname und Titel des neuen Artikels notieren
2. `grep -rl "<hostname>" wiki/` oder `grep -rl "<service-name>" wiki/` ausfuehren
3. Jeden Treffer lesen und pruefen ob ein Wikilink ergaenzt werden sollte
4. Wikilink beim ersten Vorkommen im Text ergaenzen

### Typische Verlinkungsmuster

- Server → Services die darauf laufen, Access, Site
- Service → Server auf dem er laeuft, abhaengige Services
- Access → Ziel-Server
- Site → Server an diesem Standort
- Procedure → Server/Services auf die sie sich bezieht

## Widersprueche

Wenn eine neue Quelle bestehenden Wiki-Inhalten widerspricht:

1. Nicht still ueberschreiben
2. Beide Versionen dokumentieren mit Callout:
   ```
   > [!warning] Widerspruch
   > Quelle A sagt X, Quelle B sagt Y. Zu klaeren.
   ```
3. Beide betroffenen Artikel aktualisieren
4. In `log.md` notieren: `CONFLICT: <entity> — <beschreibung>`

## Index-Aktualisierung

Nach jedem Compile-Lauf:

1. `index.md` oeffnen
2. Neuen Entity in die passende Kunden-Sektion eintragen
3. Format: `- [[slug]] — <Kurzbeschreibung> (YYYY-MM-DD)`
4. Alphabetisch innerhalb der Sektion sortieren

## Compile-Checkliste

- [ ] Quelle vollstaendig gelesen
- [ ] Alle Entity-Typen identifiziert
- [ ] Duplikat-Pruefung durchgefuehrt
- [ ] Frontmatter vollstaendig (alle Pflichtfelder)
- [ ] Minimum 3 Wikilinks pro Artikel
- [ ] Secrets entfernt
- [ ] Backlink-Audit durchgefuehrt
- [ ] index.md aktualisiert
- [ ] log.md Eintrag geschrieben

## Einträge in `log.md`

**Neueste zuerst.** Ein neuer Eintrag kommt an den Anfang des heutigen
Tagesabschnitts, ein neuer Tag ganz nach oben unter den Dateikopf. Bestehende
Einträge bleiben, wie sie sind.

Die Richtung ist keine Geschmacksfrage: im azedo-Wiki wurde von Juli bis
September an beiden Enden geschrieben, weil sie nirgends festgelegt war. Es
entstanden zwei Journale in einer Datei - 19 Tage nur im oberen Lauf, 9 nur im
unteren, sieben Tage in beiden mit **verschiedenen** Einträgen. Wer nur ein Ende
las, sah die halbe Historie. Zusammengeführt am 2026-09-06.

Für `log.md` gelten die [Schreibregeln der SKILL.md](../SKILL.md#schreibregeln)
genauso wie für Artikel - insbesondere das Dichtegebot. Ein Eintrag beantwortet
drei Fragen und hört dann auf:

1. **Was hat sich geändert** (welche Artikel, welcher Gegenstand)
2. **Warum** (der Auslöser, in einem Satz)
3. **Was daraus folgt**, falls es nicht offensichtlich ist

Kein Absatz je Fundstück, keine Nacherzählung der Sitzung, keine Wiederholung
dessen, was ohnehin im Artikel steht - der Eintrag ist ein Zeiger, nicht die
Zusammenfassung. Richtwert: ein kurzer Absatz, nicht mehrere.

Was in einem Artikel keinen Platz findet, weil es den Aufnahmefilter nicht
besteht, gehört auch nicht ersatzweise nach `log.md`.
