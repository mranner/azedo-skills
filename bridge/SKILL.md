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
| `ack <msg-id>` | Quittung für eine empfangene Nachricht formen |

## Das Problem, das der Handshake löst

`SendMessage` weckt die Gegenseite nur auf. Es gibt keine Zustellbestätigung, und
ob die andere Session zurückschreibt, ist eine Entscheidung ihres Modells - ein
blanker Text wird meist gar nicht als Antwortaufforderung gelesen. Wer eine
Nachricht abschickt, weiß danach schlicht nicht, ob sie angekommen ist.

Deshalb trägt **die Nachricht selbst** die Anweisung zur Quittung. Das ist der
Kern: die Gegenseite braucht diesen Skill nicht installiert zu haben, sie muss nur
lesen können. Ein Protokoll, das in der Konfiguration beider Seiten liegen müsste,
würde genau dann versagen, wenn man es braucht - bei einer fremden Maschine.

## Das Protokoll

Drei Zeilenformen, mehr nicht:

```
[bridge msg=<id> from=bridge:session_... reply=ack]   Nachricht, Quittung erbeten
[bridge ack=<id>]                                     Empfang bestätigt
[bridge done=<id>] <Ergebnis>                         Aufgabe erledigt
```

`ack` und `done` sind getrennt, weil sie verschiedene Fragen beantworten: „ist es
angekommen" und „ist es erledigt". Wer beides in eine Quittung legt, wartet bei
einer langen Aufgabe minutenlang und weiß nicht, ob die Nachricht überhaupt
zugestellt wurde.

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

Die Quittungszeile formt auch `bridge ack <msg-id>` bzw.
`bridge ack <msg-id> --done "<Ergebnis>"`; nötig ist das Script dafür nicht.

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

Die Adressierung über den Anzeigenamen sieht naheliegend aus und trägt nicht:

- **Anzeigenamen sind instabil.** Sie werden bridge-seitig vergeben und ändern sich
  im laufenden Betrieb. Dieselbe Session hieß am 2026-08-28 innerhalb einer Stunde
  erst `kappa-azedo-local-effervescent-wave`, dann `Remote control session name` -
  bei gleichbleibender ID.
- **Der Name, unter dem sich eine Session selbst kennt, ist von außen nicht
  adressierbar.** `SendMessage` an einen solchen Namen antwortet mit
  „No agent named '…' is reachable."
- **Refs aus `ListAgents` (`[7ae82d]`) gelten nur innerhalb einer Auflistung**, nicht
  als dauerhafte Adresse.

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
Abhilfe: Remote Control aktivieren, dann erneut aufrufen.

Findet das Script im ganzen Prozessbaum keine Session-Datei, läuft der Aufruf
vermutlich außerhalb einer Claude-Code-Session; Exit-Code 1.

## Einbahnstrassen - gebridgt ist nicht symmetrisch

Ob eine Session **senden** kann und ob sie **erreichbar** ist, sind zwei
verschiedene Dinge. Eine Session ohne verbundenes Remote Control kann eine
Nachricht beantworten und quittieren; eine Adresse hat sie aber nicht, und ein
Gespraech von dort aus verlaeuft im Sand:

- Der Versand meldet in dem Fall `one-way`. Das ist kein Fehler, sondern die
  Ansage, dass es keinen Rueckweg gibt
- `who` auf der anderen Seite liefert dann keine `address`, sondern den Hinweis,
  dass die Session nicht gebridgt ist

Praktisch heisst das: **die gebridgte Seite muss das Gespraech eroeffnen.** Sie
gibt ihre Adresse im Kopf mit, und daran haengt die Gegenseite ihre Quittung.
Umgekehrt kaeme die Antwort nirgends an. Aufgefallen beim ersten echten Testlauf
(2026-09-17): `ack` und `done` kamen sauber zurueck, obwohl die antwortende
Session selbst nicht adressierbar war - genau deshalb steht die Rueckadresse im
Nachrichtentext und nicht nur im Transport.

Erkennbar ist die Richtung vorher nicht: `ListAgents` fuehrt beide Sorten gleich
auf. Wer wissen will, ob eine Session ansprechbar ist, laesst sich dort `/bridge who`
aufrufen - oder schickt eine Nachricht und wertet das Ausbleiben der Quittung aus.

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
