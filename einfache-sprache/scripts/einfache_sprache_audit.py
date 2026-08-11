#!/usr/bin/env python3

# Sammelcheck fuer den Skill einfache-sprache:
# fuehrt Lesbarkeits-, Satz-, Wort- und Struktur-Linter zusammen, bewertet
# gegen die Zielwerte der gewaehlten Stufe und nennt die groessten Hebel.
# Mit --vergleich zusaetzlich Vorher/Nachher gegen eine zweite Datei.
# version 1.37.0

import argparse

import textcore as tc
import readability_lint
import sentence_lint
import lexicon_lint
import structure_lint


def sammle(pfad, stufe):
    vorbereitet = tc.vorbereiten(pfad)

    return {
        "datei": pfad,
        "stufe": stufe,
        "lesbarkeit": readability_lint.analysiere(vorbereitet, stufe),
        "satzbau": sentence_lint.analysiere(vorbereitet, stufe),
        "wortebene": lexicon_lint.analysiere(vorbereitet, stufe),
        "struktur": structure_lint.analysiere(vorbereitet, stufe),
    }


def hebel(daten):
    """Die groessten Hebel, absteigend nach Wirkung. Bewusst kurz: wer
    zwanzig Punkte bekommt, arbeitet keinen davon ab."""
    punkte = []
    les = daten["lesbarkeit"]
    satz = daten["satzbau"]
    wort = daten["wortebene"]
    struktur = daten["struktur"]

    if "fehler" in les:
        return [("hoch", les["fehler"])]

    ampel = les["ampel"]
    g = les["grundzahlen"]
    z = les["zielwerte"]

    if ampel.get("mittlere_satzlaenge") == "rot":
        punkte.append(("hoch", "Saetze kuerzen: Mittel %.1f Woerter, Ziel %s. "
                               "%d Saetze ueber %d Woertern."
                       % (g["mittlere_satzlaenge"], z["mittlere_satzlaenge"],
                          les["ueberlange_saetze"], z["satz_max"])))
    elif les["ueberlange_saetze"]:
        punkte.append(("mittel", "%d Saetze ueber %d Woertern teilen."
                       % (les["ueberlange_saetze"], z["satz_max"])))

    anzahl_nebensaetze = satz["regelzaehler"].get("S2-nebensaetze", 0)
    if anzahl_nebensaetze:
        punkte.append(("hoch" if anzahl_nebensaetze > 5 else "mittel",
                       "%d Saetze mit zu vielen Nebensaetzen aufteilen."
                       % anzahl_nebensaetze))

    if satz["passiv_ueber_ziel"]:
        punkte.append(("hoch", "Passiv aufloesen: %.1f %% der Saetze, Ziel %s %%. "
                               "Handelnden benennen; fehlt er im Text, als "
                               "offenen Punkt melden."
                       % (satz["passiv_pct"], satz["passiv_ziel_pct"])))

    n = wort["nominalstil"]
    if n["ueber_grenze"]:
        beispiele = ", ".join(h["wort"] for h in n["haeufigste"][:3])
        punkte.append(("hoch", "Nominalstil aufloesen: %.1f je 100 Woerter, "
                               "Ziel %.1f (%s)."
                       % (n["dichte_pro_100_woerter"], n["grenze"], beispiele)))

    if wort["funktionsverbgefuege"]:
        punkte.append(("mittel", "%d Funktionsverbgefuege durch das Vollverb "
                                 "ersetzen." % len(wort["funktionsverbgefuege"])))

    if wort["amtsdeutsch"]:
        punkte.append(("mittel", "%d Amtsdeutsch-Ausdruecke ersetzen."
                       % len(wort["amtsdeutsch"])))

    if wort["fremdwoerter"]:
        punkte.append(("mittel", "%d Fremdwoerter ersetzen oder erklaeren."
                       % len(wort["fremdwoerter"])))

    if wort["variantenmischung"]:
        punkte.append(("hoch", "%d Begriffe werden uneinheitlich benannt - je "
                               "Sache ein Wort." % len(wort["variantenmischung"])))

    if wort["abkuerzungen_ohne_einfuehrung"]:
        punkte.append(("niedrig", "%d Abkuerzungen ohne Einfuehrung."
                       % len(wort["abkuerzungen_ohne_einfuehrung"])))

    if struktur["absaetze_zu_lang"]:
        punkte.append(("mittel", "%d Absaetze zu lang - ein Gedanke je Absatz."
                       % len(struktur["absaetze_zu_lang"])))

    if struktur["listenkandidaten"]:
        punkte.append(("mittel", "%d Aufzaehlungen stecken im Fliesstext - als "
                                 "Liste setzen." % len(struktur["listenkandidaten"])))

    if struktur["anrede"]["gemischt"]:
        punkte.append(("mittel", "Anrede gemischt (Sie/du) - eine Form waehlen."))

    if struktur["datumsformate_gemischt"]:
        punkte.append(("niedrig", "Datumsformate gemischt."))

    rang = {"hoch": 0, "mittel": 1, "niedrig": 2}

    return sorted(punkte, key=lambda p: rang[p[0]])


