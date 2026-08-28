---
name: swos
description: >
  MikroTik-SwOS-Switches (CSS-Serie und RB260/SwOS-Lite) abfragen und
  konfigurieren: System-Info, VLAN-Mitglieder, Portbelegung (PVID/PoE) und
  FDB (MAC zu Port). Stufe 1 ist read-only und Standard, Stufe 2 schreibt
  Port-, VLAN- und PoE-Einstellungen mit strengen Guard-Rails.
  Von selbst nur laden, wenn das Gerät eindeutig als SwOS-Switch benannt ist:
  "SwOS", "SwOS-Lite", "CSS106", "CSS326", "CSS610", "RB260" - oder ein Gerät,
  das im Infra-Wiki als SwOS-Switch geführt ist.
  Nicht von selbst laden bei den mehrdeutigen Nachbarbegriffen "MikroTik",
  "Switch", "VLAN", "PoE", "Port" oder "MAC-Adresse" - die meinen genauso oft
  RouterOS oder einen anderen Hersteller; dort auf den ausdrücklichen Aufruf
  warten.
  Trigger: /swos.
---
# swos -- MikroTik SwOS abfragen und konfigurieren

Fragt MikroTik-**SwOS**-Switches (CSS-Serie und RB260/SwOS-Lite) ab und dekodiert die
SwOS-Blobs in lesbare Tabellen: System-Info, VLAN-Mitglieder, Portbelegung (PVID/PoE) und
FDB (MAC→Port). **Stufe 1 = read-only** (Standard). **Stufe 2 = schreibend** umfasst 12 Port-/
VLAN-/PoE-Befehle mit strengen Guard-Rails — auf `css610_new` vollständig (poe.b/link.b/fwd.b/
vlan.b), auf `css326` alles außer PoE (link.b/fwd.b/vlan.b), auf `swos_lite` (CSS106) link.b/fwd.b
plus PoE-Out beim PoE-Modell (`poe`/`prio` liegen in link.b): portname, port-enable, autoneg,
duplex, speed, vlan-mode, vlan-receive, force-vlan-id, pvid, poe-out (CSS106) — sowie
`vlan-set`/`vlan-remove`/`vlan-clear` (dialekt-generisch). `vlan-set` nutzt auf css610_new/css326
ein Member-Bitmask (`--members`), auf CSS106 das Per-Port-Egress-Enum `prt`
(`--tagged`/`--untagged`, Rest = not-a-member). Siehe
Abschnitt „Schreiben".

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
| `css326`     | CSS326-24G-2S+          | mnemonisch (`id,cip,brd,…`) | `{nm,mbr,vid}` | `fwd.b dvid[]` | — (kein PoE) |
| `css610_new` | CSS610-8P-2S+ (neue FW) | numerisch `i0x`             | `{i01,i02}`   | `fwd.b i18[]`  | `poe.b i04[]` |
| `css610_old` | CSS610-8P-2S+ (alte FW) | Einzelbuchstaben (`F,J,B,C`)| `{B,C}`       | `fwd.b Y[]`    | `poe.b E[]` |
| `swos_lite`  | CSS106 / RB260GS       | mnemonisch (`id,ip,sip,…`)  | `{vid,prt[]}` | `fwd.b dvid[]` | `link.b poe[]` (nur `*-4P-*`) |

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
# Stufe 2 (schreibend): poe-out, poe-voltage, portname, port-enable, autoneg, duplex,
#   speed, vlan-mode, vlan-receive, pvid, vlan-set  -> siehe Abschnitt "Schreiben (Stufe 2)"
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

## Schreiben (Stufe 2) — `poe.b`, `link.b`, `fwd.b`, `vlan.b`

**Zwölf** Schreibbefehle sind freigegeben, live an `.215` (css610_new), `.214` (css326) und `.193`
(swos_lite/CSS106) verifiziert (ändern → Read-back → Restore). Format je Endpoint aus DevTools-/
HAR-Capture + `engine.js` hart abgeleitet (CR4426/CR4428), nie geraten. Nicht jeder Befehl gilt auf
jedem Dialekt — siehe „Verifizierte Schreib-Dialekte" und die Dialekt-Unterabschnitte:

```bash
swos poe-out     <ziel> --port <n> --to off|on|auto|calibr [--commit]  # PoE Out (css610 poe.b i01; CSS106 link.b poe, Enum off/auto/on/calibr, Ports 2-5)
swos poe-voltage <ziel> --port <n> --to auto|low|high    [--commit]   # Voltage Level (nur css610, poe.b i03)
swos portname    <ziel> --port <n> --name <text>         [--commit]   # Port-Name (link.b i0a)
swos port-enable <ziel> --port <n> --to on|off  [--force] [--commit]   # Enabled (link.b i01)
swos autoneg     <ziel> --port <n> --to on|off  [--force] [--commit]   # Auto Negotiation (link.b i02)
swos duplex      <ziel> --port <n> --to on|off  [--force] [--commit]   # Full Duplex (link.b i03)
swos speed       <ziel> --port <n> --to <Mbit/s>      [--force][--commit]  # Forced Speed, Kupfer+SFP+ (Enum dialektabh., z.B. 1000/2500/10000)
swos vlan-mode   <ziel> --port <n> --to disabled|optional|strict [--force][--commit]  # VLAN Mode (fwd.b i15)
swos vlan-receive <ziel> --port <n> --to any|tagged|untagged [--force][--commit]      # VLAN Receive (fwd.b i17)
swos force-vlan-id <ziel> --port <n> --to on|off [--force][--commit]  # Force VLAN ID (fwd.b i19)
swos pvid        <ziel> --port <n> --vid <1..4095>        [--commit]   # Default VLAN ID / PVID (fwd.b i18)
swos vlan-set    <ziel> --vid <1..4095> --members 1,2,9   [--commit]   # VLAN-Membership (vlan.b) css610/css326, legt an falls neu
swos vlan-set    <ziel> --vid <1..4095> --tagged 6 --untagged 2,3 [--commit]  # CSS106 (swos_lite): Egress-Enum prt, Rest = not-a-member
```

**Link-/Lockout-Schutz** (`port-enable`, `autoneg`, `duplex`, `speed` sowie `vlan-mode`,
`vlan-receive`, `force-vlan-id`): eine **tatsächliche Änderung** an einem Port mit **aktivem Link** (`i06`) verlangt
`--force` (sonst Abbruch) — er könnte den Mgmt-/Uplink-Verkehr tragen, und Enable/Auto-Neg/Duplex/
Speed- bzw. VLAN-Filter-Änderungen können den Link/Zugriff kappen. Der Dry-Run zeigt die Vorschau
trotzdem; nur der `--commit` erzwingt `--force`. No-op (Zielwert = Ist) löst nie den Guard aus.
`vlan-mode`=`disabled|optional|strict`, `vlan-receive`=`any|tagged|untagged` (engine.js `fwd.b`
`i15`/`i17`).

**`speed`** (`link.b` Forced-Speed, css610 `i05` / css326 `spdc`) — **Kupfer + SFP+**. Das
Enum ist **dialekt-spezifisch** (`SPEED_ENUMS`) und divergiert ab Index 4, daher nicht generisch,
sondern aus `engine.js` + Live-DAC verifiziert:
- css326: `10M/100M/1G/10G/5G/2.5G/40G` (0–6)
- css610_new: `10M/100M/1G/10G/200M/2.5G/5G` (0–6)

`--to` in **Mbit/s** (z.B. `1000`, `2500`, `10000`), zur Laufzeit gegen das Dialekt-Enum geprüft
(ungültiger Wert → Abbruch mit Auflistung der gültigen). Kupfer-Subset `10`/`100`/`1000` = `0`/`1`/`2`
in allen Dialekten deckungsgleich. Wirkt **nur bei Auto-Neg=off** für den Port — bei Auto-Neg=on wird
der Wert gespeichert, der Dry-Run weist darauf hin. Link-Guard wie oben. **Live an css610 SFP+1 und
css326 SFP1 bestätigt** (`i05[8]`/`spdc[24]`=10G → Read-back → restauriert). CSS106 (`swos_lite`):
die **SFP-Buchse ist 1G-only** (SFP, kein SFP+; DAC handelt auf 1G runter, engine.js-Enum
`[10,100,1000]`) → Enum vollständig; `speed` an CSS106 SFP-Port (6) live bestätigt (`spdc[5]`=1G →
Read-back → restauriert).

