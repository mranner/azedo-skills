#!/usr/bin/env python3

# Baut eine multipart/alternative-Mail (Text + HTML) und gibt die komplette
# DATA-Sektion (Header + Body) auf STDOUT aus. Die Ausgabe wird per
# `swaks --data @-` versendet. Bei Anhaengen wird zusaetzlich multipart/mixed
# um das alternative-Part gelegt. Bei einer Antwort kommt der Zitatblock aus
# `imap quote` unter Body und Signatur (Top-Posting), die Threading-Header
# In-Reply-To und References haengen die Antwort an den bestehenden Thread.
# version 1.52.0

import argparse
import hashlib
import json
import mimetypes
import os
import re
import subprocess
import sys

from html import escape as html_escape

from email import encoders
from email import policy
from email.parser import BytesParser
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def resolve_claude_file(name):
    """Datei in .claude/ aufloesen: projektlokal (Vorrang) -> global ~/.claude/.
    Liefert None, wenn keine der beiden existiert."""
    for base in (os.path.join(os.getcwd(), ".claude"),
                 os.path.expanduser("~/.claude")):
        p = os.path.join(base, name)
        if os.path.isfile(p):
            return p
    return None


def load_config():
    """Versand-Defaults aus swaks.json lesen (to, from, server,
    message_id_domain). Fehlt die Datei, gilt ein leerer Satz — dann muessen
    --to und --from auf der Kommandozeile stehen."""
    path = resolve_claude_file("swaks.json")

    if not path:
        return {}

    try:
        with open(path, encoding="utf-8") as f:
            cfg = json.load(f)
    except (OSError, ValueError) as exc:
        sys.exit(f"build_mail.py: Fehler — {path} nicht lesbar: {exc}")

    if not isinstance(cfg, dict):
        sys.exit(f"build_mail.py: Fehler — {path} enthaelt kein JSON-Objekt.")

    return cfg


# --- Versandweg (Submission mit Auth) ----------------------------------------

# Der Versand selbst laeuft ueber swaks, nicht hier. Diese Funktionen loesen
# nur auf, WOHIN und MIT WELCHER Anmeldung gesendet wird, und geben das als
# SWAKS_OPT_*-Umgebungsvariablen aus (--swaks-env). Das Passwort steht damit
# in der Umgebung des swaks-Prozesses und nicht in dessen Kommandozeile, wo
# jedes `ps` es mitlesen wuerde.
#
# Quelle der Zugangsdaten ist die muttrc — dieselbe Datei, aus der schon der
# imap-Skill liest. Es gibt bewusst keine zweite Credential-Datei.
#
#   set smtp_url  = "smtp://<user>@mail.example.at:587/"
#   set smtp_pass = "..."
#
# Fehlt die muttrc oder steht dort kein smtp_url, bleibt es beim bisherigen
# Verhalten: 'server' aus swaks.json, Port 25, ohne Auth und ohne TLS. Das
# traegt, solange die Quell-IP im Relay privilegiert ist (mynetworks) — von
# einer dynamischen Leitung aus dagegen weist der Relay externe Empfaenger mit
# "454 4.7.1 Relay access denied" ab.

DEFAULT_MUTTRC = os.path.expanduser("~/.muttrc")

MUTT_KEYS = {"smtp_url", "smtp_pass", "imap_pass", "folder"}

MUTT_SET_RE = re.compile(
    r'\b([a-z_]+)\s*=\s*("([^"]*)"|\'([^\']*)\'|`([^`]*)`|(\S+))')

MUTT_HOOK_RE = re.compile(
    r'^\s*account-hook\s+(?P<url>\S+)\s+(?P<quote>[\'"])(?P<body>.*)(?P=quote)\s*$')

MUTT_SOURCE_RE = re.compile(
    r'^\s*source\s+(?P<quote>[\'"]?)(?P<path>.*?)(?P=quote)\s*$')

SMTP_URL_RE = re.compile(
    r'^(?P<scheme>smtps?)://'
    r'(?:(?P<user>[^:@/]+)(?::(?P<password>[^@/]*))?@)?'
    r'(?P<host>[^:/]+)(?::(?P<port>\d+))?')

IMAP_HOST_RE = re.compile(r'imaps?://(?:[^@/]+@)?(?P<host>[^:/]+)')


