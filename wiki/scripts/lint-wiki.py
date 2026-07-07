#!/usr/bin/env python3

# stdlib only, no pip dependencies
# version 1.15.0

"""
lint-wiki.py — Strukturpruefung fuer LLM Wikis (Infra + Projekt-Doku).

Prueft:
- Frontmatter-Pflichtfelder pro Entity-Typ
- Wikilinks (tote Links, niedrige Konnektivitaet)
- Index-Eintraege (fehlende Artikel im Index)
- Namenskonventionen (nur Kleinbuchstaben, Ziffern, Bindestriche)
- Verwaiste Seiten (keine eingehenden Links)

Remote-Pointer: Wikilinks der Form [[<remote>:<slug>]] verweisen auf ein Wiki
auf einem anderen Host. Ist <remote> ein Key in <projekt-root>/.claude/
wiki-remotes.json, gilt der Link als gueltig (kein toter Link) — das Ziel wird im
Default NICHT geprueft (offline-sicher). Mit --check-remotes wird die Existenz per
SSH (find) on demand verifiziert. Unbekanntes Praefix → weiterhin toter Link.

Aufruf: python3 lint-wiki.py [--check-remotes] <wiki-root>
        z.B. python3 lint-wiki.py wiki/azedo/   (relativ zum Projekt-Root)

Keine externen Abhaengigkeiten — reines Python 3.
"""

import sys
import re
import json
import subprocess
from pathlib import Path
from collections import defaultdict

# Eingebautes Default-Schema = Infra-Modell (Rueckwaertskompatibilitaet).
# Greift, wenn im Wiki-Root keine wiki-schema.json liegt.
# required_common gilt fuer jeden Typ; die Liste pro Typ ergaenzt typ-spezifische
# Pflichtfelder. Effektive Pflichtfelder = required_common + types[typ].
DEFAULT_SCHEMA = {
    "required_common": ["date", "tags", "type", "status", "kunde"],
    "types": {
        "server": ["hostname", "ip", "os", "location", "roles"],
        "service": ["runs-on", "port"],
        "access": ["target", "method"],
        "site": ["location", "network-segments"],
        "procedure": ["applies-to"],
    },
}


def load_schema(wiki_root):
    """Laedt das Entity-Modell aus <wiki-root>/wiki-schema.json.

    Faellt auf DEFAULT_SCHEMA (Infra-Modell) zurueck, wenn keine Config existiert.
    Gibt (required_fields_pro_typ, set_der_gueltigen_typen) zurueck.
    """
    schema_file = Path(wiki_root) / "wiki-schema.json"
    if schema_file.exists():
        data = json.loads(schema_file.read_text(encoding="utf-8"))
    else:
        data = DEFAULT_SCHEMA

    common = data.get("required_common", [])
    required = {t: common + extra for t, extra in data["types"].items()}
    return required, set(required.keys())


def load_remotes(wiki_root):
    """Laedt bekannte Remote-Wikis aus <projekt-root>/.claude/wiki-remotes.json.

    Projekt-Root = wiki_root.parent.parent (Layout <projekt>/wiki/<name>/).
    Mergt optional wiki-remotes.local.json darueber. Fehlt alles → leeres Dict
    (dann ist jeder [[x:y]]-Link mit unbekanntem x ein toter Link — wie bisher).
    Gibt {name: {"host": ..., "path": ...}} zurueck.
    """
    remotes = {}
    project_root = Path(wiki_root).resolve().parent.parent
    for fname in ("wiki-remotes.json", "wiki-remotes.local.json"):
        f = project_root / ".claude" / fname
        if f.exists():
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    remotes.update(data)
            except (json.JSONDecodeError, OSError):
                pass
    return remotes


FILENAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*\.md$")
WIKILINK_PATTERN = re.compile(r"\[\[([^\]|]+?)(?:\|[^\]]+?)?\]\]")
# Remote-Pointer [[<remote>:<slug>]] — beide Teile in Slug-Schreibweise
REMOTE_TARGET_PATTERN = re.compile(r"^([a-z0-9-]+):([a-z0-9-]+)$")
MIN_WIKILINKS = 3


def parse_remote_target(target):
    """Zerlegt 'remote:slug' → (remote, slug); sonst None."""
    m = REMOTE_TARGET_PATTERN.match(target.strip())
    return (m.group(1), m.group(2)) if m else None


