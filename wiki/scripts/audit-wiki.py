#!/usr/bin/env python3

# stdlib only, no pip dependencies
# version 1.51.4

"""
audit-wiki.py — misst Aufblähung und überholte Historie in LLM-Wikis.

Abgrenzung zu lint-wiki.py: der Linter meldet **Fehler** (tote Links, fehlende
Pflichtfelder) und liefert Exit 1. Dieses Script meldet **Bewertungen** — es gibt
keine falschen Dateien, nur auffällige. Exit ist deshalb immer 0, ausser bei
einem Aufrufproblem (2).

Gemessen wird je Artikel:
- Zeilen relativ zum p90 des eigenen Entity-Typs (eine access-Entity mit 90
  Zeilen ist auffällig, eine procedure mit 90 Zeilen ist normal)
- Historie-Dichte: Datumsangaben, "Session", CR-Nummern — im ganzen Artikel,
  "## Quellen" eingeschlossen
- Logbuch: datierte Aufzaehlungspunkte unter "## Quellen". Dort gehoert die
  Rohquelle hin, nicht die Chronologie der eigenen Sessions
- typfremder Inhalt: Codeblöcke und FALSCH/RICHTIG-Rezepte in server-, service-,
  access- oder site-Entities (gehört in eine procedure)
- dominanter Abschnitt: ein Kapitel frisst den Grossteil der Datei — nur
  gemeldet, wenn zusaetzlich Umfang oder Historie auffaellt
- Strukturtiefe: Anzahl H3 und Verschachtelung ab H4 (Punkte nur mit Befund)

Zusätzlich schlägt das Script je auffälligem Artikel bestehende Procedures als
Verschiebeziel vor (Wortüberlappung Überschrift ↔ Procedure-Slug). Das ist ein
Hinweis für die anschliessende Handarbeit, keine Entscheidung.

Aufruf: python3 audit-wiki.py [--type <typ>] [--path <teilpfad>]
                              [--top <n>] [--all] [--json] <wiki-root>

Die Baseline (p90 je Typ) wird immer über das **ganze** Wiki gerechnet, auch wenn
die Ausgabe per --type/--path eingeschränkt ist — sonst verschiebt der Filter den
Massstab.
"""

import sys
import re
import json
import math
from pathlib import Path
from collections import defaultdict

# Absolute Untergrenzen je Typ. Verhindern, dass in einem jungen Wiki mit
# durchweg kurzen Artikeln schon 60 Zeilen als "aufgeblaeht" gelten. Wirksam ist
# immer max(p90_des_typs, floor).
SIZE_FLOOR = {
    "server": 150,
    "service": 150,
    "access": 80,
    "site": 100,
    "procedure": 250,
}
DEFAULT_FLOOR = 150

# Entity-Typen, in denen ausfuehrliche Kommandofolgen fehl am Platz sind.
# Procedures sind ausgenommen — dort sind sie der Zweck.
NARRATIVE_TYPES = {"server", "service", "access", "site"}

FRONTMATTER_PATTERN = re.compile(r"^---\n(.*?)\n---\n", re.S)
HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.*)$", re.M)
FENCE_PATTERN = re.compile(r"^(```+|~~~+)", re.M)
DATE_PATTERN = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
HISTORY_PATTERN = re.compile(
    # "Session" zaehlt nur als Logbuch-Marke, also mit anhaengendem Datum.
    # Blank getroffen wuerde sonst jeder Artikel ueber SSH, Shells oder Jails,
    # wo "Session" schlicht Fachvokabular ist.
    r"\b\d{4}-\d{2}-\d{2}\b|\bSession\s+\d{4}-\d{2}-\d{2}|\bCR\d{3,5}\b|\bseit\s+\d{4}\b|\binzwischen\b|\bfrüher\b|\bmittlerweile\b|\bdamals\b",
    re.I,
)
RECIPE_PATTERN = re.compile(r"^#\s*(FALSCH|RICHTIG|WIRKUNGSLOS|GEFÄHRLICH|GEFAEHRLICH)\b", re.M)
QUELLEN_PATTERN = re.compile(r"^##+\s+Quellen\s*$", re.M | re.I)

