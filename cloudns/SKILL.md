---
name: cloudns
description: >
  DNS-Records bei ClouDNS lesen und setzen: Records einer Zone auflisten,
  anlegen, aendern, loeschen, dazu die autoritative Gegenprobe gegen die
  Nameserver der Zone. Ebenso die ganze Zone im BIND-Format sichern und
  zurueckspielen, die SOA-Werte samt Serial lesen und den DNSSEC-Status mit
  den DS-Records abfragen. Zonen des Accounts lassen sich auflisten; Zonen
  anlegen oder loeschen sowie DNSSEC schalten kann dieser Skill nicht.
  Nutze diesen Skill wenn eine Zone bei ClouDNS liegt - erkennbar an
  Nameservern auf cloudns.net oder an Vanity-Nameservern, die dorthin
  aufloesen. Auch bei "setz den CNAME", "trag den A-Record ein", "welche
  Records hat die Zone", "sichere die Zone bevor wir umstellen", "exportier
  mir die Zone", "welchen Serial hat die Zone", "ist DNSSEC aktiv",
  "ClouDNS". Nicht zustaendig fuer Zonen auf eigenen BIND-Servern oder bei
  Hetzner - dort gilt die jeweilige Wiki-Procedure. Trigger: /cloudns.
---
# cloudns -- DNS-Records bei ClouDNS

Verwaltet **Records** ueber die ClouDNS-HTTP-API. Lesen ist der Standard,
Schreiben passiert erst mit `--commit`: ohne das Flag zeigt jeder Schreibbefehl
nur den Bestand und die geplante Aenderung.

**Aufruf:** `python3 "$SKILL_DIR/cloudns" <subcommand> [optionen]`

`$SKILL_DIR` ist das Verzeichnis dieser SKILL.md. Das Script ist stdlib-only
(`urllib`), fuer die Gegenprobe wird `dig` gebraucht.

## Config

Angelegt wird sie mit `cloudns setup` - der Befehl fragt die ID-Variante ab,
liest das Passwort verdeckt (nie ueber die Kommandozeile, nie in der
Shell-History), schreibt `~/.claude/cloudns.json` mit Rechten 0600 und prueft
den Zugang gleich gegen die API. Eine bestehende Config wird nur mit `--force`
ueberschrieben. Der Aufruf braucht ein Terminal - aus einer Claude-Session
heraus also als `! python3 ~/.claude/skills/cloudns/cloudns setup`.

Von Hand geht es auch; Vorlage `cloudns.example.json`:

```json
{
  "auth-id": "12345",
  "auth-password": "..."
}
```

Genau **eine** der drei ID-Varianten setzen - die API unterscheidet sie:

| Schluessel | Wofuer |
|---|---|
| `auth-id` | Haupt-API-User, numerisch |
| `sub-auth-id` | Sub-User, numerisch |
| `sub-auth-user` | Sub-User, als Name |

Statt `auth-password` geht `auth-password-env` mit dem Namen einer
Umgebungsvariablen. Ein anderer Pfad kommt aus `CLOUDNS_CONFIG`.

**IP-Whitelist beachten:** ClouDNS erlaubt pro API-User eine Liste zugelassener
Quell-IPs. Steht dort etwas und der Runner ist nicht dabei, meldet die API
`Invalid authentication, incorrect auth-id or auth-password` - also dieselbe
Meldung wie bei einem falschen Passwort. Vor der Fehlersuche am Passwort
deshalb `check-auth` laufen lassen und die Whitelist ansehen: der Befehl nennt
den benutzten Config-Pfad und die gewaehlte ID-Variante, das Passwort nicht.

Mehrere ClouDNS-Accounts kennt der Skill nicht - die Config traegt genau einen.

## Subcommands

```bash
cloudns setup [--force]                # Config interaktiv anlegen
cloudns check-auth                     # Zugang testen
cloudns list-zones [--search <text>]   # Zonen des Accounts
cloudns list <zone> [--host <h>] [--type <t>]
cloudns add    <zone> --host <h> --type <t> --record <wert> [--ttl <n>] [--priority <n>] [--commit]
cloudns modify <zone> --id <id> [--host <h>] [--record <wert>] [--ttl <n>] [--commit]
cloudns delete <zone> --id <id> [--commit]
cloudns export <zone> [--output <datei>]
cloudns import <zone> --file <datei> [--format bind|tinydns] [--delete-existing] [--commit]
cloudns soa    <zone>
cloudns dnssec <zone>
cloudns verify <zone> [--host <h>] [--type <t>]
```

Der Hostteil steht **ohne** Zone: `--host elternportal` fuer
`elternportal.example.at`. Die Zonenwurzel ist `--host ''`.

Beispiel - CNAME auf einen externen Hoster legen:

