#!/usr/bin/env python3

# Gemeinsame Textbasis fuer die Linter des Skills einfache-sprache:
# Einlesen, Maskierung technischer Bereiche, Satz- und Worttrennung,
# Silbenzaehlung und die Stufenprofile.
# stdlib only.
# version 1.37.0

import json
import os
import re
import sys

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# Zielwerte je Stufe. Spiegelt die Tabelle in SKILL.md - beide zusammen aendern.

STUFEN = {
    "PLAIN": {
        "satz_mittel": 18, "satz_max": 30, "nebensaetze": 2,
        "lange_woerter_pct": 20.0, "passiv_pct": 20.0, "absatz_saetze": 6,
        "wstf1": 11.0, "lix": 50.0, "flesch": 50.0,
        "fachwort_pruefen": False,
    },
    "B1": {
        "satz_mittel": 15, "satz_max": 25, "nebensaetze": 1,
        "lange_woerter_pct": 15.0, "passiv_pct": 10.0, "absatz_saetze": 5,
        "wstf1": 9.0, "lix": 45.0, "flesch": 60.0,
        "fachwort_pruefen": True,
    },
    "A2": {
        "satz_mittel": 12, "satz_max": 20, "nebensaetze": 0,
        "lange_woerter_pct": 10.0, "passiv_pct": 5.0, "absatz_saetze": 3,
        "wstf1": 7.0, "lix": 40.0, "flesch": 70.0,
        "fachwort_pruefen": True,
    },
}

DEFAULT_STUFE = "B1"

# Unter dieser Satzzahl sind die Lesbarkeitsindizes nicht belastbar.

MIN_SAETZE_FUER_INDIZES = 10


def lade_wortlisten():
    """Wortlisten aus data/wortlisten.json. Fehlt die Datei, laufen die
    Linter mit leeren Listen weiter statt abzubrechen - die strukturellen
    Befunde haengen nicht daran."""
    pfad = os.path.join(DATA_DIR, "wortlisten.json")

    try:
        with open(pfad, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError) as e:
        print("warn: wortlisten.json nicht lesbar (%s)" % e, file=sys.stderr)
        return {}


def lies_text(pfad):
    with open(pfad, encoding="utf-8") as f:
        return f.read()


def juengste_markdown(verzeichnis):
    """Neueste .md-Datei in einem Verzeichnis (nicht rekursiv)."""
    kandidaten = []

    for name in os.listdir(verzeichnis):
        if name.lower().endswith((".md", ".markdown", ".txt")):
            voll = os.path.join(verzeichnis, name)
            if os.path.isfile(voll):
                kandidaten.append((os.path.getmtime(voll), voll))

    if not kandidaten:
        return None

    return sorted(kandidaten)[-1][1]


# --- Maskierung: technische Bereiche zaehlen nicht als Prosa ------------------

CODEBLOCK_RE = re.compile(r"^(```|~~~).*?^(```|~~~)", re.S | re.M)
INLINE_CODE_RE = re.compile(r"`[^`\n]+`")
FRONTMATTER_RE = re.compile(r"\A---\n.*?\n---\n", re.S)
MD_LINK_RE = re.compile(r"\[([^\]]*)\]\([^)]*\)")
MD_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\([^)]*\)")
HTML_TAG_RE = re.compile(r"<[^>\n]{1,200}>")
URL_RE = re.compile(r"\b(?:https?://|www\.)\S+")
PFAD_RE = re.compile(r"(?:(?<=\s)|\A)[~/][\w./\-]{4,}")
MAIL_RE = re.compile(r"\b[\w.%+-]+@[\w.-]+\.[A-Za-z]{2,}\b")


def entferne_prosa_fremdes(text, behalte_zeilen=True):
    """Ersetzt Code, Frontmatter, URLs, Pfade und HTML durch Platzhalter.
    behalte_zeilen erhaelt die Zeilenzahl, damit gemeldete Zeilennummern
    weiterhin auf die Originaldatei passen."""

    def leeren(m):
        roh = m.group(0)
        return "\n" * roh.count("\n") if behalte_zeilen else " "

    text = FRONTMATTER_RE.sub(leeren, text)
    text = CODEBLOCK_RE.sub(leeren, text)
    text = MD_IMAGE_RE.sub(" ", text)
    # Linktext bleibt Prosa, das Ziel nicht
    text = MD_LINK_RE.sub(lambda m: m.group(1), text)
    text = INLINE_CODE_RE.sub(" CODE ", text)
    text = HTML_TAG_RE.sub(" ", text)
    text = URL_RE.sub(" URL ", text)
    text = MAIL_RE.sub(" MAILADRESSE ", text)
    text = PFAD_RE.sub(" PFAD ", text)

    return text


ATX_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+(.*)$")
LISTEN_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
TABELLE_RE = re.compile(r"^\s*\|")
BLOCKQUOTE_RE = re.compile(r"^\s*>")


