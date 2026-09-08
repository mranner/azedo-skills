#!/usr/bin/env python3

"""Prueft das Frontmatter aller Skills im Repo gegen die Anthropic-Empfehlungen
und die Repo-Konventionen aus CLAUDE.md, dazu ihren Eintrag in install.sh.

Aufruf ohne Argumente im Repo-Wurzelverzeichnis (oder mit Pfaden auf einzelne
Skill-Verzeichnisse). Exit 0 = keine Fehler, Exit 1 = mindestens ein Fehler.
Warnungen aendern den Exit-Code nicht."""

import os
import re
import sys

# Schluessel, die Claude Code bzw. die Agent-Skills-Spec kennen. Alles andere
# ist vermutlich ein Tippfehler und wird gemeldet.

BEKANNTE_SCHLUESSEL = {
    "name",
    "description",
    "allowed-tools",
    "disable-model-invocation",
    "argument-hint",
    "metadata",
    "license",
    "compatibility",
}

MAX_DESCRIPTION = 1024
MAX_NAME = 64
MAX_BODY_ZEILEN = 500


def frontmatter(text):
    """Gibt (block, body) zurueck oder (None, None) ohne Frontmatter."""

    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None, None

    return m.group(1), text[m.end():]


def top_level_schluessel(block):
    """Sammelt die Schluessel der obersten Ebene samt ihrer Notation.

    Ein eigener Mini-Parser, weil PyYAML auf den Zielsystemen nicht
    durchgaengig installiert ist."""

    gefunden = {}
    for zeile in block.split("\n"):
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", zeile)
        if m:
            gefunden[m.group(1)] = m.group(2).strip()

    return gefunden


def description_text(block):
    """Liefert den zusammengesetzten Text der description."""

    zeilen = block.split("\n")
    for i, zeile in enumerate(zeilen):
        m = re.match(r"^description:\s*(.*)$", zeile)
        if not m:
            continue

        kopf = m.group(1).strip()
        if kopf not in (">", "|", ">-", "|-", ""):
            return kopf.strip("\"'")

        teile = []
        for folge in zeilen[i + 1:]:
            if folge.strip() and not folge.startswith("  "):
                break
            teile.append(folge.strip())

        return " ".join(t for t in teile if t)

    return None


def pruefe(verzeichnis):
    """Gibt (fehler, warnungen) fuer einen Skill zurueck."""

    fehler = []
    warnungen = []
    name_soll = os.path.basename(os.path.normpath(verzeichnis))
    pfad = os.path.join(verzeichnis, "SKILL.md")

    if not os.path.isfile(pfad):
        return ["SKILL.md fehlt"], []

    with open(pfad, encoding="utf-8") as f:
        text = f.read()

    block, body = frontmatter(text)
    if block is None:
        return ["kein YAML-Frontmatter (--- am Dateianfang)"], []

    schluessel = top_level_schluessel(block)

    # name

    name = schluessel.get("name", "").strip("\"'")
    if not name:
        fehler.append("name fehlt")
    else:
        if name != name_soll:
            fehler.append(f"name '{name}' passt nicht zum Verzeichnis '{name_soll}'")
        if not re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", name):
            fehler.append(f"name '{name}' ist nicht kebab-case")
        if len(name) > MAX_NAME:
            fehler.append(f"name laenger als {MAX_NAME} Zeichen")

    # description

    if "description" not in schluessel:
        fehler.append("description fehlt")
    else:
        notation = schluessel["description"]
        if notation and notation[0] not in ">|\"'":
            fehler.append(
                "description ist unquotiert - ein ': ' im Text (etwa in "
                "'Trigger: /name.') bricht strikte YAML-Parser. Block-Scalar "
                "'>' verwenden"
            )

        text_desc = description_text(block) or ""
        if not text_desc:
            fehler.append("description ist leer")
        elif len(text_desc) > MAX_DESCRIPTION:
            fehler.append(
                f"description hat {len(text_desc)} Zeichen, erlaubt sind {MAX_DESCRIPTION}"
            )

    # Version gehoert ausschliesslich in VERSION

    if re.search(r"^\s+version:", block, re.M):
        fehler.append(
            "version im Frontmatter - die Version steht ausschliesslich in "
            "VERSION (upstream_version fuer fremde Herkunft ist erlaubt)"
        )

    # unbekannte Schluessel

    unbekannt = [k for k in schluessel if k not in BEKANNTE_SCHLUESSEL]
    verschachtelt = set(re.findall(r"^  ([A-Za-z0-9_-]+):", block, re.M))
    unbekannt = [k for k in unbekannt if k not in verschachtelt]
    for k in unbekannt:
        warnungen.append(f"unbekannter Schluessel '{k}'")

    # Body-Laenge

    zeilen = len(body.splitlines())
    if zeilen > MAX_BODY_ZEILEN:
        warnungen.append(
            f"SKILL.md-Body hat {zeilen} Zeilen - ueber {MAX_BODY_ZEILEN} gehoert "
            "Inhalt nach references/"
        )

    return fehler, warnungen


def install_liste():
    """Liest die hartcodierte Skill-Liste aus install.sh.

    Fehlt ein Skill dort, bekommt eine frische Installation keinen Symlink -
    auf einer Maschine, die ihn schon verlinkt hat, faellt das nicht auf."""

    if not os.path.isfile("install.sh"):
        return None

    with open("install.sh", encoding="utf-8") as f:
        m = re.search(r"^for skill in (.+?); do", f.read(), re.M)

    if not m:
        return None

    return m.group(1).split()


def main():
    ziele = sys.argv[1:]
    if not ziele:
        ziele = sorted(
            d for d in os.listdir(".")
            if os.path.isfile(os.path.join(d, "SKILL.md"))
        )

    if not ziele:
        print("keine Skills gefunden - im Repo-Wurzelverzeichnis aufrufen")
        return 1

    fehler_gesamt = 0
    warnungen_gesamt = 0
    liste = install_liste()

    if liste is None:
        print("WARNUNG install.sh: Skill-Liste nicht gefunden - Eintrag ungeprueft")
        warnungen_gesamt += 1

    for ziel in ziele:
        fehler, warnungen = pruefe(ziel)
        name = os.path.basename(os.path.normpath(ziel))
        if liste is not None and name not in liste:
            fehler.append(
                "fehlt in der Skill-Liste von install.sh - eine frische "
                "Installation bekaeme keinen Symlink"
            )
        for f in fehler:
            print(f"FEHLER  {ziel}: {f}")
        for w in warnungen:
            print(f"WARNUNG {ziel}: {w}")
        fehler_gesamt += len(fehler)
        warnungen_gesamt += len(warnungen)

    if liste is not None and not sys.argv[1:]:
        namen = {os.path.basename(os.path.normpath(z)) for z in ziele}
        for verwaist in sorted(set(liste) - namen):
            print(
                f"WARNUNG install.sh: '{verwaist}' steht in der Liste, "
                "das Verzeichnis gibt es nicht"
            )
            warnungen_gesamt += 1

    print(
        f"\n{len(ziele)} Skills geprueft, "
        f"{fehler_gesamt} Fehler, {warnungen_gesamt} Warnungen"
    )

    return 1 if fehler_gesamt else 0


if __name__ == "__main__":
    sys.exit(main())
