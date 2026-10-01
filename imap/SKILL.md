---
name: imap
description: >
  IMAP-Zugriff auf mehrere Konten: Posteingang durchgehen und zusammenfassen,
  Mails einsortieren, als Spam markieren, löschen, zwischen Konten kopieren
  oder verschieben, Anhänge herausschreiben, Zitatblock für eine Antwort
  erzeugen, die Adressen eines ganzen Threads sammeln, eine Message-ID
  auflösen, eine versendete .eml in "Gesendet" ablegen. Auch bei "geh meine
  Inbox durch", "was ist heute reingekommen", "räum den Posteingang auf",
  "hol den Anhang aus der Mail", "wer war in dem Thread alles dabei".
  Trigger: /imap.
---

# imap -- Posteingang-Triage über mehrere Konten

Zugriff über das gebundelte Script `imap` (Python >=3.11, stdlib only, im
Skill-Verzeichnis). Kein Daemon, kein MCP-Server -- jeder Aufruf öffnet eine
IMAP-Verbindung und schließt sie wieder.

**Aufruf:** `python3 "$SKILL_DIR/imap" <subcommand> [options]`

`$SKILL_DIR` ist das Base Directory dieses Skills (dort wo diese SKILL.md liegt).

Die Zugangsdaten kommen aus `~/.muttrc`, der **Kontoname** ist das erste Label des
Hostnamens (`office.example.at` -> `office`), nicht der Anzeigename aus
Thunderbird. Ohne `--account` gilt das Default-Konto; `list` und `find` fragen
ohne `--account` alle Konten ab. Einrichtung, Keystore und Kontonamen im Detail:
[references/konfiguration.md](references/konfiguration.md).

## Lesende Befehle

| Befehl | Zweck |
|---|---|
| `accounts` | konfigurierte Konten (ohne Passwörter) |
| `folders -a <konto>` | Ordnerliste, Separator, Sonderordner, Server-Capabilities |
| `list [-a <konto>]` | Kopfdaten ohne Body |
| `find -m <message-id>` | Message-ID zu Konto, Ordner und UID auflösen |
| `read <uid> -a <konto>` | Textkörper einer Mail |
| `fetch --uids <liste> -a <konto>` | mehrere Mails mit **einem** Login |
| `quote <uid> -a <konto>` | Zitatblock für eine Antwort (Text oder HTML) |
| `contacts <uid> -a <konto>` | alle Adressen eines Threads sammeln (folgt der References-Kette) |
| `read <uid> --headers` | alle Rohheader statt der Kopfzeilen-Auswahl |
| `read <uid> --raw` | komplette unbearbeitete Nachricht (Header + Body) |
| `attachments <uid> -a <konto>` | Anhänge auflisten (Index, Name, Typ, Größe) |
| `save-attachment <uid> -a <konto>` | Anhang herausschreiben |

```
python3 "$SKILL_DIR/imap" list --json                     # beide Konten
python3 "$SKILL_DIR/imap" list -a office --unseen -n 30
python3 "$SKILL_DIR/imap" list -a mail --since 3          # letzte 3 Tage
python3 "$SKILL_DIR/imap" read 8841 -a office --json
python3 "$SKILL_DIR/imap" read 8841 -a office --headers
python3 "$SKILL_DIR/imap" read 8841 -a office --raw | less
```

`--json` gibt es bei jedem Befehl, vor **und** hinter dem Subcommand.
Für die eigene Weiterverarbeitung immer `--json` verwenden.

`list` holt nur Envelopes (Von, Betreff, Datum, Flags, Größe) -- das ist auch
bei mehreren hundert Mails schnell. Bodies erst bei Bedarf per `read`
nachladen, und nur für die Mails, die wirklich zusammengefasst werden.

**BODY.PEEK:** `read` setzt `\Seen` nicht. Ein Posteingang ist nach einer
Durchsicht also nicht plötzlich komplett gelesen.

`read --headers` und `--raw` sind für Mail-Probleme (Zustellweg, SPF/DKIM/DMARC,
Bcc-Leak, MIME); wann welche Variante passt: [references/header.md](references/header.md).

## Schreibende Befehle

| Aktion | Wirkung |
|---|---|
| `move <uid> -t <ziel>` | verschieben |
| `copy <uid> -t <ziel>` | kopieren |
| `spam <uid>` | in den Junk-Ordner |
| `delete <uid>` | in den Papierkorb -- **nie** expunge |
| `seen` / `unseen` | Gelesen-Status |
| `flag` / `unflag` | Markierung |
| `append <datei.eml>` | eine lokale `.eml` in einen Ordner legen (Default: Gesendet) |
| `empty-trash -a <konto>` | Papierkorb endgültig leeren; ohne `--force` nur zählen |

Als `-t/--target` sind **Sonderrollen** erlaubt: `junk`, `trash`, `archive`,
`sent`, `drafts`. Die werden per SPECIAL-USE beim Server aufgelöst, sonst über
eine Namensheuristik. Findet sich nichts, bricht der Aufruf ab, statt einen
Ordner anzulegen.