# Aufzaehlungspunkt unter "## Quellen", der ein Datum oder eine CR-Nummer traegt.
# Genau die Form, in der sich Session-Protokolle ansammeln:
#   "- Session 2026-07-05: Double-Hop giwe → mail-giwe-at"
LOGBUCH_PATTERN = re.compile(r"^\s*[-*]\s+.*(?:\b\d{4}-\d{2}-\d{2}\b|\bCR\d{3,5}\b)", re.M)

# Woerter, die in fast jeder Ueberschrift stehen und deshalb keine Aussage ueber
# das Thema treffen — beim Abgleich Ueberschrift <-> Procedure-Slug ignoriert.
STOPWORDS = {
    "der", "die", "das", "und", "oder", "mit", "ohne", "fuer", "für", "auf",
    "vom", "von", "den", "dem", "des", "ein", "eine", "einer", "einem", "als",
    "nicht", "beim", "bei", "aus", "ist", "sind", "wird", "werden", "nach",
    "ueber", "über", "unter", "zwei", "drei", "eigene", "eigenen",
}


def percentile(values, pct):
    """p-tes Perzentil einer Liste (linear, ohne numpy)."""
    if not values:
        return 0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    pos = (len(ordered) - 1) * pct
    low = int(pos)
    high = min(low + 1, len(ordered) - 1)
    return ordered[low] + (ordered[high] - ordered[low]) * (pos - low)


def clamp(value, lo=0.0, hi=1.0):
    return max(lo, min(hi, value))


def parse_type(text):
    """Liest 'type:' aus dem Frontmatter; None, wenn keines vorhanden ist."""
    m = FRONTMATTER_PATTERN.match(text)
    if not m:
        return None
    for line in m.group(1).splitlines():
        if line.startswith("type:"):
            return line.split(":", 1)[1].strip().strip("\"'")
    return None


def split_quellen(text):
    """Trennt den Artikel in Fliesstext und den Abschnitt '## Quellen'.

    Die Historie-Dichte wird ueber den ganzen Artikel gerechnet; die Trennung
    dient allein dazu, den Quellen-Block fuer das Logbuch-Signal zu finden.
    """
    m = QUELLEN_PATTERN.search(text)
    if not m:
        return text, ""
    return text[:m.start()], text[m.start():]


def section_sizes(text):
    """Zeilenumfang je H2/H3-Abschnitt, in Reihenfolge des Auftretens.

    Gibt eine Liste (level, titel, zeilen) zurueck. Der Vorspann vor der ersten
    Ueberschrift bleibt unberuecksichtigt.
    """
    lines = text.splitlines()
    marks = []
    for idx, line in enumerate(lines):
        m = re.match(r"^(#{2,3})\s+(.*)$", line)
        if m:
            marks.append((idx, len(m.group(1)), m.group(2).strip()))

    sections = []
    for i, (idx, level, title) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else len(lines)
        sections.append((level, title, end - idx))
    return sections


def tokenize(text):
    """Sinntragende Woerter einer Ueberschrift oder eines Slugs."""
    words = re.split(r"[^0-9a-zäöüß]+", text.lower())
    return {w for w in words if len(w) > 3 and w not in STOPWORDS}


