---
name: whoami
description: >
  Gibt aus, welche Claude-Session hier läuft: Name, Arbeitsverzeichnis und vor
  allem die bridge-Session-ID - die einzige stabile Adresse, unter der diese
  Session von einer anderen Maschine aus per SendMessage erreichbar ist.
  NUR auf ausdrücklichen Aufruf von /whoami laden. Nicht von selbst laden, auch
  nicht bei Fragen nach Session, Session-ID, Adresse oder Erreichbarkeit.
  Trigger: ausschließlich /whoami.
allowed-tools: [Bash]
disable-model-invocation: true
---

# whoami -- die eigene Session identifizieren

**Aufruf:** `python3 "$SKILL_DIR/whoami"`

`$SKILL_DIR` ist das Verzeichnis dieser SKILL.md. Das Script ist stdlib-only und
läuft auf FreeBSD, Linux und macOS.

```bash
python3 "$SKILL_DIR/whoami"          # Name, cwd, PID, Session-ID, Adresse
python3 "$SKILL_DIR/whoami" --id     # nur "bridge:session_..." zum Kopieren
python3 "$SKILL_DIR/whoami" --json   # zusätzlich der rohe Datensatz
```

Ausgabe des Standardaufrufs:

```json
{
  "name": "azedo-ai-5c",
  "cwd": "/home/mranner/azedo.ai",
  "pid": 35471,
  "session_id": "b895e484-1ac4-4115-a0f6-147aec3b6a87",
  "bridge_session_id": "session_01NtYtSaRns4GgRz2PbGJxri",
  "address": "bridge:session_01NtYtSaRns4GgRz2PbGJxri"
}
```

Wird der Skill gerufen, weil jemand die Session ansprechen will, ist `address` die
Antwort - das ist die Form, die `SendMessage` direkt akzeptiert. Die restlichen
Felder sind Kontext, damit erkennbar bleibt, um welche Session es geht.

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
erreichbar - das Script sagt das ausdrücklich, statt eine leere Adresse auszugeben.
Abhilfe: Remote Control aktivieren, dann erneut aufrufen.

Findet das Script im ganzen Prozessbaum keine Session-Datei, läuft der Aufruf
vermutlich außerhalb einer Claude-Code-Session; Exit-Code 1.

## Was der Skill nicht kann

Die ID einer **fremden** Session ermitteln. Deren Datei liegt auf deren Maschine, nicht
hier. Der Weg dorthin bleibt manuell: dort `/whoami` aufrufen und die Adresse
herüberreichen.
