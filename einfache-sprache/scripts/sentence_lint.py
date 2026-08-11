#!/usr/bin/env python3

# Satzbau-Linter fuer Einfache Sprache:
# Satzlaenge, Nebensatzdichte, Passiv, Konjunktiv, Genitivketten,
# weite Verbklammer, doppelte Verneinung und Einschuebe.
# Alle Muster sind Heuristiken auf Wortformen - Befunde sind Verdacht.
# version 1.37.0

import argparse
import re

import textcore as tc

# Unterordnende Konjunktionen. "da" und "wenn" sind haeufig, aber auch
# haeufig harmlos - sie zaehlen mit, entscheidend ist die Summe je Satz.

SUBJUNKTIONEN = [
    "dass", "weil", "obwohl", "obgleich", "damit", "falls", "sofern", "indem",
    "waehrend", "während", "nachdem", "bevor", "sobald", "solange", "seitdem",
    "sodass", "so dass", "soweit", "wobei", "wonach", "zumal", "insofern",
    "insoweit", "sofern", "wenngleich", "anstatt dass", "ohne dass",
    "je nachdem", "wenn", "als", "ob", "da",
]

SUBJ_RE = re.compile(r"(?<![\wäöüß])(%s)(?![\wäöüß])"
                     % "|".join(re.escape(s) for s in SUBJUNKTIONEN), re.I)

RELATIV_RE = re.compile(
    r",\s*(?:der|die|das|dem|den|dessen|deren|welche[rsnm]?)\s+[a-zäöüß]", re.I)

UM_ZU_RE = re.compile(r"(?<![\wäöüß])um\b[^,.;:]{0,80}?\bzu\s+[a-zäöüß]+en\b", re.I)

# Passiv: Form von "werden" plus Partizip II. Das Partizip ist bewusst eng
# gefasst (ge-Form, -iert, praefigierte t-Form), damit Futur-Konstruktionen
# ("wir werden liefern") nicht als Passiv gelten.

WERDEN_RE = re.compile(r"(?<![\wäöüß])(wird|werden|wurde|wurden|worden|"
                       r"wuerde|würde|wuerden|würden)(?![\wäöüß])", re.I)

PARTIZIP_RE = re.compile(
    r"(?<![\wäöüß])(?:ge[a-zäöüß]{2,}(?:t|en)"
    r"|[a-zäöüß]{3,}iert"
    r"|(?:be|ver|er|ent|zer|emp|miss|über|ueber|unter|um|durch|an|auf|aus)"
    r"[a-zäöüß]{2,}(?<!s)t)(?![\wäöüß])", re.I)

# Zustandspassiv: "ist/sind ... Partizip II". Haeufig legitim (Zustand),
# darum eigene, schwaechere Kategorie.

SEIN_RE = re.compile(r"(?<![\wäöüß])(ist|sind|war|waren)(?![\wäöüß])", re.I)

KONJUNKTIV_RE = re.compile(
    r"(?<![\wäöüß])(wuerde|würde|wuerden|würden|waere|wäre|waeren|wären|"
    r"haette|hätte|haetten|hätten|koennte|könnte|koennten|könnten|"
    r"sollte|sollten|muesste|müsste|muessten|müssten|duerfte|dürfte|"
    r"duerften|dürften|moechte|möchte|moechten|möchten)(?![\wäöüß])", re.I)

GENITIV_RE = re.compile(r"(?<![\wäöüß])(des|der|eines|einer)\s+[A-ZÄÖÜ][\wäöüß]{3,}", re.I)

NEGATION_RE = re.compile(
    r"(?<![\wäöüß])(nicht|kein|keine|keinen|keinem|keiner|keines|nie|niemals|"
    r"niemand|nichts|ohne|weder|noch nicht|kaum)(?![\wäöüß])", re.I)

UN_PRAEFIX_RE = re.compile(r"(?<![\wäöüß])un[a-zäöüß]{4,}(?![\wäöüß])")

# Finite Hilfs- und Modalverben, die eine Verbklammer oeffnen.