```bash
python3 "$SKILL_DIR/cloudns" list example.at --host elternportal
python3 "$SKILL_DIR/cloudns" add example.at --host elternportal \
    --type CNAME --record ziel.example.net            # Dry-Run
python3 "$SKILL_DIR/cloudns" add example.at --host elternportal \
    --type CNAME --record ziel.example.net --commit   # setzt und prueft nach
```

## Sichern und zurueckspielen

`export` holt die Zone im BIND-Format - ohne `--output` nach stdout, sonst in
eine Datei. Das ist die naheliegende Sicherung **vor** jeder groesseren
Aenderung und zugleich der lesbarere Gesamtueberblick, den eine Tabelle mit
Dutzenden Zeilen nicht ersetzt:

```bash
python3 "$SKILL_DIR/cloudns" export example.at --output .tmp/example.at.bind
```

`import` spielt eine solche Datei zurueck. Ohne `--commit` zeigt der Befehl nur
Herkunft, Zeilenzahl und die ersten 20 Records.

**Die exportierte Datei enthaelt den kompletten DNS-Bestand einer Kundenzone**
(DKIM-Schluessel, Verifizierungs-Tokens, interne Namen). Sie gehoert ins
Projekt-`.tmp/`, nicht ins Repo und nicht an ein Ticket.

Zwei Punkte zu `import`:

- **`--delete-existing` loescht zuerst alle Records der Zone.** Der Dry-Run
  nennt die Zahl der betroffenen Records; ohne das Flag wird nur ergaenzt.
- **Ab 100 Records laeuft der Import als Hintergrund-Job.** Der Aufruf meldet
  dann Erfolg, waehrend die Zone noch nicht vollstaendig ist - der Bestand
  direkt danach taeuscht. Der Skill weist darauf hin, gegengeprueft wird ueber
  einen erneuten `list`.

## SOA und DNSSEC

`soa` zeigt Serial, Primary-NS, Admin-Mail sowie Refresh, Retry, Expire und
Default-TTL. Der Serial belegt, dass eine Aenderung wirklich in der Zone steht.

`dnssec` nennt, ob DNSSEC fuer die Zone verfuegbar ist, und gibt die
DS-Records aus. Ist DNSSEC nicht aktiv, antwortet die API mit `status=Failed`
und `The DNSSEC is not active` - das ist die Auskunft und kein Fehler, der
Skill gibt sie als solche aus statt abzubrechen.

Beides ist read-only: DNSSEC aktivieren oder abschalten kann der Skill nicht.

## Guard-Rails

- **Dry-Run ist der Default.** `add`, `modify` und `delete` zeigen ohne
  `--commit` den Bestand und die geplante Aenderung, schreiben aber nichts.
- **CNAME-Kollision.** Ein CNAME darf neben keinem anderen Record desselben
  Namens stehen (RFC 1034). `add` bricht ab, wenn fuer den Namen schon etwas
  existiert oder ein CNAME angelegt werden soll, wo bereits Records liegen.
- **TTL.** ClouDNS nimmt nur feste Werte (60, 300, 900, 1800, 3600, 21600,
  43200, 86400, 172800, 259200, 604800, 1209600, 2592000). Ein anderer Wert
  wird vorab abgefangen, weil die API sonst nur `Invalid TTL` meldet, ohne die
  erlaubten Werte zu nennen.
- **Trailing dot.** Bei CNAME, MX, NS, PTR, SRV und ALIAS wird ein
  abschliessender Punkt entfernt und das gemeldet. ClouDNS speichert den
  Zielwert ohne Punkt; mit Punkt liefe der Name ins Leere.
- **Gegenprobe nach jedem Schreibvorgang.** Nach `add` und `modify` liest der
  Skill den Bestand zurueck und fragt den Namen bei **allen** Nameservern der
  Zone ab. Der lokale Resolver taugt dafuer nicht: er haelt das negative
  Ergebnis bis zum Ablauf der Negative-Caching-TTL fest und zeigt einen frisch
  angelegten Record noch nicht an.

## Fallstricke der API

- **Fehler kommen mit HTTP 200.** Die API antwortet auf einen abgelehnten
  Aufruf mit Status 200 und `{"status":"Failed", ...}` im Body. Wer nur den
  HTTP-Code prueft, haelt jeden Fehlschlag fuer einen Erfolg.
- **Eine leere Zone liefert `[]`, keine leere Map.** `records.json` gibt
  sonst ein Objekt zurueck, dessen Schluessel die Record-IDs sind - bei null
  Treffern wechselt der Typ. Der Skill faengt das ab.
- **Der Aenderungs-Endpoint heisst `mod-record.json`**, nicht
  `modify-record.json`. Der naheliegende Name laeuft in einen 404.
- **Prioritaet ist ein eigenes Feld.** Bei MX und SRV steht sie nicht im
  Zielwert, sondern in `priority`; die Liste zeigt sie dem Wert vorangestellt.
