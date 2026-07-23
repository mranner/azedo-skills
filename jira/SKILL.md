---
name: jira
description: >
  Jira Data Center / Server (self-hosted, z.B. jira.example.com, jira.example.com):
  Issues per JQL suchen, einzelnes Issue + Kommentare anzeigen, moegliche
  Status-Uebergaenge auflisten sowie schreibend Kommentare hinzufuegen und
  Status-Uebergaenge (Transitions) ausfuehren. Multi-Instanz ueber benannte
  Profile in ~/.claude/jira.json mit Projekt-Routing (z.B. CORTAB-* -> Ergon),
  Auth per Personal Access Token (Bearer), REST API v2.
  Nutze diesen Skill wenn der User Jira-Tickets abfragen, kommentieren oder
  deren Status aendern will (z.B. CORTAB-*). Auch aktiv verwenden bei
  "schau in Jira", "welchen Status hat CORTAB-...", "kommentier das Ticket",
  "setz das Issue auf ...". Trigger: /jira.
trigger:
  - "jira"
  - "CORTAB"
  - "issue"
  - "ticket status"
---

# jira -- Jira Data Center REST API

Fragt selbst-gehostete **Jira Data Center / Server**-Instanzen (nicht Jira Cloud) ueber die
REST API v2 ab und aendert Issues gezielt. Mehrere Instanzen (z.B. Ergon, Corris) werden ueber
benannte Profile in `~/.claude/jira.json` unterschieden; die tatsaechlichen Rechte richten sich
pro Instanz nach dem eigenen User (API-Rechte = UI-Rechte).

**Aufruf:** `python3 "$SKILL_DIR/jira" <subcommand> [--instance <name>] [optionen]`

`$SKILL_DIR` ist das Verzeichnis dieser SKILL.md.

## Setup

1. **Personal Access Token (PAT)** in der Jira-Instanz erzeugen: oben rechts Avatar -> Profil ->
   **Personal Access Tokens** -> *Create token* (Data Center 8.14+). Token wird nur einmal angezeigt.
2. `jira.json.example` als **`~/.claude/jira.json`** anlegen (bewusst ausserhalb der Skill-/Projekt-
   Repos, da `~/.claude` kein Git-Repo ist — der Token landet so nie in Git) und pro Instanz
   `host` / `token` / `projects` eintragen, dazu `default`.

```json
{
  "default": "ergon",
  "instances": {
    "ergon":  { "host": "https://jira.example.com",  "token": "<PAT>", "projects": ["CORTAB"] },
    "corris": { "host": "https://jira.example.com", "token": "<PAT>", "projects": [] }
  }
}
```

Alternativer Pfad per `JIRA_CONFIG=/pfad/jira.json` (sonst: `~/.claude/jira.json`).

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

# Paginierung / mehr Felder / rohes JSON
python3 "$SKILL_DIR/jira" search "assignee = currentUser()" --max 50 --start 0
python3 "$SKILL_DIR/jira" search "project = CORTAB" --fields summary,status --json

# Einzelnes Issue (mit Beschreibung)
python3 "$SKILL_DIR/jira" issue CORTAB-1762

# Kommentare
python3 "$SKILL_DIR/jira" comments CORTAB-1762

# Moegliche Status-Uebergaenge (id, Name, Ziel-Status)
python3 "$SKILL_DIR/jira" transitions CORTAB-1762
```

## Schreiben

Schreibende Operationen nur, soweit der eigene User es in der jeweiligen Instanz darf.

```
# Kommentar hinzufuegen ('-' liest den Body von stdin)
python3 "$SKILL_DIR/jira" comment CORTAB-1762 --body "Deploy auf DEV erledigt, bitte pruefen."

# Status-Uebergang: erst dry-run (zeigt gematchten Uebergang + Ziel-Status), dann --yes
python3 "$SKILL_DIR/jira" transition CORTAB-1762 --to "In Progress"          # dry-run
python3 "$SKILL_DIR/jira" transition CORTAB-1762 --to "In Progress" --yes    # ausfuehren
python3 "$SKILL_DIR/jira" transition CORTAB-1762 --to "Done" --comment "erledigt" --yes
```

`--to` matcht case-insensitiv auf den **Uebergangs-Namen** ODER den **Ziel-Status-Namen**. Passt
nichts, werden die moeglichen Uebergaenge aufgelistet. Ohne `--yes` wird nichts geaendert.

## Hinweise

- **Data Center, nicht Cloud:** Endpoint ist `/rest/api/2/`, Auth `Authorization: Bearer <PAT>`.
  Kommentar-/Beschreibungs-Bodies sind Plaintext/Wiki-Markup (kein Cloud-ADF).
- **Body-Text** wird 1:1 gesendet; keine Formatierungs-Konvertierung.
- Fehlt der Menuepunkt *Personal Access Tokens*, hat die Instanz PATs deaktiviert -> bei der
  jeweiligen Administration nachfragen.
