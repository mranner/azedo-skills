#!/usr/bin/env python3

# Struktur-Linter fuer Einfache Sprache:
# Absatzlaenge, Ueberschriften, Listenkandidaten, Datums- und Zahlformate,
# Anrede-Konsistenz, unaufgeloeste Verweise und Auszeichnungen.
# version 1.37.0

import argparse
import re

import textcore as tc

HEADING_MAX_WOERTER = 8
ABSCHNITT_MAX_PROSAZEILEN = 25

DATUM_MUSTER = {
    "punktformat": re.compile(r"\b\d{1,2}\.\d{1,2}\.\d{2,4}\b"),
    "iso": re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),
    "ausgeschrieben": re.compile(
        r"\b\d{1,2}\.\s*(?:Januar|Februar|Maerz|März|April|Mai|Juni|Juli|"
        r"August|September|Oktober|November|Dezember)\b"),
    "schraegstrich": re.compile(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b"),
}

SIE_RE = re.compile(r"(?<![\wäöüß])(Sie|Ihnen|Ihr|Ihre|Ihren|Ihrem|Ihres)(?![\wäöüß])")
DU_RE = re.compile(r"(?<![\wäöüß])(du|dir|dich|dein|deine|deinen|deinem)(?![\wäöüß])", re.I)

VERWEIS_RE = re.compile(
    r"(?<![\wäöüß])(siehe oben|siehe unten|wie bereits erwaehnt|wie bereits erwähnt|"
    r"wie oben beschrieben|vorstehend|nachstehend|s\.o\.|s\.u\.|"
    r"an anderer Stelle|weiter unten|weiter oben)(?![\wäöüß])", re.I)

VERSALIEN_RE = re.compile(r"(?<![\wäöüß])[A-ZÄÖÜ]{4,}(?![\wäöüß])")

# Kandidat fuer eine Aufzaehlung: drei oder mehr durch Komma/„sowie" getrennte
# Glieder in einem Satz.

AUFZAEHLUNG_RE = re.compile(r",[^,.;:]{3,60},[^,.;:]{3,60}(?:,|\s+(?:sowie|und|oder)\s)")


def absaetze(vorbereitet):
    """Absaetze aus Prosa- und Listenzeilen, mit Startzeile."""
    zeilen = vorbereitet["text"].split("\n")
    arten = vorbereitet["zeilen_arten"]
    blocks = []
    aktuell = []
    start = 1

    for idx, zeile in enumerate(zeilen):
        art = arten[idx] if idx < len(arten) else "prosa"

        if art in ("leer", "heading", "tabelle"):
            if aktuell:
                blocks.append((start, "\n".join(aktuell), art_des_blocks(aktuell)))
                aktuell = []
            continue

        if not aktuell:
            start = idx + 1
        aktuell.append(zeile)

    if aktuell:
        blocks.append((start, "\n".join(aktuell), art_des_blocks(aktuell)))

    return blocks


def art_des_blocks(zeilen):
    if all(tc.LISTEN_RE.match(z) for z in zeilen if z.strip()):
        return "liste"

    return "prosa"


