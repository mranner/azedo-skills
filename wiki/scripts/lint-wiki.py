#!/usr/bin/env python3

# stdlib only, no pip dependencies
# version 1.63.32

"""
lint-wiki.py — Strukturprüfung für LLM Wikis (Infra + Projekt-Doku).

Prüft:
- Frontmatter-Pflichtfelder pro Entity-Typ
- Wikilinks (tote Links, niedrige Konnektivität)
- Index-Einträge (fehlende Artikel im Index)
- Namenskonventionen (nur Kleinbuchstaben, Ziffern, Bindestriche)
- Verwaiste Seiten (keine eingehenden Links)
- Datumsangaben in Überschriften (Logbuch-Muster, siehe Schreibregeln)
- Optionale Vertrauensfelder verified/stale_after (Format, Ablauf)
- Optional: Frontmatter-Verweise (z.B. tests, config) gegen ihre Prüfqülle,
  konfiguriert unter "references" in wiki-schema.json
- Abschnittsverweise ([[x]], Abschnitt Y / Y-Abschnitt): gibt es Y in x noch?
- Mit --check-shrink: was eine Aktualisierung gegenüber git HEAD (ohne git:
  SVN-BASE) verloren hat

Präfix-Pointer [[<präfix>:<slug>]] werden in dieser Reihenfolge aufgelöst:

1. <präfix> ist ein Geschwister-Wiki unter <projekt-root>/wiki/<präfix>/ →
   lokaler Cross-Wiki-Pointer. Das Ziel wird direkt im Dateisystem geprüft
   (offline möglich), fehlt es, ist der Link tot.
2. <präfix> ist ein Key in der Remote-Config (~/.claude/wiki-remotes.json,
   <projekt-root>/.claude/wiki-remotes.json und -.local.json, in dieser
   Reihenfolge gemergt) → Remote-Pointer auf ein Wiki an einem anderen Host.
   Das Ziel wird im Default NICHT geprüft (offline-sicher); mit
   --check-remotes wird die Existenz per SSH (find) on demand verifiziert.
3. sonst toter Link.

Aufruf: python3 lint-wiki.py [--check-remotes] [--check-shrink] <wiki-root>
        z.B. python3 lint-wiki.py wiki/azedo/   (relativ zum Projekt-Root)

Keine externen Abhängigkeiten — reines Python 3.
"""

import sys
import re
import json
import subprocess
from datetime import date
from pathlib import Path
from collections import defaultdict

# Liegt im selben Verzeichnis; der Modulname trägt deshalb einen Unterstrich
# (siehe dortiger Docstring).
import wiki_remotes

# Eingebautes Default-Schema = Infra-Modell (Rückwärtskompatibilität).
# Greift, wenn im Wiki-Root keine wiki-schema.json liegt.
# required_common gilt für jeden Typ; die Liste pro Typ ergänzt typ-spezifische
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
    """Lädt das Entity-Modell aus <wiki-root>/wiki-schema.json.

    Fällt auf DEFAULT_SCHEMA (Infra-Modell) zurück, wenn keine Config existiert.
    Gibt (required_fields_pro_typ, set_der_gueltigen_typen, references) zurück;
    references ist {} ohne Eintrag im Schema.
    """
    schema_file = Path(wiki_root) / "wiki-schema.json"
    if schema_file.exists():
        data = json.loads(schema_file.read_text(encoding="utf-8"))
    else:
        data = DEFAULT_SCHEMA

    common = data.get("required_common", [])
    required = {t: common + extra for t, extra in data["types"].items()}
    return required, set(required.keys()), data.get("references", {})


def read_reference_source(path):
    """Text einer Prüfqülle: die Datei, oder alle Dateien darunter. None wenn sie fehlt."""
    if path.is_file():
        return path.read_text(encoding="utf-8", errors="replace")
    if path.is_dir():
        return "\n".join(f.read_text(encoding="utf-8", errors="replace")
                         for f in sorted(path.rglob("*")) if f.is_file())
    return None