KLAMMER_AUF_RE = re.compile(
    r"(?<![\wäöüß])(hat|haben|hatte|hatten|ist|sind|war|waren|wird|werden|"
    r"kann|koennen|können|muss|muessen|müssen|soll|sollen|will|wollen|"
    r"darf|duerfen|dürfen)(?![\wäöüß])", re.I)

KLAMMER_ZU_RE = re.compile(r"[a-zäöüß]{3,}(?:en|t|iert)$", re.I)

EINSCHUB_RE = re.compile(r"\([^)]{15,}\)|\s[-–—]\s[^-–—]{15,}\s[-–—]\s")

# Grenzwerte, die nicht von der Stufe abhaengen.

VERBKLAMMER_MAX = 8
GENITIVKETTE_AB = 2
NEGATION_AB = 2


def zaehle_nebensaetze(satz):
    treffer = []

    for m in SUBJ_RE.finditer(satz):
        treffer.append(m.group(1).lower())
    for m in RELATIV_RE.finditer(satz):
        treffer.append("Relativsatz")
    for m in UM_ZU_RE.finditer(satz):
        treffer.append("um ... zu")

    return treffer


def verbklammer_weite(satz):
    """Abstand zwischen finitem Hilfs-/Modalverb und dem Verb am Satzende.
    Grosse Weiten zwingen den Leser, den Satzanfang im Kopf zu behalten."""
    w = tc.woerter(satz)

    if len(w) < 6:
        return 0, None

    if not KLAMMER_ZU_RE.match(w[-1]):
        return 0, None

    for idx, wort in enumerate(w[:-1]):
        if KLAMMER_AUF_RE.fullmatch(wort):
            return len(w) - 1 - idx - 1, (wort, w[-1])

    return 0, None


def pruefe_satz(satz, zeile, stufe):
    ziel = tc.STUFEN[stufe]
    w = tc.woerter(satz)
    befunde = []

    if len(w) > ziel["satz_max"]:
        befunde.append({
            "regel": "S1-satzlaenge",
            "gewicht": "hoch",
            "detail": "%d Woerter (Grenze %d)" % (len(w), ziel["satz_max"]),
        })

    nebensaetze = zaehle_nebensaetze(satz)
    if len(nebensaetze) > ziel["nebensaetze"]:
        befunde.append({
            "regel": "S2-nebensaetze",
            "gewicht": "hoch" if len(nebensaetze) > ziel["nebensaetze"] + 1 else "mittel",
            "detail": "%d Nebensaetze (erlaubt %d): %s"
                      % (len(nebensaetze), ziel["nebensaetze"],
                         ", ".join(nebensaetze[:4])),
        })

    passiv = bool(WERDEN_RE.search(satz) and PARTIZIP_RE.search(satz))
    if passiv:
        befunde.append({
            "regel": "S3-passiv",
            "gewicht": "mittel",
            "detail": "Vorgangspassiv - wer handelt? Steht der Handelnde nicht "
                      "im Text, als offenen Punkt melden statt zu raten.",
        })
    elif SEIN_RE.search(satz) and PARTIZIP_RE.search(satz):
        befunde.append({
            "regel": "S4-zustandspassiv",
            "gewicht": "niedrig",
            "detail": "moegliches Zustandspassiv - haeufig legitim, nur bei "
                      "Haeufung aufloesen",
        })

    if KONJUNKTIV_RE.search(satz):
        befunde.append({
            "regel": "S5-konjunktiv",
            "gewicht": "mittel" if stufe == "A2" else "niedrig",
            "detail": "Konjunktiv - wenn keine echte Moeglichkeitsform gemeint "
                      "ist, im Indikativ schreiben",
        })

    genitive = GENITIV_RE.findall(satz)
    if len(genitive) >= GENITIVKETTE_AB:
        befunde.append({
            "regel": "S6-genitivkette",
            "gewicht": "mittel",
            "detail": "%d Genitivattribute - in 'von'-Fuegung oder eigenen Satz"
                      % len(genitive),
        })

    weite, paar = verbklammer_weite(satz)
    if weite > VERBKLAMMER_MAX:
        befunde.append({
            "regel": "S7-verbklammer",
            "gewicht": "mittel",
            "detail": "%d Woerter zwischen '%s' und '%s'" % (weite, paar[0], paar[1]),
        })

    negationen = len(NEGATION_RE.findall(satz)) + len(UN_PRAEFIX_RE.findall(satz))
    if negationen >= NEGATION_AB:
        befunde.append({
            "regel": "S8-verneinung",
            "gewicht": "mittel",
            "detail": "%d Verneinungen im Satz - positiv formulieren" % negationen,
        })

    if EINSCHUB_RE.search(satz):
        befunde.append({
            "regel": "S9-einschub",
            "gewicht": "niedrig",
            "detail": "langer Einschub - eigener Satz oder ans Satzende",
        })

    if not befunde:
        return None

    return {
        "zeile": zeile,
        "woerter": len(w),
        "satz": satz[:200],
        "befunde": befunde,
    }