def gesamtnote(daten):
    """Grobe Ampel ueber alles. Keine Note im Sinne einer Bewertung des
    Textes - nur ein Hinweis, wie weit der Text von der Stufe entfernt ist."""
    les = daten["lesbarkeit"]

    if "fehler" in les:
        return "unbekannt"

    rot = sum(1 for w in les["ampel"].values() if w == "rot")
    gelb = sum(1 for w in les["ampel"].values() if w == "gelb")

    if daten["satzbau"]["passiv_ueber_ziel"]:
        rot += 1
    if daten["wortebene"]["nominalstil"]["ueber_grenze"]:
        rot += 1

    if rot >= 3:
        return "weit entfernt"
    if rot >= 1:
        return "ueberarbeiten"
    if gelb >= 2:
        return "knapp"

    return "erreicht"


def bericht(daten, limit):
    les = daten["lesbarkeit"]

    print("=" * 72)
    print("Einfache Sprache - %s" % daten["datei"])
    print("Stufe %s   Bewertung: %s" % (daten["stufe"], gesamtnote(daten)))
    print("=" * 72)
    print()

    readability_lint.bericht(les)
    print()
    print("-" * 72)
    print()

    satz = daten["satzbau"]
    print("Satzbau: %d von %d Saetzen mit Befund, Passiv %.1f %% (Ziel <= %s %%)"
          % (satz["saetze_mit_befund"], satz["saetze_gesamt"],
             satz["passiv_pct"], satz["passiv_ziel_pct"]))
    if satz["regelzaehler"]:
        print("   " + ", ".join("%s: %d" % (r, a)
                                for r, a in satz["regelzaehler"].items()))

    wort = daten["wortebene"]
    n = wort["nominalstil"]
    print("Wortebene: Nominalstil %.1f/100 (Ziel %.1f), "
          "Funktionsverbgefuege %d, Amtsdeutsch %d, Fremdwoerter %d"
          % (n["dichte_pro_100_woerter"], n["grenze"],
             len(wort["funktionsverbgefuege"]), len(wort["amtsdeutsch"]),
             len(wort["fremdwoerter"])))

    struktur = daten["struktur"]
    print("Struktur: %d Ueberschriften, %d zu lange Absaetze, %d Listenkandidaten"
          % (struktur["ueberschriften"], len(struktur["absaetze_zu_lang"]),
             len(struktur["listenkandidaten"])))

    print()
    print("-" * 72)
    print()
    print("Groesste Hebel:")
    punkte = hebel(daten)

    if not punkte:
        print("   Keine. Der Text erfuellt die Zielwerte der Stufe.")
    for gewicht, text in punkte[:limit]:
        print("   [%-7s] %s" % (gewicht, text))

    print()
    print("Details je Ebene:")
    print("   sentence_lint.py  --file %s --stufe %s" % (daten["datei"], daten["stufe"]))
    print("   lexicon_lint.py   --file %s --stufe %s" % (daten["datei"], daten["stufe"]))
    print("   structure_lint.py --file %s --stufe %s" % (daten["datei"], daten["stufe"]))
    print()
    print("Befunde sind Verdacht, kein Verdikt - vor jeder Aenderung gegen den")
    print("Kontext und die Carve-outs in SKILL.md pruefen.")


