#!/usr/bin/env python3

# Baut eine multipart/alternative-Mail (Text + HTML) und gibt die komplette
# DATA-Sektion (Header + Body) auf STDOUT aus. Die Ausgabe wird per
# `swaks --data @-` versendet. Bei Anhaengen wird zusaetzlich multipart/mixed
# um das alternative-Part gelegt. Bei einer Antwort kommt der Zitatblock aus
# `imap quote` unter Body und Signatur (Top-Posting), die Threading-Header
# In-Reply-To und References haengen die Antwort an den bestehenden Thread.
# version 1.42.2

import argparse
import json
import mimetypes
import os
import re
import subprocess
import sys

from html import escape as html_escape

from email import encoders
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
#   set smtp_url  = "smtp://mranner@mail.azedo.at:587/"
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


def route_env(route):
    """Versandweg als SWAKS_OPT_*-Exportzeilen. Ein leerer Wert entspricht bei
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

    return "\n".join(
        "export SWAKS_OPT_%s='%s'" % (k, v.replace("'", "'\\''"))
        for k, v in env.items())

config = load_config()

# --show-config wird vor argparse abgefangen, damit die Abfrage ohne die sonst
# noetigen Pflichtargumente (--subject, --text-file, ...) funktioniert.

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
parser.add_argument("--html-file", required=True)
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
html = read(args.html_file)

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

sys.stdout.write(out)