def mutt_backtick(cmd):
    """Backtick-Substitution wie mutt sie macht — erlaubt einen Keystore
    (`smtp_pass=\\`pass show mail/azedo\\``) statt Klartext in der muttrc."""
    try:
        out = subprocess.run(cmd, shell=True, capture_output=True,
                             text=True, timeout=30)
    except subprocess.TimeoutExpired:
        sys.exit(f"build_mail.py: Fehler — Backtick-Befehl lief in einen Timeout: {cmd}")

    if out.returncode != 0:
        sys.exit(f"build_mail.py: Fehler — Backtick-Befehl fehlgeschlagen "
                 f"({out.returncode}): {cmd}")

    return out.stdout.strip()


def mutt_set_values(text):
    """Alle key=value aus einem set- oder account-hook-Stueck ziehen. Die
    Whitelist verhindert Treffer aus Makros und Formatstrings."""
    values = {}

    for m in MUTT_SET_RE.finditer(text):
        key = m.group(1)

        if key not in MUTT_KEYS:
            continue

        if m.group(3) is not None:
            values[key] = m.group(3)
        elif m.group(4) is not None:
            values[key] = m.group(4)
        elif m.group(5) is not None:
            values[key] = mutt_backtick(m.group(5))
        else:
            values[key] = m.group(6)

    return values


def parse_muttrc(path, _seen=None):
    """muttrc lesen und (globale Werte, imap_pass je Host) liefern. Ausgewertet
    wird nur eine Teilmenge der muttrc-Syntax: set, account-hook, source und
    Backticks. Fehlt die Datei, ist das kein Fehler — dann gilt der Fallback."""
    _seen = set() if _seen is None else _seen
    real = os.path.realpath(path)

    if real in _seen or not os.path.isfile(path):
        return {}, {}

    _seen.add(real)

    globals_ = {}
    per_host = {}

    with open(path, encoding="utf-8", errors="replace") as f:
        for raw in f:
            line = raw.rstrip("\n")
            stripped = line.strip()

            if not stripped or stripped.startswith("#"):
                continue

            m = MUTT_SOURCE_RE.match(line)

            if m and "account-hook" not in line:
                sub = m.group("path")

                # source "cmd |" fuehrt einen Befehl aus statt eine Datei zu lesen

                if sub.endswith("|"):
                    globals_.update(mutt_set_values(mutt_backtick(sub[:-1].strip())))
                    continue

                sub_path = os.path.expanduser(sub)

                if not os.path.isabs(sub_path):
                    sub_path = os.path.join(os.path.dirname(path), sub_path)

                sub_glob, sub_host = parse_muttrc(sub_path, _seen)
                globals_.update(sub_glob)
                per_host.update(sub_host)
                continue

            m = MUTT_HOOK_RE.match(line)

            if m:
                host = IMAP_HOST_RE.search(m.group("url"))
                vals = mutt_set_values(m.group("body"))

                if host and vals.get("imap_pass"):
                    per_host[host.group("host")] = vals["imap_pass"]

                continue

            if re.match(r"^\s*set\s", line):
                globals_.update(mutt_set_values(line))

    return globals_, per_host


def resolve_route(cfg, muttrc_path=DEFAULT_MUTTRC):
    """Versandweg bestimmen: Submission mit Auth aus der muttrc, sonst der
    bisherige Weg ueber 'server' aus swaks.json ohne Auth."""
    globals_, per_host = parse_muttrc(muttrc_path)
    url = globals_.get("smtp_url")

    if not url:
        server = cfg.get("server")

        if not server:
            sys.exit("build_mail.py: Fehler — kein Versandweg. Entweder "
                     "'server' in .claude/swaks.json setzen oder 'set smtp_url' "
                     f"in {muttrc_path} hinterlegen.")

        return {"server": server, "port": 25, "tls": None,
                "auth_user": None, "auth_password": None, "source": "swaks.json"}

    m = SMTP_URL_RE.match(url)

    if not m:
        sys.exit(f"build_mail.py: Fehler — smtp_url in {muttrc_path} nicht "
                 f"lesbar: {url}")

    host = m.group("host")
    port = int(m.group("port")) if m.group("port") else (
        465 if m.group("scheme") == "smtps" else 587)

    # smtps = implizites TLS ab dem ersten Byte (--tls-on-connect),
    # smtp = STARTTLS. Beides ist Pflicht, sobald ein Passwort mitgeht.

    tls = "wrapper" if m.group("scheme") == "smtps" else "starttls"

    user = m.group("user")

    # Passwort: erst smtp_pass, sonst das imap_pass desselben Hosts. Beide sind
    # in der Praxis dasselbe Konto — der Fallback erspart eine zweite Kopie.

    password = m.group("password") or globals_.get("smtp_pass") or per_host.get(host)

    if user and not password:
        sys.exit(f"build_mail.py: Fehler — smtp_url in {muttrc_path} nennt den "
                 f"Benutzer '{user}', aber es findet sich kein Passwort "
                 f"(weder 'set smtp_pass' noch imap_pass fuer {host}). Abbruch "
                 "statt unauthentifiziert zu senden — externe Empfaenger wuerden "
                 "sonst mit 'Relay access denied' abgewiesen.")

    return {"server": host, "port": port, "tls": tls,
            "auth_user": user, "auth_password": password, "source": muttrc_path}


