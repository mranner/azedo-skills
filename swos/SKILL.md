# swos -- MikroTik SwOS read-only Abfrage

Fragt MikroTik-**SwOS**-Switches (CSS-Serie und RB260/SwOS-Lite) ab und dekodiert die
SwOS-Blobs in lesbare Tabellen: System-Info, VLAN-Mitglieder, Portbelegung (PVID/PoE) und
FDB (MAC→Port). **Stufe 1 = read-only** (Standard). **Stufe 2 = schreibend** ist bisher auf
**genau einen** Befehl beschränkt: `poe-out` (PoE Out je Port, nur `css610_new`) mit strengen
Guard-Rails — siehe Abschnitt „Schreiben".

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
swos poe-out     <ziel> --port <n> --to off|on|auto     [--commit]   # Stufe 2, schreibend (s.u.)
swos poe-voltage <ziel> --port <n> --to auto|low|high   [--commit]   # Stufe 2, schreibend (s.u.)
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

## Schreiben (Stufe 2) — nur `poe.b` (`poe-out`, `poe-voltage`)

**Zwei** Schreibbefehle sind freigegeben, beide auf `poe.b` (dessen GET nachweislich config-treu
ist). Alles andere bleibt bewusst offen (siehe „Bewusst zurückgestellt" unten) — nichts wird geraten.

```bash
swos poe-out     <ziel> --port <n> --to off|on|auto          # Dry-Run: zeigt Ist/Soll, sendet NICHTS
swos poe-out     <ziel> --port <n> --to off|on|auto --commit # sendet + Read-back-Verify
swos poe-voltage <ziel> --port <n> --to auto|low|high        # Voltage Level, gleiche Mechanik
```

`poe-out` setzt **„PoE Out"** (`off`|`on` forced|`auto`), `poe-voltage` das **„Voltage Level"**
(`auto`|`low`|`high`). Format hart verifiziert (DevTools-/HAR-Capture `.215` + `engine.js`, CR4426):
`POST /poe.b`, `Content-Type: text/plain`, Body ein roher Teil-Blob `{i01,i02,i03,i0a}` (8 Kupferports;
`i01`=PoE Out, `i02`=Priority, `i03`=Voltage Level, `i0a`=global). Das Tool liest `poe.b`, ändert **nur**
das Zielfeld am Zielport und postet den Rest unverändert zurück.

**Guard-Rails:**
- **`"writable": true`** im Inventory Pflicht (nur die 3 Büro-Sandkasten-Switches). Ohne Flag,
  bei `--swb`/`--ip` oder unbekanntem Switch → Abbruch. Produktion (Seiersberg) bleibt read-only.
- **Nur `css610_new`** und nur `direct`-Transport (css326 hat kein PoE; swos_lite/CSS106 führt PoE
  in `link.b`, Format noch nicht gecaptured).
- **`--dry-run` ist Default:** zeigt aktuelles/geplantes Feld und den exakten POST-Body, sendet
  nichts. Erst `--commit` schreibt.
- **Snapshot vor der ersten Änderung:** zieht einmalig ein `.swb` nach `.tmp/swos-snapshot-<sw>.swb`
  — Rollback-Punkt.
- **Read-back-Verify** nach jedem Commit: liest `poe.b` neu, prüft dass **nur** das Zielfeld sich
  geändert hat; sonst Abbruch mit Snapshot-Hinweis.

### Bewusst zurückgestellt (Format verifiziert, aber Semantik/Sicherheit offen — CR4426)

Der Read-back-Verify hat diese beim Live-Test abgefangen, bevor Schaden blieb:

- **`poe-priority`** (`poe.b i02`): keine freie Zahl je Port, sondern ein **eindeutiger Rang
  (Permutation 0–7)** — der Switch schichtet beim Setzen um. Braucht ein Ranking-Modell.
- **`portname` (`link.b`), `pvid` (`fwd.b`), `vlan-set` (`vlan.b`)**: Der `link.b`-Write hat im
  Test die **Enabled-Maske umgeworfen** (Ports deaktiviert). **Lehre:** Config-Basis für Writes ist
  **immer der Live-GET** (der ist config-treu — Feld-für-Feld deckungsgleich mit der Web-UI),
  **niemals** der `.swb`-Parser (lieferte falsche Bitmasken). Der link/fwd/vlan-Write-Nebeneffekt ist
  erst kontrolliert nachzuweisen, bevor diese Befehle zurückkommen.

**Bekannter Read-only-Bug (unabhängig):** Der `ports`-View liest den PoE-**Modus** aus `poe.b i04`
(= **Runtime-Status** `2=idle,3=liefert`), der Config-Modus steht in `i01`. Der Write nutzt korrekt
`i01`; der Lese-View ist separat zu fixen. Ebenso: `!dhost.b` liefert im `direct`-Modus gelegentlich
Short-Reads (`BlobError`).

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

- **Schreiben nur `poe-out` (css610_new).** VLAN/PVID, Portname/Identity, Mgmt-IP und PoE auf
  anderen Dialekten sind **noch nicht** implementiert — jeweils erst nach DevTools-Verifikation
  des POST-Formats (nicht raten), jeder Write mit Read-back-Verify. `backup` (GET `/backup.swb`)
  ist reines Lesen und faellt weiterhin unter Stufe 1 — keine Config-Aenderung am Switch.
- **`.swb`-Restore-/Upload-Weg noch offen.** Der Snapshot-**Pull** vor dem ersten Write steht
  (via `backup`), das **Einspielen** eines `.swb` (Restore-POST) ist noch nicht verifiziert — das
  vollstaendige Rollback-Netz fehlt also noch.
- **`ports`-View liest PoE-Modus aus dem falschen Feld** (`i04`=Runtime statt `i01`=Config, nur
  css610) — siehe Abschnitt „Schreiben". `poe-out` selbst ist davon nicht betroffen.
- **swos_lite-PoE** (CSS106-1G-4P-1S): `poe.b` fehlt, PoE-Info steckt in `link.b` (`poe`/`poes`);
  die genaue Semantik von `poes` ist noch nicht gegen `engine.js` verifiziert und wird bewusst
  **nicht** als Modus ausgegeben (nicht raten).
- **Link/Speed** wird noch nicht dekodiert (Speed-Codes modellabhaengig, unsicher).
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
