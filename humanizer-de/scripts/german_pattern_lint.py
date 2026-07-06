#!/usr/bin/env python3
"""Report German naturalness pattern clusters for Humanizer-de."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


AI_MARKERS = (
    "beleuchten",
    "eintauchen",
    "unterstreichen",
    "aufzeigen",
    "spannend",
    "entscheidend",
    "maßgeblich",
    "massgeblich",
    "nahtlos",
    "vielschichtig",
    "facettenreich",
    "dynamisch",
    "ganzheitlich",
    "maßgeschneidert",
    "massgeschneidert",
    "digitale landschaft",
    "zusammenspiel",
)
COPULA_AVOIDANCE = (
    "fungiert als",
    "dient als",
    "stellt",
    "stellt dar",
    "verfügt über",
    "verfuegt ueber",
    "zeichnet sich",
    "erweist sich als",
    "repräsentiert",
    "repraesentiert",
)
ABSTRACTA = (
    "maßnahmen",
    "massnahmen",
    "aspekte",
    "lösungen",
    "loesungen",
    "herausforderungen",
    "faktoren",
    "prozesse",
)
PARTICLES = ("ja", "doch", "eben", "halt", "wohl", "mal", "schon")

# --- azedo-Erweiterung: Muster 67 (Business-Anglizismen / Denglisch-Jargon) ---
# Kuratiertes Lexikon englischer Business-/Consulting-Begriffe -> deutsche
# Entsprechungen. Abgegrenzt von Muster 45 (harte Transfers) und Muster 64
# (deutsche KI-Marker). Match ist case-insensitiv und lässt nur ein eng
# begrenztes deutsches Flexions-Suffix zu (kein offenes \w*), damit Formen wie
# "instrumentiert" greifen, Kurztokens wie "Gate"/"IP" aber nicht in
# "Gateway"/"ZIP" mitmatchen. Cluster-/registergesteuert (BUSINESS_ANGLICISM_THRESHOLDS).
BUSINESS_ANGLICISMS = {
    "lean": ["schlank"],
    "Entscheidungs-Gate": ["Entscheidungspunkt"],
    "Gate": ["Entscheidungspunkt"],
    "evidenzgetrieben": ["faktenbasiert", "datengestützt"],
    "instrumentier": ["durchgängig messen", "erfassen"],
    "R&D": ["F&E"],
    "Plattform-IP": ["Plattform-Know-how", "geistiges Eigentum"],
    "IP": ["geistiges Eigentum"],
    "Headline": ["Überschrift", "Auf einen Blick"],
    "buy-vs-build": ["Zukauf vs. Eigenbau"],
    "Capex": ["einmalige Investition"],
    "Opex": ["Betriebskosten", "laufende Kosten"],
    "productisier": ["zum Produkt ausbauen", "produktreif machen"],
}

# Negativliste etablierter Fachbegriffe: nie ein Befund. Vor dem Lexikon-Match
# ausmaskiert, damit z.B. "A/B-Testing" oder "KI" keinen Treffer auslösen.
BUSINESS_ANGLICISM_ALLOWLIST = (
    "MVP", "SaaS", "Multi-Tenant", "CRM", "RAG", "2FA", "QR", "NFC",
    "A/B-Testing", "White-Label", "Drag&Drop", "LLM", "KI", "Stripe",
    "Payrexx", "RaiseNow", "Self-Serve", "scope-abhängig", "Onboarding",
    "Tracking", "Funnel", "Journeys", "Live-Vorschau",
)

# Cluster-Schwelle pro Modus: formal jeden Treffer, sachlich ab kleinem Cluster,
# locker nur bei Häufung.
BUSINESS_ANGLICISM_THRESHOLDS = {"locker": 4, "sachlich": 2, "formal": 1}


# Eng begrenztes deutsches Flexions-Suffix (Deklination/Konjugation). Bewusst
# geschlossen statt \w*, damit "Gate"/"IP" nicht in "Gateway"/"IPsec" laufen.
ANGLICISM_INFLECTION = r"(?:e|en|es|er|em|te|ten|t|st|s)?"


def anglicism_regex(marker: str) -> re.Pattern:
    # Grenzen gegen Wortzeichen; der Marker selbst darf & / - enthalten
    # (R&D, buy-vs-build, Plattform-IP). Danach nur das begrenzte Flexions-Suffix.
    return re.compile(rf"(?<![\w&/-]){re.escape(marker)}{ANGLICISM_INFLECTION}(?!\w)", re.IGNORECASE)


def count_business_anglicisms(text: str) -> dict:
    # Erst Allowlist-Treffer ausmaskieren, dann das Lexikon von lang nach kurz
    # matchen und getroffene Spannen ebenfalls maskieren (verhindert
    # Doppelzählung von "IP" innerhalb "Plattform-IP").
    masked = text
    for term in BUSINESS_ANGLICISM_ALLOWLIST:
        masked = anglicism_regex(term).sub(lambda match: "\x00" * len(match.group(0)), masked)

    hits: dict = {}
    for marker in sorted(BUSINESS_ANGLICISMS, key=len, reverse=True):
        spans = list(anglicism_regex(marker).finditer(masked))
        if not spans:
            continue
        hits[marker] = {"count": len(spans), "vorschlaege": BUSINESS_ANGLICISMS[marker]}
        for match in spans:
            start, end = match.span()
            masked = masked[:start] + "\x00" * (end - start) + masked[end:]
    return hits

# --- Ende azedo-Erweiterung ---


def marker_stem(marker: str) -> str:
    if marker.endswith("en") and len(marker) > 5:
        return marker[:-2]
    return marker


def count_marker(text: str, marker: str) -> int:
    lowered = text.lower()
    if " " in marker:
        return len(re.findall(rf"\b{re.escape(marker)}\w*\b", lowered))
    stem = marker_stem(marker)
    return len(re.findall(rf"\b{re.escape(stem)}\w*\b", lowered))


def count_particle(text: str, marker: str) -> int:
    lowered = text.lower()
    return len(re.findall(rf"\b{re.escape(marker)}\b", lowered))


def lint(text: str, mode: str = "sachlich") -> dict:
    lowered = text.lower()
    findings: list[dict] = []

    ai_hits = {marker: count_marker(lowered, marker) for marker in AI_MARKERS if count_marker(lowered, marker)}
    if sum(ai_hits.values()) >= 3:
        findings.append({"pattern": 64, "kind": "ai_marker_cluster", "severity": "warning", "evidence": ai_hits})

    copula_hits = {marker: count_marker(lowered, marker) for marker in COPULA_AVOIDANCE if count_marker(lowered, marker)}
    if sum(copula_hits.values()) >= 2:
        findings.append({"pattern": 65, "kind": "copula_avoidance_cluster", "severity": "warning", "evidence": copula_hits})

    abstract_hits = {marker: count_marker(lowered, marker) for marker in ABSTRACTA if count_marker(lowered, marker)}
    if sum(abstract_hits.values()) >= 3:
        findings.append({"pattern": 58, "kind": "abstraction_cluster", "severity": "warning", "evidence": abstract_hits})

    particle_count = sum(count_particle(lowered, marker) for marker in PARTICLES)
    if mode in {"sachlich", "formal"} and particle_count:
        findings.append({"pattern": 63, "kind": "particles_outside_locker", "severity": "warning", "evidence": {"count": particle_count}})
    if mode == "locker" and particle_count > 3:
        findings.append({"pattern": 63, "kind": "particle_overdose", "severity": "warning", "evidence": {"count": particle_count}})

    colon_headings = [
        line.strip()
        for line in text.splitlines()
        if re.match(r"^\s{0,3}#{1,3}\s+.+:.+", line)
    ]
    if len(colon_headings) >= 2:
        findings.append({"pattern": 54, "kind": "colon_heading_cluster", "severity": "warning", "evidence": colon_headings})

    anglicism_hits = count_business_anglicisms(text)
    anglicism_total = sum(item["count"] for item in anglicism_hits.values())
    if anglicism_total >= BUSINESS_ANGLICISM_THRESHOLDS.get(mode, 2):
        findings.append({"pattern": 67, "kind": "business_anglicism_cluster", "severity": "warning", "evidence": anglicism_hits})

    return {"ok": not findings, "mode": mode, "findings": findings}


def check_fixture(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    report = lint(data["text"], mode=data.get("mode", "sachlich"))
    expected = set(data.get("expect_kinds", []))
    actual = {item["kind"] for item in report["findings"]}
    return {"fixture": str(path), "ok": actual == expected, "report": report}


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Report German naturalness pattern clusters.")
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--text")
    source.add_argument("--file", type=Path)
    source.add_argument("--fixture", type=Path)
    parser.add_argument("--mode", choices=["locker", "sachlich", "formal"], default="sachlich")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if args.fixture:
        files = sorted(args.fixture.glob("*.json")) if args.fixture.is_dir() else [args.fixture]
        results = [check_fixture(file_path) for file_path in files]
        print(json.dumps({"ok": all(item["ok"] for item in results), "results": results}, ensure_ascii=False, indent=2))
        return 0 if all(item["ok"] for item in results) else 1

    text = args.file.read_text(encoding="utf-8") if args.file else args.text or ""
    report = lint(text, mode=args.mode)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
