#!/usr/bin/env python3

# Lesbarkeitsmessung fuer deutsche Sachtexte:
# Wiener Sachtextformel 1-4, LIX, Flesch (deutsche Fassung nach Amstad),
# Satzlaengenverteilung und die laengsten Saetze.
# Formeln und ihre Grenzen: references/lesbarkeitsmasse.md
# version 1.37.0

import argparse

import textcore as tc


def wiener_sachtextformel(k):
    """Vier Varianten, alle in Schulstufen (4 = sehr leicht, 15 = sehr schwer).
    MS = Anteil Woerter mit 3+ Silben, SL = mittlere Satzlaenge,
    IW = Anteil Woerter ueber 6 Zeichen, ES = Anteil Einsilber."""
    ms = k["pct_woerter_3plus_silben"]
    sl = k["mittlere_satzlaenge"]
    iw = k["pct_woerter_ueber_6_zeichen"]
    es = k["pct_einsilber"]

    return {
        "wstf1": 0.1935 * ms + 0.1672 * sl + 0.1297 * iw - 0.0327 * es - 0.875,
        "wstf2": 0.2007 * ms + 0.1682 * sl + 0.1373 * iw - 2.779,
        "wstf3": 0.2963 * ms + 0.1905 * sl - 1.1144,
        "wstf4": 0.2656 * sl + 0.2744 * ms - 1.693,
    }


def lix(k):
    """Laesbarhetsindex: Satzlaenge plus Anteil langer Woerter.
    < 40 leicht, 40-50 mittel, 50-60 schwer, > 60 sehr schwer."""
    return k["mittlere_satzlaenge"] + k["pct_woerter_ueber_6_zeichen"]


def flesch_amstad(k):
    """Flesch-Reading-Ease in der deutschen Anpassung nach Amstad.
    0-30 sehr schwer, 60-70 mittel, 90-100 sehr leicht."""
    return 180 - k["mittlere_satzlaenge"] - 58.5 * k["silben_je_wort"]


def schulstufe_text(wert):
    if wert < 6:
        return "sehr leicht"
    if wert < 9:
        return "leicht"
    if wert < 12:
        return "mittel"
    if wert < 14:
        return "schwer"

    return "sehr schwer"


def verteilung(satzlaengen):
    grenzen = [(0, 8), (9, 15), (16, 20), (21, 25), (26, 35), (36, 10**6)]
    namen = ["bis_8", "9_bis_15", "16_bis_20", "21_bis_25", "26_bis_35", "ueber_35"]
    ergebnis = {}

    for name, (unten, oben) in zip(namen, grenzen):
        ergebnis[name] = sum(1 for l in satzlaengen if unten <= l <= oben)

    return ergebnis


def analysiere(vorbereitet, stufe):
    ziel = tc.STUFEN[stufe]
    saetze = vorbereitet["saetze"]
    k = tc.kennwerte(saetze)

    if not k:
        return {"fehler": "kein auswertbarer Prosatext gefunden"}

    wstf = wiener_sachtextformel(k)
    lix_wert = lix(k)
    flesch = flesch_amstad(k)

    lange_saetze = sorted(
        [(len(tc.woerter(s)), s, z) for s, z in saetze],
        reverse=True,
    )[:5]

    ampel = {}

    def bewerte(name, wert, grenze, kleiner_ist_besser=True):
        if kleiner_ist_besser:
            ok = wert <= grenze
            knapp = wert <= grenze * 1.15
        else:
            ok = wert >= grenze
            knapp = wert >= grenze * 0.85
        ampel[name] = "gruen" if ok else ("gelb" if knapp else "rot")

    bewerte("mittlere_satzlaenge", k["mittlere_satzlaenge"], ziel["satz_mittel"])
    bewerte("pct_woerter_3plus_silben", k["pct_woerter_3plus_silben"],
            ziel["lange_woerter_pct"])
    bewerte("wstf1", wstf["wstf1"], ziel["wstf1"])
    bewerte("lix", lix_wert, ziel["lix"])
    bewerte("flesch", flesch, ziel["flesch"], kleiner_ist_besser=False)

    ueberlang = [(l, s, z) for l, s, z in lange_saetze if l > ziel["satz_max"]]

    return {
        "stufe": stufe,
        "belastbar": k["saetze"] >= tc.MIN_SAETZE_FUER_INDIZES,
        "hinweis_kurztext": None if k["saetze"] >= tc.MIN_SAETZE_FUER_INDIZES else
            "Unter %d Saetzen sind die Indizes nicht belastbar."
            % tc.MIN_SAETZE_FUER_INDIZES,
        "grundzahlen": {
            "saetze": k["saetze"],
            "woerter": k["woerter"],
            "silben": k["silben"],
            "mittlere_satzlaenge": round(k["mittlere_satzlaenge"], 1),
            "silben_je_wort": round(k["silben_je_wort"], 2),
            "pct_woerter_3plus_silben": round(k["pct_woerter_3plus_silben"], 1),
            "pct_woerter_ueber_6_zeichen": round(k["pct_woerter_ueber_6_zeichen"], 1),
        },
        "indizes": {
            "wstf1": round(wstf["wstf1"], 1),
            "wstf2": round(wstf["wstf2"], 1),
            "wstf3": round(wstf["wstf3"], 1),
            "wstf4": round(wstf["wstf4"], 1),
            "wstf1_einordnung": schulstufe_text(wstf["wstf1"]),
            "lix": round(lix_wert, 1),
            "flesch": round(flesch, 1),
        },
        "zielwerte": {
            "mittlere_satzlaenge": ziel["satz_mittel"],
            "satz_max": ziel["satz_max"],
            "pct_woerter_3plus_silben": ziel["lange_woerter_pct"],
            "wstf1": ziel["wstf1"],
            "lix": ziel["lix"],
            "flesch": ziel["flesch"],
        },
        "ampel": ampel,
        "satzlaengen_verteilung": verteilung(k["satzlaengen"]),
        "laengste_saetze": [
            {"woerter": l, "zeile": z, "satz": s[:160]} for l, s, z in lange_saetze
        ],
        "ueberlange_saetze": len(ueberlang),
    }