Mechanik überall gleich (**wie die SwOS-Web-UI**): GET des Endpoints (= config-treu, s. u.) →
schreibbaren Feld-Subset übernehmen → **nur das Zielfeld** ersetzen → `POST /<ep>.b`
(`Content-Type: text/plain`, roher Blob) → Read-back-Verify. `--members` sind Portnummern
(1..8 Kupfer, 9=SFP+1, 10=SFP+2).

**Guard-Rails:**
- **`"writable": true`** im Inventory Pflicht (nur die 3 Büro-Sandkasten-Switches). Ohne Flag,
  bei `--swb`/`--ip` oder unbekanntem Switch → Abbruch. Produktion (Seiersberg) bleibt read-only.
- **Verifizierte Schreib-Dialekte:** `css610_new` (poe.b/link.b/fwd.b/vlan.b), `css326`
  (link.b/fwd.b/vlan.b; kein PoE) und `swos_lite`/CSS106 (link.b/fwd.b/vlan.b; PoE-Out in link.b nur
  beim PoE-Modell; `vlan-set` via Egress-Enum). Andere Dialekte → sauberer Abbruch. Nur
  `direct`-Transport. Der geforderte Endpoint muss für den erkannten Dialekt freigegeben sein
  (`WRITE_FIELDS`), sonst Abbruch mit klarer Meldung. `poe-out`/`poe-voltage` lösen ihren Endpoint
  dialektabhängig auf (css610 → `poe.b`, CSS106 → `link.b`; `poe-voltage` nur css610).
- **`--dry-run` ist Default:** zeigt aktuelles/geplantes Feld und den exakten POST-Body, sendet
  nichts. Erst `--commit` schreibt.
- **Snapshot vor der ersten Änderung** (`swos-snapshot-<sw>.swb`) als Rollback-Punkt. Ablageort:
  `SWOS_SNAPSHOT_DIR` (falls gesetzt) → sonst `<cwd>/.tmp` → Fallback `~/.cache/swos`, wenn aus dem
  Skill-Verzeichnis aufgerufen (nie ins `$SKILL_DIR` schreiben).
- **Read-back-Verify** nach jedem Commit: nur das Zielfeld darf sich geändert haben, sonst Abbruch.

