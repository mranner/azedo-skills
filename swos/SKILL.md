# swos -- MikroTik SwOS read-only Abfrage

Fragt MikroTik-**SwOS**-Switches (CSS-Serie und RB260/SwOS-Lite) read-only ab und
dekodiert die SwOS-Blobs in lesbare Tabellen: System-Info, VLAN-Mitglieder,
Portbelegung (PVID/PoE) und FDB (MAC→Port). **Stufe 1 = read-only** (kein Schreibzugriff).

**Aufruf:** `python3 "$SKILL_DIR/swos" <subcommand> [ziel] [optionen]`

`$SKILL_DIR` ist das Verzeichnis dieser SKILL.md. Das Script ist stdlib-only
(`urllib`, kein `requests`), lauffaehig auf FreeBSD und Linux.

## Architektur: ein Decoder, drei Transporte

Die Decode-Logik ist ueberall gleich, nur der Zugriff unterscheidet sich:

- **A) direct** -- `urllib` HTTP-Digest direkt auf die Switch-IP (Runner routbar, z.B. Buero).
- **B) ssh-curl** -- `curl --digest` auf einem Jump-Host (interne Switches, nur ueber Gateway
  erreichbar). Passwoerter mit `$` werden korrekt behandelt (Script via STDIN an `sh`, kein
  `!`-Escaping noetig).
- **C) swb** -- offline aus einem `.swb`-Backup (`strings` + Decoder), gleiche Views.

## Vier SwOS-Feld-Dialekte

SwOS serialisiert je nach Modell/Firmware unterschiedlich. Der Dialekt wird aus `sys.b`
**autodetektiert** (nicht am ersten Key -- Live-Reihenfolge weicht vom Backup ab):

| Dialekt | Modell | Keys | VLAN-Format | PVID | PoE |
|---|---|---|---|---|---|
| `css326`     | CSS326-24G-2S+          | mnemonisch (`id,cip,brd,…`) | `{nm,mbr,vid}` | `fwd.b dvid[]` | — |
| `css610_new` | CSS610-8P-2S+ (neue FW) | numerisch `i0x`             | `{i01,i02}`   | `fwd.b i18[]`  | `poe.b i04[]` |
| `css610_old` | CSS610-8P-2S+ (alte FW) | Einzelbuchstaben (`F,J,B,C`)| `{B,C}`       | `fwd.b Y[]`    | `poe.b E[]` |
| `swos_lite`  | CSS106 / RB260GS       | mnemonisch (`id,ip,sip,…`)  | `{vid,prt[]}` | `fwd.b dvid[]` | (offen, s.u.) |

VLAN-Namen kommen aus dem Geraet (`vlan.b nm`, nur css326), Modell aus `brd`/`i07` --
nichts wird hartcodiert. IP=little-endian hex, Identity/Version/Modell/Serial=hex-ASCII.

## Ziel angeben

Jeder View-Befehl nimmt genau ein Ziel:

- **Inventory-Name:** `swos sys swvs1` -- aufgeloest ueber `inventory.json` (IP, Modus, Jump, Credential).
- **Ad-hoc live:** `swos sys --ip 192.168.201.215 --mode direct [--password '' --user admin]`
  bzw. `--mode ssh-curl --jump gateway.example.at --password …`.
- **Offline:** `swos sys --swb /pfad/backup.swb`.

`--json` liefert bei jedem View die strukturierte Form statt der Tabelle.

## Subcommands

```bash
swos list                         # Inventory anzeigen
swos sys    <ziel>                # System-Info (Modell, IP, MAC, Serial, Temp, …)
swos vlan   <ziel>                # VLAN-Mitglieder (id, Name, Ports)
swos ports  <ziel>                # Portbelegung: PVID (untagged VLAN) + PoE-Modus
swos hosts  <ziel>                # FDB: MAC -> Port (live; im Backup leer)
swos all    <ziel>                # alle vier Views
swos raw    <ziel> <endpoint>     # roher Endpoint-Blob als JSON (Debug), z.B. sys.b, !dhost.b
swos backup <ziel> [--output <pfad>]  # Live-Backup ziehen (GET /backup.swb), Default <ziel>.swb
```

Beispiele:

```bash
python3 "$SKILL_DIR/swos" all swvs1                      # ssh-curl via gatekeeper
python3 "$SKILL_DIR/swos" ports css610test              # direct
python3 "$SKILL_DIR/swos" vlan --swb ~/.tmp/swb/swvs1.swb
python3 "$SKILL_DIR/swos" raw css326test '!dhost.b'
python3 "$SKILL_DIR/swos" backup swvs1 --output ~/.tmp/swvs1.swb
```