def check_references(fm, references, sources):
    """Prüft Frontmatter-Verweise gegen ihre Prüfqülle (references im Schema).

    references: {feld: {"pattern": regex mit {name}, "path": ...}},
    sources: {feld: Quelltext}. Gibt die Meldungen zu nicht gefundenen Einträgen zurück.
    """
    found = []
    for field, spec in references.items():
        if field not in sources or fm.get(field) is None:
            continue
        values = fm[field] if isinstance(fm[field], list) else [fm[field]]
        for name in values:
            if not name:
                continue
            pattern = spec["pattern"].replace("{name}", re.escape(name))
            if not re.search(pattern, sources[field], re.M):
                found.append(f"{field}-Eintrag '{name}' nicht gefunden in {spec['path']}")
    return found


def load_remotes(wiki_root):
    """Lädt bekannte Remote-Wikis für das Projekt über wiki_root.

    Projekt-Root = wiki_root.parent.parent (Layout <projekt>/wiki/<name>/);
    welche Dateien gelesen und in welcher Reihenfolge sie gemergt werden, steht
    in wiki_remotes.py. Fehlt alles → leeres Dict (dann ist jeder [[x:y]]-Link
    mit unbekanntem x ein toter Link — wie bisher).
    """
    project_root = Path(wiki_root).resolve().parent.parent
    return wiki_remotes.load_remotes(project_root)


def load_local_wikis(wiki_root):
    """Findet Geschwister-Wikis unter <projekt-root>/wiki/<name>/.

    Layout <projekt>/wiki/<name>/ — Geschwister sind also die übrigen
    Verzeichnisse in wiki_root.parent, die selbst ein wiki/-Unterverzeichnis
    haben. Das eigene Wiki bleibt außen vor (dafür gibt es all_slugs).
    Gibt {name: Path} zurück.
    """
    local = {}
    wiki_root = Path(wiki_root).resolve()
    for d in sorted(wiki_root.parent.glob("*")):
        if d == wiki_root or not (d / "wiki").is_dir():
            continue
        local[d.name] = d
    return local


def local_wiki_slugs(wiki_path, _cache={}):
    """Slugs eines lokalen Wikis (Dateinamen ohne .md), gecacht pro Pfad."""
    key = str(wiki_path)
    if key not in _cache:
        _cache[key] = {f.stem for f in (wiki_path / "wiki").rglob("*.md")}
    return _cache[key]


FILENAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*\.md$")
WIKILINK_PATTERN = re.compile(r"\[\[([^\]|]+?)(?:\|[^\]]+?)?\]\]")
# Code-Bereiche, die von der Wikilink-Erkennung ausgenommen werden. Ein Regex
# wie `class[[:space:]]+timthumb` in einem Shell-Beispiel ist kein Wikilink —
# jede POSIX-Zeichenklasse sieht für WIKILINK_PATTERN wie [[...]] aus und
# wurde bis 1.34.3 als toter Link gemeldet.
# Fence: ``` oder ~~~ (auch länger), bis zum passenden Schluss-Fence oder EOF
# (ein unterminierter Block am Dateiende zählt komplett als Code).
CODE_FENCE_PATTERN = re.compile(
    r"^(?P<fence>```+|~~~+)[^\n]*\n.*?(?:^(?P=fence)[^\n]*$|\Z)",
    re.S | re.M,
)
# Inline-Code `...` bzw. ``...`` — die Backtick-Anzahl muss beidseitig passen.
INLINE_CODE_PATTERN = re.compile(r"(?<!`)(`+)(?!`).+?(?<!`)\1(?!`)", re.S)
# Präfix-Pointer [[<präfix>:<slug>]] — beide Teile in Slug-Schreibweise
REMOTE_TARGET_PATTERN = re.compile(r"^([a-z0-9-]+):([a-z0-9-]+)$")
MIN_WIKILINKS = 3

