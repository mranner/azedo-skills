#!/usr/bin/env python3

# Baut eine multipart/alternative-Mail (Text + HTML) und gibt die komplette
# DATA-Sektion (Header + Body) auf STDOUT aus. Die Ausgabe wird per
# `swaks --data @-` versendet. Bei Anhaengen wird zusaetzlich multipart/mixed
# um das alternative-Part gelegt.
# version 1.31.0

import argparse
import mimetypes
import os
import sys

from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


parser = argparse.ArgumentParser()
parser.add_argument("--subject", required=True)
parser.add_argument("--to", required=True)
parser.add_argument("--cc", help="Sichtbarer Cc:-Header (kommasepariert). Die Adressen zusaetzlich in den swaks-Envelope --to aufnehmen.")
parser.add_argument("--bcc", help="Bcc-Empfaenger (kommasepariert). Setzt bewusst KEINEN Header (sonst waeren die Empfaenger sichtbar) — die Adressen nur in den swaks-Envelope --to aufnehmen.")
parser.add_argument("--from", dest="sender", required=True)
parser.add_argument("--text-file", required=True)
parser.add_argument("--html-file", required=True)
parser.add_argument("--sig-text-file",
                    help="Text-Signatur. Ohne Angabe wird die Standard-Signatur "
                         "aufgeloest (projektlokal .claude/ vor global ~/.claude/).")
parser.add_argument("--sig-html-file",
                    help="HTML-Signatur. Ohne Angabe: Standard-Signatur (s. --sig-text-file).")
parser.add_argument("--no-sig", action="store_true",
                    help="Keine Signatur anhaengen (auch nicht die Standard-Signatur).")
parser.add_argument("--attach", action="append", default=[])
args = parser.parse_args()


def resolve_sig(name):
    """Standard-Signaturpfad aufloesen: projektlokal .claude/<name> (Vorrang) ->
    global ~/.claude/<name>. Liefert None, wenn keine der beiden existiert (dann
    wird schlicht keine Signatur angehaengt)."""
    for base in (os.path.join(os.getcwd(), ".claude"),
                 os.path.expanduser("~/.claude")):
        p = os.path.join(base, name)
        if os.path.isfile(p):
            return p
    return None


# Signaturpfade bestimmen: explizite Flags haben Vorrang, sonst Auto-Resolve;
# --no-sig schaltet komplett ab. Explizit angegebene Pfade muessen existieren
# (read() bricht sonst hart ab); auto-aufgeloeste sind per isfile() gesichert.
if args.no_sig:
    sig_text_file = sig_html_file = None
else:
    sig_text_file = args.sig_text_file or resolve_sig("swaks-signature.txt")
    sig_html_file = args.sig_html_file or resolve_sig("swaks-signature.html")

text = read(args.text_file)
html = read(args.html_file)

# Signaturen anhaengen (Text mit Leerzeile Abstand, HTML als Block)

if sig_text_file:
    text = text.rstrip("\n") + "\n\n" + read(sig_text_file)

if sig_html_file:
    html = html.rstrip() + "\n" + read(sig_html_file)

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
msg["From"] = args.sender
msg["To"] = args.to

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

msg["Date"] = formatdate(localtime=True)
msg["Message-ID"] = make_msgid(domain="azedo.at")

out = msg.as_string()

# Letzte Sicherung: niemals leere DATA ausgeben (sonst faellt swaks auf seine
# eingebaute Default-Test-Mail zurueck).

if not out.strip():
    sys.exit("build_mail.py: Fehler — leere Ausgabe. Abbruch, kein Versand.")

sys.stdout.write(out)
