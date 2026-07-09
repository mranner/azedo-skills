---
name: md2pdf
description: >
  Rendert Markdown zu einem "schoenen" PDF (Typora-naher Look) via pandoc ->
  HTML (CSS+SVG inline) -> headless Chrome. Mermaid-Bloecke werden via mmdc
  gerendert. Nutze diesen Skill wenn der User aus einer .md-Datei ein PDF
  erzeugen will, Doku als PDF exportieren oder versenden moechte.
  Auch aktiv verwenden wenn der User sagt "mach ein PDF draus",
  "Markdown zu PDF", "Doku als PDF exportieren", o.ae.
  Trigger: /md2pdf.
---

# md2pdf -- Markdown zu "schoenem" PDF

Rendert eine Markdown-Datei ueber das gebundelte Shell-Script `md2pdf` (bash,
im Skill-Verzeichnis) zu einem PDF mit Typora-nahem Look.

**Pipeline:** `pandoc` -> self-contained HTML (CSS + SVG inline) -> headless
Chrome `--print-to-pdf`. Kein LaTeX noetig. Laeuft unter macOS, Linux und FreeBSD.

**Aufruf:** `"$SKILL_DIR/md2pdf" <input.md> [output.pdf] [--css <file>] [--no-mermaid]`

`$SKILL_DIR` ist das Base Directory dieses Skills (dort wo diese SKILL.md liegt).

```bash
# Standard: PDF neben die .md legen (gleicher Name, .pdf-Endung)
"$SKILL_DIR/md2pdf" docs/Datenmodell_Entwurf.md

# Expliziter Ausgabepfad
"$SKILL_DIR/md2pdf" docs/Review.md /home/mmuster/out/review.pdf

# Ohne Mermaid-Rendering (Bloecke bleiben als Code)
"$SKILL_DIR/md2pdf" docs/Review.md --no-mermaid

# Eigenes CSS statt des eingebauten Stylesheets
"$SKILL_DIR/md2pdf" docs/Review.md --css my-style.css
```

**Wichtig:** Ohne `output.pdf` wird die neben der `.md` liegende `.pdf`
**ueberschrieben** (gleicher Basisname). Bei Bedarf expliziten Ausgabepfad angeben.

## Voraussetzungen

| Tool                | Pflicht | Paket / Installation                                  |
|---------------------|---------|-------------------------------------------------------|
| `pandoc`            | ja      | macOS `brew install pandoc`, FreeBSD `pkg install hs-pandoc`, Linux `apt/dnf install pandoc` |
| Chrome / Chromium   | ja      | macOS Google Chrome, FreeBSD `pkg install chromium` (Binary heisst `chrome`), Linux `apt/dnf install chromium` |
| `mmdc` (mermaid-cli)| nein    | `npm i -g @mermaid-js/mermaid-cli` (nur fuer ```mermaid-Bloecke) |
| `bash`              | ja      | FreeBSD `pkg install bash` (unter `/usr/local/bin/bash`) |

Fehlt `mmdc`, degradiert das Script sauber: Mermaid-Bloecke bleiben als Code und
es wird eine Warnung ausgegeben (kein Abbruch).

## Was funktioniert

- Tabellen, Code-Bloecke, Blockquotes gestylt (GitHub/Typora-artig)
- Inline-SVG (z.B. eingebettete ER-Diagramme) scharf im PDF
- Mermaid-Bloecke (```mermaid) via `mmdc` als SVG gerendert (wenn installiert)
- Plattformuebergreifender Font-Stack (macOS/Linux/BSD)

## Optionen

| Option         | Beschreibung                                        |
|----------------|-----------------------------------------------------|
| `--css <file>` | Eigenes Stylesheet statt des eingebauten            |
| `--no-mermaid` | Mermaid-Rendering ausschalten (Bloecke als Code)    |

## Env-Overrides

| Variable        | Zweck                                                       |
|-----------------|-------------------------------------------------------------|
| `MD2PDF_CHROME` | Pfad zur Chrome/Chromium-Binary erzwingen (wenn Auto-Discovery fehlschlaegt) |

## Troubleshooting

- **"Kein Chrome/Chromium gefunden"** -> Binary-Pfad per `MD2PDF_CHROME=<pfad>`
  setzen. Auf FreeBSD installiert `www/chromium` das Binary als `chrome`.
- **Chrome startet nicht als root / in einer Jail** -> das Script setzt auf
  Linux/FreeBSD bereits `--no-sandbox --disable-dev-shm-usage`. Bleibt es leer,
  Chrome-Version pruefen.
- **Mermaid-Diagramm bleibt leer / als Code** -> `mmdc` installieren
  (`npm i -g @mermaid-js/mermaid-cli`). Auf Linux/FreeBSD nutzt `mmdc` intern
  Puppeteer-Chromium; das Script uebergibt automatisch eine Puppeteer-Config mit
  `--no-sandbox`. Notfalls `PUPPETEER_EXECUTABLE_PATH` auf das System-Chromium setzen.
- **Fonts sehen haesslich aus** -> Noto/DejaVu-Fonts installieren
  (Linux `fonts-noto` / `dejavu`, FreeBSD `pkg install noto-basic dejavu`).
