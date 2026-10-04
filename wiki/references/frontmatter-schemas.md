# Entity-Templates

Vorlagen für alle Wiki-Entity-Typen. Beim Anlegen neuer Entities diese Templates verwenden.

**Inhalt:** server · service · access · site · procedure · Pflichtfelder pro Typ · Optionale Vertrauensfelder (`verified`, `stale_after`, Abweichungen zur OKF-Referenz)

Der Abschnitt `## Quellen` in den Vorlagen ist **optional**: er nimmt nur echte
Rohquellen auf - die Datei unter `raw/`, ein externes Dokument, ein Ticket. Gibt
es keine, fällt er ersatzlos weg. Keine Liste der eigenen Sessions und keine
Chronologie; dafür gibt es git.

## server

```yaml
---
date: YYYY-MM-DD
tags: [server-infra, <kunde-slug>]
type: server
status: active | inactive | standby
hostname: <FQDN>
ip: <primary IP oder Liste>
os: <OS und Version, z.B. "FreeBSD 14.4">
location: "[[site-slug]]"
kunde: <Kundenname>
roles: [gateway, webserver, jailer, mailserver, dns, database, builder, standby]
---

# <hostname>

<Kurzbeschreibung der Rolle>

## Rollen

- <Rolle 1>: <Details>
- <Rolle 2>: <Details>

## Jail-System

<ezjail | iocage | keines> — <Liste der Jails mit Kurzbeschreibung>

## Besonderheiten

<Server-spezifische Konfiguration, z.B. CARP, spezielle Firewall-Regeln>

## Verwandte Entities

- Service: [[service-slug]]
- Access: [[access-slug]]
- Site: [[site-slug]]

## Quellen

- Originaldoku: `raw/articles/<quelldatei>`
```

## service

```yaml
---
date: YYYY-MM-DD
tags: [server-infra, <kunde-slug>]
type: service
status: active | inactive
runs-on: "[[server-slug]]"
port: <Nummer oder Liste>
version: <String>
kunde: <Kundenname>
dependencies: ["[[andere-service]]"]
---

# <Service-Name> auf [[server-slug]]

<Kurzbeschreibung>

## Konfiguration

- Config-Pfad: <Pfad>
- <weitere Konfigurationsdetails>

## Besonderheiten

<Service-spezifische Details>

## Quellen

- Originaldoku: `raw/articles/<quelldatei>`
```

## access

```yaml
---
date: YYYY-MM-DD
tags: [server-infra, access]
type: access
status: active
target: "[[server-slug]]"
method: ssh | vpn | jail-exec
kunde: <Kundenname>
---

# Zugriff auf [[server-slug]]

## SSH

\`\`\`bash
sudo ssh -C root@<hostname>
\`\`\`

## Jail-Zugriff

<Falls Jails vorhanden: iocage exec / ezjail-Pfade>

## Besonderheiten

<Jump-Hosts, VPN-Voraussetzungen, sudo-Regeln>

## Quellen

- Originaldoku: `raw/articles/<quelldatei>`
```

## site

```yaml
---
date: YYYY-MM-DD
tags: [server-infra, <kunde-slug>]
type: site
status: active
location: <physischer Standort>
network-segments: [<VLAN/Subnetz-Liste>]
kunde: <Kundenname>
---

# Standort <Name>

<Kurzbeschreibung des Standorts>

## Netzwerk

| Segment | Beschreibung | Subnetz |
|---------|-------------|---------|
| <VLAN X> | <Zweck> | <IP-Range> |

## Server an diesem Standort

- [[server-slug-1]]
- [[server-slug-2]]

## Quellen

- Originaldoku: `raw/articles/<quelldatei>`
```

## procedure

```yaml
---
date: YYYY-MM-DD
tags: [server-infra, <domain-tag>]
type: procedure
status: active
applies-to: ["[[server-oder-service-slug]]"]
kunde: alle | <spezifischer Kunde>
---

# <Procedure-Name>

<Kurzbeschreibung: Wann und warum diese Procedure anwenden>

## Voraussetzungen

- <Voraussetzung 1>

## Schritte

1. <Schritt 1>
2. <Schritt 2>

## Erwartete Ausgabe

<Was nach erfolgreicher Ausführung zu sehen ist>

## Fallstricke

<Bekannte Probleme, häufige Fehler>

## Quellen

- Originaldoku: `raw/articles/<quelldatei>`
```