`backup` holt den Endpoint `/backup.swb` **roh** (keine Blob-Parse, direkter Byte-Dump) —
denselben `.swb`-Container, den auch der SwOS-Web-UI-Backup-Knopf liefert und den `--swb`
offline dekodiert. Funktioniert mit Inventory-Namen, `--ip/--mode` oder Ad-hoc-Zielen; **nicht**
mit `--swb` (ein Backup ist kein Live-Ziel). **Achtung:** Die `.swb`-Datei enthaelt das
Digest-Passwort hex-kodiert (`.pwd.b`) — nicht unbedacht weitergeben oder an Tickets anhaengen.

## Inventory-Config

`inventory.json` (neben dem Script, **gitignored**) oder Pfad via `SWOS_INVENTORY`,
alternativ `~/.config/swos-inventory.json`. Vorlage: `inventory.example.json`.

```json
{
  "defaults": { "user": "admin" },
  "credentials": {
    "site1": { "user": "admin", "password_env": "SWOS_PW_SITE1" }
  },
  "switches": {
    "css610test": { "ip": "192.168.201.215", "mode": "direct", "password": "" },
    "swvs1": { "ip": "10.1.13.4", "mode": "ssh-curl",
               "jump": "gatekeeper.example.com", "cred": "site1" }
  }
}
```

**Credential-Aufloesung** pro Switch: `password` (inline, z.B. `""` fuer die Buero-Switches)
ODER `cred: "<name>"` -> `credentials.<name>` mit `password` / `password_env` / `password_file`.
**Passwoerter nie ins Repo einchecken** -- `password_env` (Umgebungsvariable) oder
`password_file` verwenden. Beispiel site1: `export SWOS_PW_SITE1='…'` vor dem Aufruf.

## Grenzen / offen (Stufe 2 und Nacharbeit)

- **read-only.** Keine Writes (VLAN/PVID/PoE/Mgmt-IP). Stufe 2 erst nach Verifikation des
  POST-Formats aus `engine.js`, jeder Write mit Read-back-Verify. `backup` (GET `/backup.swb`)
  ist reines Lesen und faellt weiterhin unter Stufe 1 — keine Config-Aenderung am Switch.
- **swos_lite-PoE** (CSS106-1G-4P-1S): `poe.b` fehlt, PoE-Info steckt in `link.b` (`poe`/`poes`);
  die genaue Semantik von `poes` ist noch nicht gegen `engine.js` verifiziert und wird bewusst
  **nicht** als Modus ausgegeben (nicht raten).
- **Link/Speed** wird noch nicht dekodiert (Speed-Codes modellabhaengig, unsicher).
- **ssh-curl** macht pro Endpoint eine SSH-Session; `all` = mehrere Sessions (funktioniert,
  aber nicht gebuendelt).
- **Dialekt-Fehlerkennung bei frischen `.swb`-Backups (CSS610):** Ein per `backup` gezogenes
  `.swb` eines CSS610 mit `css610_new`-Live-Dialekt wird von `detect_dialect()` teils als
  `css610_old` erkannt (Backup-`sys.b` enthaelt sowohl `F`- als auch `J`-Keys, was aktuell fest
  als `css610_old`-Signatur gilt) — Modell/Version/MAC/Serial/Portnamen fallen dann auf
  Fallback-Werte zurueck. VLAN/PVID/PoE bleiben korrekt (andere Felder). Live vs. `.swb` scheinen
  fuer denselben physischen Switch unterschiedliche Key-Dialekte zu verwenden; noch nicht
  gegen `engine.js` verifiziert, daher hier nur dokumentiert statt gefixt (2026-07-21,
  aufgefallen an `swbs02poe`/CR4369).

## Hinweise

- Fixture-Backups fuer Regressionstests: `gatekeeper.example.com:/archive/backups/switches`
  (naechtlich). Der Decoder liefert fuer `.swb` (C) und Live (`ssh-curl` B) dasselbe Ergebnis.
- Ausgabe ist bewusst lesbar (Tabellen); `--json` fuer maschinelle Weiterverarbeitung.
- Hintergrund/Erkenntnisse: Kanboard **CR4426** (Handoff), Memory `reference_swos_lite_endpoints`.