def zeilen_klassifizieren(text):
    """Ordnet jeder Zeile eine Art zu: heading, liste, tabelle, zitat, leer,
    prosa. Grundlage fuer structure_lint und fuer den Ausschluss von
    Ueberschriften aus der Satzstatistik."""
    arten = []

    for zeile in text.split("\n"):
        if not zeile.strip():
            arten.append("leer")
        elif ATX_HEADING_RE.match(zeile):
            arten.append("heading")
        elif TABELLE_RE.match(zeile):
            arten.append("tabelle")
        elif LISTEN_RE.match(zeile):
            arten.append("liste")
        elif BLOCKQUOTE_RE.match(zeile):
            arten.append("zitat")
        else:
            arten.append("prosa")

    return arten


# --- Saetze ------------------------------------------------------------------

# Abkuerzungen, nach denen ein Punkt keinen Satz beendet.

ABKUERZUNGEN = {
    "z.b", "u.a", "d.h", "bzw", "ca", "evtl", "ggf", "inkl", "exkl", "usw",
    "u.s.w", "etc", "vgl", "s.o", "s.u", "bspw", "max", "min", "nr", "abs",
    "art", "bzgl", "dr", "prof", "ing", "gem", "sog", "tsd", "mio", "mrd",
    "jh", "jhd", "st", "hr", "fr", "zzgl", "abzgl", "einschl", "lt", "pos",
    "tel", "mwst", "i.d.r", "z.t", "u.u", "o.ae", "u.ae", "ff", "f",
}

SATZ_ENDE_RE = re.compile(r"([.!?:;]+)(\s+|$)")


def _ist_abkuerzung(vortext):
    """Prueft, ob der Punkt zu einer Abkuerzung gehoert."""
    letztes = re.split(r"[\s(\[]", vortext.strip())[-1] if vortext.strip() else ""
    letztes = letztes.rstrip(".").lower()

    if not letztes:
        return False
    if letztes in ABKUERZUNGEN:
        return True
    # Einzelbuchstabe mit Punkt: Initiale oder Gliederung
    if len(letztes) == 1 and letztes.isalpha():
        return True
    # Ordnungszahl (1. Januar, 3. Absatz)
    if letztes.isdigit():
        return True

    return False


def zerlege_saetze(text, zeilen_arten=None):
    """Zerlegt Prosa in Saetze. Liefert Tupel (satz, zeilennummer).
    Ueberschriften, Listenpunkte, Tabellen- und Zitatzeilen werden
    ausgeschlossen - sie folgen eigenen Regeln und wuerden die
    Satzstatistik verzerren."""
    zeilen = text.split("\n")

    if zeilen_arten is None:
        zeilen_arten = zeilen_klassifizieren(text)

    saetze = []
    puffer = ""
    puffer_zeile = 1

    for idx, zeile in enumerate(zeilen):
        art = zeilen_arten[idx] if idx < len(zeilen_arten) else "prosa"

        if art in ("heading", "tabelle", "zitat"):
            continue

        if art == "leer":
            if puffer.strip():
                saetze.append((puffer.strip(), puffer_zeile))
                puffer = ""
            continue

        inhalt = zeile
        if art == "liste":
            inhalt = LISTEN_RE.sub("", zeile)

        if not puffer.strip():
            puffer_zeile = idx + 1

        puffer = (puffer + " " + inhalt).strip() if puffer else inhalt

        # Innerhalb des Puffers alle abgeschlossenen Saetze abtrennen
        while True:
            treffer = None
            for m in SATZ_ENDE_RE.finditer(puffer):
                if m.group(1) == "." and _ist_abkuerzung(puffer[:m.start()]):
                    continue
                treffer = m
                break

            if not treffer:
                break

            satz = puffer[:treffer.end(1)].strip()
            if satz:
                saetze.append((satz, puffer_zeile))
            puffer = puffer[treffer.end():].strip()
            puffer_zeile = idx + 1

        # Listenpunkte ohne Satzzeichen gelten trotzdem als abgeschlossen
        if art == "liste" and puffer.strip():
            saetze.append((puffer.strip(), puffer_zeile))
            puffer = ""

    if puffer.strip():
        saetze.append((puffer.strip(), puffer_zeile))

    return saetze


# --- Woerter und Silben ------------------------------------------------------

WORT_RE = re.compile(r"[A-Za-zÄÖÜäöüßÀ-ÿ]+(?:[-'][A-Za-zÄÖÜäöüßÀ-ÿ]+)*")

VOKALE = "aeiouäöüy"
DIPHTHONGE = ("eau", "aa", "ae", "ai", "au", "äu", "ee", "ei", "eu", "ie",
              "ii", "oo", "oe", "ou", "ue", "uu")


