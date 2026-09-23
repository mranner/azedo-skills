---
name: bridge
description: >
  Nachrichten zwischen Claude-Code-Sessions über Remote Control, mit einem
  rudimentären Handshake: eigene Session-Adresse ausgeben, erreichbare Sessions
  auflisten, eine Nachricht mit Empfangsquittung aufbauen und eine empfangene
  Nachricht quittieren. Trigger: /bridge.
allowed-tools: [Bash, SendMessage, ListAgents]
disable-model-invocation: true
---

# bridge -- zwischen Claude-Sessions reden, mit Quittung

**Aufruf:** `python3 "$SKILL_DIR/bridge" <befehl>`

`$SKILL_DIR` ist das Verzeichnis dieser SKILL.md. Das Script ist stdlib-only und
läuft auf FreeBSD, Linux und macOS.

| Befehl | Zweck |
|---|---|
| `who` | eigene Session: Name, cwd, PID, Session-ID, bridge-Adresse |
| `list` | erreichbare Sessions (kein Script-Befehl, siehe unten) |
| `send <ziel> <text>` | Nachrichtentext samt Handshake-Kopf bauen |
| `ack <msg-id> [...]` | Quittung (`ack`, `done`, `wait`) für empfangene Nachrichten formen |

## Das Problem, das der Handshake löst

`SendMessage` weckt die Gegenseite nur auf. Die Meldung `accepted by the server …
not confirmed read` (bzw. `delivery not confirmed`) kommt bei **jedem** Versand,
auch bei einem, der ankommt: sie betrifft die Annahme durch den Server, nicht das
Lesen, und ist kein Warnsignal. Ob die Gegenseite antwortet, entscheidet ihr
Modell - ein blanker Text wird meist nicht als Antwortaufforderung gelesen.
Klarheit bringen erst `ack` bzw. `done`.

Deshalb trägt **die Nachricht selbst** die Anweisung zur Quittung. Die Gegenseite
braucht diesen Skill nicht, sie muss nur lesen können - ein Protokoll in der
Konfiguration beider Seiten versagte genau bei einer fremden Maschine.

## Das Protokoll

Vier Zeilenformen, mehr nicht:

```
[bridge msg=<id> from=bridge:session_... reply=ack]   Nachricht, Quittung erbeten
[bridge ack=<id>]                                     Empfang bestätigt
[bridge done=<id>] <Ergebnis>                         Aufgabe erledigt
[bridge wait=<id>] <was fehlt>                        blockiert oder abgelehnt
```

`ack` und `done` sind getrennt, weil sie verschiedene Fragen beantworten: „ist es
angekommen" und „ist es erledigt". Wer beides in eine Quittung legt, wartet bei
einer langen Aufgabe minutenlang und weiß nicht, ob die Nachricht überhaupt
zugestellt wurde.

`done` heißt **erledigt** und nichts anderes. Fehlt eine Freigabe, eine Angabe
oder ein Recht, oder lehnt die Session die Aufgabe ab, lautet die Antwort
`wait` samt dem, was fehlt.

Der Kopf kennt neben `msg` und `from` diese Felder:

| Feld | Bedeutung |
|---|---|
| `reply=ack` | Default: `ack` sofort, `done` bzw. `wait` nach der Arbeit |
| `reply=none` | reine Info, keine Quittung |
| `reply=ack;done=objection` | `ack` sofort, `done` nur bei Einwand - „Antwort nur bei Einwand" |
| `topic=<CR/Stichwort>` | optional, wenn mehrere Themen parallel laufen |
| `decision=relayed` | die Nachricht reicht eine Entscheidung des Users der anderen Session weiter |

Mehrere Quittungen dürfen in **einer** Nachricht stehen, eine Zeile je id, jede am
Zeilenanfang:

```
[bridge ack=f0f4]
[bridge done=91c2] Dienst läuft.
```

Die `msg-id` sind vier Hex-Zeichen. Sie muss nicht global eindeutig sein, sondern
nur innerhalb der laufenden Unterhaltung unterscheidbar.

## Senden

```bash
python3 "$SKILL_DIR/bridge" send bridge:session_01Abc... "Prüf bitte, ob der Dienst läuft."
python3 "$SKILL_DIR/bridge" send bridge:session_01Abc... < nachricht.txt
```

Das Script baut nur den **Text**. Verschickt wird er danach mit dem Tool
`SendMessage` an dasselbe Ziel - auf den Versand hat ein Script keinen Zugriff.
Die ausgegebene `msg-id` merken, auf sie bezieht sich die Quittung.

Ohne Text-Argument kommt der Text von STDIN; das ist der Weg für mehrzeilige
Nachrichten, bei denen das Quoting sonst stört.