# Optionale Vertrauensfelder (nach Open Knowledge Format 0.2, dort verschachtelt,
# hier flach — der Frontmatter-Parser oben liest nur flaches YAML).
# verified: Liste von "<akteur>@<YYYY-MM-DD>", stale_after: ein ISO-Datum.
VERIFIED_PATTERN = re.compile(r"^([a-z0-9][a-z0-9.:_/-]*)@(\d{4}-\d{2}-\d{2})$")
ISO_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# Datum in einer Überschrift = Logbuch-Muster. Eine Überschrift benennt einen
# Gegenstand, kein Ereignis; "Umbau 2026-08-15" oder "Stand 2026-08-15" markiert
# eine Sitzung, die jemand mitgeschrieben hat. Diese Abschnitte wachsen monoton,
# weil die nächste Sitzung den nächsten anlegt, statt den alten zu ersetzen.
# Ein Datum im Fließtext ("seit 2026-08-15") ist unbedenklich und wird nicht
# geprüft. Siehe SKILL.md, Abschnitt Schreibregeln.
#
# Erkannt werden ISO (2026-08-15) und die deutsche Schreibweise (15.08.2026).
# Letztere verlangt ein vierstelliges Jahr, damit Versionsnummern ("8.2.33")
# und Abschnittsnummern nicht als Datum durchgehen.
DATED_HEADING_PATTERN = re.compile(
    r"^#{1,6}\s+.*?(\d{4}-\d{2}-\d{2}|\b\d{1,2}\.\d{1,2}\.(?:19|20)\d{2}\b|\bStand\s+\d{4}\b|\b(?:Q[1-4]|Jaenner|Januar|Februar|Maerz|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s+\d{4}\b)",
    re.M,
)


# Abschnitts-Überschriften ab Ebene 2 — die Gliederung eines Artikels. Ebene 1
# ist der Titel und steht genau einmal, die zählt nicht mit.
HEADING_PATTERN = re.compile(r"^#{2,6}\s+(.+?)\s*$")


def find_headings(text):
    """Überschriften ab Ebene 2 (Code-Blöcke ausgenommen)."""
    out = []
    in_fence = False
    for line in text.splitlines():
        if line.lstrip().startswith(("```", "~~~")):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = HEADING_PATTERN.match(line)
        if m:
            out.append(m.group(1))
    return out


# Verweis auf einen Abschnitt eines anderen Artikels. Formen im Bestand:
#   [[x]], Abschnitt Double-Hop      [[x]], Abschnitt „Lokale UCEPROTECT-Mirrors"
#   [[x]] (Double-Hop-Abschnitt)
# Ein Name in Anführungszeichen darf über den Zeilenumbruch laufen, ein
# nackter endet am Satzzeichen. Beschreibende Nennungen ("Abschnitt zu
# `localhost` in Jails") sind keine Namen und werden nicht geprüft.
SECTION_REF_PATTERNS = (
    re.compile(r"\[\[([^\]|]+?)\]\],?\s*\(?Abschnitt\s+[„\"»]([^\"“«]+)[\"“«]"),
    re.compile(r"\[\[([^\]|]+?)\]\],?\s*\(?Abschnitt\s+(?!(?:zu|zum|zur|über|ueber|oben|unten)\b)([^.,;:)\n\"„“«»]+)"),
    re.compile(r"\[\[([^\]|]+?)\]\]\s*\(([^()\n]+?)-Abschnitt\)"),
)


def normalize_heading(text):
    """Überschrift oder Abschnittsnennung ohne Markup, klein geschrieben."""
    return re.sub(r"[`*„“\"»«]", "", text).strip().lower()


def find_section_refs(text):
    """(ziel, abschnitt) für jeden Abschnittsverweis im Fließtext."""
    # Nur Codeblöcke entfernen: Inline-Code gehört oft zum Abschnittsnamen.
    prose = CODE_FENCE_PATTERN.sub("", text)
    refs = set()
    for pattern in SECTION_REF_PATTERNS:
        for m in pattern.finditer(prose):
            refs.add((m.group(1), " ".join(m.group(2).split())))
    return sorted(refs)


def section_exists(section, headings):
    """Nennt eine Überschrift des Ziels den Abschnitt?

    Genannt wird oft eine Kurzform ("Double-Hop" für "Double-Hop: SSH über
    Gateway ..."), deshalb reicht es, wenn alle Wörter der Nennung in einer
    Überschrift stehen.
    """
    words = [w for w in re.split(r"[\s/]+", normalize_heading(section)) if w]
    return any(all(w in normalize_heading(h) for w in words) for h in headings)