**Frisch nach Factory-Reset ist kein Write möglich** (bewusst so): SwOS liefert `/backup.swb`
unmittelbar nach einem Reset **leer** (0 Byte) — bis zum **ersten Config-Write**, der das Backup
erst „scharf" macht. Der Snapshot-Once findet dann kein Rollback-Netz und bricht ab. Verifiziert
identisch auf CSS610 (.215) und CSS326 (.214), also **dialektunabhängig** — und **nicht** an die
Identity gekoppelt (ein Default-`id:'MikroTik'` mit bereits geschriebener Config liefert sehr wohl
ein Backup). Auch das SwOS-**Failsafe-Image** liefert ein leeres Backup (engine.js-Hinweis „a
backup version of SwOS is running"). Bewusste Entscheidung: **Write nur, wenn ein echtes
`/backup.swb` ziehbar ist** — kein GET-Fallback-Snapshot. Konsequenz für frisch resettete Switches:
zuerst **eine** Änderung über die Web-UI setzen (z. B. Identity), damit `/backup.swb` befüllt wird;
danach greift der Tool-Schreibpfad normal.

### Zwei hart erkaufte Lehren (CR4426)

1. **Hex byte-aligned senden (gerade Anzahl Ziffern), wie der Browser.** Der SwOS-Parser liest
   Hex **bytewise** — ungerade Breite `0x3ff` wird zu `0x3f` (=63) fehlinterpretiert. Ein früher
   `link.b`-Write mit `i01:0x3ff` (ungerade) warf so die **Enabled-Maske** auf Ports 1–6 zurück
   (7–10 deaktiviert). `_blob_hex` paddet jetzt auf gerade Breite (`0x03ff`). `poe.b` war nie
   betroffen (Werte 0–7 sind ohnehin 2-stellig).
2. **Config-Basis für Writes ist IMMER der Live-GET**, niemals der `.swb`-Parser. Der GET ist
   config-treu — Feld-für-Feld deckungsgleich mit der Web-UI (verifiziert: `link.b i01`=Enabled,
   `i02`=Auto-Neg, `i03`=Full-Duplex, `i05`=Speed). Der css610_old-`.swb`-Parser lieferte dagegen
   **falsche Bitmasken** (`0x37f/0x3ff` statt `0x37/0x3f`).

### css326-Schreibpfad (CR4428)

`link.b`/`fwd.b` sprechen auf css326 **benannte** statt numerischer Keys, sind aber Feld-für-Feld
1:1 zu css610_new (aus HAR `.214` + `engine.js` verifiziert, nicht geraten):
`en/nm/an/spdc/dpxc/fctc/fctr` (link.b) und `vlan/vlni/dvid/fvid` (fwd.b), 26 Ports (24G+2×SFP+).
Die Feldnamen je Dialekt stehen in `WRITE_FIELDS`, die Kommandos lösen Rollen darüber auf.

**`vlan-set` (vlan.b)** ist ebenfalls dialekt-fähig, in **zwei Membership-Modellen**:

- **Bitmask** (css610_new/css326, `--members 1,2,9`): css326-Einträge tragen `{vid,nm,piso,lrn,mrr,
  igmp,mbr}` (Member-Maske `mbr`) statt css610 `{i01,i03,i02}`. Falle: die **GET-Reihenfolge weicht
  von der POST-Reihenfolge ab** (GET liefert `nm,mbr,vid,…`, die UI POSTet `vid,nm,…,mbr`) — daher
  wird jeder Eintrag in die kanonische `order` serialisiert (nicht verbatim durchgereicht),
  bestehende VLANs feldtreu erhalten, neue mit Defaults (Isolation/Learning an) angelegt.
- **Egress-Enum** (swos_lite/CSS106, `--tagged`/`--untagged`): Mitgliedschaft ist das Per-Port-Feld
  `prt` (engine.js `["leave as is","always strip","add if missing","not a member"]` = 0/1/2/3), kein
  Bitmask. `--tagged` → `add if missing` (2), `--untagged` → `always strip` (1), alle **nicht**
  genannten Ports → `not a member` (3). Deklarativ: der komplette Membership-Satz wird gesetzt (wie
  die volle Maske); die Mode `leave as is` (0) ist über tagged/untagged bewusst nicht erreichbar.
  Enum + Multi-VLAN-Struktur aus Live-Capture `.193`/`.204` (CR4428) verifiziert, nicht abgeleitet.

Portzahl kommt in beiden Modellen aus `link.b` (Namen-Array), nicht hartcodiert.

**`vlan-remove --vid N` / `vlan-clear`** ergänzen den Löschweg: `vlan-remove` entfernt einen Eintrag
und erhält die übrigen feldtreu, `vlan-clear` setzt vlan.b auf `[]`. Beide laufen über denselben
dialekt-generischen vlan.b-Pfad (css610_new + css326 + swos_lite), No-op wenn das VID fehlt bzw. die
Liste schon leer ist, mit Read-back-Verify (Ziel weg, Rest unverändert).

**Hart erkaufte Lehre: Enums divergieren je Dialekt.** VLAN Mode ist auf css326
`["disabled","optional","enabled","strict"]` → **`strict`=3** (plus Extra-Wert `enabled`=2),
auf css610_new nur `["disabled","optional","strict"]` → `strict`=2. Das css610-Enum blind zu
übernehmen hätte `strict` auf css326 fälschlich als `enabled` gesetzt. `VLANMODE_BY_DIALECT`
hält beide; jeder Enum-Wert wird gegen den erkannten Dialekt validiert. `vlan-receive` und der
Kupfer-Speed-Subset (10/100/1000=0/1/2) sind dagegen identisch (SFP+-Speedstufen nicht abgedeckt).

### swos_lite / CSS106-Schreibpfad (CR4428)

Aus `engine.js` (Tab-Definitionen) + Live-GET `.193` (CSS106-1G-4P-1S, PoE) und `.204`
(CSS106-5G-1S, ohne PoE) verifiziert, nicht geraten. **6 Ports** (5×Kupfer + **1** SFP → `speed`
1–5). Feldnamen in `WRITE_FIELDS["swos_lite"]`:

- **`link.b`** POST-Subset `en/nm/an/spdc/dpxc/fct` — Flow Control ist **ein** Feld `fct` (nicht
  `fctc/fctr` wie css326). Portname/enable/autoneg/duplex/speed laufen darüber.
- **PoE liegt in `link.b`** (`poe`=PoE Out, `prio`=Priority), **nicht** in `poe.b` (das gibt `303`).
  Die PoE-Felder rendert `engine.js` nur beim PoE-Modell (`Z()`-Wrapper, Board `CSS106-1G-4P-1S`) —
  daher ist der link.b-POST-Subset **modellabhängig**: mit PoE zusätzlich `poe,prio`. `poe-out`
  erkennt das PoE-Modell an `-4P-` im Board und bricht sonst sauber ab. **PoE-Out-Enum divergiert:**
  `["off","auto","on","calibr"]` = 0/1/2/3 (≠ css610 `off/on/auto`). Gültige PoE-Ports **2–5**
  (`engine.js O:1,P:5`; Port 1 Uplink / Port 6 SFP haben kein PoE). **Kein `poe-voltage`** (CSS106
  hat kein Voltage-Level-Feld).
- **`fwd.b`** POST-Subset `vlan/vlni/dvid/fvid/vlnh` — wie css326, aber mit **Extra-Feld `vlnh`**
  (VLAN Header, Egress). VLAN Mode 4-Werte wie css326 (`strict`=3).
- **`vlan.b`**: Einträge `{vid,ivl,igmp,prt}`. Mitgliedschaft ist ein **Per-Port-Egress-Enum `prt`**
  (engine.js `["leave as is","always strip","add if missing","not a member"]` = 0/1/2/3), **kein
  Member-Bitmask**. `vlan-set` bildet das über `--tagged` (→ 2) / `--untagged` (→ 1) ab, alle
  übrigen Ports → `not a member` (3); `vlan-remove`/`vlan-clear` laufen generisch (Reihenfolge
  `[vid,ivl,igmp,prt]`). Enum + Multi-VLAN-Struktur aus Live-Capture `.193`/`.204` (CR4428, HAR)
  verifiziert.

Live an `.193` bestätigt (ändern → Read-back → Restore): `portname` (link.b inkl. PoE-Felder im
POST), `pvid` (fwd.b), `poe-out` (link.b, `auto`↔`on`), `vlan-set` (VLAN neu anlegen + aktualisieren,
tagged/untagged), `vlan-remove` (Read-back Ziel weg, Rest feldtreu).

### Noch zurückgestellt

- **`poe-priority`** (`poe.b i02`): keine freie Zahl je Port, sondern ein **eindeutiger Rang
  (Permutation 0–7)** — der Switch schichtet beim Setzen um. Braucht ein Ranking-Modell.
- **`sys.b`** (Identity, Mgmt-IP): Format bekannt, aber Mgmt-Zone → nur mit Extra-Vorsicht.
  Passwort (`!pwd.b`) und `/reboot` bewusst außen vor.

**PoE im `ports`-View (CR4428 gefixt):** Der View zeigt jetzt den **Config-Modus** (css610
`poe.b i01` `off/on/auto`; CSS106 `link.b poe` `off/auto/on/calibr`) plus in Klammern den
**Runtime-Status** aus dem verifizierten Enum (`poe.b i04` / `link.b poes`: `waiting for load`,
`powered on`, `overload`, …). Nur PoE-fähige Ports (css610 1-8, CSS106 2-5) tragen PoE; SFP(+)/
Uplink bleiben leer. Zusätzlich zeigt der View die **ausgehandelte Ist-Geschwindigkeit**
(css326 `spd`, css610 `i08`; z.B. der DAC-Link als `10G`). Rest-Bug unabhängig: `!dhost.b`
liefert im `direct`-Modus gelegentlich Short-Reads (`BlobError`).

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

- **Schreiben auf `css610_new` (poe.b/link.b/fwd.b/vlan.b), `css326` (link.b/fwd.b/vlan.b) und
  `swos_lite`/CSS106 (link.b/fwd.b/vlan.b, PoE-Out in link.b beim PoE-Modell).**
  Noch offen: Identity/Mgmt-IP (`sys.b`), css610_old-Writes — jeweils erst nach
  DevTools-/HAR-Verifikation des POST-Formats (nicht raten), jeder Write mit Read-back-Verify.
  `backup` (GET `/backup.swb`) ist reines Lesen und faellt weiterhin unter Stufe 1 — keine
  Config-Aenderung am Switch.
- **`.swb`-Restore-/Upload-Weg noch offen.** Der Snapshot-**Pull** vor dem ersten Write steht
  (via `backup`), das **Einspielen** eines `.swb` (Restore-POST) ist noch nicht verifiziert — das
  vollstaendige Rollback-Netz fehlt also noch.
- **PoE-Modus/-Status + Ist-Speed im `ports`-View** (CR4428 gefixt, live verifiziert): Config-Modus
  aus `poe.b i01` (css610) bzw. `link.b poe` (CSS106), Runtime-Status aus `poe.b i04`/`link.b poes`
  (Enum `engine.js`), Gating auf PoE-fähige Ports; Ist-Speed aus `spd`/`i08`. Offen bleibt hier nur
  das `poes`-**Detail** über die reine Status-Anzeige hinaus (nicht nötig).
- **ssh-curl** macht pro Endpoint eine SSH-Session; `all` = mehrere Sessions (funktioniert,
  aber nicht gebuendelt).
- **`.swb`-Backups (jede CSS610-Generation) nutzen immer das alte Einzelbuchstaben-Schema.**
  Ein per `backup` gezogenes `.swb` traegt in `sys.b` `F`+`J`-Keys, egal ob das Geraet live
  `css610_new` (numerische `i0x`-Keys) oder `css610_old` meldet — `detect_dialect()` erkennt
  Backups deshalb immer als `css610_old`. Das ist fuer VLAN/PVID/PoE/Portnamen korrekt (alle vier
  Felder sind unter den `css610_old`-Buchstaben-Keys vorhanden und werden richtig dekodiert,
  `portnames` seit 2026-07-21 auf Key `K` gemappt — Gegenprobe an einem echten Alt-FW-Fixture
  [`swvspoe1.swb`] und einem frischen Neu-FW-Backup [`swbs02poe`/CR4369] verifiziert, beide
  liefern jetzt die realen Namen `Port1..8`/`SFP+1`/`SFP+2` statt der Modell-Fallbacks).
- **Modell/Version/MAC/Serial fehlen in `.swb`-Backups grundsaetzlich** (CSS610, beide FW-Stufen
  gegengeprueft) — das ist keine Dialekt-Verwechslung, sondern eine Eigenschaft des Backup-Formats
  selbst (Config-Backup, keine Identitaets-/Hardware-Daten). Bleibt `?` in der Ausgabe; noch nicht
  gegen `engine.js` verifiziert, ob es unter einem bisher ungenutzten Key doch vorliegt.

## Hinweise

- Fixture-Backups fuer Regressionstests: `gatekeeper.example.com:/archive/backups/switches`
  (naechtlich). Der Decoder liefert fuer `.swb` (C) und Live (`ssh-curl` B) dasselbe Ergebnis.
- Ausgabe ist bewusst lesbar (Tabellen); `--json` fuer maschinelle Weiterverarbeitung.
- Hintergrund/Erkenntnisse: Kanboard **CR4426** (Handoff), Memory `reference_swos_lite_endpoints`.