def route_env_vars(route):
    """Versandweg als SWAKS_OPT_*-Variablen. Ein leerer Wert entspricht bei
    swaks der Option ohne Argument (z.B. -tls)."""
    env = {"server": route["server"], "port": str(route["port"])}

    if route["tls"] == "starttls":
        env["tls"] = ""
    elif route["tls"] == "wrapper":
        env["tls_on_connect"] = ""

    if route["auth_user"]:
        env["auth"] = ""
        env["auth_user"] = route["auth_user"]
        env["auth_password"] = route["auth_password"]

    return {"SWAKS_OPT_" + k: v for k, v in env.items()}


def route_env(route):
    """Dieselben Variablen als Exportzeilen fuer `eval` in einer Shell."""
    return "\n".join(
        "export %s='%s'" % (k, v.replace("'", "'\\''"))
        for k, v in route_env_vars(route).items())


# --- Versand ------------------------------------------------------------------

# swaks steht in der vorgeschriebenen Aufrufform nie am Befehlsanfang (der
# Versandweg muss vorher per `eval` in die Shell), weshalb keine Bash-Freigabe
# darauf greifen kann. --send holt den Aufruf deshalb hierher: der Versandweg
# geht als Umgebung an den Kindprozess statt ueber stdout durch die Shell, und
# die drei Erfolgspruefungen stehen nicht mehr als kopierte Kette in jeder
# Session.

# swaks markiert jede abgelehnte Antwort mit einem '*' an dritter Stelle des
# Zeilenpraefixes - unverschluesselt '<**', innerhalb einer TLS-Sitzung '<~*'.
# Bei mehreren Empfaengern ist das der einzige Hinweis auf einen einzelnen
# Reject: swaks laeuft fuer die uebrigen weiter und endet mit Exit-Code 0.

SWAKS_REJECT_RE = re.compile(r"^<.\*", re.M)

QUEUED_RE = re.compile(r"^.*queued as.*$", re.M)


def send_eml(path, recipient, sender):
    """Fertige .eml versenden und das Ergebnis pruefen. Liefert (report, fehler)."""
    if not os.path.isfile(path):
        return {"file": path}, [f"{path} existiert nicht."]

    if os.path.getsize(path) == 0:
        return {"file": path}, [f"{path} ist leer — nichts zu senden."]

    route = resolve_route(config)

    env = dict(os.environ)
    env.update(route_env_vars(route))

    log_path = path + ".swaks.log"

    try:
        proc = subprocess.run(
            ["swaks", "--to", recipient, "--from", sender, "--data", "@" + path],
            env=env, capture_output=True, text=True)
    except FileNotFoundError:
        return ({"file": path},
                ["swaks ist nicht installiert oder nicht im PATH."])

    log = proc.stdout + proc.stderr

    with open(log_path, "w", encoding="utf-8") as f:
        f.write(log)

    report = {"file": path, "to": recipient, "from": sender,
              "server": route["server"], "port": route["port"],
              "exit_code": proc.returncode, "log": log_path}

    errors = []

    # Alle drei Pruefungen, nicht eine davon: der Exit-Code faengt Verbindungs-,
    # TLS- und Totalablehnungen, die Queue-ID das vergessene '@' bei --data
    # (swaks quittiert dann mit 250 Ok und verschickt den Pfad als Body), und
    # die Reject-Zeile den einzelnen abgelehnten Empfaenger.

    if proc.returncode != 0:
        errors.append(f"swaks endete mit Exit-Code {proc.returncode}.")

    queued = QUEUED_RE.findall(log)
    report["queued_as"] = [q.strip() for q in queued]

    if not queued:
        errors.append("Keine 'queued as'-Zeile — der Relay hat die Mail nicht "
                      "in die Queue genommen.")

    rejected = [l for l in log.splitlines() if SWAKS_REJECT_RE.match(l)]

    if rejected:
        report["rejected"] = rejected
        errors.append("Abgelehnte Antwort(en) des Relays: "
                      + " | ".join(rejected))

    return report, errors