## Pflichtfelder pro Typ

| Feld | server | service | access | site | procedure |
|------|--------|---------|--------|------|-----------|
| date | x | x | x | x | x |
| tags | x | x | x | x | x |
| type | x | x | x | x | x |
| status | x | x | x | x | x |
| kunde | x | x | x | x | x |
| hostname | x | | | | |
| ip | x | | | | |
| os | x | | | | |
| location | x | | | x | |
| roles | x | | | | |
| runs-on | | x | | | |
| port | | x | | | |
| target | | | x | | |
| method | | | x | | |
| network-segments | | | | x | |
| applies-to | | | | | x |

## Optionale Vertrauensfelder

Zwei Felder darf jede Entity jedes Typs zusätzlich tragen. Beide sind
**optional** — der Lint prüft nur, was dasteht, und verlangt nie, dass es
dasteht. Uebernommen aus dem Open Knowledge Format 0.2, dort aber verschachtelt;
hier flach gehalten, weil der Frontmatter-Parser des Lints nur flaches YAML
liest und die Felder so greppbar bleiben.

### verified

Wer den Inhalt wann an einem echten System nachgeprüft hat. Bisher stand das im
Fließtext („Verifiziert 2026-09-06 auf [[fry-azedo-at]]"); im Frontmatter ist
es auffindbar.

```yaml
verified: ["human:mranner@2026-09-06", "claude-opus-5@2026-09-14"]
```

Format je Eintrag: `<akteur>@<YYYY-MM-DD>`. Akteur ist `human:<kuerzel>` für
einen Menschen, `process:<name>` für einen automatisierten Lauf, sonst der
Modell- bzw. Werkzeugname. Der Unterschied trägt die Aussage: was ein Mensch
bestätigt hat, wiegt schwerer als was ein Agent behauptet.

```
grep -rl "verified:.*human:" wiki/       # menschlich geprüft
grep -rL "verified:" wiki/procedures/    # nie nachgeprüft
```

Das `date`-Feld bleibt davon unberührt: es sagt, wann jemand die Datei
geschrieben hat, nicht wann der Inhalt zuletzt gestimmt hat.

### stale_after

Datum, ab dem der Inhalt als überholt gilt — für Wissen, das an einen Stand
gebunden ist: Paketversionen, IP-Zuordnungen, Zertifikatslaufzeiten.

```yaml
stale_after: 2027-01-31
```

Der Lint warnt ab diesem Datum. Ohne das Feld verfällt eine Entity nie; es
gehört nur dorthin, wo ein Ablauf absehbar ist, nicht in jeden Artikel.

### Abweichungen zur OKF-Referenz

Beide Felder stammen aus dem Open Knowledge Format 0.2
(`GoogleCloudPlatform/open-knowledge-format` — die Fassung unter `okf/` in
`knowledge-catalog` ist ein eingefrorener Snapshot). Wir weichen an zwei
Stellen bewusst ab; wer je exportiert, muss beides umsetzen:

| Punkt | OKF 0.2 | Hier |
|---|---|---|
| `stale_after` | ISO-8601-Zeitstempel **mit UTC-Offset**; ein reines Datum wird von der Referenz-Implementierung ignoriert, weil es in jeder Zeitzone einen anderen Moment meint | reines Datum `YYYY-MM-DD` — Infra-Wissen läuft über Monate ab, nicht über Stunden |
| `verified` | Liste von Mappings `{by, at}`, eine einzelne Map auch ohne Listen-Strich | flache Liste `"<akteur>@<datum>"`, weil der Frontmatter-Parser des Lints nur flaches YAML liest |

Die Akteur-Konvention (`human:<id>`, `process:<id>`, sonst Werkzeugname) ist
dieselbe, ebenso die daraus abgeleiteten Vertrauensstufen: kein `verified` =
ungeprüft, nur Maschinen-Akteure = maschinell bestätigt, mindestens ein
`human:` = menschlich geprüft.
