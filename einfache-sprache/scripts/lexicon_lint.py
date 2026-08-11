#!/usr/bin/env python3

# Wort-Linter fuer Einfache Sprache:
# Nominalstil, Funktionsverbgefuege, Amtsdeutsch, Fremdwoerter, Floskeln,
# lange Komposita, nicht eingefuehrte Abkuerzungen und Begriffsvarianten.
# Ersatzvorschlaege stammen aus data/wortlisten.json und sind Vorschlaege.
# version 1.37.0

import argparse
import re
from collections import Counter

import textcore as tc

# Endungen, die typischerweise ein Verb in ein Substantiv verwandeln.
# "Rechnung", "Wohnung", "Zeitung" sind konkrete Dinge und keine
# Nominalisierung - darum zaehlt nur die Dichte, nie das Einzelwort.

NOMINAL_SUFFIXE = ("ung", "ungen", "heit", "heiten", "keit", "keiten",
                   "nis", "nisse", "tion", "tionen", "ismus", "ität",
                   "itaet", "schaft", "schaften", "barkeit", "ierung")

NOMINAL_AUSNAHMEN = {
    "rechnung", "wohnung", "zeitung", "kleidung", "leitung", "ordnung",
    "regierung", "sendung", "sitzung", "uebung", "übung", "werkzeug",
    "zahlung", "abteilung", "richtung", "meinung", "erfahrung", "erinnerung",
    "wirtschaft", "gesellschaft", "mannschaft", "landschaft", "botschaft",
    "eigenschaft", "freundschaft", "nation", "station", "portion", "position",
    "funktion", "region", "version", "option", "aktion", "sektion",
}

# Komposita-Grenzen je Stufe (Zeichen ohne Bindestrich).

KOMPOSITUM_GRENZE = {"PLAIN": 20, "B1": 16, "A2": 14}

ABK_RE = re.compile(r"(?<![\wäöüß])([A-ZÄÖÜ]{2,6})(?![\wäöüß])")
ABK_EINGEFUEHRT_RE = re.compile(r"\(\s*([A-ZÄÖÜ]{2,6})\s*\)")

NOMINALDICHTE_GRENZE = {"PLAIN": 8.0, "B1": 6.0, "A2": 4.0}


def _zeilenindex(text):
    """Liefert je Zeilennummer den Zeilentext (1-basiert)."""
    return list(enumerate(text.split("\n"), start=1))


def _phrasen_suchen(zeilen, phrasen):
    """Sucht Mehrwort-Ausdruecke, umlautunabhaengig genug fuer die
    ae/ue/oe-Schreibung in den Wortlisten."""
    treffer = []

    for nummer, zeile in zeilen:
        klein = zeile.lower()
        klein_norm = (klein.replace("ä", "ae").replace("ö", "oe")
                           .replace("ü", "ue").replace("ß", "ss"))

        for phrase, ersatz in phrasen.items():
            such = phrase.lower()
            such_norm = (such.replace("ä", "ae").replace("ö", "oe")
                             .replace("ü", "ue").replace("ß", "ss"))

            if such_norm in klein_norm:
                treffer.append({
                    "zeile": nummer,
                    "fund": phrase,
                    "vorschlag": ersatz,
                })

    return treffer


def nominalstil(zeilen, stufe):
    kandidaten = []
    gesamt_woerter = 0

    for nummer, zeile in zeilen:
        for wort in tc.woerter(zeile):
            gesamt_woerter += 1
            klein = wort.lower()

            if len(wort) < 7 or klein in NOMINAL_AUSNAHMEN:
                continue
            if not wort[0].isupper():
                continue
            if klein.endswith(NOMINAL_SUFFIXE):
                kandidaten.append((nummer, wort))

    dichte = 100.0 * len(kandidaten) / gesamt_woerter if gesamt_woerter else 0.0
    haeufig = Counter(w for _n, w in kandidaten).most_common(10)

    return {
        "anzahl": len(kandidaten),
        "dichte_pro_100_woerter": round(dichte, 1),
        "grenze": NOMINALDICHTE_GRENZE[stufe],
        "ueber_grenze": dichte > NOMINALDICHTE_GRENZE[stufe],
        "haeufigste": [{"wort": w, "anzahl": n} for w, n in haeufig],
        "stellen": [{"zeile": n, "wort": w} for n, w in kandidaten[:40]],
    }


def lange_komposita(zeilen, stufe):
    grenze = KOMPOSITUM_GRENZE[stufe]
    treffer = []
    gesehen = set()

    for nummer, zeile in zeilen:
        for wort in tc.woerter(zeile):
            if tc.ist_technisches_wort(wort):
                continue
            kern = wort.replace("-", "")
            if len(kern) < grenze:
                continue
            if wort.lower() in gesehen:
                continue
            gesehen.add(wort.lower())
            treffer.append({
                "zeile": nummer,
                "wort": wort,
                "zeichen": len(kern),
                "silben": tc.silben(wort),
                "hat_bindestrich": "-" in wort,
            })

    return sorted(treffer, key=lambda t: -t["zeichen"])


def abkuerzungen(text, bekannte):
    eingefuehrt = set(ABK_EINGEFUEHRT_RE.findall(text))
    bekannt = {b.upper() for b in bekannte}
    zaehler = Counter()
    erste_zeile = {}

    for nummer, zeile in _zeilenindex(text):
        for abk in ABK_RE.findall(zeile):
            zaehler[abk] += 1
            erste_zeile.setdefault(abk, nummer)

    offen = []
    for abk, anzahl in zaehler.items():
        if abk in eingefuehrt or abk in bekannt:
            continue
        offen.append({"abkuerzung": abk, "anzahl": anzahl,
                      "erste_zeile": erste_zeile[abk]})

    return sorted(offen, key=lambda a: -a["anzahl"])