def find_dated_headings(text):
    """Überschriften mit Datumsangabe (Code-Blöcke ausgenommen).

    Gibt eine Liste (überschrift, treffer) zurück.
    """
    hits = []
    in_fence = False
    for line in text.splitlines():
        if line.lstrip().startswith(("```", "~~~")):
            in_fence = not in_fence
            continue
        if in_fence:
            continue

        # Bewusst auf der Rohzeile arbeiten, nicht auf strip_code(): dessen
        # Inline-Code-Entfernung würde `datei.php` aus der Überschrift
        # schneiden und die Meldung unlesbar machen.
        m = DATED_HEADING_PATTERN.match(line)
        if m:
            hits.append((line.strip(), m.group(1)))
    return hits


def parse_iso_date(value):
    """ISO-Datum → date, sonst None (auch bei 2026-02-31)."""
    if not isinstance(value, str) or not ISO_DATE_PATTERN.match(value.strip()):
        return None
    try:
        return date.fromisoformat(value.strip())
    except ValueError:
        return None


def check_trust_fields(fm, today=None):
    """Prüft die optionalen Felder verified und stale_after.

    Beide dürfen fehlen — geprüft wird nur, was dasteht. Gibt eine Liste
    (level, meldung) zurück, level ist "error" (kaputtes Format) oder
    "warning" (abgelaufen, Datum in der Zukunft).
    """
    today = today or date.today()
    found = []

    verified = fm.get("verified")
    if verified is not None:
        entries = verified if isinstance(verified, list) else [verified]
        for entry in entries:
            m = VERIFIED_PATTERN.match(str(entry).strip())
            if not m:
                found.append(("error", f"verified-Eintrag '{entry}' hat nicht die Form <akteur>@<YYYY-MM-DD>"))
                continue
            when = parse_iso_date(m.group(2))
            if when is None:
                found.append(("error", f"verified-Eintrag '{entry}' enthält kein gültiges Datum"))
            elif when > today:
                found.append(("warning", f"verified-Eintrag '{entry}' liegt in der Zukunft"))

    stale_after = fm.get("stale_after")
    if stale_after is not None:
        when = parse_iso_date(stale_after)
        if when is None:
            found.append(("error", f"stale_after '{stale_after}' ist kein ISO-Datum (YYYY-MM-DD)"))
        elif when <= today:
            found.append(("warning", f"Inhalt seit {when} überfällig (stale_after) — prüfen und Datum neu setzen"))

    return found


def parse_remote_target(target):
    """Zerlegt 'remote:slug' → (remote, slug); sonst None."""
    m = REMOTE_TARGET_PATTERN.match(target.strip())
    return (m.group(1), m.group(2)) if m else None


def check_remote_target(remote_conf, slug):
    """Prüft per SSH, ob <slug>.md im Remote-Wiki existiert.

    Gibt (True, None) bei Fund, (False, grund) sonst. Nutzt BatchMode (kein
    Passwort-Prompt). Nur bei --check-remotes aufgerufen.
    """
    host = remote_conf.get("host")
    path = remote_conf.get("path")
    if not host or not path:
        return False, "unvollständige Remote-Config (host/path)"
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
    """Extrahiert YAML-Frontmatter aus einer Markdown-Datei."""
    return parse_frontmatter_text(filepath.read_text(encoding="utf-8"))


def parse_frontmatter_text(text):
    """Extrahiert YAML-Frontmatter aus einem Markdown-Text.

    Einfacher Key-Value-Parser für flaches YAML-Frontmatter.
    Unterstützt: Strings, Listen (YAML-Inline [...] und mehrzeilig mit -),
    quoted Strings mit Wikilinks.
    """
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

        # Neuen Key gefunden — vorherige Liste abschließen
        current_list = None

        key = stripped[:colon_pos].strip()
        value = stripped[colon_pos + 1:].strip()

        if not value:
            # Nächste Zeilen könnten eine Liste sein
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


def strip_code(text):
    """Entfernt Code-Fences und Inline-Code aus dem Text.

    Damit zählt nur Fließtext als Wikilink-Quelle. Betrifft beide Auswertungen:
    tote Links (ein Regex im Code-Beispiel ist kein Link) und die Konnektivität
    (ein Link im Code-Block ist kein Beleg für Vernetzung).
    """
    text = CODE_FENCE_PATTERN.sub("", text)
    return INLINE_CODE_PATTERN.sub("", text)