def bericht(daten):
    if "fehler" in daten:
        print("Fehler: %s" % daten["fehler"])
        return

    g = daten["grundzahlen"]
    i = daten["indizes"]
    z = daten["zielwerte"]
    a = daten["ampel"]

    marke = {"gruen": "ok  ", "gelb": "knapp", "rot": "ZU HOCH"}

    print("Stufe %s - %d Saetze, %d Woerter" % (daten["stufe"], g["saetze"], g["woerter"]))

    if daten["hinweis_kurztext"]:
        print("Hinweis: %s" % daten["hinweis_kurztext"])

    print()
    print("  Satzlaenge (Mittel)     %5.1f   Ziel <= %-5s  %s"
          % (g["mittlere_satzlaenge"], z["mittlere_satzlaenge"],
             marke[a["mittlere_satzlaenge"]]))
    print("  Woerter mit 3+ Silben   %5.1f%%  Ziel <= %-4s%%  %s"
          % (g["pct_woerter_3plus_silben"], z["pct_woerter_3plus_silben"],
             marke[a["pct_woerter_3plus_silben"]]))
    print("  Wiener Sachtextformel 1 %5.1f   Ziel <= %-5s  %s   (%s)"
          % (i["wstf1"], z["wstf1"], marke[a["wstf1"]], i["wstf1_einordnung"]))
    print("  LIX                     %5.1f   Ziel <= %-5s  %s"
          % (i["lix"], z["lix"], marke[a["lix"]]))
    print("  Flesch (Amstad)         %5.1f   Ziel >= %-5s  %s"
          % (i["flesch"], z["flesch"], marke[a["flesch"]]))

    print()
    print("  Satzlaengen: " + ", ".join(
        "%s: %d" % (name.replace("_", " "), wert)
        for name, wert in daten["satzlaengen_verteilung"].items() if wert))

    if daten["laengste_saetze"]:
        print()
        print("  Laengste Saetze (Grenze %d Woerter):" % z["satz_max"])
        for eintrag in daten["laengste_saetze"]:
            if eintrag["woerter"] <= z["satz_max"]:
                continue
            print("   Z%-4d %3d Woerter  %s" % (eintrag["zeile"], eintrag["woerter"],
                                                eintrag["satz"]))


def main():
    p = argparse.ArgumentParser(description="Lesbarkeitsindizes fuer deutsche Sachtexte")
    p.add_argument("--file")
    p.add_argument("--latest", help="juengste Markdown-/Textdatei im Verzeichnis")
    p.add_argument("--stufe", default=tc.DEFAULT_STUFE, help="PLAIN, B1 oder A2")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    stufe = tc.stufe_pruefen(args.stufe)
    pfad = tc.quelle_aufloesen(args)
    daten = analysiere(tc.vorbereiten(pfad), stufe)
    daten["datei"] = pfad

    if not tc.ausgeben(daten, args.json):
        bericht(daten)


if __name__ == "__main__":
    main()