def variantenmischung(text, gruppen):
    klein = text.lower()
    befunde = []

    for gruppe in gruppen:
        gefunden = []
        for variante in gruppe:
            muster = re.compile(r"(?<![\wäöüß-])%s(?![\wäöüß])"
                                % re.escape(variante.lower()))
            anzahl = len(muster.findall(klein))
            if anzahl:
                gefunden.append({"variante": variante, "anzahl": anzahl})

        if len(gefunden) >= 2:
            gefunden.sort(key=lambda g: -g["anzahl"])
            befunde.append({
                "varianten": gefunden,
                "vorschlag": "durchgehend '%s' verwenden"
                             % gefunden[0]["variante"],
            })

    return befunde


def analysiere(vorbereitet, stufe):
    listen = tc.lade_wortlisten()
    text = vorbereitet["text"]
    zeilen = _zeilenindex(text)

    fachwort_pruefen = tc.STUFEN[stufe]["fachwort_pruefen"]

    ergebnis = {
        "stufe": stufe,
        "nominalstil": nominalstil(zeilen, stufe),
        "funktionsverbgefuege": _phrasen_suchen(
            zeilen, listen.get("funktionsverbgefuege", {})),
        "amtsdeutsch": _phrasen_suchen(zeilen, listen.get("amtsdeutsch", {})),
        "floskeln": _phrasen_suchen(zeilen, listen.get("floskeln", {})),
        "lange_komposita": lange_komposita(zeilen, stufe),
        "abkuerzungen_ohne_einfuehrung": abkuerzungen(
            text, listen.get("bekannte_abkuerzungen", [])),
        "variantenmischung": variantenmischung(
            text, listen.get("variantengruppen", [])),
    }

    # Fremdwoerter sind in PLAIN kein Befund: dort liest Fachpublikum.
    ergebnis["fremdwoerter"] = (
        _phrasen_suchen(zeilen, listen.get("fremdwoerter", {}))
        if fachwort_pruefen else []
    )
    ergebnis["fremdwoerter_geprueft"] = fachwort_pruefen

    return ergebnis


def _block(titel, eintraege, formatter, limit):
    if not eintraege:
        return

    print("%s (%d)" % (titel, len(eintraege)))
    for eintrag in eintraege[:limit]:
        print("   " + formatter(eintrag))
    if len(eintraege) > limit:
        print("   ... %d weitere" % (len(eintraege) - limit))
    print()


def bericht(daten, limit):
    n = daten["nominalstil"]

    print("Wortebene - Stufe %s" % daten["stufe"])
    print()
    print("Nominalstil: %.1f je 100 Woerter (Grenze %.1f)%s"
          % (n["dichte_pro_100_woerter"], n["grenze"],
             "  ZU HOCH" if n["ueber_grenze"] else ""))
    if n["haeufigste"]:
        print("   haeufigste: " + ", ".join(
            "%s (%d)" % (h["wort"], h["anzahl"]) for h in n["haeufigste"][:6]))
    print()

    _block("Funktionsverbgefuege", daten["funktionsverbgefuege"],
           lambda e: "Z%-4d %-32s -> %s" % (e["zeile"], e["fund"], e["vorschlag"]),
           limit)

    _block("Amtsdeutsch", daten["amtsdeutsch"],
           lambda e: "Z%-4d %-32s -> %s" % (e["zeile"], e["fund"], e["vorschlag"]),
           limit)

    if daten["fremdwoerter_geprueft"]:
        _block("Fremdwoerter", daten["fremdwoerter"],
               lambda e: "Z%-4d %-32s -> %s" % (e["zeile"], e["fund"], e["vorschlag"]),
               limit)
    else:
        print("Fremdwoerter: in Stufe PLAIN nicht geprueft (Fachpublikum)")
        print()

    _block("Floskeln", daten["floskeln"],
           lambda e: "Z%-4d %-32s -> %s" % (e["zeile"], e["fund"], e["vorschlag"]),
           limit)

    _block("Lange Woerter", daten["lange_komposita"],
           lambda e: "Z%-4d %-32s %d Zeichen, %d Silben%s"
                     % (e["zeile"], e["wort"], e["zeichen"], e["silben"],
                        "" if e["hat_bindestrich"] else "  (ohne Bindestrich)"),
           limit)

    _block("Abkuerzungen ohne Einfuehrung", daten["abkuerzungen_ohne_einfuehrung"],
           lambda e: "Z%-4d %-10s %dx - bei erster Nennung ausschreiben"
                     % (e["erste_zeile"], e["abkuerzung"], e["anzahl"]),
           limit)

    _block("Begriffsvarianten", daten["variantenmischung"],
           lambda e: "%s  ->  %s"
                     % (", ".join("%s (%d)" % (v["variante"], v["anzahl"])
                                  for v in e["varianten"]), e["vorschlag"]),
           limit)


def main():
    p = argparse.ArgumentParser(description="Wort-Linter fuer Einfache Sprache")
    p.add_argument("--file")
    p.add_argument("--latest")
    p.add_argument("--stufe", default=tc.DEFAULT_STUFE)
    p.add_argument("--limit", type=int, default=12)
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