def find_wikilinks(text):
    """Findet alle Wikilinks im Text (Code-Bereiche ausgenommen)."""
    return WIKILINK_PATTERN.findall(strip_code(text))


def check_filename(filepath):
    """Prüft ob der Dateiname der Konvention entspricht."""
    name = filepath.name
    if not FILENAME_PATTERN.match(name):
        return f"Dateiname '{name}' verletzt Namenskonvention (nur a-z, 0-9, -)"
    return None


def git_repo_root(path):
    """Repo-Wurzel über <path>, oder None wenn dort kein git-Repo liegt."""
    try:
        res = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=20,
        )
    except (subprocess.SubprocessError, OSError):
        return None
    return Path(res.stdout.strip()) if res.returncode == 0 else None


def git_show(repo_root, ref, rel_path):
    """Dateiinhalt aus einem git-Ref, oder None (neu, ungetrackt, kein Repo)."""
    try:
        res = subprocess.run(
            ["git", "-C", str(repo_root), "show", f"{ref}:{rel_path}"],
            capture_output=True, text=True, timeout=20,
        )
    except (subprocess.SubprocessError, OSError):
        return None
    return res.stdout if res.returncode == 0 else None


def svn_working_copy(path):
    """True, wenn <path> in einer SVN-Arbeitskopie liegt."""
    try:
        res = subprocess.run(
            ["svn", "info", str(path)],
            capture_output=True, text=True, timeout=20,
        )
    except (subprocess.SubprocessError, OSError):
        return False
    return res.returncode == 0


def svn_cat(path):
    """Dateiinhalt aus der SVN-BASE, oder None (neu, unversioniert)."""
    try:
        res = subprocess.run(
            ["svn", "cat", "-r", "BASE", str(path)],
            capture_output=True, text=True, timeout=20,
        )
    except (subprocess.SubprocessError, OSError):
        return None
    return res.stdout if res.returncode == 0 else None


def repointed_links(old_body, new_body):
    """Links, die an ihrer Stelle durch einen anderen Link ersetzt wurden.

    Beim Zerlegen eines Artikels werden eingehende Verweise umgehängt: aus
    "siehe [[a]]" wird "siehe [[b]]". Das ist kein Verlust, sondern der Zweck.
    Erkannt wird es zeilenweise: steht in einem geänderten Zeilenblock ein Link
    weniger und dafür ein neuer, gilt der alte als umgehängt.
    """
    import difflib
    old_lines = strip_code(old_body).splitlines()
    new_lines = strip_code(new_body).splitlines()
    moved = set()
    matcher = difflib.SequenceMatcher(None, old_lines, new_lines, autojunk=False)
    for op, i1, i2, j1, j2 in matcher.get_opcodes():
        if op != "replace":
            continue
        before = set(WIKILINK_PATTERN.findall("\n".join(old_lines[i1:i2])))
        after = set(WIKILINK_PATTERN.findall("\n".join(new_lines[j1:j2])))
        if after - before:
            moved |= before - after
    return moved


def check_shrink(old_text, new_text):
    """Was eine Aktualisierung an Inventar verloren hat.

    Gemeint ist nicht die Länge: Verdichten ist erwünscht (siehe
    Schreibregeln, "Aktualisieren heißt ersetzen"). Gemeint ist, was sich
    aufzählen lässt und damit auffällt, wenn es fehlt — ein Frontmatter-Feld,
    ein Abschnitt, ein Verweis auf eine andere Entity. Verschwindet davon etwas,
    ist das entweder eine gewollte Verdichtung oder ein Versehen beim
    Überschreiben; unterscheiden kann das nur ein Mensch, deshalb Warnung.

    Gibt eine Liste von Meldungen zurück.
    """
    old_fm, old_body = parse_frontmatter_text(old_text)
    new_fm, new_body = parse_frontmatter_text(new_text)
    found = []

    lost_keys = sorted(set(old_fm or {}) - set(new_fm or {}))
    if lost_keys:
        found.append(f"Frontmatter-Feld entfernt: {', '.join(lost_keys)}")

    lost_headings = [h for h in find_headings(old_body) if h not in find_headings(new_body)]
    if lost_headings:
        shown = ", ".join(f"\"{h}\"" for h in lost_headings[:5])
        more = f" (und {len(lost_headings) - 5} weitere)" if len(lost_headings) > 5 else ""
        found.append(f"Abschnitt entfernt: {shown}{more}")

    lost_links = sorted(
        set(find_wikilinks(old_body)) - set(find_wikilinks(new_body))
        - repointed_links(old_body, new_body)
    )
    if lost_links:
        shown = ", ".join(f"[[{t}]]" for t in lost_links[:5])
        more = f" (und {len(lost_links) - 5} weitere)" if len(lost_links) > 5 else ""
        found.append(f"Wikilink entfernt: {shown}{more}")

    return found


