# Entity-Templates

Vorlagen fuer alle Wiki-Entity-Typen. Beim Anlegen neuer Entities diese Templates verwenden.

Der Abschnitt `## Quellen` in den Vorlagen ist **optional**: er nimmt nur echte
Rohquellen auf - die Datei unter `raw/`, ein externes Dokument, ein Ticket. Gibt
es keine, faellt er ersatzlos weg. Keine Liste der eigenen Sessions und keine
Chronologie; dafuer gibt es git.

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

<Was nach erfolgreicher Ausfuehrung zu sehen ist>

## Fallstricke

<Bekannte Probleme, haeufige Fehler>

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
