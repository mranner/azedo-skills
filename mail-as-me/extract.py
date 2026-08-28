#!/usr/bin/env python3
"""mail-as-me: Extraktor.

Liest Mail-Samples (.eml, .mbox, Maildir/Cyrus-Ordner) und schreibt pro Mail den
bereinigten Eigentext als Markdown mit Frontmatter nach <out>/clean/<id>.md.

Bereinigung: erster text/plain-Part, Zitat (>, 'Am ... schrieb:') und Signatur
(ab '-- ') entfernt, format=flowed weich, Anhaenge ignoriert. Register- und
Dialekt-Vorschlag pro Mail (der setup-Interview bestaetigt/korrigiert).

Nutzung:
  extract.py --input <datei|ordner> --out <profil>/corpus [--config <config.json>]
  extract.py --analyze <datei>        # nur anzeigen, nichts schreiben
"""

# version 1.29.0

import argparse
import email
import email.policy
import json
import mailbox
import re
from email.header import decode_header, make_header
from pathlib import Path

QUOTE_INTRO = re.compile(
    r"(schrieb\s+.*:|wrote:|hat\s+.*geschrieben:|"
    r"^Am\s.+\sum\s.+:$|^Gesendet:|^Von:|^-----\s*Urspr)", re.I)

# Dialekt-Marker mit WORTGRENZEN (\b) — sonst matcht 'eh' in 'geehrter' u.ae.
AT_MARKERS = [r"\beh\b", r"\bohnehin\b", r"\bheuer\b", r"\bJänner\b",
              r"\ballfällig\w*", r"schlimmsten Fall", r"sich \w*aus(?:zu)?geh",
              r"\bpasst\b", r"passen würde", r"doch einfach"]


def hdr(msg, name):
    v = msg.get(name, "")
    try:
        return str(make_header(decode_header(v)))
    except Exception:
        return v


def first_domain(*headers):
    for h in headers:
        m = re.search(r"[\w.+-]+@([\w.-]+)", h or "")
        if m:
            return m.group(1).lower()
    return ""


def get_plain(msg):
    """Erster text/plain-Part, der KEIN Anhang ist."""
    for part in msg.walk():
        if part.get_content_type() != "text/plain":
            continue
        if part.get_content_disposition() == "attachment":
            continue
        try:
            return part.get_content()
        except Exception:
            payload = part.get_payload(decode=True) or b""
            cs = part.get_content_charset() or "utf-8"
            return payload.decode(cs, errors="replace")
    return ""


def deflow(text):
    """format=flowed entfalten: Zeilen mit Trailing-Space sind Soft-Umbrueche
    (Fortsetzung), das Space bleibt erhalten, der Umbruch faellt weg."""
    out, buf = [], ""
    for ln in text.split("\n"):
        if ln.endswith(" ") and ln.strip() != "":
            buf += ln
        else:
            out.append(buf + ln)
            buf = ""
    if buf:
        out.append(buf)
    return "\n".join(out)


def strip_blocks(text):
    """Grosse eingefuegte Code-/JSON-Bloecke durch [...] ersetzen (Stil-Rauschen,
    oft auch sensible Daten). Heuristik: ```-Fences und eigenstaendige {..}-Bloecke
    ueber mehrere Zeilen (Klammer-Zaehlung; ignoriert Klammern in Strings nicht)."""
    lines, out, i, n = text.split("\n"), [], 0, len(text.split("\n"))
    while i < n:
        s = lines[i].strip()
        if s.startswith("```"):
            j = i + 1
            while j < n and not lines[j].strip().startswith("```"):
                j += 1
            out.append("[…]")
            i = j + 1
            continue
        if s == "{":
            depth, j = 0, i
            while j < n:
                depth += lines[j].count("{") - lines[j].count("}")
                j += 1
                if depth <= 0:
                    break
            if j - i > 1:
                out.append("[…]")
                i = j
                continue
        out.append(lines[i])
        i += 1
    return "\n".join(out)