def vergleich_bericht(vorher, nachher):
    print("=" * 72)
    print("Vergleich - Stufe %s" % nachher["stufe"])
    print("  vorher:  %s" % vorher["datei"])
    print("  nachher: %s" % nachher["datei"])
    print("=" * 72)
    print()

    v = vorher["lesbarkeit"]
    n = nachher["lesbarkeit"]

    if "fehler" in v or "fehler" in n:
        print("Kein auswertbarer Prosatext in mindestens einer Datei.")
        return

    zeilen = [
        ("Satzlaenge (Mittel)", v["grundzahlen"]["mittlere_satzlaenge"],
         n["grundzahlen"]["mittlere_satzlaenge"], n["zielwerte"]["mittlere_satzlaenge"], "<="),
        ("Woerter 3+ Silben %", v["grundzahlen"]["pct_woerter_3plus_silben"],
         n["grundzahlen"]["pct_woerter_3plus_silben"],
         n["zielwerte"]["pct_woerter_3plus_silben"], "<="),
        ("Wiener Sachtextf. 1", v["indizes"]["wstf1"], n["indizes"]["wstf1"],
         n["zielwerte"]["wstf1"], "<="),
        ("LIX", v["indizes"]["lix"], n["indizes"]["lix"], n["zielwerte"]["lix"], "<="),
        ("Flesch (Amstad)", v["indizes"]["flesch"], n["indizes"]["flesch"],
         n["zielwerte"]["flesch"], ">="),
        ("Passiv %", vorher["satzbau"]["passiv_pct"], nachher["satzbau"]["passiv_pct"],
         nachher["satzbau"]["passiv_ziel_pct"], "<="),
        ("Nominalstil /100", vorher["wortebene"]["nominalstil"]["dichte_pro_100_woerter"],
         nachher["wortebene"]["nominalstil"]["dichte_pro_100_woerter"],
         nachher["wortebene"]["nominalstil"]["grenze"], "<="),
    ]

    print("  %-22s %8s %8s %8s   %s" % ("Kennwert", "vorher", "nachher", "Ziel", ""))
    for name, alt, neu, ziel, richtung in zeilen:
        erreicht = neu <= ziel if richtung == "<=" else neu >= ziel
        print("  %-22s %8.1f %8.1f %8s   %s"
              % (name, alt, neu, ziel, "ok" if erreicht else "offen"))

    print()
    print("  Woerter: %d -> %d" % (v["grundzahlen"]["woerter"], n["grundzahlen"]["woerter"]))
    print("  Saetze:  %d -> %d" % (v["grundzahlen"]["saetze"], n["grundzahlen"]["saetze"]))
    print()
    print("  Zahlen sagen nichts darueber, ob Inhalt verloren ging.")
    print("  Fristen, Betraege, Bedingungen und Rechtsfolgen von Hand abgleichen.")


def main():
    p = argparse.ArgumentParser(
        description="Sammelcheck Einfache Sprache (Lesbarkeit, Satz, Wort, Struktur)")
    p.add_argument("--file")
    p.add_argument("--latest", help="juengste Markdown-/Textdatei im Verzeichnis")
    p.add_argument("--stufe", default=tc.DEFAULT_STUFE, help="PLAIN, B1 oder A2")
    p.add_argument("--vergleich", help="zweite Datei als Vorher-Stand")
    p.add_argument("--limit", type=int, default=8)
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    stufe = tc.stufe_pruefen(args.stufe)
    pfad = tc.quelle_aufloesen(args)
    daten = sammle(pfad, stufe)
    daten["bewertung"] = gesamtnote(daten)
    daten["hebel"] = [{"gewicht": g, "text": t} for g, t in hebel(daten)]

    if args.vergleich:
        vorher = sammle(args.vergleich, stufe)
        if args.json:
            tc.ausgeben({"vorher": vorher, "nachher": daten}, True)
        else:
            vergleich_bericht(vorher, daten)
        return

    if not tc.ausgeben(daten, args.json):
        bericht(daten, args.limit)


if __name__ == "__main__":
    main()