# --- Darstellungspruefung: HTML-Part und fertige .eml -------------------------

# Zwei Fehlerklassen, die der Versand selbst nicht bemerkt, weil swaks nur die
# uebertragenen Bytes quittiert:
#
#   1. Der HTML-Part enthaelt rohen Text ohne ein einziges Tag — jeder Client
#      rendert die Mail dann als einen einzigen Absatz. Entsteht, sobald
#      --text-file und --html-file auf dieselbe Datei zeigen.
#   2. Die .eml wurde zwischen Bauen und Senden ueberschrieben (parallele
#      Session, gleicher Pfad). Der Versand ist fehlerfrei, der Inhalt falsch.
#
# Fall 1 faengt html_has_markup() beim Bauen ab, Fall 2 der --verify-Modus
# unmittelbar vor dem swaks-Aufruf.

MARKUP_RE = re.compile(r"<\s*(p|br|div|table|tr|td|ul|ol|li|h[1-6]|blockquote|a|"
                       r"strong|em|b|i|pre|span|img|hr)\b[^>]*>", re.I)


def html_has_markup(html):
    """True, wenn im HTML wenigstens ein darstellungsrelevantes Tag steht.
    Ein HTML-Part ohne jedes Markup ist praktisch immer ein Versehen."""
    return bool(MARKUP_RE.search(html))


def text_to_html(text):
    """Text in Absaetze umwandeln — der freundliche Weg fuer 'ich habe nur
    Text': Leerzeilen trennen <p>, einfache Umbrueche werden zu <br>."""
    blocks = re.split(r"\n\s*\n", text.strip("\n"))
    out = []

    for block in blocks:
        lines = [html_escape(l.rstrip()) for l in block.split("\n") if l.strip()]

        if lines:
            out.append("<p>" + "<br>\n".join(lines) + "</p>")

    return "\n".join(out) + "\n" if out else ""


def sha256_file(path):
    h = hashlib.sha256()

    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)

    return h.hexdigest()


def normalize(s):
    """Fuer den Marker-Vergleich: Zeilenumbrueche und Mehrfach-Leerzeichen
    einebnen. quoted-printable bricht Zeilen an anderer Stelle als der
    Entwurf, ein roher Vergleich schluege deshalb falsch fehl."""
    return re.sub(r"\s+", " ", s).strip()


def verify_eml(path, expect_sha256=None, expect_marker=None):
    """Die fertige .eml pruefen, bevor sie an swaks geht. Liefert (report, fehler)."""
    errors = []

    if not os.path.isfile(path):
        return {"file": path}, [f"{path} existiert nicht."]

    size = os.path.getsize(path)
    digest = sha256_file(path)

    report = {"file": path, "bytes": size, "sha256": digest}

    if size == 0:
        return report, [f"{path} ist leer."]

    if expect_sha256 and digest != expect_sha256:
        errors.append(
            f"Pruefsumme weicht ab: erwartet {expect_sha256}, gefunden {digest}. "
            "Die Datei wurde zwischen Bauen und Senden veraendert — sehr "
            "wahrscheinlich von einer parallel laufenden Session, die denselben "
            "Pfad benutzt. Abbruch statt fremden Inhalt zu versenden.")

    with open(path, "rb") as f:
        msg = BytesParser(policy=policy.default).parse(f)

    report["subject"] = msg.get("Subject")
    report["from"] = msg.get("From")
    report["to"] = msg.get("To")

    tpart = msg.get_body(preferencelist=("plain",))
    hpart = msg.get_body(preferencelist=("html",))

    text = tpart.get_content() if tpart else ""
    html = hpart.get_content() if hpart else ""

    report["text_chars"] = len(text)
    report["html_chars"] = len(html)

    if not text.strip():
        errors.append("Kein oder leerer Text-Part.")

    if not html.strip():
        errors.append("Kein oder leerer HTML-Part.")
    else:
        if not html_has_markup(html):
            errors.append(
                "Der HTML-Part enthaelt kein einziges Tag — er wuerde beim "
                "Empfaenger als ein einziger Absatz ankommen.")

        if normalize(text)[:200] and normalize(text)[:200] == normalize(html)[:200]:
            errors.append(
                "Text- und HTML-Part sind identisch — vermutlich zeigen "
                "--text-file und --html-file auf dieselbe Datei.")

    if expect_marker:
        marker = normalize(expect_marker)

        if marker and marker not in normalize(text):
            errors.append(
                f"Marker nicht im Text-Part gefunden: {expect_marker!r}. Die "
                ".eml enthaelt nicht den freigegebenen Entwurf. (Ein grep auf "
                "die rohe .eml genuegt hier nicht — der Body ist "
                "quoted-printable kodiert.)")

        report["marker_ok"] = not any("Marker nicht" in e for e in errors)

    return report, errors