Jede schreibende Aktion kennt `--dry-run`. Ausnahme ist `empty-trash`: dort ist
der Probelauf der Default. Ohne `--force` nennt der Aufruf nur die Anzahl und endet
mit Exit 1, erst `--force` löscht - **nicht wiederherstellbar**, auch Mails, die
schon vorher im Papierkorb lagen. `-a` ist Pflicht, das Default-Konto greift hier
nicht. Gelöscht werden nur die beim Aufruf gezählten UIDs; was währenddessen
hinzukommt, bleibt liegen. Nur auf ausdrückliche Anweisung des Nutzers, und
vorher die Anzahl aus dem Probelauf nennen.

## Batch -- der Normalfall für Aktionen

Zwei Schritte: erst die Aktionsliste als Datei nach `.tmp/` schreiben, dann den
`batch`-Aufruf **als eigenständigen Befehl** darauf ansetzen.

```
# Schritt 1 -- Datei schreiben (eigener Befehl)
cat > .tmp/imap-batch.json <<'EOF'
[
  {"account":"office","action":"spam",  "uid":8815},
  {"account":"office","action":"move",  "uid":8802, "target":"Archives.2026"},
  {"account":"office","action":"delete","uid":8819},
  {"account":"office","action":"move",  "uid":8790, "target":"Archives.2026", "to_account":"mail"}
]
EOF

# Schritt 2 -- Probelauf, dann Ausführung (je ein eigener Befehl)
python3 "$SKILL_DIR/imap" batch <pfad>/.tmp/imap-batch.json --dry-run --json
python3 "$SKILL_DIR/imap" batch <pfad>/.tmp/imap-batch.json --json
```

Ein Login je Konto statt eines je Mail. Das ist nicht nur schneller, sondern
vermeidet auch, dass eine Aufräumsitzung als Login-Serie in den Auth-Logs
landet und dort die Brute-Force-Erkennung streift.

Felder: `account`, `action`, `uid`, optional `folder` (Default `INBOX`),
`target`, `to_account`. `--dry-run` gilt für den ganzen Lauf.

**Warum zwei Befehle und nicht die kürzere Pipe?** `batch` liest die Liste zwar
auch von stdin (`batch -`), aber die naheliegende Form
`echo '[…]' | python3 "$SKILL_DIR/imap" batch -` wird in Agent-Umgebungen mit
Berechtigungsprüfung **abgelehnt**: die Freigabe für den Skill greift nur, wenn
der Aufruf am Anfang des Befehls steht. Sobald eine Pipe, ein Heredoc oder ein
verkettetes `&&` davor hängt, trifft die Regel nicht mehr, und die Aktion bricht
mit einer Meldung ab, die nach einem Skill-Fehler aussieht statt nach einer
Berechtigungsfrage. Dasselbe gilt für `mkdir … && cat > datei <<EOF … && python3 …`
in einem Rutsch. Die Zwei-Schritt-Form ist deshalb nicht umständlicher, sondern
die einzige, die zuverlässig durchläuft -- und sie hinterlässt die Aktionsliste
als nachvollziehbare Datei.

## Weitere Befehle

Vollständige Referenz daneben, bei Bedarf lesen:

| Datei | Inhalt |
|---|---|
| `references/quote.md` | `quote` - Zitatblock für eine Antwort, `--message-id`, format=flowed, `--format html`, `--json` |
| `references/contacts.md` | `contacts` - Adressen eines Threads sammeln, kontoübergreifende Suche, `--no-thread` |
| `references/anhaenge.md` | Anhänge auflisten und herausschreiben, Rezept für den Weg an einen Task |
| `references/find-fetch.md` | `find` (Message-ID zu UID), `fetch` (Stapel Mails mit einem Login) |
| `references/konfiguration.md` | muttrc, Keystore statt Klartext, Kontoname vs. Thunderbird-Anzeigename |
| `references/header.md` | `read --headers` / `--raw` bei Mail-Problemen |
| `references/alerts.md` | Alert-Mails vor dem Melden gegenprüfen |
| `references/append-konten.md` | `append` (versendete Mail in "Gesendet"), kontoübergreifendes Kopieren und Verschieben |

## Persönliche Regeldatei (`~/.claude/imap-triage.md`)

Wie eine Inbox einzuordnen ist, ist **persönlich**: welche Absender Rauschen
sind, was einen Push wert ist, was ohne Rückfrage weggeräumt werden darf.
Solche Präferenzen gehören nicht in diesen Skill und nicht in ein Wiki,
sondern in `~/.claude/imap-triage.md`.

**Vor jeder Triage diese Datei lesen, falls vorhanden.** Existiert sie nicht,
gilt der Default-Ablauf unten unverändert -- kein Grund, sie anzulegen oder
danach zu fragen.

Was sie typischerweise festlegt:

- **Klassifikation je Absender/Muster** (Rauschen, Spam, Push, Kenntnisnahme).
- **Autonomie:** welche Kategorien ohne Rückfrage in den Papierkorb dürfen.
  Nur was dort ausdrücklich als automatisch markiert ist -- der Default bleibt
  "nichts ohne Zustimmung".
