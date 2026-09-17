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