config = load_config()

# --show-config wird vor argparse abgefangen, damit die Abfrage ohne die sonst
# noetigen Pflichtargumente (--subject, --text-file, ...) funktioniert.

if "--verify" in sys.argv[1:]:
    vp = argparse.ArgumentParser(prog="build_mail.py --verify")
    vp.add_argument("--verify", metavar="EML", required=True,
                    help="Fertige .eml pruefen und beenden: Pruefsumme, "
                         "Text-/HTML-Part, Markup, optional ein Marker aus dem "
                         "freigegebenen Entwurf. Exit != 0 bei jedem Befund.")
    vp.add_argument("--expect-sha256",
                    help="sha256 der .eml direkt nach dem Bauen. Weicht sie ab, "
                         "hat jemand die Datei zwischenzeitlich ueberschrieben.")
    vp.add_argument("--expect-marker",
                    help="Woertliches Textstueck aus dem freigegebenen Entwurf. "
                         "Muss im dekodierten Text-Part stehen.")
    vargs, _ = vp.parse_known_args()

    report, errors = verify_eml(vargs.verify, vargs.expect_sha256,
                                vargs.expect_marker)
    report["ok"] = not errors
    report["errors"] = errors

    print(json.dumps(report, indent=2, ensure_ascii=False))

    if errors:
        for e in errors:
            print(f"build_mail.py: Fehler — {e}", file=sys.stderr)

        sys.exit(1)

    sys.exit(0)

if "--send" in sys.argv[1:]:
    sp = argparse.ArgumentParser(prog="build_mail.py --send")
    sp.add_argument("--send", metavar="EML", required=True,
                    help="Fertige .eml versenden und beenden: Versandweg laden, "
                         "swaks aufrufen, Ergebnis pruefen (Exit-Code, "
                         "Queue-ID, abgelehnte Empfaenger). Exit != 0 bei "
                         "jedem Befund.")
    sp.add_argument("--to", help="Envelope-Empfaenger (kommasepariert, inkl. Cc "
                                 "und Bcc). Ohne Angabe gilt 'to' aus swaks.json.")
    sp.add_argument("--from", dest="sender",
                    help="Envelope-Absender. Ohne Angabe gilt 'from' aus swaks.json.")
    sargs, _ = sp.parse_known_args()

    to = sargs.to or config.get("to")
    frm = sargs.sender or config.get("from")

    if not to:
        sys.exit("build_mail.py: Fehler — kein Empfaenger. Entweder --to angeben "
                 "oder 'to' in .claude/swaks.json (projektlokal oder ~/) setzen.")

    if not frm:
        sys.exit("build_mail.py: Fehler — kein Absender. Entweder --from angeben "
                 "oder 'from' in .claude/swaks.json (projektlokal oder ~/) setzen.")

    report, errors = send_eml(sargs.send, to, frm)
    report["ok"] = not errors
    report["errors"] = errors

    print(json.dumps(report, indent=2, ensure_ascii=False))

    if errors:
        for e in errors:
            print(f"build_mail.py: Fehler — {e}", file=sys.stderr)

        sys.exit(1)

    sys.exit(0)

if "--swaks-env" in sys.argv[1:]:
    print(route_env(resolve_route(config)))
    sys.exit(0)