Optionen für die Kopffelder aus der Tabelle oben: `--reply none|ack|ack;done=objection`,
`--topic <CR/Stichwort>` und `--relayed` für `decision=relayed`. Der Fußtext der
Nachricht passt sich an `--reply` an. Den Wert `ack;done=objection` quoten, sonst
trennt die Shell am Semikolon.

Ist die eigene Session **nicht gebridgt**, bricht `send` ab, statt eine Nachricht
mit unbeantwortbarer Rückadresse zu bauen.

## Empfangen und quittieren

Kommt eine Nachricht mit `[bridge msg=<id> from=<adresse> reply=ack]` herein:

1. **Sofort** quittieren, vor jeder inhaltlichen Arbeit:
   `SendMessage(to="<adresse>", message="[bridge ack=<id>]")`
2. Die Aufgabe bearbeiten.
3. Das Ergebnis zurückschicken: `[bridge done=<id>] <Ergebnis>`

Schritt 1 zuerst - sonst hängt die andere Seite im Ungewissen, solange die Aufgabe
läuft, und das ist der Fall, für den das Ganze gebaut ist.

Ist die Aufgabe blockiert oder abgelehnt, lautet Schritt 3
`[bridge wait=<id>] <was fehlt>`, nicht `done`. Bei `reply=ack;done=objection`
entfällt Schritt 3, solange kein Einwand besteht; bei `reply=none` entfallen alle
Quittungen.

Die Quittungszeilen formt auch das Script: `bridge ack <msg-id> [<msg-id> …]`,
`bridge ack <msg-id> --done "<Ergebnis>"` bzw. `bridge ack <msg-id> --wait "<was fehlt>"`;
nötig ist es dafür nicht.

**Blockiertes ack:** Verweigert der Auto-Mode-Klassifikator den Versand der
Quittung, ersetzt das folgende `done` sie. Das `ack` einmal wiederholen oder im
`done` als eigene Zeile nachreichen - nicht öfter.

### Gegenfragen und Nachträge

Auch der Empfänger schickt Gegenfragen und Nachträge über `bridge send`, jede mit
eigener msg-id - nicht als formlosen Text. Sonst hat die Rückfrage keine Quittung
und der Absender weiß nicht, ob sie angekommen ist. Reine Infos gehen mit
`--reply none`.

### Nachricht ohne Kopf

Kommt eine Nachricht ohne `[bridge …]`-Kopf herein, mit `bridge send` antworten.
Der Kopf und der Fußtext schlagen der Gegenseite das Protokoll damit von selbst vor.

## Freigaben und Befunde

**Keine weitergereichte Freigabe** für einen Versand nach außen oder für
Irreversibles. Das Go des Users in Session A gilt nicht für Session B: der Absender
sagt seinem User, dass er das Go **in der anderen Session** geben muss. Andere
Entscheidungen, die eine Session weiterreicht, tragen `decision=relayed` im Kopf
(`bridge send --relayed`), damit die Gegenseite sie nicht für eine eigene hält.

**Befunde kennzeichnen:** Jede Aussage über einen Befund trägt „geprüft" (selbst
nachgesehen) oder „abgeleitet" (geschlossen, nicht nachgesehen). Über zwei
Sessions hinweg ist das sonst nicht mehr zu unterscheiden.

## Ein vollständiger Austausch

Der Ablauf am Stück, weil die Reihenfolge der springende Punkt ist. Session A ist
gebridgt und eröffnet, Session B arbeitet und meldet zurück.

**A baut den Text:**

```
$ python3 "$SKILL_DIR/bridge" send bridge:session_01Bbb... "Prüf bitte, ob der Dienst auf dem Testhost läuft."
msg-id: f0f4
Senden mit: SendMessage(to="bridge:session_01Bbb...", message=<Text unten>)

[bridge msg=f0f4 from=bridge:session_01Aaa... reply=ack]

Prüf bitte, ob der Dienst auf dem Testhost läuft.

Quittiere den Empfang als erste Aktion: SendMessage an "bridge:session_01Aaa..." mit
dem Text "[bridge ack=f0f4]". Erst danach die Aufgabe bearbeiten. Das Ergebnis kommt
spaeter als "[bridge done=f0f4] <Ergebnis>" an dieselbe Adresse.
```

**A verschickt ihn** mit `SendMessage(to="bridge:session_01Bbb...", message=<der Text>)`.

**B bekommt ihn** als `<cross-session-message>` und quittiert **zuerst**, ohne
irgendetwas anderes zu tun:

```
SendMessage(to="bridge:session_01Aaa...", message="[bridge ack=f0f4]")
```

Das `from`-Attribut des Wrappers taugt dafür nicht zwingend - bei einer nicht
gebridgten Gegenstelle steht dort `unknown`. Verwendet wird die Adresse aus dem
`from=` **im Nachrichtenkopf**.

**B arbeitet** und meldet danach das Ergebnis:

```
SendMessage(to="bridge:session_01Aaa...", message="[bridge done=f0f4] Dienst laeuft, seit 6 Tagen ohne Neustart.")
```

**A sieht** zwei getrennte Nachrichten: erst `[bridge ack=f0f4]` - ab da ist die
Zustellung geklärt - und später `[bridge done=f0f4] …` mit dem Ergebnis. Genau diese
Trennung ist der Zweck der Übung: ohne sie wäre die Zeit zwischen Absenden und
Ergebnis von einer toten Verbindung nicht zu unterscheiden.

## `list` -- erreichbare Sessions

Kein Script-Unterbefehl: die Peers stehen in keiner Datei, sondern kommen aus dem
Tool `ListAgents`. Bei `/bridge list` also `ListAgents` aufrufen und Name, Ref und
Status ausgeben.

**Die Namen und Refs von dort taugen nicht als dauerhafte Adresse** (siehe unten).
Für eine Session auf derselben Maschine reicht der Name; alles andere geht über die
bridge-Session-ID.

## Warum die bridge-Session-ID und nicht der Name

- **Anzeigenamen sind instabil.** Sie werden bridge-seitig vergeben und ändern
  sich im laufenden Betrieb, bei gleichbleibender ID.
- **Der Name, unter dem sich eine Session selbst kennt, ist von außen nicht
  adressierbar** (`No agent named '…' is reachable.`).
- **Refs aus `ListAgents` (`[7ae82d]`) gelten nur innerhalb einer Auflistung.**

Stabil ist allein die bridge-Session-ID. Sie steht weder in der `ListAgents`-Ausgabe
noch in der `SendMessage`-Dokumentation als Adressform - deshalb dieser Skill.

## Woher die Angaben kommen

Jede laufende Session schreibt `~/.claude/sessions/<pid>.json` mit `name`, `cwd`,
`sessionId` und - sofern gebridgt - `bridgeSessionId`.

Das Script sucht die **eigene** Datei über den Prozessbaum: von der eigenen PID
aufwärts über die jeweilige Eltern-PID, bis eine passende Datei gefunden ist. Das ist
der Grund, warum es auch dann stimmt, wenn mehrere Sessions gleichzeitig laufen -
eine Heuristik wie „die zuletzt geänderte Datei" erwischt in dem Fall gelegentlich
die falsche.

`sessionId` und `bridgeSessionId` sind zwei verschiedene Werte. Adressiert wird über
`bridgeSessionId`.

## Wenn keine Adresse herauskommt

Fehlt `bridgeSessionId`, ist die Session nicht gebridgt und von außen nicht
erreichbar - `who` sagt das ausdrücklich, statt eine leere Adresse auszugeben.
Abhilfe: in der betroffenen Session `/remote-control` aufrufen, danach steht die
Adresse.

Findet das Script im ganzen Prozessbaum keine Session-Datei, läuft der Aufruf
vermutlich außerhalb einer Claude-Code-Session; Exit-Code 1.

## Einbahnstraßen - gebridgt ist nicht symmetrisch

Ob eine Session **senden** kann und ob sie **erreichbar** ist, sind zwei
verschiedene Dinge. Eine Session ohne verbundenes Remote Control kann antworten
und quittieren, hat aber keine eigene Adresse:

- Ihr Versand meldet `one-way: Remote Control is not connected` - kein Fehler,
  sondern die Ansage, dass es keinen Rückweg gibt; steht nur im Tool-Ergebnis.
- `who` liefert dort keine `address`, sondern den Hinweis, dass die Session
  nicht gebridgt ist. Behoben wird es **auf der betroffenen Seite** mit
  `/remote-control`.

Praktisch heißt das: **die gebridgte Seite eröffnet das Gespräch.** Ihre Adresse
steht im Kopf, daran hängt die Gegenseite ihre Quittung - deshalb steht die
Rückadresse im Nachrichtentext und nicht nur im Transport.

`ListAgents` führt beide Sorten gleich auf. Ob eine Session ansprechbar ist, zeigt
dort `/bridge who` - oder das Ausbleiben der Quittung.

## Wenn die Quittung ausbleibt

`ListAgents` prüfen: `busy` heißt verzögert, die Session arbeitet noch an etwas
anderem. Fehlt die Zeile ganz, ist die Session weg. Danach **einmal** erneut senden,
dann melden statt still weiterzuprobieren.

Ein ausbleibender `ack` beweist nicht, dass die Nachricht nicht angekommen ist -
er beweist nur, dass keine Quittung zurückkam. Das bleibt die Grenze des Verfahrens:
der Handshake ist eine Konvention, kein Transportprotokoll.

## Was der Skill nicht kann

Die ID einer **fremden** Session ermitteln. Deren Datei liegt auf deren Maschine, nicht
hier. Der Weg dorthin bleibt manuell: dort `/bridge who` aufrufen und die Adresse
herüberreichen.
