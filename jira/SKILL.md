---
name: jira
description: >
  Jira Data Center / Server (self-hosted, z.B. jira.example.com) UND Jira Cloud
  (*.atlassian.net, z.B. example.atlassian.net): Issues per JQL suchen, einzelnes
  Issue + Kommentare anzeigen, moegliche Status-Uebergaenge auflisten, Nutzer
  suchen (accountId/Username) sowie schreibend Kommentare hinzufuegen und
  bestehende Kommentare bearbeiten (inkl. @-Mentions im Text),
  Status-Uebergaenge (Transitions) ausfuehren,
  Issues zuweisen, Beschreibungen setzen, Unteraufgaben anlegen sowie Dateien
  anhaengen, auflisten und herunterladen. Multi-Instanz ueber benannte Profile in ~/.claude/jira.json mit
  Projekt-Routing (z.B. CORTAB-* -> Ergon, SADM-* -> Corris). DC: PAT-Bearer,
  REST API v2. Cloud: Basic-Auth email:API-Token, REST API v3, ADF-Bodies.
  Nutze diesen Skill wenn der User Jira-Tickets abfragen, kommentieren oder
  deren Status aendern will (z.B. CORTAB-*, SADM-*). Auch aktiv verwenden bei
  "schau in Jira", "welchen Status hat CORTAB-...", "kommentier das Ticket",
  "setz das Issue auf ...". Trigger: /jira.
trigger:
  - "jira"
  - "CORTAB"
  - "issue"
  - "ticket status"
---

# jira -- Jira REST API (Data Center + Cloud)

Fragt Jira-Instanzen ueber die REST API ab und aendert Issues gezielt — sowohl selbst-gehostetes
**Data Center / Server** (Ergon, `jira.example.com`) als auch **Jira Cloud** (`*.atlassian.net`,
Corris, `example.atlassian.net`). Mehrere Instanzen werden ueber benannte Profile in
`~/.claude/jira.json` unterschieden; die tatsaechlichen Rechte richten sich pro Instanz nach dem
eigenen User (API-Rechte = UI-Rechte).

**DC vs. Cloud** — der Skill waehlt den Pfad automatisch (Host `*.atlassian.net` oder
`"type": "cloud"` in der Config); die Subcommands sind identisch:

| | Data Center | Cloud |
|---|---|---|
| API | `/rest/api/2/` | `/rest/api/3/` |
| Auth | `Authorization: Bearer <PAT>` | `Basic base64(email:API-Token)` |
| Body (Beschreibung/Kommentar) | Plaintext/Wiki-Markup | ADF (JSON) — vom Skill transparent gewandelt |
| Such-Paginierung | `--start` (startAt) | `--token` (nextPageToken) |

**Aufruf:** `python3 "$SKILL_DIR/jira" <subcommand> [--instance <name>] [optionen]`

`$SKILL_DIR` ist das Verzeichnis dieser SKILL.md.

## Setup

`jira.json.example` als **`~/.claude/jira.json`** anlegen (bewusst ausserhalb der Skill-/Projekt-
Repos, da `~/.claude` kein Git-Repo ist — der Token landet so nie in Git). Pro Instanz je nach Typ:

**Data Center** — Personal Access Token: oben rechts Avatar -> Profil -> **Personal Access Tokens**
-> *Create token* (DC 8.14+). Felder: `host`, `token`, `projects`.

**Cloud** — API-Token am Atlassian-Account: **https://id.atlassian.com/manage-profile/security/api-tokens**
-> *Create API token* (eingeloggt mit der E-Mail des Cloud-Accounts). Der Token gilt kontoweit fuer
alle Cloud-Sites. Felder: `host` (`https://<site>.atlassian.net`), `email`, `token`, `projects`, und
`"type": "cloud"` (bei `*.atlassian.net`-Hosts optional — wird sonst am Host erkannt).

```json
{
  "default": "ergon",
  "instances": {
    "ergon":  { "host": "https://jira.example.com", "token": "<PAT>", "projects": ["CORTAB"] },
    "corris": { "host": "https://example.atlassian.net", "type": "cloud",
                "email": "<account-email>", "token": "<API-Token>",
                "projects": ["SADM", "ITSD", "CSW"] }
  }
}
```

Cloud braucht **email + token** (Basic-Auth) — der Token allein reicht nicht. Alternativer
Config-Pfad per `JIRA_CONFIG=/pfad/jira.json` (sonst: `~/.claude/jira.json`).

## Instanzen & Routing

Die Ziel-Instanz wird in dieser Reihenfolge bestimmt:

1. **`--instance <name>`** (bzw. `-i`) — expliziter Override, gewinnt immer.
2. **Projekt-Routing** — aus dem Issue-Key (`CORTAB-1760` -> `CORTAB`) bzw. aus `project = X`
   in der JQL wird das Projekt abgeleitet und die Instanz gewaehlt, deren `projects`-Liste es
   enthaelt.
3. **`default`** aus der Config, wenn nichts passt.

```
python3 "$SKILL_DIR/jira" instances          # Instanzen, Hosts, Projekte, Default anzeigen
```

## Lesen

```
# Issues per JQL (Default: 20 Treffer, kompakte Tabelle)
python3 "$SKILL_DIR/jira" search "project = CORTAB AND status != Closed ORDER BY updated DESC"

# Paginierung: DC ueber --start (startAt), Cloud ueber --token (nextPageToken,
# die Suche zeigt den Folge-Token am Ende an)
python3 "$SKILL_DIR/jira" search "assignee = currentUser()" --max 50 --start 0
python3 "$SKILL_DIR/jira" search "project = SADM ORDER BY updated DESC" --token <nextPageToken>
python3 "$SKILL_DIR/jira" search "project = CORTAB" --fields summary,status --json

# Einzelnes Issue (mit Beschreibung)
python3 "$SKILL_DIR/jira" issue CORTAB-1762

# Kommentare (Kopfzeile enthaelt die Kommentar-id -- die braucht comment-edit)
python3 "$SKILL_DIR/jira" comments CORTAB-1762

# Nutzer suchen: Cloud accountId, DC Username (Suchbegriff = E-Mail, Name, Username)
python3 "$SKILL_DIR/jira" users -i corris --query "vorname.nachname@example.org"
python3 "$SKILL_DIR/jira" users -i corris --query "bucher" --json

# Moegliche Status-Uebergaenge (id, Name, Ziel-Status)
python3 "$SKILL_DIR/jira" transitions CORTAB-1762

# Anhaenge auflisten (id, Name, Groesse, Typ, Datum, Autor)
python3 "$SKILL_DIR/jira" attachments SADM-69

# Anhaenge herunterladen: alle in ein Verzeichnis, oder einen per --id
python3 "$SKILL_DIR/jira" download SADM-69 --output ./.tmp
python3 "$SKILL_DIR/jira" download SADM-69 --id 107792 --output ./bericht.pdf
```

`download` folgt dem 302 auf den Media-/S3-Host und entfernt dabei den Auth-Header (sonst Ablehnung).
Ohne `--id` werden alle Anhaenge geladen; gleichnamige bekommen die Attachment-ID vorangestellt, damit
nichts still ueberschrieben wird.

## Schreiben

Schreibende Operationen nur, soweit der eigene User es in der jeweiligen Instanz darf.

```
# Kommentar hinzufuegen ('-' liest den Body von stdin)
python3 "$SKILL_DIR/jira" comment CORTAB-1762 --body "Deploy auf DEV erledigt, bitte pruefen."

# Bestehenden Kommentar ueberschreiben (id aus 'comments')
python3 "$SKILL_DIR/jira" comment-edit ITSD-16162 --id 214989 --body "Korrigierter Text."

# Status-Uebergang: erst dry-run (zeigt gematchten Uebergang + Ziel-Status), dann --yes
python3 "$SKILL_DIR/jira" transition CORTAB-1762 --to "In Progress"          # dry-run
python3 "$SKILL_DIR/jira" transition CORTAB-1762 --to "In Progress" --yes    # ausfuehren
python3 "$SKILL_DIR/jira" transition CORTAB-1762 --to "Done" --comment "erledigt" --yes
```

`--to` matcht case-insensitiv auf den **Uebergangs-Namen** ODER den **Ziel-Status-Namen**. Passt
nichts, werden die moeglichen Uebergaenge aufgelistet. Ohne `--yes` wird nichts geaendert.

### @-Mentions im Body

`@[<schluessel>]` im Text wird zur echten Erwaehnung — bei **Cloud** als ADF-`mention`-Knoten
(loest die Benachrichtigung aus), bei **DC** als Wiki-Markup `[~username]`. Gilt in jedem
geschriebenen Body: `comment`, `comment-edit`, `describe` und `transition --comment`.

```
python3 "$SKILL_DIR/jira" comment ITSD-16162 --body "Hallo @[vorname.nachname@example.org], bitte pruefen."
python3 "$SKILL_DIR/jira" comment ITSD-16162 --body "cc @[0123456789abcdef01234567]"
```

Als Schluessel taugt:

| Schluessel | Aufloesung |
|---|---|
| E-Mail-Adresse | `user/search`, exakter Treffer auf `emailAddress` — **eindeutig, bevorzugen** |
| accountId (Cloud) / Username (DC) | direkt uebernommen, nur der Anzeigename wird nachgeladen |
| Anzeigename | `user/search`, exakter Treffer auf `displayName` |

**Bei Mehrdeutigkeit wird abgebrochen, nicht geraten.** Auf der Corris-Cloud gibt es mehrere aktive
Accounts mit identischem Anzeigenamen (`@[Max Mustermann]` -> 3 Treffer, nur einer mit sichtbarer
E-Mail). Der Skill listet dann die Kandidaten mit accountId und E-Mail auf und schreibt nichts —
danach mit E-Mail oder accountId wiederholen. Ein Schluessel ohne Treffer bricht ebenfalls ab; es
landet nie unaufgeloester `@[...]`-Text im Ticket.

Cloud verbirgt E-Mail-Adressen je nach Profil-Einstellung in der Antwort. Die Suche matcht sie
trotzdem: bleibt genau ein Kandidat uebrig, wird er genommen, auch wenn `emailAddress` leer ist.
`@[...]` wird immer als Mention gelesen — fuer literalen Text diese Schreibweise meiden.

```
# Assignee setzen / entfernen
python3 "$SKILL_DIR/jira" assign SADM-69 --to me            # eigener Account (myself)
python3 "$SKILL_DIR/jira" assign SADM-69 --to <accountId>   # Cloud: accountId, DC: Username
python3 "$SKILL_DIR/jira" assign SADM-69 --unassign         # Assignee entfernen
```

`--to me` loest den eigenen Account auf (Cloud: `accountId`, DC: `name`). Ansonsten ist der Wert bei
**Cloud eine accountId**, bei **DC ein Username** — Cloud kennt keine Zuweisung per Username mehr.

```
# Beschreibung setzen ('-' liest den Body von stdin; Cloud -> ADF, DC -> Plaintext)
python3 "$SKILL_DIR/jira" describe SADM-69 --body "Neue Beschreibung, mehrere Zeilen moeglich."

# Unteraufgabe anlegen (Subtask-Issuetype wird automatisch ermittelt; --owner optional)
python3 "$SKILL_DIR/jira" subtask SADM-69 --title "Teilaufgabe X" --owner me

# Datei anhaengen (absoluter Pfad)
python3 "$SKILL_DIR/jira" attach SADM-69 --file /pfad/zur/datei.pdf
```

Bei `subtask` wird ein evtl. `--owner` **nach** dem Anlegen per separatem Assignee-Call gesetzt —
Jira ignoriert den Assignee beim Create je nach Screen-Konfiguration (v.a. Cloud) still.

## Hinweise

- **DC vs. Cloud wird automatisch erkannt** (Host `*.atlassian.net` oder `"type": "cloud"`), die
  Subcommands sind identisch. DC: `/rest/api/2/` + `Bearer <PAT>`. Cloud: `/rest/api/3/` +
  `Basic email:token`.
- **Body-Format:** DC-Bodies sind Plaintext/Wiki-Markup und werden 1:1 gesendet. Cloud nutzt ADF
  (JSON): beim **Lesen** wandelt der Skill ADF zu Plaintext (Absaetze, Zeilenumbrueche, `@`-Mentions,
  Emojis), beim **Schreiben** Plaintext zu ADF (ein Absatz je Zeile). Rich-Formatierung (Tabellen,
  Panels, Bilder) wird beim Lesen best-effort verflacht.
- **Nutzersuche:** Cloud `user/search?query=` (matcht Anzeigename **und** E-Mail), DC
  `user/search?username=` (matcht Username, Name, E-Mail). `users` gibt links die Kennung aus, die
  anderswo gebraucht wird: Cloud die `accountId` (fuer `assign --to` und `@[...]`), DC den Username.
- **Antwort ist kein JSON:** kommt statt der API-Antwort eine HTML-Seite (Status 200, Redirect auf
  eine Login-/SSO-URL), meldet der Skill das mit Ziel-URL statt mit einem Traceback. Ursache ist
  praktisch immer ein abgelaufener PAT bzw. ein vorgeschaltetes Auth-Gateway — Token erneuern.
- **Cloud-Suche** laeuft ueber `/rest/api/3/search/jql` (der alte `/search`-Endpoint wurde 2025 fuer
  Cloud entfernt): Token-Paginierung (`--token`), **kein** `total` — die Suche meldet nur die Anzahl
  der aktuellen Seite und ggf. den Folge-Token.
- Fehlt bei DC der Menuepunkt *Personal Access Tokens*, hat die Instanz PATs deaktiviert -> bei der
  jeweiligen Administration nachfragen.