if "--show-config" in sys.argv[1:]:
    route = resolve_route(config)

    # Passwort nie ausgeben — die Anzeige dient der Kontrolle des Weges,
    # nicht der Weitergabe der Zugangsdaten.

    shown = dict(route)
    shown["auth_password"] = "<gesetzt>" if route["auth_password"] else None

    print(json.dumps({"config": config, "route": shown},
                     indent=2, ensure_ascii=False))
    sys.exit(0)

parser = argparse.ArgumentParser()
parser.add_argument("--show-config", action="store_true",
                    help="Aufgeloeste Versand-Defaults aus swaks.json und den "
                         "ermittelten Versandweg ausgeben und beenden "
                         "(Passwort maskiert).")
parser.add_argument("--verify", metavar="EML",
                    help="Fertige .eml unmittelbar vor dem Versand pruefen und "
                         "beenden (Pruefsumme, Text-/HTML-Part, Markup, Marker). "
                         "Siehe --expect-sha256 und --expect-marker.")
parser.add_argument("--expect-sha256",
                    help="Nur mit --verify: erwartete sha256 der .eml.")
parser.add_argument("--expect-marker",
                    help="Nur mit --verify: Textstueck aus dem freigegebenen Entwurf.")
parser.add_argument("--send", metavar="EML",
                    help="Fertige .eml versenden und beenden: Versandweg laden, "
                         "swaks aufrufen und das Ergebnis pruefen (Exit-Code, "
                         "Queue-ID, abgelehnte Empfaenger). Envelope ueber --to "
                         "und --from. Das Passwort verlaesst dabei den Prozess "
                         "nicht — anders als bei --swaks-env.")
parser.add_argument("--swaks-env", action="store_true",
                    help="Versandweg als SWAKS_OPT_*-Exportzeilen ausgeben und "
                         "beenden. Per eval in die Shell holen, dann braucht "
                         "swaks weder --server noch Auth-Optionen.")
parser.add_argument("--subject", required=True)
parser.add_argument("--to", help="Empfaenger. Ohne Angabe gilt 'to' aus swaks.json.")
parser.add_argument("--cc", help="Sichtbarer Cc:-Header (kommasepariert). Die Adressen zusaetzlich in den swaks-Envelope --to aufnehmen.")
parser.add_argument("--bcc", help="Bcc-Empfaenger (kommasepariert). Setzt bewusst KEINEN Header (sonst waeren die Empfaenger sichtbar) — die Adressen nur in den swaks-Envelope --to aufnehmen.")
parser.add_argument("--from", dest="sender",
                    help="Absender. Ohne Angabe gilt 'from' aus swaks.json.")
parser.add_argument("--text-file", required=True)
parser.add_argument("--html-file",
                    help="HTML-Body. Ohne Angabe wird er aus --text-file "
                         "erzeugt (Absaetze). Auf --text-file zeigen lassen "
                         "darf man ihn nicht: der Part haette dann kein Markup "
                         "und kaeme als eine einzige Zeile an.")
parser.add_argument("--sig-text-file",
                    help="Text-Signatur. Ohne Angabe wird die Standard-Signatur "
                         "aufgeloest (projektlokal .claude/ vor global ~/.claude/).")
parser.add_argument("--sig-html-file",
                    help="HTML-Signatur. Ohne Angabe: Standard-Signatur (s. --sig-text-file).")
parser.add_argument("--no-sig", action="store_true",
                    help="Keine Signatur anhaengen (auch nicht die Standard-Signatur).")
parser.add_argument("--quote-text-file",
                    help="Zitatblock (Text) aus `imap quote`. Wird UNTER Body und "
                         "Signatur angehaengt (Top-Posting).")
parser.add_argument("--quote-html-file",
                    help="Zitatblock (HTML) aus `imap quote --format html`. Ohne "
                         "Angabe wird der Text-Quote escaped nachgebaut.")
parser.add_argument("--in-reply-to",
                    help="Message-ID der Mail, auf die geantwortet wird "
                         "(Feld reply.in_reply_to aus `imap quote --json`).")
parser.add_argument("--references",
                    help="References-Kette der Antwort "
                         "(Feld reply.references aus `imap quote --json`).")