def check_remote_target(remote_conf, slug):
    """Prueft per SSH, ob <slug>.md im Remote-Wiki existiert.

    Gibt (True, None) bei Fund, (False, grund) sonst. Nutzt BatchMode (kein
    Passwort-Prompt). Nur bei --check-remotes aufgerufen.
    """
    host = remote_conf.get("host")
    path = remote_conf.get("path")
    if not host or not path:
        return False, "unvollstaendige Remote-Config (host/path)"
    cmd = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8", host,
           f"find {path}/wiki -type f -name '{slug}.md'"]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
    except (subprocess.SubprocessError, OSError) as exc:
        return False, f"SSH-Fehler ({exc})"
    if res.returncode != 0:
        return False, f"SSH-Exit {res.returncode}"
    return (True, None) if res.stdout.strip() else (False, "Ziel nicht gefunden")


def parse_frontmatter(filepath):
    """Extrahiert YAML-Frontmatter aus einer Markdown-Datei.

    Einfacher Key-Value-Parser fuer flaches YAML-Frontmatter.
    Unterstuetzt: Strings, Listen (YAML-Inline [...] und mehrzeilig mit -),
    quoted Strings mit Wikilinks.
    """
    text = filepath.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None, text

    # Frontmatter-Block extrahieren
    end_match = re.search(r"\n---\s*\n", text[3:])
    if not end_match:
        return None, text

    fm_text = text[4:end_match.start() + 3]
    body = text[end_match.end() + 3:]

    fm = {}
    current_key = None
    current_list = None

    for line in fm_text.split("\n"):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # Mehrzeilige Liste (- item)
        if stripped.startswith("- ") and current_key and current_list is not None:
            val = stripped[2:].strip().strip('"').strip("'")
            current_list.append(val)
            fm[current_key] = current_list
            continue

        # Key: Value Zeile
        colon_pos = stripped.find(":")
        if colon_pos == -1:
            continue

        # Neuen Key gefunden — vorherige Liste abschliessen
        current_list = None

        key = stripped[:colon_pos].strip()
        value = stripped[colon_pos + 1:].strip()

        if not value:
            # Naechste Zeilen koennten eine Liste sein
            current_key = key
            current_list = []
            fm[key] = current_list
            continue

        current_key = key

        # Inline-Liste [a, b, c]
        if value.startswith("[") and value.endswith("]"):
            items = value[1:-1].split(",")
            fm[key] = [item.strip().strip('"').strip("'") for item in items if item.strip()]
            current_list = fm[key]
            continue

        # Quoted string
        if (value.startswith('"') and value.endswith('"')) or \
           (value.startswith("'") and value.endswith("'")):
            fm[key] = value[1:-1]
            continue

        fm[key] = value

    return fm, body


def find_wikilinks(text):
    """Findet alle Wikilinks im Text."""
    return WIKILINK_PATTERN.findall(text)


def check_filename(filepath):
    """Prueft ob der Dateiname der Konvention entspricht."""
    name = filepath.name
    if not FILENAME_PATTERN.match(name):
        return f"Dateiname '{name}' verletzt Namenskonvention (nur a-z, 0-9, -)"
    return None


