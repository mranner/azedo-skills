# swaks - Versandweg, Kontakte, Signatur

Woher die Zugangsdaten kommen, Kontaktaufloesung, Signatur, Encoding.

## Versandweg und Authentifizierung

**Nicht `--server` von Hand setzen.** Den Versandweg löst `build_mail.py` auf.

**Der Regelweg ist `--send`:** der Helper lädt den Weg selbst, gibt ihn als
`SWAKS_OPT_*` an die Umgebung des `swaks`-Prozesses weiter und prüft das
Ergebnis. Das Passwort verlässt den Prozess dabei nicht.

```bash
python3 ~/.claude/skills/swaks/build_mail.py --send $M/mail.eml \
  --to "empfaenger@example.com" --from <absender>
```

`--swaks-env` bleibt für den Aufruf von Hand — es gibt dieselben Variablen als
Exportzeilen aus, `swaks` liest sie dann selbst aus der Umgebung statt aus der
Kommandozeile, wo jedes `ps` sie mitliest:

```bash
ENV=$(python3 ~/.claude/skills/swaks/build_mail.py --swaks-env) \
  && test -n "$ENV" \
  && eval "$ENV"
```

**Die Ausgabe von `--swaks-env` nie ungefiltert anzeigen** — sie enthält das
Passwort im Klartext und landet sonst in Transcript und Shell-History. Zur
Kontrolle des Weges ist `--show-config` da (Passwort maskiert):

```bash
python3 ~/.claude/skills/swaks/build_mail.py --show-config
```

### Woher die Zugangsdaten kommen

Aus der **muttrc** — derselben Datei, aus der auch der `imap`-Skill liest. Es gibt
bewusst **keine** zweite Credential-Datei:

```
set smtp_url  = "smtp://<user>@mail.example.at:587/"
set smtp_pass = "..."
```

`smtp://` bedeutet STARTTLS (Default-Port 587), `smtps://` implizites TLS
(Default-Port 465). Ein Port in der URL gewinnt. Das Passwort wird in dieser
Reihenfolge gesucht: in der URL selbst, dann `set smtp_pass`, dann das
`imap_pass` desselben Hosts aus dem `account-hook` — in der Praxis ist das
dasselbe Konto. Backticks funktionieren wie bei mutt, ein Keystore statt
Klartext ist also möglich:

```
set smtp_pass = `pass show mail/example`
```

Nennt `smtp_url` einen Benutzer, findet sich aber **kein** Passwort, bricht
`build_mail.py` ab, statt unauthentifiziert zu senden.

### Fallback ohne muttrc

Fehlt die muttrc oder steht dort kein `smtp_url`, bleibt es beim bisherigen
Verhalten: `server` aus `swaks.json`, Port 25, ohne Auth und ohne TLS.

Das trägt nur, solange die **Quell-IP im Relay privilegiert** ist
(`mynetworks`). Läuft der Skill von einer dynamischen Leitung aus, nimmt der
Relay zwar Mail an azedo-interne Adressen an, weist externe Empfänger aber mit
`454 4.7.1 Relay access denied` ab. Der Fehler fällt im Alltag nicht auf, weil
die interne Post weiter durchgeht — er trifft genau die Mails nach draußen.
Deshalb ist die muttrc-Variante der Normalfall und der Fallback die Ausnahme.

## Kontakte

### Antwort auf einen Thread: `imap contacts`

**Der Regelweg**, sobald auf eine bestehende Mail geantwortet wird. Der Befehl
folgt der `References`-Kette und sammelt `From`, `Reply-To`, `To` und `Cc`
**aller** Mails des Threads ein — über alle konfigurierten Konten hinweg:

```bash
python3 ~/.claude/skills/imap/imap contacts <uid> -a <konto> [-f <ordner>]
```

Das ist kein Komfort, sondern der Unterschied zwischen vollständig und fast
vollständig: eine Adresse aus dem Verteiler steht oft nur in einer einzigen
älteren Mail, und die eigenen Antworten liegen im „Gesendet" eines anderen
Kontos. Von Hand ist das ein Abklappern der Kette mit je einem Aufruf pro Mail
(CR4613). Die eigene Adresse steht mit in der Liste und gehört beim Envelope in
der Regel heraus.

Details: `references/contacts.md` im `imap`-Skill.

### Neue Mail an einen Namen: `swaks-contacts.tsv`

Für eine Mail **ohne** Vorgeschichte, wenn der User einen Namen statt einer
Adresse nennt („schick das an Karin"). Die Datei liegt projektlokal unter
`.claude/swaks-contacts.tsv` oder global unter `~/.claude/swaks-contacts.tsv`
(TSV: `kurzname<TAB>email`, eine Zeile pro Kontakt) — sie ist **optional** und
existiert nicht überall:

```bash
grep -i <name> .claude/swaks-contacts.tsv
```

Kein Treffer **oder keine Datei** heißt: nachfragen, nicht raten. Eine fehlende
Datei ist kein Fehler und kein Grund, sie anzulegen — sie entsteht, wenn der
erste Kontakt darin landet.

Neue Kontakte nach dem Versand ergänzen:

```bash
printf '%s\t%s\n' "kurzname" "email@adresse" >> .claude/swaks-contacts.tsv
```

## Signatur

Zwei Signaturdateien, **automatisch aufgelöst** von `build_mail.py` – ohne `--sig-*-file` musst du nichts angeben:

- **Standard (global):** `~/.claude/swaks-signature.txt` / `~/.claude/swaks-signature.html`
- **Projektlokaler Override (Vorrang):** `.claude/swaks-signature.txt` / `.html` im Arbeitsverzeichnis, falls vorhanden

Auflösungsreihenfolge je Datei: projektlokal `.claude/` **vor** global `~/.claude/`; existiert keine, wird schlicht keine Signatur angehängt (kein Fehler). Explizite `--sig-text-file`/`--sig-html-file` überschreiben die Auto-Auflösung – ein **explizit** angegebener Pfad muss existieren (sonst Abbruch).

Beim Standardversand (Multipart, siehe unten) hängt `build_mail.py` beide an – Text-Signatur mit Leerzeile Abstand, HTML-Signatur als Block. Bei reinem Text-Body nur die `.txt`-Signatur.

**Wichtig – die globale Signatur ist die persönliche des Nutzers** (Name und Firmenwortlaut stehen in der Signaturdatei, nicht hier). Geht die Mail unter der eigenen Adresse des Nutzers raus ("in seinem Namen") → **immer** die globale Signatur dranlassen, Auto-Auflösung genügt. Das ist **kein** Ausschlussgrund. `--no-sig` hier nur, wenn der Nutzer das **ausdrücklich** sagt.

Die Signatur wird **nicht** angehängt wenn:

- Der User explizit "ohne Signatur" / "no sig" sagt → `--no-sig` an `build_mail.py` übergeben (schaltet auch die Standard-Signatur ab)
- Die Mail im Namen einer **dritten** Person verfasst wird – **weder der Nutzer noch Claude**, sondern ein anderer `--from` → dann keine Standard-Signatur, ggf. deren eigene per `--sig-*-file`. Der Wechsel vom Default-Absender (`from` aus der Config) auf die eigene Adresse des Nutzers ist **kein** solcher Fall (s.o.).

## Encoding

Immer UTF-8 Header mitgeben, damit Umlaute korrekt ankommen:

```
--header "Content-Type: text/plain; charset=utf-8" \
--header "Content-Transfer-Encoding: 8bit"
```

Für HTML-Mails stattdessen `text/html; charset=utf-8` (siehe Abschnitt HTML-Body).