def clean_body(text):
    kept = []
    for ln in text.splitlines():
        s = ln.rstrip()
        if s.strip() in ("--", "-- "):
            break
        if QUOTE_INTRO.search(s):
            break
        if s.lstrip().startswith(">"):
            continue
        kept.append(ln)
    body = strip_blocks(deflow("\n".join(kept)))
    body = re.sub(r"\[…\](?:\s*\[…\])+", "[…]", body)
    return re.sub(r"\n{3,}", "\n\n", body).strip()


def guess_register(body, domain, register_map):
    for pattern, reg in (register_map or {}).items():
        rx = "^" + re.escape(pattern).replace(r"\*", ".*") + "$"
        if re.match(rx, domain):
            return reg
    # Fallback-Heuristik aus dem Text
    if re.search(r"Sehr geehrte|\bIhnen\b|\bSie\b", body):
        return "formell"
    return "partner"


def detect_dialect(body):
    return sorted({re.search(p, body, re.I).group(0)
                   for p in AT_MARKERS if re.search(p, body, re.I)})


def parse_one(raw_bytes):
    msg = email.message_from_bytes(raw_bytes, policy=email.policy.default)
    return {
        "to": hdr(msg, "To"), "cc": hdr(msg, "Cc"),
        "subject": hdr(msg, "Subject"), "date": hdr(msg, "Date"),
        "domain": first_domain(hdr(msg, "To"), hdr(msg, "Cc")),
        "body": clean_body(get_plain(msg)),
    }


def iter_messages(path):
    """Liefert (id, raw_bytes) fuer .eml, .mbox oder Ordner (eml/mbox/Cyrus)."""
    if path.is_file():
        if path.suffix.lower() == ".mbox":
            for i, m in enumerate(mailbox.mbox(str(path)), 1):
                yield f"{path.stem}-{i}", m.as_bytes()
        else:
            yield path.stem, path.read_bytes()
        return
    for f in sorted(path.iterdir()):
        if f.is_dir():
            continue
        if f.suffix.lower() == ".mbox":
            for i, m in enumerate(mailbox.mbox(str(f)), 1):
                yield f"{f.stem}-{i}", m.as_bytes()
        elif f.suffix.lower() == ".eml":
            yield f.stem, f.read_bytes()
        elif f.name.endswith("."):        # Cyrus-Nummerndatei
            yield f.name.rstrip("."), f.read_bytes()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input")
    ap.add_argument("--out")
    ap.add_argument("--config")
    ap.add_argument("--analyze", help="einzelne Datei nur anzeigen")
    args = ap.parse_args()

    register_map = {}
    if args.config and Path(args.config).exists():
        register_map = json.loads(Path(args.config).read_text()).get("register_map", {})

    if args.analyze:
        d = parse_one(Path(args.analyze).read_bytes())
        reg = guess_register(d["body"], d["domain"], register_map)
        print(f"to={d['to']}  cc={d['cc']}")
        print(f"subject={d['subject']}  date={d['date']}")
        print(f"[auto] register={reg}  domain={d['domain']}  "
              f"dialekt={detect_dialect(d['body']) or '(keine)'}  "
              f"len={len(d['body'])}")
        print("\n----- EIGENTEXT -----\n" + d["body"])
        return

    outdir = Path(args.out) / "clean"
    outdir.mkdir(parents=True, exist_ok=True)
    for mid, raw in iter_messages(Path(args.input)):
        d = parse_one(raw)
        if not d["body"]:
            print(f"{mid}: leer, uebersprungen")
            continue
        reg = guess_register(d["body"], d["domain"], register_map)
        fm = (f"---\nid: {mid}\nbucket: {reg}\nto: {d['to']}\n"
              f"subject: {d['subject']}\ndate: {d['date']}\n"
              f"dialekt_auto: {detect_dialect(d['body'])}\n---\n\n{d['body']}\n")
        (outdir / f"{mid}.md").write_text(fm, encoding="utf-8")
        print(f"{mid} [{reg}] {len(d['body']):5d}  {d['subject'][:55]}")


if __name__ == "__main__":
    main()