def lint_wiki(wiki_root, check_remotes=False, check_shrink_flag=False):
    """Hauptfunktion: prüft das gesamte Wiki."""
    wiki_root = Path(wiki_root)
    wiki_dir = wiki_root / "wiki"
    index_file = wiki_root / "index.md"

    if not wiki_dir.exists():
        print(f"FEHLER: Wiki-Verzeichnis nicht gefunden: {wiki_dir}")
        return 1

    # Entity-Modell pro Wiki laden (Config oder Infra-Default)
    required_fields, valid_types, references = load_schema(wiki_root)

    # Bekannte Ziele für [[<präfix>:<slug>]]-Pointer: erst die lokalen
    # Geschwister-Wikis, dann die Remotes.
    local_wikis = load_local_wikis(wiki_root)
    remotes = load_remotes(wiki_root)

    errors = []
    warnings = []

    # Prüfqüllen der Frontmatter-Verweise, Pfade relativ zum Projekt-Root
    project_root = wiki_root.resolve().parent.parent
    reference_sources = {}
    for field, spec in references.items():
        text = read_reference_source(project_root / spec["path"])
        if text is None:
            errors.append(f"wiki-schema.json: Prüfqülle für '{field}' fehlt: {spec['path']}")
        else:
            reference_sources[field] = text

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

    # Pro Artikel prüfen
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

        # Optionale Vertrauensfelder
        for level, msg in check_trust_fields(fm):
            (errors if level == "error" else warnings).append(f"{prefix}: {msg}")

        # Verweise auf Tests, Config usw. (nur mit references im Schema)
        for msg in check_references(fm, references, reference_sources):
            errors.append(f"{prefix}: {msg}")

        # Wikilinks zählen — Frontmatter-Werte + Body
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

        # Datum in Überschriften — Logbuch statt Artikel
        for heading, hit in find_dated_headings(body):
            short = heading if len(heading) <= 60 else heading[:57] + "…"
            warnings.append(
                f"{prefix}: Datum in Überschrift ({hit}) — \"{short}\"; "
                f"Zustand beschreiben statt Verlauf, Datum in den Fließtext"
            )

    # Tote Links (Remote-Pointer [[<remote>:<slug>]] ausgenommen, wenn <remote> bekannt)
    remote_pointers = []  # (source_slug, remote_name, target_slug)
    for slug, targets in outgoing_links.items():
        for target in targets:
            if target in all_slugs:
                continue
            rp = parse_remote_target(target)
            if rp and rp[0] in local_wikis:
                # lokales Nachbar-Wiki — Ziel direkt im Dateisystem prüfbar
                if rp[1] in local_wiki_slugs(local_wikis[rp[0]]):
                    continue
                errors.append(f"{articles[slug]['rel_path']}: Toter Wikilink [[{target}]] — Ziel existiert nicht im Wiki '{rp[0]}'")
                continue
            if rp and rp[0] in remotes:
                # gültiger Remote-Pointer — kein toter Link (Default offline-sicher)
                remote_pointers.append((slug, rp[0], rp[1]))
                continue
            errors.append(f"{articles[slug]['rel_path']}: Toter Wikilink [[{target}]] — Ziel existiert nicht")

    # Abschnittsverweise: das Ziel existiert, der genannte Abschnitt vielleicht
    # nicht mehr. Nach dem Zerlegen eines Sammelartikels zeigen solche Verweise
    # weiter auf den Rumpf, während das Thema längst in einem neuen Artikel
    # steht - der Link selbst ist nicht tot und fällt deshalb sonst nicht auf.
    for slug, info in articles.items():
        for target, section in find_section_refs(info["body"]):
            if target not in articles:
                continue
            if not section_exists(section, find_headings(articles[target]["body"])):
                warnings.append(
                    f"{info['rel_path']}: Abschnittsverweis [[{target}]] \"{section}\" — "
                    f"diesen Abschnitt gibt es dort nicht (mehr); Verweis auf den neuen Ort umhängen"
                )

    # Tote Links in log.md und index.md. Beide liegen eine Ebene über wiki/ und
    # sind damit nicht in der Sammlung oben — sie stehen aber voller Wikilinks.
    # Als Quelle zählen sie, als Ziel nicht: sonst meldeten sie sich selbst als
    # verwaiste Seite und als nicht im Index gelistet. Warnung statt Fehler, weil
    # log.md historisch ist — ein alter Eintrag darf auf einen seither
    # aufgelösten Artikel zeigen, ohne dass der Lauf fehlschlägt.
    for extra_file in (wiki_root / "log.md", index_file):
        if not extra_file.exists():
            continue
        for target in sorted(set(find_wikilinks(extra_file.read_text(encoding="utf-8")))):
            if target in all_slugs:
                continue
            rp = parse_remote_target(target)
            if rp and rp[0] in local_wikis:
                if rp[1] in local_wiki_slugs(local_wikis[rp[0]]):
                    continue
                warnings.append(f"{extra_file.name}: Toter Wikilink [[{target}]] — Ziel existiert nicht im Wiki '{rp[0]}'")
                continue
            if rp and rp[0] in remotes:
                continue
            warnings.append(f"{extra_file.name}: Toter Wikilink [[{target}]] — Ziel existiert nicht")

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

    # Index-Einträge prüfen
    if index_file.exists():
        # Gleiche Regel wie bei den Wikilinks: ein [[slug]] in einem Code-Block
        # des Index ist ein Beispiel, kein Index-Eintrag.
        index_text = strip_code(index_file.read_text(encoding="utf-8"))
        for slug in all_slugs:
            if f"[[{slug}]]" not in index_text:
                warnings.append(f"{articles[slug]['rel_path']}: Nicht in index.md gelistet")
    else:
        errors.append("index.md nicht gefunden")

    # Optional: was die Arbeitskopie gegenüber git HEAD bzw. SVN-BASE verloren hat
    if check_shrink_flag:
        repo_root = git_repo_root(wiki_root)
        if repo_root is not None:
            def base_text(path):
                return git_show(repo_root, "HEAD", path.resolve().relative_to(repo_root))
        elif svn_working_copy(wiki_root):
            base_text = svn_cat
        else:
            base_text = None
            warnings.append("--check-shrink: weder git-Repo noch SVN-Arbeitskopie über dem Wiki gefunden, übersprungen")
        if base_text is not None:
            for slug in sorted(articles):
                info = articles[slug]
                new_text = info["path"].read_text(encoding="utf-8")
                old_text = base_text(info["path"])
                if old_text is None or old_text == new_text:
                    continue
                for msg in check_shrink(old_text, new_text):
                    warnings.append(f"{info['rel_path']}: {msg} — gewollt verdichtet oder beim Überschreiben verloren?")

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

    check_shrink_flag = False
    if "--check-shrink" in args:
        check_shrink_flag = True
        args.remove("--check-shrink")

    if len(args) != 1:
        print(f"Aufruf: {sys.argv[0]} [--check-remotes] [--check-shrink] <wiki-root>")
        print(f"  z.B.: {sys.argv[0]} wiki/azedo/")
        print(f"  --check-remotes: [[<remote>:<slug>]]-Ziele per SSH verifizieren")
        print(f"  --check-shrink:  Frontmatter-Felder, Abschnitte und Wikilinks melden,")
        print(f"                   die die Arbeitskopie gegenüber git HEAD bzw. SVN-BASE verloren hat")
        sys.exit(2)
    sys.exit(lint_wiki(args[0], check_remotes=check_remotes,
                       check_shrink_flag=check_shrink_flag))