def collect(wiki_root):
    """Liest alle Artikel unter <wiki-root>/wiki/ ein und misst sie."""
    root = Path(wiki_root)
    wiki_dir = root / "wiki"
    if not wiki_dir.is_dir():
        print(f"Fehler: {wiki_dir} existiert nicht.", file=sys.stderr)
        sys.exit(2)

    articles = []
    for path in sorted(wiki_dir.rglob("*.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        body, quellen = split_quellen(text)
        lines = text.count("\n") + 1

        headings = HEADING_PATTERN.findall(text)
        sections = section_sizes(text)
        biggest = max(sections, key=lambda s: s[2]) if sections else (0, "", 0)

        articles.append({
            "rel_path": str(path.relative_to(root)),
            "slug": path.stem,
            "type": parse_type(text) or "unbekannt",
            "lines": lines,
            "hist_hits": len(HISTORY_PATTERN.findall(text)),
            "hist_per_100": len(HISTORY_PATTERN.findall(text)) * 100.0 / lines,
            "oldest_date": min(DATE_PATTERN.findall(text), default=None),
            "logbuch_hits": len(LOGBUCH_PATTERN.findall(quellen)),
            "fences": len(FENCE_PATTERN.findall(text)) // 2,
            "recipes": len(RECIPE_PATTERN.findall(text)),
            "h3": sum(1 for h in headings if len(h[0]) == 3),
            "deep": sum(1 for h in headings if len(h[0]) >= 4),
            "big_section": biggest[1],
            "big_share": biggest[2] / lines if lines else 0,
            "sections": sections,
        })
    return articles


def score(article, p90_by_type):
    """Punkte 0..100 aus sechs Einzelsignalen plus die Befundliste.

    Die Gewichte sind bewusst grob — die Rangfolge soll stimmen, die absolute
    Zahl bedeutet nichts. Entschieden wird an den Rohwerten in der Ausgabe.
    """
    typ = article["type"]
    baseline = max(p90_by_type.get(typ, 0), SIZE_FLOOR.get(typ, DEFAULT_FLOOR))
    ratio = article["lines"] / baseline if baseline else 0
    article["baseline"] = baseline
    article["ratio"] = ratio

    findings = []
    points = 0.0

    # Umfang: logarithmisch ab dem 1,0-fachen der Baseline, ausgereizt erst beim
    # 8-fachen. Eine lineare Skala mit Deckel bei 3x sah zwischen 4,5x und 3,9x
    # keinen Unterschied — 118 entfernte Zeilen bewegten den Score um 0,1 Punkte.
    # Genau die Artikel, an denen man arbeitet, liegen aber ueber dem Deckel.
    size_pts = 30 * clamp(math.log2(ratio) / 3.0) if ratio > 0 else 0
    is_long = ratio > 1.0
    if is_long:
        findings.append(f"LANG ({article['lines']} Zeilen, {ratio:.1f}x Baseline {typ})")
    points += size_pts

    # Historie: Dichte und absolute Menge gemeinsam. Die Dichte allein ist ein
    # Verhaeltnis und steigt, sobald man historienarme Zeilen entfernt — ein
    # Artikel wuerde sich durchs Aufraeumen verschlechtern.
    hist_pts = 25 * clamp(
        0.6 * clamp(article["hist_per_100"] / 6.0)
        + 0.4 * clamp(article["hist_hits"] / 40.0)
    )
    is_historic = article["hist_per_100"] >= 3.0 and article["hist_hits"] >= 8
    if is_historic:
        findings.append(
            f"HISTORIE ({article['hist_hits']} Marker, {article['hist_per_100']:.1f}/100 Zeilen"
            + (f", ältester {article['oldest_date']}" if article["oldest_date"] else "")
            + ")"
        )
    points += hist_pts

    # Logbuch: datierte Aufzaehlung unter "## Quellen". Eigenes Signal statt Teil
    # von HISTORIE, weil die Behandlung eine andere ist — HISTORIE meint einen
    # Zustand im Fliesstext, der nicht mehr gilt, LOGBUCH eine Chronologie der
    # eigenen Arbeit, die nie in den Artikel gehoert hat. Ein einzelner datierter
    # Beleg ist kein Logbuch, deshalb erst ab dem dritten Eintrag.
    log_hits = article["logbuch_hits"]
    points += 20 * clamp(log_hits / 8.0)
    if log_hits >= 3:
        findings.append(
            f"LOGBUCH ({log_hits} datierte Einträge unter '## Quellen')"
        )

    # Typfremdes: Kommandofolgen in erzaehlenden Entities
    if typ in NARRATIVE_TYPES:
        proc_pts = 20 * clamp((article["fences"] + article["recipes"]) / 12.0)
        if article["fences"] + article["recipes"] >= 5:
            findings.append(
                f"PROZEDURAL ({article['fences']} Codeblöcke, {article['recipes']} FALSCH/RICHTIG"
                f" in einer {typ}-Entity)"
            )
        points += proc_pts

    # Dominanter Abschnitt: erst ab einem Viertel der Datei zaehlend, und nur bei
    # einem Artikel, der ohnehin durch Umfang oder Historie auffaellt. Fuer sich
    # genommen ist ein Schwerpunkt kein Mangel, sondern die Bauform — er erklaert
    # bei einem zu langen Artikel, *wo* der Ballast sitzt. Ueber 205 Artikel des
    # azedo-Wikis hat die Rohbedingung ohne zweiten Grund ausschliesslich kurze
    # Artikel getroffen (38-62 % der Typ-Schwelle); ein Zerlegen waere dort falsch.
    dom_counts = is_long or is_historic
    if dom_counts:
        points += 15 * clamp((article["big_share"] - 0.25) / 0.35)
        if article["big_share"] > 0.30 and article["lines"] > 80:
            findings.append(
                f"DOMINANT (\"{article['big_section']}\" = {article['big_share']*100:.0f}% der Datei)"
            )

    # Struktur: viele H3 oder Verschachtelung ab H4. Punkte nur mit Befund — sonst
    # verschiebt das Signal die Rangfolge, ohne in der Ausgabe zu erscheinen.
    # Im azedo-Wiki loest keiner der 205 Artikel den Befund aus (h3 max 13 gegen
    # Schwelle 15, H4 max 1 gegen 5), waehrend struct_pts bis zu 5,2 Punkte
    # beitrug. Ausserdem folgt h3 im Wesentlichen der Laenge, die LANG schon misst.
    if article["h3"] >= 15 or article["deep"] >= 5:
        findings.append(f"TIEF ({article['h3']}x H3, {article['deep']}x H4+)")
        points += 10 * clamp(article["h3"] / 25.0)

    article["score"] = round(points, 1)
    article["findings"] = findings
    return article


def suggest_targets(article, procedures, token_df):
    """Bestehende Procedures, die zu grossen Abschnitten des Artikels passen.

    Wortueberlappung Ueberschrift <-> Procedure-Slug, entschaerft gegen zwei
    Rauschquellen: Woerter, die in drei oder mehr Procedure-Slugs vorkommen
    ("diagnose", "wp"), taugen nicht zur Unterscheidung und fliegen raus; ein
    einzelnes gemeinsames Wort zaehlt nur ab sechs Zeichen, sonst braucht es
    zwei. Bleibt ein Hinweis fuer die Handarbeit, keine Zuordnung.
    """
    hits = defaultdict(set)
    for level, title, size in article["sections"]:
        if size < 20:
            continue
        tokens = tokenize(title)
        for slug, slug_tokens in procedures:
            if slug == article["slug"]:
                continue
            common = {t for t in tokens & slug_tokens if token_df.get(t, 0) < 3}
            if not common:
                continue
            if len(common) == 1 and max(len(t) for t in common) < 6:
                continue
            hits[slug].add(title)
    ranked = sorted(hits.items(), key=lambda kv: -len(kv[1]))
    return ranked[:3]


def audit(wiki_root, type_filter=None, path_filter=None, top=10, show_all=False,
          as_json=False):
    articles = collect(wiki_root)
    if not articles:
        print("Keine Artikel gefunden.", file=sys.stderr)
        return 2

    # Baseline immer ueber das ganze Wiki, damit ein Filter den Massstab nicht verschiebt
    by_type = defaultdict(list)
    for a in articles:
        by_type[a["type"]].append(a["lines"])
    p90_by_type = {t: percentile(v, 0.90) for t, v in by_type.items()}

    procedures = [
        (a["slug"], tokenize(a["slug"]))
        for a in articles if a["type"] == "procedure"
    ]

    # Wie viele Procedure-Slugs enthalten ein Wort — Grundlage fuer den
    # Rausch-Filter in suggest_targets()
    token_df = defaultdict(int)
    for _, slug_tokens in procedures:
        for t in slug_tokens:
            token_df[t] += 1

    for a in articles:
        score(a, p90_by_type)

    selected = articles
    if type_filter:
        selected = [a for a in selected if a["type"] == type_filter]
    if path_filter:
        selected = [a for a in selected if path_filter in a["rel_path"]]

    flagged = [a for a in selected if a["findings"]]
    flagged.sort(key=lambda a: -a["score"])
    shown = flagged if show_all else flagged[:top]

    if as_json:
        rounded = {"baseline": 0, "ratio": 2, "hist_per_100": 1, "big_share": 3}
        payload = [
            {
                k: (round(a[k], rounded[k]) if k in rounded else a[k])
                for k in (
                    "rel_path", "slug", "type", "lines", "baseline", "ratio", "score",
                    "hist_hits", "hist_per_100", "oldest_date", "fences", "recipes",
                    "h3", "deep", "big_section", "big_share", "findings", "logbuch_hits",
                )
            }
            for a in shown
        ]
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print(f"\n{'='*72}")
    print(f"Wiki Audit — {wiki_root}")
    print(f"{'='*72}")

    scope = []
    if type_filter:
        scope.append(f"Typ={type_filter}")
    if path_filter:
        scope.append(f"Pfad~{path_filter}")
    print(f"\nArtikel gesamt: {len(articles)}"
          + (f"   Auswahl: {len(selected)} ({', '.join(scope)})" if scope else ""))

    print("\nBaseline je Typ (p90 Zeilen / wirksame Schwelle):")
    for t in sorted(p90_by_type):
        eff = max(p90_by_type[t], SIZE_FLOOR.get(t, DEFAULT_FLOOR))
        print(f"  {t:<12} n={len(by_type[t]):<3} p90={p90_by_type[t]:>5.0f}   Schwelle={eff:>5.0f}")

    print(f"\nAuffällig: {len(flagged)} von {len(selected)}"
          + (f" (gezeigt: {len(shown)})" if len(shown) < len(flagged) else ""))

    for rank, a in enumerate(shown, 1):
        print(f"\n{'-'*72}")
        print(f"{rank}. [{a['score']:>5.1f}] {a['rel_path']}   ({a['type']}, {a['lines']} Zeilen)")
        for f in a["findings"]:
            print(f"     • {f}")
        targets = suggest_targets(a, procedures, token_df)
        if targets:
            print("     Verschiebeziele (Wortüberlappung, ungeprüft):")
            for slug, titles in targets:
                sample = "; ".join(sorted(titles)[:2])
                print(f"       → [[{slug}]]  ({sample})")

    if not shown:
        print("\nKeine auffälligen Artikel in der Auswahl.")

    print(f"\n{'-'*72}")
    print("Nächster Schritt: /wiki refactor <slug> — analysiert eine Entity")
    print("abschnittsweise und legt einen Vorschlag vor (schreibt nichts).")
    print()
    return 0


if __name__ == "__main__":
    args = sys.argv[1:]
    opts = {"type": None, "path": None, "top": 10, "all": False, "json": False}

    positional = []
    i = 0
    while i < len(args):
        arg = args[i]
        if arg in ("--type", "--path", "--top") and i + 1 < len(args):
            key = arg[2:]
            opts[key] = int(args[i + 1]) if key == "top" else args[i + 1]
            i += 2
        elif arg == "--all":
            opts["all"] = True
            i += 1
        elif arg == "--json":
            opts["json"] = True
            i += 1
        else:
            positional.append(arg)
            i += 1

    if len(positional) != 1:
        print(f"Aufruf: {sys.argv[0]} [--type <typ>] [--path <teilpfad>] "
              f"[--top <n>] [--all] [--json] <wiki-root>")
        print(f"  z.B.: {sys.argv[0]} wiki/azedo/")
        print(f"        {sys.argv[0]} --type service --top 5 wiki/azedo/")
        print(f"        {sys.argv[0]} --path procedures --all wiki/azedo/")
        sys.exit(2)

    sys.exit(audit(positional[0], type_filter=opts["type"], path_filter=opts["path"],
                   top=opts["top"], show_all=opts["all"], as_json=opts["json"]))
