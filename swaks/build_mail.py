#!/usr/bin/env python3

# Baut eine multipart/alternative-Mail (Text + HTML) und gibt die komplette
# DATA-Sektion (Header + Body) auf STDOUT aus. Die Ausgabe wird per
# `swaks --data @-` versendet. Bei Anhaengen wird zusaetzlich multipart/mixed
# um das alternative-Part gelegt. Bei einer Antwort kommt der Zitatblock aus
# `imap quote` unter Body und Signatur (Top-Posting), die Threading-Header
# In-Reply-To und References haengen die Antwort an den bestehenden Thread.
# version 1.40.0

import argparse
import json
import mimetypes
import os
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


config = load_config()

# --show-config wird vor argparse abgefangen, damit die Abfrage ohne die sonst
# noetigen Pflichtargumente (--subject, --text-file, ...) funktioniert.

if "--show-config" in sys.argv[1:]:
    print(json.dumps(config, indent=2, ensure_ascii=False))
    sys.exit(0)

parser = argparse.ArgumentParser()
parser.add_argument("--show-config", action="store_true",
                    help="Aufgeloeste Versand-Defaults aus swaks.json ausgeben und beenden.")
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