parser.add_argument("--sha-file",
                    help="sha256 der gebauten DATA zusaetzlich in diese Datei "
                         "schreiben. Der Wert geht danach an "
                         "`--verify --expect-sha256`, unmittelbar vor dem "
                         "swaks-Aufruf.")
parser.add_argument("--attach", action="append", default=[])
args = parser.parse_args()

# Empfaenger und Absender: Kommandozeile hat Vorrang, sonst swaks.json.

recipient = args.to or config.get("to")
sender = args.sender or config.get("from")

if not recipient:
    sys.exit("build_mail.py: Fehler — kein Empfaenger. Entweder --to angeben "
             "oder 'to' in .claude/swaks.json (projektlokal oder ~/) setzen.")

if not sender:
    sys.exit("build_mail.py: Fehler — kein Absender. Entweder --from angeben "
             "oder 'from' in .claude/swaks.json (projektlokal oder ~/) setzen.")


# Signaturpfade bestimmen: explizite Flags haben Vorrang, sonst Auto-Resolve;
# --no-sig schaltet komplett ab. Explizit angegebene Pfade muessen existieren
# (read() bricht sonst hart ab); auto-aufgeloeste sind per isfile() gesichert.
if args.no_sig:
    sig_text_file = sig_html_file = None
else:
    sig_text_file = args.sig_text_file or resolve_claude_file("swaks-signature.txt")
    sig_html_file = args.sig_html_file or resolve_claude_file("swaks-signature.html")

text = read(args.text_file)

# HTML-Part: fehlt er, wird er aus dem Text gebaut. Kommt er als Datei, aber
# ohne jedes Tag (haeufigster Fall: --text-file und --html-file zeigen auf
# denselben Pfad), wird er ebenfalls umgewandelt — roh durchgereicht kaeme die
# Mail beim Empfaenger als ein einziger Absatz an, ohne dass beim Versand
# irgendetwas auffaellt.

if not args.html_file:
    html = text_to_html(text)
else:
    html = read(args.html_file)

    same_path = os.path.realpath(args.html_file) == os.path.realpath(args.text_file)

    if same_path or not html_has_markup(html):
        reason = ("zeigt auf dieselbe Datei wie --text-file" if same_path
                  else "enthaelt kein einziges Tag")

        print(f"build_mail.py: Warnung — --html-file {reason}; der Part wird "
              "in Absaetze umgewandelt. Ohne das kaeme die Mail beim "
              "Empfaenger in einer einzigen Zeile an.", file=sys.stderr)

        html = text_to_html(html if not same_path else text)

# Signaturen anhaengen (Text mit Leerzeile Abstand, HTML als Block)

if sig_text_file:
    text = text.rstrip("\n") + "\n\n" + read(sig_text_file)

if sig_html_file:
    html = html.rstrip() + "\n" + read(sig_html_file)

# Zitatblock anhaengen — UNTER Body und Signatur (Top-Posting, so entschieden).
# Er kommt fertig formatiert aus `imap quote` und wird hier nicht mehr angefasst:
# Praefixe, Umbruch und Attributionszeile sind dort deterministisch erzeugt.

quote_text = read(args.quote_text_file) if args.quote_text_file else ""
quote_html = read(args.quote_html_file) if args.quote_html_file else ""

# Eine angegebene, aber leere Quote-Datei ist ein Fehler, kein "kein Zitat":
# sie entsteht, wenn `imap quote` fehlschlaegt (falsche UID, Mail inzwischen
# verschoben) und die Ausgabe trotzdem umgeleitet wurde. Ohne diese Pruefung
# ginge die Antwort still ohne Zitat raus — genau der Fall, den der Aufruf
# von `imap quote` verhindern soll.

for flag, path, content in (
    ("--quote-text-file", args.quote_text_file, quote_text),
    ("--quote-html-file", args.quote_html_file, quote_html),
):
    if path and not content.strip():
        sys.exit(f"build_mail.py: Fehler — {flag} ist leer. `imap quote` duerfte "
                 f"fehlgeschlagen sein (falsche UID oder falscher Ordner); die "
                 f"Antwort ginge sonst ohne Zitat raus.")