def lint_wiki(wiki_root, check_remotes=False):
    """Hauptfunktion: prueft das gesamte Wiki."""
    wiki_root = Path(wiki_root)
    wiki_dir = wiki_root / "wiki"
    index_file = wiki_root / "index.md"

    if not wiki_dir.exists():
        print(f"FEHLER: Wiki-Verzeichnis nicht gefunden: {wiki_dir}")
        return 1

    # Entity-Modell pro Wiki laden (Config oder Infra-Default)
    required_fields, valid_types = load_schema(wiki_root)

    # Bekannte Remote-Wikis (fuer [[<remote>:<slug>]]-Pointer)
    remotes = load_remotes(wiki_root)

    errors = []
    warnings = []

    # Alle Wiki-Artikel sammeln
    articles = {}
    all_slugs = set()
    incoming_links = defaultdict(set)
    outgoing_links = defaultdict(set)

    for md_file in wiki_dir.rglob("*.md"):
        rel_path = md_file.relative_to(wiki_dir)
        slug = md_file.stem
        all_slugs.add(slug)
        fm, body = parse_frontmatter(md_file)
        articles[slug] = {
            "path": md_file,
            "rel_path": rel_path,
            "frontmatter": fm,
            "body": body,
        }

    # Pro Artikel pruefen
    for slug, info in articles.items():
        filepath = info["path"]
        fm = info["frontmatter"]
        body = info["body"]
        prefix = f"{info['rel_path']}"

        # Dateiname
        err = check_filename(filepath)
        if err:
            errors.append(f"{prefix}: {err}")

        # Frontmatter vorhanden?
        if fm is None:
            errors.append(f"{prefix}: Kein YAML-Frontmatter gefunden")
            continue

        # type-Feld
        entity_type = fm.get("type")
        if not entity_type:
            errors.append(f"{prefix}: Pflichtfeld 'type' fehlt")
            continue

        if entity_type not in valid_types:
            errors.append(f"{prefix}: Unbekannter Typ '{entity_type}' (erlaubt: {', '.join(sorted(valid_types))})")
            continue

        # Pflichtfelder
        for field in required_fields[entity_type]:
            if field not in fm or fm[field] is None:
                errors.append(f"{prefix}: Pflichtfeld '{field}' fehlt (Typ: {entity_type})")

        # Wikilinks zaehlen — Frontmatter-Werte + Body
        fm_str = "\n".join(
            v if isinstance(v, str) else " ".join(v) if isinstance(v, list) else str(v)
            for v in fm.values()
        )
        full_text = fm_str + "\n" + body
        links = find_wikilinks(full_text)
        outgoing_links[slug] = set(links)

        for link_target in links:
            incoming_links[link_target].add(slug)

        if len(links) < MIN_WIKILINKS:
            warnings.append(f"{prefix}: Nur {len(links)} Wikilinks (Minimum: {MIN_WIKILINKS})")

    # Tote Links (Remote-Pointer [[<remote>:<slug>]] ausgenommen, wenn <remote> bekannt)
    remote_pointers = []  # (source_slug, remote_name, target_slug)
    for slug, targets in outgoing_links.items():
        for target in targets:
            if target in all_slugs:
                continue
            rp = parse_remote_target(target)
            if rp and rp[0] in remotes:
                # gueltiger Remote-Pointer — kein toter Link (Default offline-sicher)
                remote_pointers.append((slug, rp[0], rp[1]))
                continue
            errors.append(f"{articles[slug]['rel_path']}: Toter Wikilink [[{target}]] — Ziel existiert nicht")

    # Optional: Remote-Pointer-Ziele per SSH verifizieren
    if check_remotes and remote_pointers:
        for src, rname, tslug in remote_pointers:
            ok, reason = check_remote_target(remotes[rname], tslug)
            if not ok:
                warnings.append(f"{articles[src]['rel_path']}: Remote-Pointer [[{rname}:{tslug}]] — {reason}")

    # Verwaiste Seiten
    for slug in all_slugs:
        if slug not in incoming_links or len(incoming_links[slug]) == 0:
            warnings.append(f"{articles[slug]['rel_path']}: Verwaiste Seite — keine eingehenden Links")

    # Index-Eintraege pruefen
    if index_file.exists():
        index_text = index_file.read_text(encoding="utf-8")
        for slug in all_slugs:
            if f"[[{slug}]]" not in index_text:
                warnings.append(f"{articles[slug]['rel_path']}: Nicht in index.md gelistet")
    else:
        errors.append("index.md nicht gefunden")

    # Ergebnis ausgeben
    print(f"\n{'='*60}")
    print(f"Wiki Lint Report — {wiki_root}")
    print(f"{'='*60}")
    print(f"\nArtikel gesamt: {len(articles)}")

    # Statistik pro Typ
    type_counts = defaultdict(int)
    for info in articles.values():
        if info["frontmatter"] and "type" in info["frontmatter"]:
            type_counts[info["frontmatter"]["type"]] += 1
    for t in sorted(type_counts):
        print(f"  {t}: {type_counts[t]}")

    if errors:
        print(f"\nFEHLER ({len(errors)}):")
        for e in sorted(errors):
            print(f"  x {e}")

    if warnings:
        print(f"\nWARNUNGEN ({len(warnings)}):")
        for w in sorted(warnings):
            print(f"  ! {w}")

    if not errors and not warnings:
        print("\nKeine Probleme gefunden.")

    print()
    return 1 if errors else 0


if __name__ == "__main__":
    args = sys.argv[1:]
    check_remotes = False
    if "--check-remotes" in args:
        check_remotes = True
        args.remove("--check-remotes")

    if len(args) != 1:
        print(f"Aufruf: {sys.argv[0]} [--check-remotes] <wiki-root>")
        print(f"  z.B.: {sys.argv[0]} wiki/azedo/")
        print(f"  --check-remotes: [[<remote>:<slug>]]-Ziele per SSH verifizieren")
        sys.exit(2)
    sys.exit(lint_wiki(args[0], check_remotes=check_remotes))