def analysiere(vorbereitet, stufe):
    treffer = []
    passiv_saetze = 0

    for satz, zeile in vorbereitet["saetze"]:
        ergebnis = pruefe_satz(satz, zeile, stufe)
        if ergebnis:
            treffer.append(ergebnis)
            if any(b["regel"] == "S3-passiv" for b in ergebnis["befunde"]):
                passiv_saetze += 1

    anzahl_saetze = len(vorbereitet["saetze"]) or 1
    passiv_pct = 100.0 * passiv_saetze / anzahl_saetze
    ziel = tc.STUFEN[stufe]

    zusammenfassung = {}
    for eintrag in treffer:
        for b in eintrag["befunde"]:
            zusammenfassung[b["regel"]] = zusammenfassung.get(b["regel"], 0) + 1

    return {
        "stufe": stufe,
        "saetze_gesamt": len(vorbereitet["saetze"]),
        "saetze_mit_befund": len(treffer),
        "passiv_pct": round(passiv_pct, 1),
        "passiv_ziel_pct": ziel["passiv_pct"],
        "passiv_ueber_ziel": passiv_pct > ziel["passiv_pct"],
        "regelzaehler": dict(sorted(zusammenfassung.items(),
                                    key=lambda x: -x[1])),
        "treffer": treffer,
    }


def bericht(daten, limit):
    print("Satzbau - Stufe %s: %d von %d Saetzen mit Befund"
          % (daten["stufe"], daten["saetze_mit_befund"], daten["saetze_gesamt"]))
    print("Passiv: %.1f %% der Saetze (Ziel <= %s %%)%s"
          % (daten["passiv_pct"], daten["passiv_ziel_pct"],
             "  ZU HOCH" if daten["passiv_ueber_ziel"] else ""))

    if daten["regelzaehler"]:
        print()
        for regel, anzahl in daten["regelzaehler"].items():
            print("  %-20s %d" % (regel, anzahl))

    rang = {"hoch": 0, "mittel": 1, "niedrig": 2}
    sortiert = sorted(
        daten["treffer"],
        key=lambda t: (min(rang[b["gewicht"]] for b in t["befunde"]), -t["woerter"]),
    )

    print()
    for eintrag in sortiert[:limit]:
        print("Z%-4d (%d Woerter) %s" % (eintrag["zeile"], eintrag["woerter"],
                                         eintrag["satz"]))
        for b in eintrag["befunde"]:
            print("      [%s] %s: %s" % (b["gewicht"], b["regel"], b["detail"]))
        print()

    if len(sortiert) > limit:
        print("... %d weitere Saetze mit Befund (--limit erhoehen)"
              % (len(sortiert) - limit))


def main():
    p = argparse.ArgumentParser(description="Satzbau-Linter fuer Einfache Sprache")
    p.add_argument("--file")
    p.add_argument("--latest")
    p.add_argument("--stufe", default=tc.DEFAULT_STUFE)
    p.add_argument("--limit", type=int, default=15)
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    stufe = tc.stufe_pruefen(args.stufe)
    pfad = tc.quelle_aufloesen(args)
    daten = analysiere(tc.vorbereiten(pfad), stufe)
    daten["datei"] = pfad

    if not tc.ausgeben(daten, args.json):
        bericht(daten, args.limit)


if __name__ == "__main__":
    main()