def analysiere(vorbereitet, stufe):
    ziel = tc.STUFEN[stufe]
    roh_zeilen = vorbereitet["roh"].split("\n")
    arten = vorbereitet["zeilen_arten"]
    text = vorbereitet["text"]

    # Absaetze
    lange_absaetze = []
    listenkandidaten = []

    for start, block, art in absaetze(vorbereitet):
        if art == "liste":
            continue

        saetze = tc.zerlege_saetze(block, ["prosa"] * (block.count("\n") + 1))
        if len(saetze) > ziel["absatz_saetze"]:
            lange_absaetze.append({
                "zeile": start,
                "saetze": len(saetze),
                "grenze": ziel["absatz_saetze"],
                "anfang": block.strip()[:100],
            })

        # zerlege_saetze zaehlt innerhalb des Blocks ab 1 - auf die Datei umrechnen
        for satz, zeile in saetze:
            if AUFZAEHLUNG_RE.search(satz):
                listenkandidaten.append({"zeile": zeile + start - 1,
                                         "satz": satz[:140]})

    # Ueberschriften
    headings = []
    lange_headings = []
    abstaende = []
    prosa_seit_heading = 0
    letzte_heading_zeile = None

    for idx, art in enumerate(arten):
        if art == "heading":
            titel = tc.ATX_HEADING_RE.match(roh_zeilen[idx]).group(1).strip()
            headings.append({"zeile": idx + 1, "titel": titel})

            if len(tc.woerter(titel)) > HEADING_MAX_WOERTER:
                lange_headings.append({
                    "zeile": idx + 1, "titel": titel,
                    "woerter": len(tc.woerter(titel)),
                })

            if letzte_heading_zeile is not None and \
               prosa_seit_heading > ABSCHNITT_MAX_PROSAZEILEN:
                abstaende.append({
                    "von_zeile": letzte_heading_zeile,
                    "bis_zeile": idx + 1,
                    "prosazeilen": prosa_seit_heading,
                })

            letzte_heading_zeile = idx + 1
            prosa_seit_heading = 0
        elif art in ("prosa", "liste"):
            prosa_seit_heading += 1

    if letzte_heading_zeile is not None and prosa_seit_heading > ABSCHNITT_MAX_PROSAZEILEN:
        abstaende.append({
            "von_zeile": letzte_heading_zeile,
            "bis_zeile": len(arten),
            "prosazeilen": prosa_seit_heading,
        })

    # Datumsformate
    datumsformate = {}
    for name, muster in DATUM_MUSTER.items():
        treffer = muster.findall(text)
        if treffer:
            datumsformate[name] = len(treffer)

    # Anrede
    sie = len(SIE_RE.findall(text))
    du = len(DU_RE.findall(text))

    # Verweise, Versalien, Ausrufezeichen
    verweise = []
    versalien = []
    for nummer, zeile in enumerate(text.split("\n"), start=1):
        for m in VERWEIS_RE.finditer(zeile):
            verweise.append({"zeile": nummer, "fund": m.group(1)})
        for m in VERSALIEN_RE.finditer(zeile):
            versalien.append({"zeile": nummer, "fund": m.group(0)})

    ausrufezeichen = text.count("!")

    return {
        "stufe": stufe,
        "absaetze_zu_lang": lange_absaetze,
        "listenkandidaten": listenkandidaten,
        "ueberschriften": len(headings),
        "ueberschriften_zu_lang": lange_headings,
        "abschnitte_ohne_ueberschrift": abstaende,
        "datumsformate": datumsformate,
        "datumsformate_gemischt": len(datumsformate) > 1,
        "anrede": {"Sie": sie, "du": du, "gemischt": bool(sie and du)},
        "verweise_ohne_ziel": verweise,
        "versalien": versalien,
        "ausrufezeichen": ausrufezeichen,
    }


def bericht(daten, limit):
    print("Struktur - Stufe %s: %d Ueberschriften" % (daten["stufe"], daten["ueberschriften"]))
    print()

    if daten["absaetze_zu_lang"]:
        print("Zu lange Absaetze (Grenze %d Saetze):"
              % daten["absaetze_zu_lang"][0]["grenze"])
        for e in daten["absaetze_zu_lang"][:limit]:
            print("   Z%-4d %d Saetze  %s" % (e["zeile"], e["saetze"], e["anfang"]))
        print()

    if daten["ueberschriften_zu_lang"]:
        print("Zu lange Ueberschriften (Grenze %d Woerter):" % HEADING_MAX_WOERTER)
        for e in daten["ueberschriften_zu_lang"][:limit]:
            print("   Z%-4d %d Woerter  %s" % (e["zeile"], e["woerter"], e["titel"]))
        print()

    if daten["abschnitte_ohne_ueberschrift"]:
        print("Lange Abschnitte ohne Zwischenueberschrift:")
        for e in daten["abschnitte_ohne_ueberschrift"][:limit]:
            print("   Z%d bis Z%d: %d Zeilen" % (e["von_zeile"], e["bis_zeile"],
                                                 e["prosazeilen"]))
        print()

    if daten["listenkandidaten"]:
        print("Aufzaehlungen im Fliesstext (Liste pruefen):")
        for e in daten["listenkandidaten"][:limit]:
            print("   Z%-4d %s" % (e["zeile"], e["satz"]))
        print()

    if daten["datumsformate_gemischt"]:
        print("Gemischte Datumsformate: " + ", ".join(
            "%s (%d)" % (k, v) for k, v in daten["datumsformate"].items()))
        print("   Ein Format durchgehend verwenden.")
        print()

    if daten["anrede"]["gemischt"]:
        print("Gemischte Anrede: Sie %dx, du %dx - eine Form waehlen."
              % (daten["anrede"]["Sie"], daten["anrede"]["du"]))
        print("   Fehlalarm moeglich: 'Sie' am Satzanfang als 3. Person zaehlt mit.")
        print()

    if daten["verweise_ohne_ziel"]:
        print("Verweise ohne konkretes Ziel:")
        for e in daten["verweise_ohne_ziel"][:limit]:
            print("   Z%-4d %s" % (e["zeile"], e["fund"]))
        print()

    if daten["versalien"]:
        print("Versalien (schlecht lesbar): " + ", ".join(
            e["fund"] for e in daten["versalien"][:limit]))
        print()

    if daten["ausrufezeichen"] > 2:
        print("Ausrufezeichen: %d - in Sachtexten sparsam einsetzen."
              % daten["ausrufezeichen"])
        print()


def main():
    p = argparse.ArgumentParser(description="Struktur-Linter fuer Einfache Sprache")
    p.add_argument("--file")
    p.add_argument("--latest")
    p.add_argument("--stufe", default=tc.DEFAULT_STUFE)
    p.add_argument("--limit", type=int, default=10)
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