def woerter(text):
    return WORT_RE.findall(text)


def silben(wort):
    """Silbenzahl nach Vokalgruppen, mit Diphthong-Zusammenfassung.
    Heuristik: bei Fremdwoertern und Eigennamen regelmaessig um eine Silbe
    daneben. Fuer die Indizes reicht das, fuer Einzelurteile nicht."""
    w = wort.lower()
    w = w.replace("ß", "ss")

    # Bindestrich-Komposita silbenweise addieren
    if "-" in w:
        teile = [t for t in w.split("-") if t]
        return max(1, sum(silben(t) for t in teile))

    if not w:
        return 0

    anzahl = 0
    i = 0
    vorher_vokal = False

    while i < len(w):
        zeichen = w[i]

        if zeichen in VOKALE:
            if not vorher_vokal:
                anzahl += 1
                # Diphthong: die naechsten Zeichen gehoeren zur selben Silbe
                rest = w[i:i + 3]
                if rest[:3] in DIPHTHONGE:
                    i += 3
                    vorher_vokal = False
                    continue
                if w[i:i + 2] in DIPHTHONGE:
                    i += 2
                    vorher_vokal = False
                    continue
            vorher_vokal = True
        else:
            vorher_vokal = False

        i += 1

    # -tion, -sion: das i bildet eine eigene Silbe (Vokalgruppe faengt das nicht)
    if re.search(r"[ts]ion(en)?$", w):
        anzahl += 1

    # Stummes h zwischen Vokalen wurde bereits als Trenner gewertet - ok.
    return max(1, anzahl)


def ist_technisches_wort(wort):
    """Versionsnummern, Bezeichner und Grossbuchstaben-Kuerzel sollen nicht
    als Wortungetuem gelten."""
    if any(z.isdigit() for z in wort):
        return True
    if wort.isupper() and len(wort) <= 6:
        return True
    if "_" in wort:
        return True

    return False


def kennwerte(saetze):
    """Grundzahlen ueber eine Satzliste: Basis fuer alle Indizes."""
    alle_woerter = []
    satzlaengen = []

    for satz, _zeile in saetze:
        w = woerter(satz)
        if not w:
            continue
        alle_woerter.extend(w)
        satzlaengen.append(len(w))

    anzahl_woerter = len(alle_woerter)
    anzahl_saetze = len(satzlaengen)

    if not anzahl_woerter or not anzahl_saetze:
        return None

    silbenzahlen = [silben(w) for w in alle_woerter]

    lang_6 = sum(1 for w in alle_woerter if len(w) > 6)
    silben_3plus = sum(1 for s in silbenzahlen if s >= 3)
    einsilbig = sum(1 for s in silbenzahlen if s == 1)

    return {
        "woerter": anzahl_woerter,
        "saetze": anzahl_saetze,
        "silben": sum(silbenzahlen),
        "satzlaengen": satzlaengen,
        "mittlere_satzlaenge": anzahl_woerter / anzahl_saetze,
        "silben_je_wort": sum(silbenzahlen) / anzahl_woerter,
        "pct_woerter_ueber_6_zeichen": 100.0 * lang_6 / anzahl_woerter,
        "pct_woerter_3plus_silben": 100.0 * silben_3plus / anzahl_woerter,
        "pct_einsilber": 100.0 * einsilbig / anzahl_woerter,
    }


def stufe_pruefen(name):
    schluessel = (name or DEFAULT_STUFE).upper()

    if schluessel not in STUFEN:
        raise SystemExit("Unbekannte Stufe '%s'. Moeglich: %s"
                         % (name, ", ".join(STUFEN)))

    return schluessel


def quelle_aufloesen(args):
    """Gemeinsame --file/--latest-Logik aller Linter."""
    if getattr(args, "latest", None):
        pfad = juengste_markdown(args.latest)
        if not pfad:
            raise SystemExit("Keine Markdown-/Textdatei in %s" % args.latest)
        return pfad

    if not getattr(args, "file", None):
        raise SystemExit("--file oder --latest angeben")

    if not os.path.isfile(args.file):
        raise SystemExit("Datei nicht gefunden: %s" % args.file)

    return args.file


def vorbereiten(pfad):
    """Einheitliche Aufbereitung: roher Text, maskierter Text, Zeilenarten,
    Satzliste. Alle Linter starten hier."""
    roh = lies_text(pfad)
    maskiert = entferne_prosa_fremdes(roh)
    arten = zeilen_klassifizieren(roh)
    saetze = zerlege_saetze(maskiert, arten)

    return {
        "pfad": pfad,
        "roh": roh,
        "text": maskiert,
        "zeilen_arten": arten,
        "saetze": saetze,
    }


def ausgeben(daten, als_json):
    if als_json:
        print(json.dumps(daten, ensure_ascii=False, indent=2))
        return True

    return False
