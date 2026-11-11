---
name: bookstack
description: >
  BookStack über die REST-API: Regale, Bücher, Kapitel und Seiten (Markdown)
  suchen, lesen, anlegen, ändern, exportieren; Anhänge, Rechte, Rollen, User,
  Audit-Log und Papierkorb. Trigger: /bookstack.
disable-model-invocation: true
argument-hint: "Suchbegriff, Seite anlegen, Rechte setzen, ... (optional)"
---

# bookstack -- BookStack REST-API

Alles läuft über das gebündelte Script `bookstack` (Python >= 3.11, stdlib):

```bash
python3 "$SKILL_DIR/bookstack" <subcommand> [options]
```

`$SKILL_DIR` ist das Base Directory dieses Skills. `--help` am Subcommand listet
die Optionen. Ausgabe ist JSON, `--brief` kürzt Listen und Suchtreffer.

**Andere Skills** können diesen Skill nicht laden (`disable-model-invocation`).
Sie rufen das Script direkt auf: `python3 ~/.claude/skills/bookstack/bookstack …`.

## Config

`BOOKSTACK_URL`, `BOOKSTACK_TOKEN_ID`, `BOOKSTACK_TOKEN_SECRET` aus
`BOOKSTACK_ENV`, sonst `.env` im Arbeitsverzeichnis (nur mit `BOOKSTACK_*`-Schlüssel),
sonst `~/.env`. Das Token erzeugt der User in BookStack unter **Profil bearbeiten
→ API-Tokens**; seine Rolle braucht „Zugriff auf System-API“. Die Admin-Befehle
unten brauchen ein Token mit Admin-Rolle.

## Inhalt

| Aufgabe | Aufruf |
|---|---|
| Suchen | `search "<text>" [--type page,book] [--tag kunde=x] --brief` |
| Auflisten | `list books --filter book_id=3 --sort=-updated_at --brief` (`--all` blättert durch) |
| Lesen | `get page <id>` (Markdown; `--html` zusätzlich HTML) |
| Anlegen | `create page --book <id>\|--chapter <id> --name "…" --markdown-file <pfad> [--tag k=v]` |
| Ändern | `update page <id> [--markdown-file <pfad>] [--name …]` |
| Verschieben | `update page <id> --book <id>` bzw. `--chapter <id>`; Reihenfolge mit `--priority <n>` |
| Regal | neues Buch: `create book --name … --shelf <id>`, vorhandenes: `shelve <shelf> <book>` |
| Export | `export page\|chapter\|book <id> --format markdown\|pdf\|html\|zip [--output <datei>]` |
| Anhang | `attach <page_id> <datei> [--name …]`, `attach <page_id> --link <url> --name …`, `get attachment <id> --output <datei>` |

- **Inhalt immer per Datei** (`--markdown-file`) - Markdown mit Backticks, `$` und
  `|` übersteht so jedes Shell-Quoting. Die Datei ins Projekt-`.tmp/` legen
  (fehlt es: `mkdir -m 700 .tmp`) und danach löschen.
- **`--tag` ersetzt bei `update` alle Tags.** Ohne `--tag` bleiben sie unverändert;
  zum Ergänzen erst `get` lesen und alle Tags mitgeben. Ebenso ersetzt
  `update shelf --books` die ganze Bücherliste - `shelve` hängt nur an.
- **Sortierung absteigend** mit Gleichheitszeichen: `--sort=-updated_at`.
- Nach dem Anlegen oder Ändern einer Seite den Link melden:
  `<BOOKSTACK_URL>/link/<page_id>`.

## Löschen

`delete <typ> <id>` zeigt ohne `--force` nur das Ziel und bricht mit Exit-Code 1 ab;
erst der zweite Aufruf mit `--force` löscht. Gelöscht wird nur auf ausdrückliche
Anweisung des Users.

- Regale, Bücher, Kapitel, Seiten landen im **Papierkorb**:
  `list recycle-bin`, `restore <deletion_id>`.
- **Endgültig** sind User, Rollen, Anhänge, Kommentare und
  `delete recycle-bin <deletion_id>`. Ein User hinterlässt Inhalte; mit
  `--migrate-ownership-id <user_id>` gehen sie an einen anderen.

## Admin

| Aufgabe | Aufruf |
|---|---|
| Version | `system` |
| User, Rollen | `list users --brief`, `list roles --brief`, `get user\|role <id>` |
| Audit-Log | `list audit-log --sort=-created_at --filter type=page_update --brief` |
| Rechte lesen | `permissions bookshelf\|book\|chapter\|page <id>` |
| Rechte setzen | `permissions book <id> --file <json>` |
| Alles andere | `docs <gruppe> [--endpoint create] --example`, dann `api POST\|PUT <pfad> --file <json>` |

- **Request-Body aus `docs` holen**, nicht aus dem Gedächtnis: `docs` liest die
  API-Referenz der laufenden Instanz und passt damit immer zu ihrer Version.
- **`role_permissions` ersetzt die ganze Liste.** Vor `permissions --file` den
  Bestand lesen und die unveränderten Rollen mitgeben; weggelassene Schlüssel
  (`owner_id`, `fallback_permissions`) bleiben unverändert.
- `api DELETE` verlangt `--force`; für Löschungen `delete` nehmen, das zeigt das
  Ziel vorher.

Instanz-Einstellungen (Name, Registrierung) haben keine API - die setzt der User in
der Oberfläche. Serverseitige Wartung (Artisan, Suchindex, Update) steht im
Infra-Wiki: `/wiki query BookStack`.
