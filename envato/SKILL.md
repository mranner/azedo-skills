---
name: envato
description: >
  Envato Market (ThemeForest, CodeCanyon): Kaeufe auflisten, Items
  herunterladen, Kaufdetails anzeigen. Nutze diesen Skill wenn der User
  ein Theme oder Plugin von ThemeForest/CodeCanyon herunterladen, Kaeufe
  durchsuchen oder Kaufdetails abrufen will.
  Trigger: /envato.
---

# envato -- Envato Market (ThemeForest, CodeCanyon)

Kaeufe und Downloads werden ueber das gebundelte Script `envato` (Python >=3.11, im Skill-Verzeichnis) verwaltet.

**Aufruf:** `python3 "$SKILL_DIR/envato" <subcommand> [options]`

`$SKILL_DIR` ist das Base Directory dieses Skills (dort wo diese SKILL.md liegt).

## Setup

1. Personal Token auf https://build.envato.com/create-token/ erstellen mit den Berechtigungen:
   - **Download your purchased items** (purchase:download)
   - **List purchases** (purchase:list)
   - **View your items' sales history** (optional)

2. Token in `.env` eintragen (im Arbeitsverzeichnis oder `~/.env`):
   ```
   ENVATO_TOKEN=your_token_here
   ```

3. Verbindung testen:
   ```bash
   python3 "$SKILL_DIR/envato" ping
   ```

## Subcommands

### Verbindung testen

```bash
python3 "$SKILL_DIR/envato" ping
```

### Kaeufe auflisten

```bash
python3 "$SKILL_DIR/envato" list-purchases [--page <n>] [--filter-by <filter>]
```

Filter-Werte: `wordpress-themes`, `wordpress-plugins`, `site-templates`, etc.

### Kaufdetails abrufen

```bash
python3 "$SKILL_DIR/envato" get-purchase <purchase_code>
```

### Item herunterladen

```bash
# Via Item-ID
python3 "$SKILL_DIR/envato" download --item-id <id> [-o /pfad/zur/datei.zip]

# Via Purchase-Code
python3 "$SKILL_DIR/envato" download --purchase-code <code> [-o /pfad/zur/datei.zip]
```

Ohne `-o` wird die Download-URL als JSON ausgegeben. Mit `-o` wird die Datei direkt heruntergeladen.

### Item-Details anzeigen

```bash
python3 "$SKILL_DIR/envato" item-details <item_id>
```

### Items suchen

```bash
python3 "$SKILL_DIR/envato" search "<suchbegriff>" [--site themeforest.net] [--sort <sort>] [--page <n>]
```

Sort-Werte: `relevance`, `rating`, `date`, `sales`, `price`.

### Account-Infos

```bash
python3 "$SKILL_DIR/envato" user-account
python3 "$SKILL_DIR/envato" user-email
```

## Workflow

1. Parameter aus der Nutzeranfrage ableiten (Item-Name, ID, Purchase-Code).
2. Falls Item-ID unbekannt: `list-purchases` ausfuehren und das gewuenschte Item identifizieren.
3. Download via `download --item-id <id> -o <pfad>`.
4. Ergebnis dem User melden (Dateipfad, Groesse).

## Hinweise

- Config (`ENVATO_TOKEN`) wird aus `.env` im aktuellen Arbeitsverzeichnis gelesen (oder via `ENVATO_ENV` Environment-Variable, Fallback `~/.env`).
- Temporaere Dateien und Downloads gehoeren ins Projekt-Verzeichnis `.tmp/`, **nicht** in `$SKILL_DIR/.tmp/`.
- Output ist JSON — relevante Felder extrahieren und lesbar darstellen.
- Der Download-Endpunkt liefert eine temporaere URL, die nur kurz gueltig ist.
- Bei WordPress-Themes liefert die API getrennte URLs fuer "Installable WordPress file only" und "All files & documentation".