- **Eskalationsschwellen**, z.B. Flapping-Alerts erst ab N Paaren melden.
- **Gegenchecks** vor einem Alarm (siehe [references/alerts.md](references/alerts.md)).

Widerspricht die Datei einer Regel hier, gewinnt die Datei -- außer bei den
Sicherheitszusagen des Scripts (`BODY.PEEK`, `delete` = Papierkorb, nie
`expunge`).

## Triage-Ablauf

Der eigentliche Zweck des Skills. Ablauf bei "geh meine Inbox durch":

1. `~/.claude/imap-triage.md` lesen, falls vorhanden
2. `list --json` über alle Konten
3. Bodies **nur** für die inhaltlich relevanten Mails per `read --json`;
   Monitoring- und Reminder-Mails vor dem Melden gegen den Ist-Zustand prüfen
   ([references/alerts.md](references/alerts.md))
4. Zusammenfassung ausgeben, dann Vorschlag -- in dieser Reihenfolge:

```
── Antwort nötig ──
• Absender, Zeit [ungelesen]        konto/uid
  Ein bis zwei Zeilen Inhalt.

── Kenntnisnahme ──
• ...

── Unsicher, bleibt liegen ──
• ...

VORSCHLAG
Spam    → office/8815, 8822
Ablage  → office/8802 → Archives.2026
Löschen → office/8819

ok / einzeln anpassen?
```

5. **Warten.** Nichts ausführen, bevor der Nutzer zugestimmt hat.
6. Nach Freigabe: Aktionsliste als Datei schreiben, mit `--dry-run` gegenlesen,
   dann ausführen -- drei eigenständige Befehle (siehe [Batch](#batch----der-normalfall-für-aktionen)).
   Der Probelauf zeigt, wohin die Sonderrollen tatsächlich auflösen (`-> Trash`,
   `-> Junk`) und welche UID in welchem Ordner getroffen wird. Weil UIDs
   ordner-lokal sind, ist das die letzte Gelegenheit, eine falsch adressierte
   Aktion zu bemerken -- danach liegt die falsche Mail im Papierkorb.
7. Ergebnis melden.

**Regeln für die Vorschlagsgruppen:**

- Spam, Werbung und Newsletter nach Absender und Betreff einordnen -- dafür
  reicht der Envelope, kein Body nötig.
- Alles Zweifelhafte kommt in **"Unsicher"** und bleibt liegen. Lieber zu viel
  im Posteingang als eine wichtige Mail weggeräumt.
- `delete` heißt Papierkorb, nicht weg. Endgültiges Löschen gibt es nicht.
- Keine schreibende Aktion ohne ausdrückliche Zustimmung. "Geh die Inbox
  durch" ist eine Leseaufforderung, keine Freigabe zum Aufräumen. Einzige
  Ausnahme: Kategorien, die `~/.claude/imap-triage.md` **namentlich** als
  automatisch erlaubt kennzeichnet -- die stehende Freigabe des Nutzers. Alles
  andere bleibt im Vorschlag.

## Fallstricke

- **Ordnernamen sind serverspezifisch.** Cyrus mit `altnamespace: yes` hat
  `Spam` ohne `INBOX.`-Präfix und `.` als Separator; Dovecot nutzt hier `/`.
  Nie einen Ordnernamen raten, immer `folders` fragen oder eine Sonderrolle
  verwenden.
- **UIDs sind ordner-lokal.** Dieselbe Nummer existiert in jedem Ordner und
  meint dort eine andere Mail. Zu jeder UID gehört deshalb `-f <ordner>`,
  sobald sie nicht aus der INBOX stammt -- ein fehlendes `-f` liefert keinen
  Fehler, sondern die falsche Mail. Wo nur die Message-ID bekannt ist, `find`
  bzw. `quote --message-id` verwenden, statt die UID zu suchen.
- **Zitate nie selbst tippen.** Für eine Antwort immer `quote` aufrufen. Ein
  von Hand gesetztes `> ` sieht auf den ersten Blick gleich aus, weicht aber bei
  jeder Mail leicht ab und ignoriert `format=flowed` und die Threading-Header.
- **Leerer Posteingang ist kein Fehler.** Wenn serverseitige Sieve-Regeln oder
  ein anderer Client bereits einsortieren, ist die INBOX schlicht leer.

## Verwandte Skills

- [swaks](../swaks/SKILL.md) -- Versand; dieser Skill ist die Lese-Seite dazu
  und mit `append` die Ablage danach (ruft swaks mit `--file-sent`/`--draft` selbst auf)
- [mail-as-me](../mail-as-me/SKILL.md) -- Antworten im eigenen Schreibstil
- [pushover](../pushover/SKILL.md) -- Zusammenfassung als Push aufs Handy
- [kanboard](../kanboard/SKILL.md) / [jira](../jira/SKILL.md) -- Ziel für
  Anhänge aus einer Mail (`attach-file` bzw. `attach`)