if quote_text or quote_html:

    # Fehlt eine der beiden Fassungen, wird sie aus der anderen gebaut. Sonst
    # haette ein Part das Zitat und der andere nicht — je nachdem, welchen der
    # Client anzeigt, fehlte dem Empfaenger der Bezug.

    if not quote_text and quote_html:
        sys.exit("build_mail.py: Fehler — --quote-html-file ohne --quote-text-file. "
                 "Den Text-Quote mit `imap quote <uid>` erzeugen; ohne ihn bliebe "
                 "der Text-Part der Mail ohne Zitat.")

    if not quote_html:
        quote_html = ("<blockquote type=\"cite\">\n"
                      + "<br>\n".join(html_escape(l) for l in quote_text.split("\n"))
                      + "\n</blockquote>")

    text = text.rstrip("\n") + "\n\n" + quote_text.rstrip("\n") + "\n"
    html = html.rstrip() + "\n" + quote_html.rstrip() + "\n"

# Hart abbrechen bei leerem Body: sonst wuerde swaks eine inhaltslose Mail
# senden bzw. bei komplett leerer Ausgabe auf seine Default-Test-Mail zurueckfallen.

if not text.strip() and not html.strip():
    sys.exit("build_mail.py: Fehler — leerer Body (Text und HTML leer). Abbruch, kein Versand.")

alt = MIMEMultipart("alternative")
alt.attach(MIMEText(text, "plain", "utf-8"))
alt.attach(MIMEText(html, "html", "utf-8"))

if args.attach:
    msg = MIMEMultipart("mixed")
    msg.attach(alt)

    for path in args.attach:
        ctype, enc = mimetypes.guess_type(path)
        if ctype is None or enc is not None:
            ctype = "application/octet-stream"
        maintype, subtype = ctype.split("/", 1)

        with open(path, "rb") as f:
            part = MIMEBase(maintype, subtype)
            part.set_payload(f.read())

        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition", "attachment", filename=os.path.basename(path)
        )
        msg.attach(part)
else:
    msg = alt

msg["Subject"] = args.subject
msg["From"] = sender
msg["To"] = recipient

if args.cc:
    msg["Cc"] = args.cc

# Bcc bewusst NICHT als Header setzen (wuerde die Empfaenger sichtbar machen).
# Zustellung erfolgt ausschliesslich ueber den swaks-Envelope (--to).

if args.bcc:
    print(
        "build_mail.py: Hinweis — Bcc-Adressen erscheinen bewusst NICHT im Header; "
        "sie muessen im swaks-Envelope (--to) stehen, damit sie zugestellt werden.",
        file=sys.stderr,
    )

# Threading: ohne diese beiden Header startet die Antwort im Client des
# Empfaengers einen neuen Thread, statt am bestehenden zu haengen
# (RFC 5322 3.6.4). Die Werte liefert `imap quote --json` im Feld `reply`.

if args.in_reply_to:
    msg["In-Reply-To"] = args.in_reply_to

if args.references:
    msg["References"] = args.references

msg["Date"] = formatdate(localtime=True)

# Message-ID-Domain: aus swaks.json, sonst die Domain des Absenders. Ohne
# beides entscheidet make_msgid selbst (FQDN des Hosts).

msgid_domain = config.get("message_id_domain") or sender.rpartition("@")[2].strip("> ")
msg["Message-ID"] = make_msgid(domain=msgid_domain) if msgid_domain else make_msgid()

out = msg.as_string()

# Letzte Sicherung: niemals leere DATA ausgeben (sonst faellt swaks auf seine
# eingebaute Default-Test-Mail zurueck).

if not out.strip():
    sys.exit("build_mail.py: Fehler — leere Ausgabe. Abbruch, kein Versand.")

# Bytes explizit schreiben, damit die Pruefsumme unten ueber genau das
# laeuft, was in der Datei landet — unabhaengig vom Locale der Umgebung.

data = out.encode("utf-8")
sys.stdout.buffer.write(data)

# Pruefsumme der gebauten DATA auf stderr. Sie ist der Wert fuer
# `--verify --expect-sha256` unmittelbar vor dem swaks-Aufruf und gehoert in
# die Erfolgsmeldung an den Nutzer: "versendet" allein stuetzt sich sonst auf
# den Rueckgabewert von swaks, der nur die uebertragenen Bytes quittiert.

digest = hashlib.sha256(data).hexdigest()

print("build_mail.py: sha256(DATA) = %s (%d Byte)" % (digest, len(data)),
      file=sys.stderr)

if args.sha_file:
    with open(args.sha_file, "w", encoding="utf-8") as f:
        f.write(digest + "\n")
