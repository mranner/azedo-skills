# wiki - Remote-Wikis (read-only)

Wikis anderer Hosts per SSH abfragen.

## Remote-Wikis (read-only)

Ein Wiki, das auf einem **anderen Host** liegt, kann read-only abgefragt werden —
ohne lokale Kopie, ohne Sync. `query` ist reines Datei-Lesen (CLAUDE.md + index.md
lesen, Entities greppen, Treffer lesen, synthetisieren); genau dieser Read-Path
laeuft dann ueber SSH. Es wird **nie** remote ins Wiki geschrieben.

### Konfiguration: `.claude/wiki-remotes.json`

Im Projekt-Root unter `.claude/` (Tooling-Config, kein Wiki-Inhalt), projekt-relativ
aufgeloest wie `wiki/<name>/`:

```json
{
  "azedo": {
    "host": "mom",
    "path": "~/azedo.ai/wiki/azedo",
    "readonly": true
  }
}
```

- `host` — SSH-Ziel, muss per Key erreichbar sein (kein Passwort-Prompt im
  Agent-Kontext).
- `path` — Wiki-Root auf dem Host; `~` wird von der Remote-Shell expandiert.
- Enthaelt **keine Secrets** (nur Host/Pfad) → darf eingecheckt/geteilt werden.
- Optional `.claude/wiki-remotes.local.json` fuer maschinenlokale Remotes (analog zu
  Claudes `settings.local.json`) — nur bei realem Bedarf, nicht auf Vorrat.

### Lesen ueber SSH

Die User-Shell auf den Zielhosts ist `bash` (nicht die `csh` der root-Shell), daher
normales Quoting — kein `sh -c`-Wrapping noetig. `~` **innerhalb** des
remote-quotierten Strings lassen, damit die Remote-Shell expandiert; sonst expandiert
die lokale Shell auf das falsche Home:

```bash
# CLAUDE.md + Schema + Index lesen
ssh <host> "cat <path>/CLAUDE.md"
ssh <host> "cat <path>/index.md"

# Entities nach Begriffen durchsuchen, Treffer lesen
ssh <host> "grep -rl 'suchbegriff' <path>/wiki/"
ssh <host> "cat <path>/wiki/servers/fry-azedo-at.md"
```

`<host>`/`<path>` stammen aus dem Eintrag in `.claude/wiki-remotes.json`. Die Antwort
wird **lokal** aus den gelesenen Inhalten synthetisiert.

### Read-only erzwungen

Schreibende Subcommands (`ingest`, `compile`, `init`) sind fuer Remote-Wikis **nicht**
erlaubt — mit klarem Hinweis abbrechen, nichts remote schreiben. Neue Erkenntnisse
fuer ein Remote-Wiki werden nicht remote geschrieben, sondern mit `<remote>:handoff`
(siehe [handoff](pflege.md#handoff)) als lokale Note erzeugt und **manuell auf dem Zielhost**
eingepflegt (dort lokal `ingest`/`compile`/`lint`). Read-only ist damit *by
construction*, nicht per Konvention.

### Auf Entities anderer Wikis verweisen (Hints)

Ein Wikilink mit Präfix verweist über die Wiki-Grenze - auf ein **Nachbar-Wiki im
selben Projekt** ebenso wie auf ein **Remote-Wiki** auf einem anderen Host. Die
Schreibweise ist dieselbe und folgt der `<name>:`-Subcommand-Syntax:

```
Details zum Host im Infra-Wiki:  [[azedo:fry-azedo-at]]
Vorwissen im Nachbar-Wiki:       [[mathematik:schriftliches-dividieren]]
```

Der Linter löst das Präfix in dieser Reihenfolge auf:

1. **Lokales Nachbar-Wiki** - `wiki/<präfix>/` existiert im selben Projekt. Das Ziel
   wird direkt im Dateisystem gesucht (`wiki/<präfix>/wiki/**/<slug>.md`); fehlt es,
   ist der Link **tot**. Hier gibt es keine Nachsicht: anders als beim Remote liegt
   das Ziel greifbar da, es gibt also nichts zu vermuten.
2. **Remote-Wiki** - `<präfix>` ist ein Key in `.claude/wiki-remotes.json`. Der Link
   gilt als **gültiger Remote-Pointer** - kein toter Link, keine „Waise"-Folgefehler.
   Das Ziel wird im Default **nicht** geprüft (offline-sicher);
   `python3 "$SKILL_DIR/scripts/lint-wiki.py" --check-remotes <WIKI_ROOT>` verifiziert
   es on demand per SSH.
3. **Sonst** - unbekanntes Präfix, weiterhin **toter Link**.

Ist ein Präfix lokal *und* als Remote eingetragen, gewinnt der lokale Weg: er prüft
strenger und braucht kein SSH. Ein Verzeichnis unter `wiki/` ohne eigenen
`wiki/`-Unterordner zählt nicht als Wiki und löst kein Präfix auf.

Der Verweis ist in beiden Fällen **einseitig**: das andere Wiki weiß nichts davon.
Bestehende lokale `[[slug]]` ohne Präfix bleiben unverändert.

Bei `query` darf ein solcher Pointer aufgelöst werden (Ziel-Datei lesen, Antwort
anreichern): beim Nachbar-Wiki schlicht lokal lesen, beim Remote per SSH - siehe
Lesen ueber SSH oben.
