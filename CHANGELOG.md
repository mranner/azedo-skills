# Changelog

Alle Aenderungen an den azedo-skills, absteigend nach Version. Aktuelle Version steht auch im
[README](README.md#changelog); der vollstaendige Verlauf lebt hier.

### 1.35.0

- **Kunden-, Personen- und Infrastrukturdaten aus dem public Repo entfernt (CR4461).** 1.34.7 hatte
  nur die Mailadressen erwischt; ein vollstaendiger Durchgang foerderte deutlich mehr zutage.
  - **Credentials:** `pushover/SKILL.md` fuehrte **zwei echte Pushover-User-Keys** im Klartext
    (Adressbuch-Beispiel und `recipients add`) — der eigene und der einer Kollegin. Beide gegen
    `~/.pushover-recipients` als produktiv verifiziert, ersetzt durch `uAAA…`/`uBBB…`. Die Keys
    stehen weiter in der Git-Historie und muessen in der Pushover-App neu ausgestellt werden; ein
    Doku-Fix allein reicht dafuer nicht.
  - **Personen:** Klarname und Login einer Kollegin (`kanboard/SKILL.md` -> `Karin Musterfrau`),
    der Alias einer Kollegin an 11 Stellen (`pushover`, `README.md`) -> `kollege`, Klarname eines
    Kunden-Accounts (`jira/SKILL.md` -> `Max Mustermann`), `imap_user` (`imap/SKILL.md` ->
    `<username>`), ein Vorname in `swaks`/`mail-as-me`. Bei den `pushover`-Trigger-Phrasen im
    Frontmatter bewusst ein Platzhalter-**Name** statt einer namenlosen Umschreibung: was das
    Triggering traegt, ist das Muster „push + Empfaenger + Nachricht", nicht die Zeichenkette.
  - **Kunden:** Jira-Instanzen und -Profile (Kunden-Hosts ->
    `jira.example.com`/`example.atlassian.net`, Profile -> `dc`/`cloud`), ein Kundenprojekt samt
    Domain, wwwuser und Jail-Pfad (`wp-nf`), Empfaenger-Beispiele (`mail-as-me`), ein Gateway
    (`swos`). Im `CHANGELOG.md` zusaetzlich die **Sicherheitsarchitektur** eines Kunden
    (SSO-Portal, MFA-Produkt) — inhaltlich heikler als der blosse Name.
  - **Eigene Infrastruktur:** DEV-Host, Jail-Name, Vhost-Pfade und Dateigruppe (`wp-sync-dev`),
    Dashboard-Host (`mainwp`), IMAP-Hosts (`imap`), Beispielserver (`wp-cli`), die beiden
    Whitelist-IPs (`wiki/SKILL.md`).
  - **Konkrete Vorgangs-IDs** (Issue-, Kommentar-, Attachment-IDs, eine Atlassian-accountId) durch
    formatgleiche Platzhalter ersetzt, damit die Beispiele die Syntax weiter zeigen.
  - Changelog-Eintraege ab 1.30 wurden **umformuliert** statt ersetzt — ein Suchen-und-Ersetzen
    haette Saetze wie „Ausloeser: <Kundenname> laeuft auf Cloud" unverstaendlich oder falsch gemacht.
    Aeltere Eintraege nur bei den harten Identifiern angefasst.
  - `CLAUDE.md`: neuer Abschnitt **„Das Repo ist public"** mit den fuenf verbotenen Kategorien, der
    Ersatzstrategie und zwei Pruef-Greps fuer vor dem Push.
- **`swaks`: Versand-Defaults kommen aus `.claude/swaks.json` (CR4461).** Der Skill hatte fuer
  Empfaenger, Absender und Server keine Config-Quelle — die Werte standen als Prosa in der
  `SKILL.md`, `build_mail.py` verlangte `--to`/`--from` als Pflichtargumente.
  - Neue Config mit `to`, `from`, `server`, `message_id_domain`; Aufloesung projektlokal
    `.claude/` **vor** global `~/.claude/`, also dieselbe Reihenfolge wie bei den Signaturen
    (`resolve_sig()` ist zu `resolve_claude_file()` verallgemeinert und wird von beiden genutzt).
  - `--to`/`--from` sind jetzt **optional**: Kommandozeile schlaegt Config. Fehlt beides, bricht
    der Helper mit einer Meldung ab, die Datei und Schluessel nennt — statt eine unadressierte
    Mail zu bauen.
  - `--show-config` gibt die aufgeloeste Config aus (vor argparse abgefangen, damit die Abfrage
    ohne `--subject`/`--text-file`/`--html-file` funktioniert). Daraus holt der Aufrufer den
    `server` fuer die swaks-Zeile, den der Helper selbst nicht braucht.
  - Die Message-ID-Domain war hartkodiert und kommt jetzt aus `message_id_domain`; ohne Eintrag
    faellt sie auf die Domain des Absenders zurueck. Bei abweichendem `--from` gewinnt weiterhin
    die Config — die Message-ID gehoert zum sendenden System, nicht zum From-Header.
  - `install.sh` meldet eine fehlende `~/.claude/swaks.json`, legt sie aber **nicht** an: eine mit
    `example.org` vorbelegte Config wuerde Mail an eine Platzhalter-Adresse zustellen statt
    hoerbar zu scheitern. Vorlage `swaks/swaks.json.example`.
- **`wetter`: Kontaktadresse im User-Agent aus Config oder Environment (CR4461).** Die Adresse war
  hartkodiert und ging bei **jedem** Aufruf an GeoSphere, die Warn-API und Nominatim. Jetzt
  `WETTER_CONTACT` (Vorrang) -> `contact` aus `~/.claude/wetter.json` -> Fallback ohne Kontakt.
  Bewusst **kein** Abbruch ohne Config: Nominatim verlangt nur eine identifizierende
  User-Agent-Zeile, die Kontaktadresse ist eine Empfehlung fuer nennenswertes Abrufvolumen — der
  Skill bleibt auf einem frischen Rechner voll funktionsfaehig. Die `SKILL.md` fragt einmalig
  danach (nur beim Geocoding per **Ortsname**, bei Koordinaten geht kein Request an Nominatim);
  eine Ablehnung wird als leerer `contact` festgehalten, damit die Frage nicht wiederkommt.
  Vorlage `wetter/wetter.json.example`.
- **`wp-sync-dev`: DEV-Umgebung kommt aus dem Infra-Wiki.** Die Prod-Seite war laengst
  parametrisiert (`<jailer>`, `<jailname>`, `<wwwuser>`, `<domain>`), die DEV-Seite hartkodiert.
  Jetzt symmetrisch ueber `<dev-host>`, `<dev-jail>` und `<dev-group>`, die per
  `/wiki query "DEV-Webhost"` aus der Server-Entity kommen — dort sind sie samt Jail-IP, Pfaden
  und Zugang ohnehin gepflegt, das Duplikat im Skill war reine Redundanz.
- **`jira`: Doku nennt keine Profilnamen mehr.** Die Profile heissen pro Rechner anders; ein
  Beispiel `-i cloud` waere gegen eine bestehende Config ins Leere gelaufen. Beispiele nutzen
  `-i <instanz>`, dazu der Hinweis, die vorhandenen Namen per `instances` aufzulisten statt sie
  aus der Doku zu raten. Bestehende `~/.claude/jira.json` bleiben unveraendert gueltig.

### 1.34.7

- **Echte Mailadressen aus der Doku entfernt.** `mail-as-me/SKILL.md` fuehrte die private Adresse
  des Repo-Eigentuemers achtmal im Klartext (Beispiel-`config.json` und swaks-Aufruf), der
  `CHANGELOG.md`-Eintrag 1.32.1 zweimal, `jira/SKILL.md` eine echte Kundenadresse in zwei
  Beispielbefehlen. Alle drei Stellen sind reine Doku-Beispiele: die Versand-Identitaet liest
  `mail-as-me` zur Laufzeit aus `config.json.send` des Profils, der Jira-Aufruf bekommt die Adresse
  als Argument mit. Ersetzt durch `ich@example.org` bzw. `vorname.nachname@example.org`; die
  Formulierungen drumherum kommen ohne Personenbezug aus.
- Der swaks-Default-Absender bleibt in `mail-as-me/SKILL.md` und im Changelog stehen — das ist der
  tatsaechliche swaks-Default, ein Platzhalter wuerde die Aussage falsch machen. `swaks/SKILL.md`
  nennt die eigene Adresse weiterhin als dokumentierten Default-Empfaenger: der Skill hat dafuer
  keine Config-Quelle (`build_mail.py` verlangt `--to`/`--from`), die Angabe steht nur in der Prosa.

### 1.34.6

- **`mail-as-me`: Absender und Bcc kommen aus dem Profil (CR4459).** Gesendet wird ueber
  `swaks`, und dessen Defaults sind die von Claude — eine Mail in der eigenen Stimme ging
  deshalb von `claude@azedo.at` raus, solange `--from` nicht bei jedem Versand haendisch
  mitgegeben wurde; dasselbe fuer die Bcc-Kopie an sich selbst. `config.json` traegt jetzt
  einen Block `send` mit `from` und `bcc` (beide optional: ohne `from` gilt der
  swaks-Default, ohne `bcc` geht keine Kopie raus, mehrere Adressen kommasepariert). Beim
  Versand eines Entwurfs aus `draft`/`rewrite` wird er ohne Rueckfrage angewendet — eine
  Vorgabe des Nutzers im Auftrag hat Vorrang. `from` geht an Header **und** Envelope, `bcc`
  **nur** in den Envelope-`--to` von swaks (`build_mail.py --bcc` setzt bewusst keinen
  Header; fehlt die Adresse im Envelope, kommt trotz `--bcc` nichts an). Das `setup`-Interview
  fragt die beiden Adressen mit ab, der swaks-Skill verweist bei mail-as-me-Entwuerfen auf
  den Profil-Block statt auf seine eigenen Defaults.

### 1.34.5

- **`kimai`: `import-hours` konfiguriert sich aus der Eingabedatei (CR4455).** Projekte, User und
  Stundensaetze standen hartcodiert in `cmd_import_hours` — und weil das Repo auf GitHub liegt,
  mussten die echten Projektnamen durch Platzhalter ersetzt werden. Da die Dict-Schluessel zugleich
  die JSON-Schluessel der Eingabedatei sind, zwang das die private Eingabedatei zu denselben
  Fantasienamen; die echten Namen brachen den Import mit "Unbekanntes Projekt" ab.
  Die Eingabedatei traegt jetzt `user`, `raten` (`extern`/`kimai`) und `projekte`
  (`id`, `activity_id`, optional `name`); der Skill kennt weder Projekte noch Raten noch
  Mitarbeiter. `user` darf ein Username sein (Aufloesung ueber `instance.json`) oder eine
  numerische ID. Fehlende Felder brechen mit einer benannten Meldung ab statt still einen
  fremden Stundensatz anzuwenden. **Breaking:** bestehende Eingabedateien brauchen die drei
  neuen Bloecke.

### 1.34.4

- **`wiki`: Lint ignoriert Code-Bereiche bei der Wikilink-Pruefung (CR4440).** Ein Shell-Beispiel
  mit POSIX-Zeichenklasse — `grep -E "class[[:space:]]+timthumb"` in `apache-fry` — wurde als
  toter Wikilink `[[:space:]]` gemeldet. Betroffen ist jede Zeichenklasse in einem Code-Block
  oder Inline-Code, also genau die Stellen, an denen Befehle wortgetreu dokumentiert werden
  sollen. `find_wikilinks()` entfernt jetzt vorher Code-Fences (``` und ~~~, auch unterminiert
  bis Dateiende) und Inline-Code; die Index-Pruefung nutzt dieselbe Regel, damit ein `[[slug]]`
  im Code-Beispiel des Index nicht als Index-Eintrag zaehlt. Links in Frontmatter und Fliesstext
  zaehlen unveraendert. Regressionslauf ueber das azedo-Wiki (139 Artikel): unveraendert sauber.

### 1.34.3

- **`jira`: Kommentare bearbeiten, @-Mentions im Body, Nutzersuche (CR4444).** Aufgefallen an
  ITSD-2000: eine Mention musste ueber ein Ad-hoc-Skript direkt gegen die REST API gesetzt werden,
  weil der Skill weder bestehende Kommentare aendern noch Erwaehnungen erzeugen konnte.
  - **`comment-edit <ISSUE> --id <commentId> --body ...`** ueberschreibt einen bestehenden
    Kommentar (`PUT issue/{key}/comment/{id}`, Cloud ADF / DC Plaintext, `--body -` liest stdin).
    Damit die id ohne `--json` auffindbar ist, steht sie jetzt in der Kopfzeile von `comments`:
    `[2026-07-27 22:50] MMuster (id 20001):`.
  - **`@[<schluessel>]` im Body wird zur echten Erwaehnung** — Cloud als ADF-`mention`-Knoten, DC
    als Wiki-Markup `[~username]`. Gilt fuer jeden geschriebenen Body (`comment`, `comment-edit`,
    `describe`, `transition --comment`); enthaelt ein Text keine `@[...]`, laeuft auch kein
    zusaetzlicher API-Call. Schluessel ist eine E-Mail (exakter Treffer auf `emailAddress`), eine
    accountId/ein Username (direkt uebernommen) oder ein Anzeigename.
  - **Mehrdeutigkeit bricht ab, statt zu raten.** Auf einer der Cloud-Instanzen liefert `@[Max Mustermann]`
    drei aktive Accounts gleichen Namens (nur einer mit sichtbarer E-Mail) — der Skill listet die
    Kandidaten mit accountId und E-Mail und schreibt nichts. Ein Schluessel ohne Treffer bricht
    ebenso ab; unaufgeloester `@[...]`-Text landet nie im Ticket. Umgekehrt gilt: verbirgt Cloud die
    E-Mail in der Antwort, matcht die Suche sie trotzdem — bleibt genau ein Kandidat, wird er
    genommen.
  - **`users --query <suchbegriff>`** schlaegt die noetigen Kennungen nach (Cloud
    `user/search?query=` -> accountId, DC `user/search?username=` -> Username), mit Anzeigename,
    E-Mail und Inaktiv-Markierung.
  - **Nicht-JSON-Antworten melden sich lesbar** statt mit `JSONDecodeError`-Traceback: liefert die
    Instanz auf 200 eine HTML-Login-/SSO-Seite (bei der DC-Instanz derzeit auf **allen**
    Endpoints, auch `myself` — abgelaufener PAT), nennt der Fehler Content-Type und Ziel-URL. Der
    DC-Pfad dieses Release ist daher nur gegen Cloud verifiziert.

### 1.34.2

- **`mail-as-me`: humanizer-de-Audit ist verbindlich, plus Ausfuehrungsnachweis (CR4439).**
  Schritt 4 von `draft`/`rewrite` war als "Self-Audit ... via humanizer-de" formuliert und
  liess sich als manueller Abgleich gegen die Anti-Pattern-Liste in `referenz.md` lesen. Genau
  das ist beim Entwurf an einen Kunden passiert: der Skill wurde nie aufgerufen, der Fehler fiel
  erst auf Nachfrage auf. Schritt 4 verlangt jetzt den **Aufruf** des Skills `humanizer-de`
  (Modus Sachlich, Zweig Nur Audit) und haelt fest, dass der manuelle Abgleich ihn nicht ersetzt.
  Umgekehrt gilt genauso: die Linter finden die inhaltliche Klasse nicht (Zeitkolorit im
  Einstieg, Abstraktum statt Sachverhalt, Nebenbefunde ohne Handlungsrelevanz, doppeltes
  Hedging), deshalb bleibt die `referenz.md`-Checkliste als zweiter Durchgang daneben stehen.
  - **Neuer Abschnitt "Ausfuehrungszeile".** Jeder gezeigte Entwurf beginnt mit einer Zeile
    ueber die tatsaechlich gelaufenen Schritte (Profil, Register + Herkunft, geladene Beispiele,
    humanizer-de-Modus + Ergebnis). Ein uebersprungener Schritt wird damit sofort sichtbar,
    statt unbemerkt zu bleiben. Nicht Gelaufenes wird ausgeschrieben (`humanizer-de: nicht
    gelaufen`), nicht weggelassen; die Zeile ist Arbeitsprotokoll und geht nicht mit der Mail
    raus.
  - **Verworfen:** ein PreToolUse-Hook, der `swaks` blockt, wenn kein humanizer-de-Lauf
    stattfand. Er traefe auch reine Dateiversendungen ohne Textentwurf.

### 1.34.1

- **`imap`: persoenliche Triage-Regeln aus `~/.claude/imap-triage.md`.** Wie eine Inbox
  einzuordnen ist, ist Praeferenz und keine Skill-Logik: welche Absender Rauschen sind, was einen
  Push wert ist, was ohne Rueckfrage weggeraeumt werden darf. Der Skill liest die Datei jetzt
  **vor** jeder Triage (Schritt 1 des Ablaufs); fehlt sie, gilt der Default unveraendert und es
  wird auch nicht nach ihr gefragt. Widerspricht sie einer Regel im Skill, gewinnt die Datei --
  ausser bei den Sicherheitszusagen des Skripts (`BODY.PEEK`, `delete` = Papierkorb, nie
  `expunge`).
  - **Autonomie-Ausnahme praezisiert:** Der Skill raeumt weiterhin nichts ohne Zustimmung auf.
    Einzige Ausnahme sind Kategorien, die die Regeldatei **namentlich** als automatisch erlaubt
    kennzeichnet -- das ist die stehende Freigabe des Nutzers, kein Freibrief fuer den ganzen
    Posteingang.
  - **Neuer Abschnitt "Alert-Mails gegenpruefen".** Monitoring- und Reminder-Mails beschreiben
    einen vergangenen Zustand; vor Meldung oder Push wird der Ist-Zustand geprueft
    (`nc -z <host> 22` beim sshd-Alert, `openssl s_client` beim Zertifikats-Reminder). Das aendert
    die Bewertung regelmaessig: ein "Wildcard laeuft morgen ab" ist harmlos, wenn der Host laengst
    ein Let's-Encrypt-Zertifikat ausliefert. Umgekehrt werden Alert-Paare erst nach einem
    Monitoring-Intervall bewertet -- monit schickt die Recovery typisch nach ~2 Minuten, vorher
    gilt ein Failed-Alert zu Unrecht als offener Befund.

### 1.34.0

- **Neuer Skill `imap`: Posteingang-Triage ueber mehrere Konten.** Gegenstueck zu `swaks` — der
  bestehende Skill versendet, dieser liest und raeumt auf. stdlib-only Python, kein Daemon, kein
  MCP-Server. Verifiziert gegen zwei Konten auf getrennten Servern: einmal Dovecot, einmal
  Cyrus IMAP 2.5.17.
  - **Zugangsdaten aus der muttrc**, keine zweite Credential-Datei. Ausgewertet wird eine
    Teilmenge der muttrc-Syntax: `set`, `account-hook`, `source` (auch `source "cmd |"`) und
    Backtick-Substitution — damit funktioniert auch `imap_pass=\`pass show ...\`` aus einem
    Keystore. Konten ohne vollstaendige Angaben werden uebersprungen statt geraten. Kontoname ist
    das erste Label des Hostnamens (`mail.example.at` -> `mail`).
  - **Lesend:** `accounts`, `folders` (Ordner, Separator, Sonderordner, Capabilities), `list`
    (Envelopes ohne Body, `--unseen`/`--since`/`-n`, ohne `--account` ueber alle Konten) und
    `read` (Textkoerper, HTML wird entschlackt). Gelesen wird durchgehend mit **`BODY.PEEK`**, der
    Ungelesen-Status bleibt also unangetastet.
  - **Schreibend:** `move`, `copy`, `spam`, `delete`, `seen`/`unseen`, `flag`/`unflag`, jeweils mit
    `--dry-run`. `delete` verschiebt in den Papierkorb und expunged **nie**. Als Ziel sind
    Sonderrollen (`junk`, `trash`, `archive`, `sent`, `drafts`) erlaubt, die per SPECIAL-USE beim
    Server aufgeloest werden; findet sich nichts, bricht der Aufruf ab, statt einen Ordner anzulegen.
  - **`batch`** fuehrt eine JSON-Liste von Operationen mit **einem Login je Konto** aus statt einem
    je Mail — schneller und ohne Login-Serie in den Auth-Logs, die die Brute-Force-Erkennung
    streift. Das ist der vorgesehene Weg fuer alle Aktionen, nachdem der Nutzer den Vorschlag
    freigegeben hat.
  - **Kontouebergreifend** kennt IMAP kein `MOVE`: die Mail wird geholt und per `APPEND` im Ziel
    eingefuegt (mit Flags und `INTERNALDATE`), die Quelle wird **erst nach** erfolgreichem `APPEND`
    geraeumt. Schlaegt er fehl, bleibt die Quelle unangetastet — im schlimmsten Fall ein Duplikat,
    nie ein Verlust. Vorherige Message-ID-Pruefung macht einen abgebrochenen Lauf wiederholbar.
    Bare LF wird vor dem `APPEND` verlustfrei auf CRLF normalisiert, sonst weist Cyrus Mails
    zurueck, die Dovecot klaglos gespeichert hat.
  - **Capabilities werden nach dem Login erneut geholt.** imaplib behaelt die aus dem Greeting;
    Dovecot meldet `MOVE` und `UIDPLUS` aber erst im authentifizierten Zustand — ohne den
    zusaetzlichen `CAPABILITY`-Call waere der Skill unnoetig in den COPY-Fallback gelaufen und
    haette Mails in der Quelle als geloescht markiert liegen gelassen. Der Fallback nutzt
    **`UID EXPUNGE`**, nicht das nackte `EXPUNGE`, das alle als geloescht markierten Mails des
    Ordners mitnehmen wuerde.
  - **Triage-Ablauf in der SKILL.md festgeschrieben:** erst Zusammenfassung (Antwort noetig /
    Kenntnisnahme / Unsicher), dann Vorschlag (Spam / Ablage / Loeschen), dann **warten**. Keine
    schreibende Aktion ohne ausdrueckliche Zustimmung; Zweifelhaftes bleibt liegen.

### 1.33.0

- **`kanboard`: CR<->Jira-Verknuepfung ueber `jira:<KEY>`-Tag.** Analog zum bestehenden
  `kimai:<shortcut>` merkt ein Tag `jira:<KEY>` (z.B. `jira:SADM-100`) das zum CR gehoerende
  Jira-Issue; `cr` hebt es als eigenes Feld `jira` heraus, sodass der `jira`-Skill ohne erneute
  Key-Angabe darauf arbeiten kann. Neuer Subcommand `set-jira <task_id> --key <KEY>` (ersetzt einen
  vorhandenen `jira:*`-Tag, normiert auf Grossschreibung). Bewusst **kein** Commit-Prefix — der CR
  bleibt der einzige Commit-Anker, keine Kollision. SKILL.md: Tag-Konvention, `cr`-Feld und
  Write-back-Regel dokumentiert (CR4435).
- **`jira`: Jira-Cloud-Unterstuetzung (`*.atlassian.net`) neben Data Center.** Ausloeser: eine der genutzten
  Instanzen laeuft auf Cloud (`*.atlassian.net`), der Skill sprach bisher nur DC (REST v2, PAT-Bearer)
  und konnte Cloud gar nicht erreichen (CR4435).
  - **Auto-Erkennung** des Instanz-Typs: Host `*.atlassian.net` oder `"type": "cloud"` in der
    Config schaltet auf den Cloud-Pfad; die Subcommands (`search`/`issue`/`comments`/`transitions`/
    `comment`/`transition`) bleiben identisch.
  - **Cloud-Pfad:** REST API v3, **Basic-Auth** `base64(email:API-Token)` (Cloud braucht daher
    `email` **und** `token` in der Config), Suche ueber `/rest/api/3/search/jql` mit
    Token-Paginierung (`--token`, da der alte `/search`-Endpoint 2025 fuer Cloud entfernt wurde;
    kein `total` mehr). DC-Pfad (v2, Bearer, `--start`) unveraendert.
  - **ADF-Bruecke:** Cloud liefert/erwartet Bodies als ADF (JSON). Beim **Lesen** werden
    Beschreibung und Kommentare zu Plaintext verflacht (Absaetze, Zeilenumbrueche, `@`-Mentions ohne
    Doppel-`@`, Emojis); beim **Schreiben** (Kommentar, Transition-Kommentar) wird Plaintext zu ADF
    gewandelt (ein Absatz je Zeile). DC-Bodies weiter 1:1 Plaintext.
  - Config-Refactor: `resolve_instance` liefert jetzt ein `Instance`-Objekt (name/host/is_cloud/
    fertiger Auth-Header), `api_call` waehlt v2/v3 danach. `instances` zeigt `[dc]`/`[cloud]`.
  - **Neue Subcommands** `assign`, `describe`, `subtask`, `attach`:
    - `assign` (`--to me` / `--to <accountId|Username>` / `--unassign`) ueber `PUT
      /issue/{key}/assignee`; DC vs. Cloud waehlt automatisch das Identifikator-Feld (`name` vs.
      `accountId`), `me` wird via `myself` aufgeloest.
    - `describe <key> --body <text|->` setzt die Beschreibung (Cloud -> ADF, DC -> Plaintext).
    - `subtask <parent> --title <t> [--owner]` legt eine Unteraufgabe an; der Subtask-Issuetype
      wird per createmeta ermittelt (Cloud „Unteraufgabe", DC „Sub-task" o.ae.). `--owner` wird
      **nach** dem Create per separatem Assignee-Call gesetzt, da Jira den Assignee beim Create je
      nach Screen-Config (v.a. Cloud) still ignoriert.
    - `attach <key> --file <pfad>` haengt eine Datei an (multipart, `X-Atlassian-Token: no-check`).
    - `attachments <key>` listet die Anhaenge (id, Name, Groesse, Typ, Datum, Autor).
    - `download <key> [--id <att-id>] [--output <pfad>]` laedt einen oder alle Anhaenge eines Issues.
      Folgt dem 302 auf den Media-/S3-Host und entfernt dabei den `Authorization`-Header (sonst
      Ablehnung); gleichnamige Anhaenge bekommen beim Sammel-Download die ID vorangestellt (kein
      stilles Ueberschreiben).
  - Live gegen eine Cloud-Instanz verifiziert: Login, Projekt-Discovery, Suche mit Routing,
    Issue-/Kommentar-Anzeige inkl. Umlaute/Emojis/Mentions, Transition-Dry-Run. **Schreib-Pfad
    komplett live bestaetigt** am Test-Ticket SADM-100: Kommentar (ADF, mehrzeilig), `assign` (alle
    Varianten), `describe`, `subtask` (inkl. `--owner`), `attach`, `attachments` und `download`
    (Inhalt byte-identisch verifiziert). Nur `transition` mit `--yes` bislang nur als Dry-Run.

### 1.32.4

- **`mail-as-me`: „nie spiegeln"-Regel als prominente Grundregel + konkretes Anti-Beispiel; Trigger
  geschaerft.** Ausloeser: Bei „schreib eine Mail wie ich" wurde der Skill mehrfach uebersprungen und
  direkt in swaks getextet — Ergebnis war die schweizerische Grussformel „Hoi" (Spiegelung eines
  `example.com`-Empfaengers) statt des korrekten oesterreichischen „Hallo Karin," (CR4437).
  - Neue Sektion **„Grundregel: eigene Stimme, nie spiegeln"** ganz oben mit dem wiederkehrenden
    Fehlgriff als konkretem Anti-Beispiel: CH/DE-Empfaenger (`example.com`, `example.ch`) bekommen
    trotzdem „Hallo {Vorname}," — nie „Hoi"/„Grüezi"/„Grüessech"/„Grüess di"/„Servus". Die abstrakte
    de-AT/Nicht-spiegeln-Regel stand bisher nur verstreut in den `draft`/`rewrite`-Schritten.
  - **Trigger-Beschreibung** um „schreib eine Mail wie ich" ergaenzt und mit der Anweisung versehen,
    bei „wie ich"/„in meinem Stil"-Mails **immer zuerst** `mail-as-me` aufzurufen und die Mail nicht
    direkt in swaks zu texten. Reine Doku-/Trigger-Aenderung, keine Code-Aenderung an `extract.py`.

### 1.32.3

- **`pushover`: `--host` bei der `digest`-Vorlage nachgeruestet.** Die `SKILL.md` dokumentierte `--host`
  („ergaenzt eine Fusszeile") pauschal fuer alle drei Vorlagen, `alert`/`recovery` implementierten es auch
  — nur `digest` kannte den Parameter nicht (`unrecognized arguments: --host`). Jetzt akzeptiert `digest`
  `--host` ebenfalls und haengt dieselbe Fusszeile `<i>Host: …</i>` wie `alert`/`recovery` an. Aufgefallen
  beim Umstellen eines Post-Update-Monitoring-Loops von Telegram auf Pushover (CR4436).

### 1.32.2

- **Neuer Skill `jira`: Jira Data Center / Server per REST API v2 (multi-instanz).** Selbst-gehostete
  Jira-Instanzen (z.B. `jira.example.com`) abfragen und aendern, Auth per Personal
  Access Token (Bearer).
  - Subcommands: `instances`, `search` (JQL), `issue`, `comments`, `transitions` (lesend); `comment`,
    `transition` (schreibend; `transition` mit Dry-run-Guard, echt erst mit `--yes`).
  - Config `~/.claude/jira.json` (bewusst **ausserhalb** der Git-Repos — `~/.claude` ist kein Repo,
    der Token landet nie in Git) mit benannten Instanzen und **Projekt-Routing**: der Issue-Key
    (`CORTAB-1000` → `CORTAB`) bzw. `project = X` in der JQL waehlt die Instanz, `--instance`
    ueberschreibt, sonst greift `default`. stdlib-only, keine pip-Abhaengigkeiten.
  - Hinweis: eine der DC-Instanzen liegt hinter einem SSO-Portal mit MFA → PAT-Zugriff von
    aussen (noch) blockiert; Klaerung mit dem Betreiber laeuft (CR4435).
- **`mail-as-me`: „Gegenueber nie spiegeln" als universelle Engine-Regel verankert.** `draft`/`rewrite`
  schreiben immer in der eigenen Stimme des Profils — weder Sprache, Stil, Register, Region/Dialekt,
  Anrede noch Grussformel des Gegenuebers uebernehmen (bei Reply-`.eml` nicht Ton/Region des Absenders
  spiegeln); die Sprache nur auf **explizite** Ansage wechseln. Vorher nur im `michael`-Profil vermerkt,
  jetzt profil-unabhaengig in `SKILL.md`.

### 1.32.1

- **`swaks`: Signatur-Wording geschaerft — Mails von der eigenen Adresse nie mehr ohne Signatur.**
  Ausloeser: Der „anderer `--from` → keine Standard-Signatur"-Passus wurde zweimal auf Michael selbst
  angewandt (Default-`--from` ist `claude@azedo.at`), sodass Mails in seinem Namen faelschlich mit
  `--no-sig` ohne Signatur rausgingen. Die globale Signatur **ist** aber Michaels eigene.
  - `SKILL.md`: Signatur-Abschnitt + Ablauf-Schritt 4 stellen jetzt explizit klar, dass `--from`
    mit der eigenen Adresse **immer** die globale Signatur bekommt (kein Ausschlussgrund) und `--no-sig`
    hier nur auf ausdrueckliche Ansage. Der „fremder Absender"-Ausschluss ist auf eine **dritte** Person
    (weder Michael noch Claude) praezisiert; der Wechsel `claude@` → `michael@` ist ausdruecklich ausgenommen.
  - Begleitend (ausserhalb dieses Repos, auf den Arbeitsrechnern): ein `PreToolUse`/`Bash`-Guard
    `~/.claude/hooks/swaks-require-signature.py` blockt hart die Kombination `--from`/`-f` = Michael
    **plus** `--no-sig`; bewusster Ausweg per Kommentar-Token `# SIG_GUARD_OK`. Nicht Teil des Skill-Repos,
    hier nur zur Nachvollziehbarkeit vermerkt.

### 1.32.0

- **`swos`: `vlan-set` auf CSS106 (`swos_lite`) freigegeben (CR4428).** Der in 1.30.0 bewusst
  offengelassene Fall — CSS106-VLAN-Membership ist ein Per-Port-Egress-Enum `prt`, kein
  Member-Bitmask — ist jetzt umgesetzt:
  - Neue Flags **`--tagged <ports>`** (→ `add if missing`/2) und **`--untagged <ports>`**
    (→ `always strip`/1); alle **nicht** genannten Ports → `not a member` (3). Deklarativ: setzt den
    kompletten Membership-Satz des VLANs (wie das Bitmask-`--members` die volle Maske). Die vierte
    Mode `leave as is` (0) ist ueber tagged/untagged bewusst **nicht** erreichbar.
  - `WRITE_FIELDS["swos_lite"]["vlan.b"]` bekommt `"egress": "prt"`; `cmd_vlan` verzweigt ueber
    `member` (Bitmask-Pfad css610/css326) vs. `egress` (CSS106). Die jeweils falschen Flags werden
    sauber abgewiesen (`--members` auf CSS106 / `--tagged` auf Bitmask-Dialekten), ebenso
    tagged∩untagged-Ueberschneidung und leere Auswahl.
  - Enum-Werte + Multi-VLAN-Struktur `{vid,ivl,igmp,prt[]}` aus **Live-HAR** `.193` (CSS106-1G-4P-1S)
    und `.204` (CSS106-5G-1S) + `engine.js` verifiziert, nicht geraten. `vlan-set`
    (neu-anlegen + aktualisieren, tagged/untagged) und `vlan-remove` **live an `.193`** mit
    Read-back bestaetigt (aendern → verify → restore). Damit ist der in 1.30.0 vermerkte offene Punkt
    „CSS106-`vlan.b`-Write live noch ungetestet" geschlossen.
- **`swos`: `speed` deckt jetzt auch SFP+-Ports ab (CR4428).** Das Forced-Speed-Enum ist
  **dialekt-spezifisch** und divergiert ab Index 4 — aus `engine.js` + Live-DAC verifiziert (nicht
  generisch): css326 `10M/100M/1G/10G/5G/2.5G/40G`, css610_new `10M/100M/1G/10G/200M/2.5G/5G` (10G=3
  in beiden). Neu `SPEED_ENUMS` je Dialekt; `cmd_speed` laesst SFP-Ports zu und prueft den Wert
  gegen das Dialekt-Enum (`--to` in Mbit/s, z.B. `2500`/`10000`). Kupfer-Subset 10/100/1000
  unveraendert. Live an **css610 SFP+1, css326 SFP1 UND CSS106 SFP (Port 6)** bestaetigt
  (`i05[8]`/`spdc[24]`/`spdc[5]` gesetzt → Read-back → restauriert). CSS106-SFP ist **1G-only**
  (SFP, kein SFP+; engine.js-Enum `[10,100,1000]`), Enum damit vollstaendig. Read-View dekodiert
  jetzt auch CSS106-Ist-Speed (`spd`).
  - **Bestaetigt das bekannte Leeres-Backup-Verhalten** (SKILL.md „Frisch nach Factory-Reset kein
    Write"): css326test lieferte `/backup.swb` erst leer (0 B) → Snapshot-Guard brach ab; nach einem
    einmaligen Backup im SwOS-UI liefert es Daten (0 B → 2847 B) und css326-Writes laufen normal.
    Also **kein** css326-Modelldefizit, sondern der noch nicht „scharf" gemachte Snapshot.
- **`swos`: `ports`-View zeigt PoE-Modus/-Status korrekt + Ist-Speed (CR4428).** Behebt drei
  Lese-Bugs, alle live verifiziert:
  - **PoE-Modus** aus dem **Config**-Feld statt Runtime: css610 `poe.b i01` (`off/on/auto`) statt
    faelschlich `i04`; CSS106 neu aus `link.b poe` (`off/auto/on/calibr`, vorher gar nicht angezeigt).
  - **PoE-Status** als eigene Angabe aus dem verifizierten Enum (`poe.b i04` / `link.b poes`:
    `waiting for load/powered on/overload/…`, engine.js). Falsches `POE_MODES`-Enum entfernt.
  - **Gating** auf PoE-faehige Ports (css610 1-8, CSS106 2-5) — SFP(+)/Uplink tragen kein PoE mehr.
  - **Ist-Speed** dekodiert (`spd`/`i08` ueber `SPEED_ENUMS`, Index ausserhalb = kein Link) — zeigt
    z.B. den DAC-Link als `10G`.
- **`swos`: Snapshot-Ablage cwd-robust (CR4428).** `_snapshot_once` legte den `.swb`-Snapshot in
  `os.getcwd()/.tmp` — bei Aufruf aus dem Skill-Verzeichnis landete er faelschlich in `$SKILL_DIR/.tmp`.
  Neues `_snapshot_dir()` mit Praezedenz `SWOS_SNAPSHOT_DIR` → `<cwd>/.tmp` → `~/.cache/swos` (Fallback,
  wenn cwd im Skill-Verzeichnis liegt) — schreibt nie mehr ins Skill-Verzeichnis.

### 1.31.0

- **`swaks`: Signatur-Auto-Resolve + `--no-sig`.** `build_mail.py` loest die Signatur jetzt selbst
  auf — projektlokal `.claude/swaks-signature.{txt,html}` (Vorrang) → global
  `~/.claude/swaks-signature.{txt,html}` → sonst keine (kein Fehler). Explizite
  `--sig-text-file`/`--sig-html-file` ueberschreiben weiterhin (ein **explizit** angegebener Pfad
  muss existieren); neues **`--no-sig`** schaltet auch die Standard-Signatur ab. Behebt den
  Footgun der alten Doku, die den relativen Pfad `.claude/swaks-signature.txt` als Beispiel vorgab
  → `FileNotFoundError`/Exit 1, wenn projektlokal keine Datei lag. SKILL.md: Beispielaufruf ohne
  `--sig-*`-Zeilen, Standard = global. Standard-Signaturen nach `~/.claude/` gelegt.

### 1.30.0

- **`swos`: CSS106-Reihe (`swos_lite`) beschreibbar (CR4428).** Stufe-2-Writes jetzt auch auf der
  CSS106-Reihe, nicht mehr nur css610_new/css326:
  - **`link.b`** (`en/nm/an/spdc/dpxc/fct`): portname, port-enable, autoneg, duplex, speed. Flow
    Control ist **ein** Feld `fct` (nicht `fctc/fctr` wie css326). Nur **1** SFP-Port (Port 6) →
    `speed` deckt Kupfer 1-5 ab (`SFP_PORTS`-Map, dialektabhaengig).
  - **`fwd.b`** (`vlan/vlni/dvid/fvid/vlnh`, Extra-Feld `vlnh`): vlan-mode (4-Werte, `strict`=3),
    vlan-receive, pvid, force-vlan-id.
  - **PoE-Out in `link.b`** (`poe`/`prio`), **nicht** `poe.b` (das gibt 303). Nur beim PoE-Modell
    `CSS106-1G-4P-1S` (engine.js `Z()`-Gate, Marker `-4P-`) → link.b-POST-Subset modellabhaengig
    (`post_poe`). Enum **`off/auto/on/calibr`** = 0/1/2/3 (≠ css610), gueltige Ports **2-5**
    (`O:1,P:5`). `poe-out`/`poe-voltage` loesen ihren Endpoint dialektabhaengig auf; **kein
    `poe-voltage`** auf CSS106 (kein Voltage-Level-Feld).
  - **`vlan-set` auf CSS106 bewusst nicht** freigegeben: Mitgliedschaft ist ein Per-Port-Egress-Enum
    `prt` (leave/strip/add/not-member), kein Member-Bitmask — ohne verifizierte Multi-VLAN-Referenz
    nicht ableitbar (nicht raten). `vlan-remove`/`vlan-clear` laufen generisch (`[vid,ivl,igmp,prt]`).
  - Feldnamen/Enums/POST-Reihenfolge aus `engine.js` (Tab-Definitionen) + Live-GET `.193`
    (CSS106-1G-4P-1S) / `.204` (CSS106-5G-1S) verifiziert, nie geraten. link.b/fwd.b/PoE live an
    `.193` bestaetigt (aendern → Read-back → Restore). CSS106-`vlan.b`-Write nur logisch abgeleitet
    (Sandbox-vlan.b leer).

### 1.29.0

- **Neuer Skill `mail-as-me`:** Entwirft und ueberarbeitet E-Mails im persoenlichen
  Schreibstil (Register, Anrede, Sign-off, Dialekt, Hedging) statt in generischem
  KI-Deutsch. Universelle Engine im Skill, pro-Person-Profil (Beispiel-Korpus +
  Stilregeln) unter `~/.claude/mail-as-me/<profil>/` (getrennt vom versionierten Skill).
- **`extract.py`:** liest `.eml`/`.mbox`/Maildir/Cyrus, strippt Zitat + Signatur,
  ignoriert Anhaenge, schlaegt je Mail Register (Domain→`register_map`) und Dialekt-Marker
  (Wortgrenzen-Regex, kein `eh`-in-`geehrter`-Fehlgriff) vor. `setup` = Auto-Extraktion
  + kurzes Interview (nur was Samples nicht hergeben: Sign-off-Sonderfaelle, Du/Sie,
  Dialekt, Domain→Register).
- **Subcommands** `setup`/`draft`/`rewrite`/`learn` (Feedback-Loop: Entwurf↔gesendet
  diffen, Korrekturen ins Profil). **Reuse statt Duplikat:** KI-Tell-Audit ueber
  `humanizer-de`, Versand ueber `swaks`.

### 1.28.1

- **Repo-Doku:** `CLAUDE.md` angelegt (Release-Workflow, „Neuer Skill → install.sh mitpflegen",
  Konsumenten-Seite, Umgang mit temporaeren Dateien).
- **`.gitignore`:** `.tmp/` ergaenzt; die getrackte SwOS-Sicherung
  `.tmp/swos-snapshot-css610test.swb` aus dem Tracking genommen (temporaere Arbeitsdateien
  gehoeren nie ins Repo — `.swb`-Backups enthalten zudem das Switch-Passwort im Klartext).

### 1.28.0

- **Neuer Skill `pushover`:** Push-Notifications von Claude Code / Loops / cron via
  `api.pushover.net` aufs Handy (iOS/Android/Desktop). stdlib-only Python, kein Server-Prozess,
  outbound-only. Kernbefehl `send` mit `--title`, `--priority -2..1` (Emergency=2 bewusst nicht),
  `--sound`, `--user`/`--device` (komma-faehig), `--url`/`--url-title`, `--html`|`--monospace`,
  `--ttl`, `--attachment` (Bild <=5 MB, multipart), `--silent`; Text via Arg/`--file`/STDIN.
- **Vorlagen `alert`/`recovery`/`digest`** (telegram-Paritaet, Emoji-Titel + `--host`-Fusszeile,
  sinnvolle Default-Prioritaeten 1/0/-1) plus `validate` (Token/User-Key + Geraeteliste) und
  `sounds`. `.env`: `PUSHOVER_TOKEN` (+ optional `PUSHOVER_USER`-Fallback/`PUSHOVER_DEVICE`/
  `PUSHOVER_CA_BUNDLE`). Limits (1024 Zeichen / 5 MB) werden vorab geprueft, Restkontingent aus
  den Response-Headern.
- **Empfaenger-Verzeichnis (Adressbuch):** `recipients add/list` mappt Alias-Namen auf Keys, sodass
  `--user kollege` statt eines 30-Zeichen-Keys genuegt (Aliase gewinnen, sonst wird der Wert als
  roher Key genommen). Default-Empfaenger ist der Alias `me`, `PUSHOVER_USER` nur noch Fallback. Ein
  Alias kann auch ein Delivery-Group-Key sein (ein `send` an alle). Datei `~/.pushover-recipients`
  (Discovery cwd → home, per `PUSHOVER_RECIPIENTS` ueberschreibbar), gitignored.

### 1.27.0

- **swos: css326-Schreibpfad (`link.b`/`fwd.b`/`vlan.b`) + Loeschweg `vlan-remove`/`vlan-clear`
  (CR4428).** Damit sind auf `css326` 10 der 12 Port-/VLAN-Schreibbefehle nutzbar (alles ausser
  PoE): `portname`, `port-enable`, `autoneg`, `duplex`, `speed`, `vlan-mode`, `vlan-receive`,
  `force-vlan-id`, `pvid`, `vlan-set`. `link.b`/`fwd.b` sprechen auf css326 **benannte** statt
  numerischer Keys (`en/nm/an/spdc/dpxc/fctc/fctr`, `vlan/vlni/dvid/fvid`), sind aber feldweise 1:1
  zu css610_new — aus HAR (`.214`) + `engine.js` verifiziert, nicht geraten. Die Feldnamen je
  Dialekt stehen in `WRITE_FIELDS`, die Kommandos loesen Rollen darueber auf.
- **`vlan-set` dialekt-faehig, plus neuer Loeschweg.** css326-VLAN-Eintraege tragen `{vid,nm,piso,
  lrn,mrr,igmp,mbr}` statt css610 `{i01,i03,i02}`; Falle: die GET-Reihenfolge weicht von der
  POST-Reihenfolge ab, daher wird jeder Eintrag in die kanonische `order` serialisiert. Neu:
  `vlan-remove --vid N` (entfernt einen Eintrag, Rest feldtreu) und `vlan-clear` (`vlan.b = []`),
  beide dialekt-generisch mit Read-back-Verify.
- **Hart erkaufte Lehre: Enums divergieren je Dialekt.** VLAN Mode ist auf css326
  `[disabled,optional,enabled,strict]` (`strict`=3), auf css610_new nur `[disabled,optional,strict]`
  (`strict`=2). `VLANMODE_BY_DIALECT` haelt beide; jeder Enum-Wert wird gegen den erkannten Dialekt
  validiert.
- **Frisch nach Factory-Reset kein Write moeglich** (bewusst so): SwOS liefert `/backup.swb`
  unmittelbar nach einem Reset leer (0 Byte), bis zum ersten Config-Write. Der Snapshot-Once findet
  dann kein Rollback-Netz und bricht ab (dialektunabhaengig auf CSS610/.215 + CSS326/.214 verifiziert).
  Konsequenz: zuerst eine Aenderung ueber die Web-UI setzen (z. B. Identity), danach greift der
  Tool-Schreibpfad. Live an `.214`/`.215` verifiziert.

### 1.26.6

- **swos: die restlichen `fwd.b`-VLAN-Port-Felder als Schreibbefehle — `vlan-mode` (i15),
  `vlan-receive` (i17), `force-vlan-id` (i19) (CR4426).**
  `swos vlan-mode <sw> --port <n> --to disabled|optional|strict`,
  `swos vlan-receive … --to any|tagged|untagged`,
  `swos force-vlan-id … --to on|off` (jeweils `[--force] [--commit]`). Werte aus `engine.js`
  (`i15 u:[disabled,optional,strict]`, `i17 u:[any,only tagged,only untagged]`, `i19 t:D`
  Per-Port-Bitmaske). Gemeinsamer `fwd.b`-Enum-Helfer (`_fwd_enum_write`) plus Bitmasken-Variante
  für `force-vlan-id`; alle drei mit **Link-/Lockout-Schutz** (Änderung an Port mit aktivem Link
  nur mit `--force`, da VLAN-Filterung den Zugriff kappen kann). Live an `.215` verifiziert (Ports
  3/5/7 einzeln + permutiert gegen die UI gegengeprüft). Damit sind alle vier `fwd.b`-Portfelder
  schreibbar (i15/i17/i18=PVID/i19). Zwölf Schreibbefehle gesamt.

### 1.26.5

- **swos: neunter Schreibbefehl `speed` (link.b i05, Forced Speed je Kupferport) — Enum aus der
  UI verifiziert (CR4426).** `swos speed <sw> --port 1..8 --to 10|100|1000 [--force] [--commit]`.
  Die Index→Speed-Enum (`engine.js` `a=[]`, dynamisch je Port) wurde per DevTools-Capture +
  Nutzerangabe der Dropdown-Werte geklärt: `0`=10, `1`=100, `2`=1000 Mbit/s (Kupferports; SFP+ 9/10
  haben andere Werte → abgelehnt). Wirkt nur bei Auto-Neg=off; der Dry-Run weist darauf hin, wenn
  Auto-Neg für den Port noch on ist. Link-/Lockout-Guard wie bei den übrigen link.b-Writes
  (Änderung an Port mit aktivem Link nur mit `--force`). Live an `.215` verifiziert (Port 7
  1000→100→1000; zyklische Permutation der Ports 3/5/7 gegen die UI gegengeprüft).

### 1.26.4

- **swos: `autoneg` (link.b i02) + `duplex` (link.b i03) — Auto Negotiation & Full Duplex je Port
  (CR4426).** `swos autoneg|duplex <sw> --port <n> --to on|off [--force] [--commit]`. Beide sind
  Bitmasken-Writes wie `port-enable`; die drei link.b-Bitmaskenfelder (i01 Enabled / i02 Auto-Neg /
  i03 Full-Duplex) teilen jetzt einen gemeinsamen Helfer `_link_bit_write` mit **Link-/Lockout-
  Schutz**: eine tatsächliche Änderung an einem Port mit aktivem Link (`i06`) verlangt `--force`
  (Enable/Auto-Neg/Duplex-Änderungen können den Link stören). Live an `.215` verifiziert (autoneg
  Port7 off→`i02=0x3bf`→on; duplex Port7 on→`i03=0x7f`→off; Guard greift an Port 2 mit Link).
  **Speed** (link.b i05) bleibt bewusst offen: Index→Speed-Enum ist in `engine.js` dynamisch je Port
  befüllt und nur bei Auto-Neg=off wirksam — erst nach Capture der Dropdown-Werte, nicht geraten.

### 1.26.3

- **swos: sechster Schreibbefehl `port-enable` (link.b i01, „Enabled" je Port) mit Lockout-Schutz
  (CR4426).** `swos port-enable <sw> --port <n> --to on|off [--force] [--commit]` setzt/löscht das
  Enabled-Bit eines Ports in der `link.b`-Bitmaske `i01`. **Lockout-Schutz:** einen Port mit
  aktivem Link (`i06`) zu deaktivieren verlangt `--force` (sonst Abbruch — er könnte den Mgmt-/
  Uplink-Verkehr tragen); Aktivieren ist immer erlaubt, der Dry-Run zeigt die Vorschau auch ohne
  `--force`. Live an `.215` verifiziert (Port 7 off → Read-back `i01=0x3bf` → wieder on → `0x3ff`),
  byte-aligned Hex greift auch hier. Gleiche Guard-Rails wie die übrigen Writes.

### 1.26.2

- **swos: `link.b`/`fwd.b`/`vlan.b`-Writes entsperrt — Ursache des Enabled-Vorfalls gefunden
  (byte-aligned Hex) + `portname`/`pvid`/`vlan-set` zurückgeholt (CR4426).** Root-Cause des
  früheren Vorfalls (ein `link.b`-Write warf die Enabled-Maske auf Ports 1–6 zurück): `_blob_hex`
  serialisierte Werte mit **ungerader** Hex-Breite (`0x3ff`), der SwOS-Parser liest Hex aber
  **bytewise** und interpretierte `0x3ff` als `0x3f` (=63). Fix: byte-aligned (gerade Breite,
  `0x03ff`) wie die SwOS-Web-UI; kontrolliert an `.215` nachgewiesen (Enabled bleibt `0x3ff`,
  nur das Zielfeld ändert sich). `poe.b` war nie betroffen (Werte 0–7 ohnehin 2-stellig). Damit
  sind die drei zurückgestellten Befehle wieder da und live verifiziert: `portname` (link.b i0a),
  `pvid` (fwd.b i18, Default VLAN ID), `vlan-set` (vlan.b Member-Bitmask, legt VLAN an falls neu) —
  jeweils ändern → Read-back → Restore getestet. Gleiche Guard-Rails (writable-Flag, `--dry-run`-
  Default, Snapshot, Read-back-Verify, css610_new/direct). **Weiterhin zurückgestellt:**
  `poe-priority` (Rang/Permutation statt Skalar). SKILL.md-Schreib-Sektion überarbeitet
  (fünf Befehle + zwei Kern-Lehren: byte-aligned Hex; Config-Basis ist der GET, nie der `.swb`).

### 1.26.1

- **swos: zweiter Schreibbefehl `poe-voltage` (poe.b i03) + gemeinsame Write-Basis + harte
  Sicherheits-Lehren aus dem Live-Test (CR4426).** `swos poe-voltage <sw> --port <n> --to
  auto|low|high [--commit]` setzt das PoE „Voltage Level" (`engine.js` `i03 u:[auto,low,high]`).
  Der Write-Pfad wurde auf eine gemeinsame Basis refaktoriert (generischer Blob-Serializer,
  `_write_guard`/`_post_subset`/`_commit_write`, Read-back-Verify) — `poe-out` und `poe-voltage`
  teilen sie, beide live an `.215` verifiziert (Ändern + Read-back + Restore). **Bewusst NICHT
  ausgeliefert** (Format zwar aus einem vollständigen HAR verifiziert, aber der Read-back-Verify
  hat beim Live-Test echte Probleme abgefangen): `poe-priority` — PoE-Priority ist ein **eindeutiger
  Rang/Permutation**, kein Skalar je Port (Switch schichtet um); `portname`/`pvid`/`vlan-set` —
  ein `link.b`-Testwrite hat die **Enabled-Maske umgeworfen** (Ports deaktiviert). **Zentrale
  Lehre, jetzt dokumentiert:** Config-Basis für Writes ist **immer der Live-GET** (nachweislich
  config-treu, Feld-für-Feld deckungsgleich mit der SwOS-Web-UI), **niemals** der `.swb`-Parser
  (lieferte falsche Bitmasken `0x37f/0x3ff` statt `0x37/0x3f`, was einen Fix-POST scheitern ließ).
  Diese vier Befehle kehren erst nach kontrolliertem Nachweis ihres Write-Nebeneffekts zurück.
  Inventory-`writable`-Flag, `--dry-run`-Default, Snapshot-once und Nur-`css610_new`/`direct`
  gelten unverändert. SKILL.md-Schreib-Sektion überarbeitet.

### 1.26.0

- **swos: erster Schreibbefehl `poe-out` (Stufe 2) — PoE Out je Port setzen, Format verifiziert
  statt geraten.** `swos poe-out <switch> --port <n> --to off|on|auto [--commit]`. Das POST-Format
  wurde per Browser-DevTools-Capture an `.215` (CSS610, `css610_new`) plus der `engine.js`-Feldtabelle
  hart abgeleitet, nicht geraten: `POST /poe.b`, `Content-Type: text/plain`, Body als **roher Teil-Blob**
  `{i01,i02,i03,i0a}` mit 8 Kupferport-Elementen (keine SFP/Runtime-Felder). Feldsemantik aus `engine.js`:
  `i01`=**PoE Out** (`u:[off,on,auto]` → `0/1/2`), `i02`=PoE Priority, `i03`=Voltage Level, `i0a`=global.
  **Wichtig:** der Config-Modus steht in `i01` — der bisherige read-only `ports`-View liest faelschlich
  `i04` (= Runtime-Status), das bleibt ein offener Read-only-Bug. **Guard-Rails:** Inventory-Flag
  `"writable": true` ist Pflicht (nur die 3 Buero-Sandkasten-Switches; Seiersberg bleibt read-only);
  `--dry-run` ist Default (zeigt Ist-/Soll-`i01` + exakten POST-Body, sendet nichts), erst `--commit`
  postet; vor der **ersten** Aenderung zieht das Tool automatisch einen `.swb`-Snapshot nach `.tmp/`
  als Rollback-Punkt; nach jedem Commit **Read-back-Verify** (nur `i01[port]` darf sich geaendert haben,
  sonst Abbruch mit Snapshot-Hinweis); Write bisher nur `css610_new` (andere Dialekte abgelehnt, bis
  separat gecaptured), nur `direct`-Transport (nicht ssh-curl). Live gegen `css610test` (.215)
  verifiziert: Port 8 `on`→`auto` zurueckgesetzt, Read-back + unabhaengige Gegenprobe bestaetigt. (CR4426)

### 1.25.3

- **swos: Dialekt-Bug gefixt — `.swb`-Backups verlieren nicht mehr die echten Portnamen.**
  `.swb`-Backups jeder CSS610-Generation tragen in `sys.b` sowohl `F`- als auch `J`-Keys, egal ob
  das Geraet live `css610_new` oder `css610_old` meldet — `detect_dialect()` erkennt Backups
  deshalb immer als `css610_old`. VLAN/PVID/PoE waren davon nicht betroffen (korrekt unter den
  `css610_old`-Buchstaben-Keys dekodiert), aber `portnames` stand faelschlich auf `None` und fiel
  immer auf die generischen `ether1..8`/`SFP+1/2`-Fallbacks zurueck, obwohl `link.b` unter Key `K`
  die echten Namen (`Port1..8`/`SFP+1`/`SFP+2`) enthaelt. Fix: `css610_old.portnames = "K"`.
  Gegenprobe an zwei unabhaengigen `.swb`-Quellen: dem echten Alt-FW-Fixture `swvspoe1.swb`
  (site1-Nightly) und einem frischen Neu-FW-Backup von `swbs02poe` (CR4369, per `backup`
  gezogen) — beide liefern jetzt die realen Portnamen. Modell/Version/MAC/Serial bleiben `?`:
  das ist keine Dialekt-Verwechslung mehr, sondern fehlt in **beiden** Referenz-Backups
  gleichermassen und damit vermutlich grundsaetzlich im `.swb`-Format (Config-Backup ohne
  Identitaets-/Hardware-Daten) — dokumentiert statt geraten.

### 1.25.2

- **swos: neuer Subcommand `backup` (Live-Backup ziehen, GET `/backup.swb`).** Referenz-Fund:
  `/root/bin/swos-backup.sh` auf `gatekeeper.example.com` zeigte den bisher unbekannten
  Backup-Endpoint (Digest-Auth, gleiches Passwort wie die `.b`-Endpoints), der denselben
  `.swb`-Container liefert wie der SwOS-Web-UI-Backup-Knopf und den `--swb` bereits offline
  dekodiert. Roher Byte-Dump (keine Blob-Parse) ueber `direct`/`ssh-curl`; funktioniert mit
  Inventory-Namen, `--ip/--mode` oder Ad-hoc-Zielen, nicht mit `--swb`. Bleibt Stufe 1
  (read-only) — reines GET, keine Config-Aenderung am Switch. Live gegen `swbs02poe` (CSS610,
  CR4369) verifiziert: bytegenau identisch zum manuellen curl-Download. **Nebenbefund
  dokumentiert, nicht gefixt:** ein frisches `.swb` desselben Switches wird vom bestehenden
  Dialekt-Detector faelschlich als `css610_old` statt `css610_new` erkannt (Backup-`sys.b`
  traegt sowohl `F`- als auch `J`-Keys) — Modell/Version/MAC/Serial/Portnamen fallen dann auf
  Fallback-Werte zurueck, VLAN/PVID/PoE bleiben korrekt. Neue Erkenntnis (Backup-Passwort
  hex-kodiert in `.pwd.b`) zusaetzlich in `reference_swos_lite_endpoints`-Memory festgehalten.

### 1.25.1

- **humanizer-de: zwei neue Leitplanken fuer explizite Nutzer-Stilvorgaben.** (1) Hat der Nutzer hinterlegt, dass er generell (ausser in Word) keine echten Gedankenstriche verwendet, geht das der Standard-Cluster-Regel vor: `—`/`–` werden dann durchgaengig durch den einfachen Bindestrich `-` ersetzt, ohne Satzumbau. (2) Nutzerspezifische Stilpraeferenzen jenseits der Muster-Kataloge (z. B. keine erklaerenden Nebensaetze fuer Offensichtliches, sparsames Bold in Aufzaehlungen, kurze sachliche Ueberschriften) werden auf Wunsch angewendet, auch wenn Preflight/Lint dafuer kein Muster findet — solche expliziten Vorgaben stehen ueber der reinen Cluster-Regel. Anlass: Abgleich eines E-Mail-Entwurfs mit der vom Nutzer final versendeten Fassung (CR4369) zeigte genau diese beiden Abweichungen, obwohl der Preflight-Audit selbst „low risk" meldete. Reiner SKILL.md-Doku-Change, keine Script-Aenderung.

### 1.25.0

- **kanboard: `search` findet Text auch in Beschreibung/Kommentar (`--anywhere` / `--in`) + Doku der Feld-Filter.** Kanboards `searchTasks` matcht ein **unqualifiziertes** Stichwort nur gegen den **Titel** — steht der String nur in Beschreibung oder Kommentar, lieferte `search "printsrv"` faelschlich nichts (real erlebt: der Pfad `Print_and_Follow` in der Beschreibung von CR4271 blieb ueber bloße Wortsuche unauffindbar, obwohl Kanboard `description:`/`comment:` nativ, case-insensitiv und als Teilstring durchsucht). Neu: `--anywhere` (Kurzform fuer `--in title,description,comment`) und `--in <felder>` behandeln die `query` als reinen Begriff, wickeln sie in jeden Feld-Filter (Phrasen mit Leerzeichen werden gequotet) und unionieren die Treffer nach `id`; jeder Treffer bekommt `matched_in` (Liste der Fundfelder). Der klassische Query-Modus (Operatoren `status:`/`assignee:`/`title:` …) bleibt unveraendert. SKILL.md-Abschnitt „Tasks suchen" um die Titel-Falle, die nativen Feld-Filter (`title:`/`description:`/`comment:`), die AND/ODER-Semantik (verschiedene Felder = UND, gleiches Feld doppelt = ODER) und die neuen Flags erweitert. Live gegen die azedo-Instanz verifiziert.
- **install.sh: `Edit(...)`- statt `Write(...)`-Permissions (+ Alt-Regeln aufraeumen).** Claude Code matcht `Write(path)`-Allow-Regeln nicht mehr — nur `Edit(path)` deckt die datei-schreibenden Tools ab —, weshalb `install.sh` bei jedem Update (der post-merge/post-rewrite-Hook ruft es nach jedem `git pull`) vier „Write(...) is not matched … use Edit(...) instead"-Warnungen ausloeste. `install.sh` traegt jetzt `Edit(~/.claude/azedo-skills/**)` bzw. `Edit(~/.claude/skills/**)` (je HOME-absolut und `~`) ein **und entfernt** die frueher gesetzten `Write(...)`-Altregeln fuer dieselben Pfade aus `permissions.allow` (fremde Regeln bleiben unberuehrt, idempotent). Ein einziger `git pull` heilt beide Maschinen selbst, da der Hook danach die neue `install.sh` faehrt. Auch der python3-Fallback-Hinweis nennt jetzt `Edit(...)`.

### 1.24.0

- **Neuer Skill `swos` (MikroTik SwOS read-only Abfrage).** Python-Script (stdlib only, `urllib` HTTP-Digest, kein `requests`), lauffaehig auf FreeBSD und Linux. **Ein Decoder, drei Transporte:** `direct` (urllib direkt auf die Switch-IP), `ssh-curl` (curl --digest auf einem Jump-Host — Passwoerter mit `$` werden korrekt via STDIN-Pipe an `sh` behandelt, kein `!`-Escaping noetig) und `swb` (offline aus `.swb`-Backup via `strings`). Dekodiert die SwOS-Blobs (kein valides JSON: unquoted Keys, Hex-Ints, Single-Quote-Hex-Strings) mit einem recursive-descent-Parser in lesbare Tabellen: `sys` (Modell/IP/MAC/Serial/Temp), `vlan` (Mitglieder), `ports` (PVID + PoE-Modus), `hosts` (FDB MAC→Port), `all`, `raw`. **Vier Feld-Dialekte autodetektiert** (`css326`, `css610_new`, `css610_old`, `swos_lite`) — Detektion an charakteristischen Keys, nicht am ersten sys.b-Key (Live-Reihenfolge weicht vom Backup ab). Gegenueber dem urspruenglichen `.swb`-Parser drei Bugs vermieden: VLAN-Namen werden pro Geraet aus `vlan.b nm` gelesen (nicht hardcoded), Modell aus `brd`/`i07` (nicht aus dem Dialekt geraten), und per-Endpoint-Parsing statt Whole-Text-Regex (keine Kreuzkontamination von `fwd.b`-`{B:,C:}` in die VLAN-Liste — der Original-Parser meldete dadurch eine Phantom-VLAN 1022). Inventory-Config `inventory.json` (gitignored) mit Credential-Refs (`password`/`password_env`/`password_file`) und Modus/Jump je Switch; `inventory.example.json` als Vorlage. read-only (Stufe 1); Schreibzugriff (Stufe 2) erst nach `engine.js`-Verifikation. Live verifiziert an 3 Buero-Switches (direct: CSS610/CSS326/CSS106) und site1 (ssh-curl via gatekeeper), Decoder-Gegenprobe Live == `.swb` identisch. `install.sh`-Liste ergaenzt. (CR4426)

### 1.23.1

- **kimai: Shortcut-Lookup findet `.claude/kimai-shortcuts.json` jetzt per Aufwaertssuche.** Bisher wurde die Datei nur unter `os.getcwd()/.claude/` gesucht; lief `kimai` aus einem Unterverzeichnis (z.B. `.tmp/`), kam `load_shortcuts()` leer zurueck und `log --shortcut <key>` scheiterte mit „shortcut not found" (obwohl der Key existiert). Neu: `_find_shortcuts_file()` laeuft die Elternverzeichnisse hoch bis `.claude/kimai-shortcuts.json` gefunden wird (analog git/.git), sodass der Lookup aus jedem Projekt-Unterverzeichnis funktioniert. Die `.env`-Config hatte bereits einen `~/.env`-Fallback. (CR4369)

### 1.23.0

- **Neuer Skill `telegram` (Telegram-Bot, outbound-first).** Python-Script (stdlib only, `urllib`, kein `requests`), lauffaehig auf macOS **und** FreeBSD, **kein Server-Prozess** — jeder Aufruf ein einzelner HTTPS-Call an `api.telegram.org` (auch aus cron). Kernbefehl `send` (sendMessage; Text aus Argument/`--file`/STDIN, `--parse-mode` Default Klartext, `--silent`, `--no-preview`, `--json`), Monitoring-Vorlagen `alert`/`recovery`/`digest` (HTML + Emoji, dynamische Werte HTML-geescaped), Setup-Helfer `setup` (chat_id via `getUpdates`, optional `--write` in die .env) und `me` (getMe/Token-Check). **Interaktiver Empfang** `wait` (blockiert einmalig per Long-Poll bis eine Nachricht kommt, gibt den Text aus; Exit 2 = Timeout) und `ask` (Frage senden **und** auf die Antwort warten) — beide drainen den Backlog vorab (nur Nachrichten NACH Start zaehlen) und akzeptieren per Default nur den eigenen Chat; damit kann Claude Code auf eine Telegram-Anweisung warten und danach handeln. Zusaetzlich Dauer-Empfang als Scaffold: `get-updates` (roh) und `poll` (Long-Poll im Vordergrund, fuehrt `offset` mit, loest vorab `deleteWebhook`) — kein Daemon, reine Ausbaubasis. Credentials in `.env` (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`; Auffindung wie kimai/kanboard, Env-Variablen haben Vorrang), FreeBSD-TLS-Escape-Hatch `TELEGRAM_CA_BUNDLE`. `install.sh`-Liste ergaenzt. (CR4420)

### 1.22.4

- **mainwp: Hinweis zum Auslesen des Sync-Status (Ausgabe nicht tailen).** Beim `sync-sites-v1` schlagen einzelne Sites oft fehl; das Script aggregiert ueber alle Batches und liefert `total_synced`/`total_errors` sowie `errors[]` (mit `identifier`, `code`, `message`). Diese Summen stehen **oben** im JSON, vor dem langen `synced`-Array — `| tail -N` schneidet sie ab. SKILL.md-Abschnitt „Alle Sites syncen" um eine Warnung plus fertiges Auswerte-Snippet ergaenzt (Ausgabe in Datei, stderr getrennt, dann `total_errors`/`errors[]` gezielt ausgeben).

### 1.22.3

- **wp-sync-dev: Scope-Grenze Host-Dateizugriff vs. Jail-Laufzeit klargestellt.** Der Skill beschrieb die DEV-Pfade als host-seitig (korrekt fuer rsync/chmod), sagte aber nicht, dass die DEV-Umgebung ein iocage-Jail ist und alles Laufzeitartige (`wp`-CLI, WordPress) **im Jail** laufen muss (`iocage exec <dev-jail> … sudo -u www wp …`). Fuehrte in dieser Session zur Fehlannahme, `wp` liefe direkt auf dem Jail-Host (`command not found`). DEV-Abschnitt umbenannt + Notiz mit Verweis auf Skill `wp-cli` / Wiki `wp-cli-in-jails` / Server-Entity des DEV-Hosts.

### 1.22.2

- **wp-nf: Export-Snippet faengt Schreibfehler ab.** `nf-export-form.php` pruefte den Rueckgabewert von `file_put_contents()` nicht und meldete „OK … Bytes" auch dann, wenn die Datei gar nicht geschrieben wurde (aufgefallen beim Live-Test auf DEV, als `wp` als `www` nicht ins Jail-`/tmp` schreiben durfte). Jetzt: bei `false` Abbruch mit Fehlermeldung und Exit 1. §5-Write und §8-Import wurden dabei end-to-end gegen NF 3.14.9 verifiziert (Export→Import→`element_class`-Write→Cache-Rebuild, Meta↔Cache konsistent). (CR4409)

### 1.22.1

- **wp-cli: Hinweis auf plugin-eigene CLI-Befehle (Cross-Link zu `wp-nf`).** Kurze Notiz unter der Plugins-Quick-Reference: manche Plugins registrieren eigene WP-CLI-Subcommands; Ninja Forms bringt `wp ninja-forms` mit, Details (Settings/`element_class`/Export/Import) deckt der Skill `wp-nf` ab. (CR4409)

### 1.22.0

- **Neuer Skill `wp-nf` (Ninja-Forms-Administration).** Reiner Referenz-Skill (nur SKILL.md, PHP-Snippets fuer `wp eval-file` im FreeBSD-Jail), verifiziert am Plugin-Quellcode von **Ninja Forms 3.14.8** auf apache1.acme.com. Anlass: das bei CR4266 (Kundenprojekt, GA4-CSS-Click-Events) entstandene, bisher nur im Handoff lebende NF-Wissen reproduzierbar kodieren. Inhalt: Datenmodell + Footguns (`element_class` liegt in `nf3_field_meta`, **keine** `settings`-Spalte in 3.14.8 — die aeltere Annahme ist damit widerlegt; Render-Quelle ist der Form-Cache `nf3_upgrades`, `WPN_Helper::use_cache()` liefert hart `true`), Formulare auflisten + Titel→ID-Mapping, Felder+Settings dumpen (Model-API), `element_class`-Write nach dem Muster Backup→Write→**Cache invalidieren**→Verify, **Export/Import** (`.nff`, Backend-identisch, ueber `export_form()`/`import_form()`; Import legt immer ein neues Formular an), Settings-Preflight (Meta↔Cache-Drift), Diagnose-Muster PYS-CSS-Click ↔ `element_class`, sowie eine Uebersicht der nativen `wp ninja-forms`-Extension und ihrer Grenzen (kein Export/Import, keine Settings-Details). `install.sh`-Liste ergaenzt. (CR4409)
- **wp-pys: NF-ID-Wissen nach `wp-nf` migriert.** Abschnitt „3.8 Ninja-Form-IDs ermitteln" enthielt das Roh-Snippet zur Formular-Auflistung; das gesamte NF-Datenmodell gehoert nun in den neuen Skill `wp-nf`. `wp-pys` verweist jetzt nur noch darauf (Titel-Mapping-Prinzip + Cross-Link) und ergaenzt den reziproken Hinweis, dass `css_click` auch an der NF-Feld-Klasse `element_class` haengt. Keine Duplizierung mehr zwischen den beiden Skills. (CR4409)

### 1.21.0

- **kanboard: `cr` laedt den Task-Inhalt vollstaendig.** Der `cr`-Kontext hat bisher die **Beschreibung verworfen** (Whitelist ohne `description`) — bei leerem Handoff sah ein voller Task faelschlich leer aus (Anlass: CR4377, dessen Kostenanalyse komplett in der Beschreibung stand und uebersehen wurde). `cr` liefert jetzt: `description` (immer, Volltext), `modified` (Aenderungszeitpunkt lesbar), `tags` inkl. herausgehobenem `kimai`-Feld, sowie `comments`/`attachments`-Zaehler (nur > 0). Description und Handoff sind bewusst beide dabei (Aufgabe vs. Uebergabestand). Kommentar-Volltext, Teilaufgaben, Task-Links und Anhang-Details bleiben eigene Befehle. Nebenbei schlanker: der in `cr` ungenutzte Swimlane-RPC entfaellt, `project_name` kommt aus dem `instance.json`-Cache. Feldauswahl in der SKILL.md dokumentiert. (CR4411)
- **kanboard: Tags + Kimai-Verknuepfung.** Neue Subcommands `get-tags`, `set-tags` (ersetzt alle), `add-tag`/`remove-tag` (read-merge-write, ohne Clobbern) und `set-kimai <task_id> --shortcut <key>`. Ein Tag `kimai:<shortcut>` verknuepft den Task mit einem Kimai-Shortcut (`.claude/kimai-shortcuts.json`); `cr` hebt ihn als Feld `kimai` heraus. Write-back-Regel dokumentiert (kanboard- **und** kimai-SKILL.md): nach einer Kimai-Buchung unter aktivem CR wird der Shortcut automatisch am Task getaggt, sodass er beim naechsten `cr` bereitsteht. Genau ein Kimai-Shortcut pro Task (`set-kimai` ersetzt einen vorhandenen). (CR4411)
- **kanboard: `list-tasks`-Bugfix.** `getAllTasks` liefert `column_name`/`owner_username` **nicht** mit — beide waren in jeder Auflistung leer. Werden jetzt aus `column_id` (via `getColumns`) bzw. `owner_id` (via `instance.json`) aufgeloest; `date_due` wird lesbar formatiert. (CR4411)
- **kanboard: `search` + `my-tasks`.** `search "<text>" [--project] [--all]` findet Tasks per Stichwort/Query projektuebergreifend (nutzt `searchTasks`, versteht UI-Operatoren wie `status:open`/`assignee:…`; Default nur offene Tasks). `my-tasks [--user]` listet offene Tasks eines Users (Default `default_user`) ueber alle Projekte. Beide ziehen Spalte/Owner direkt aus `searchTasks` (keine Extra-Lookups). (CR4415)
- **kanboard: `create-task` faellt ohne `--owner` auf `default_user` zurueck** (wie `add-comment`) — neue Tasks landen standardmaessig beim eingestellten User statt unassigned; ist kein `default_user` gesetzt, bleibt der Task ohne Zuweisung.
- **kanboard: internes Refactoring.** `rpc_call`/`rpc_try` teilten ~40 Zeilen Duplikat (Payload/Auth/HTTP/JSON-Parse) und wurden auf einen gemeinsamen Kern `_rpc(method, params, strict)` zusammengefuehrt — `strict=True` exit-on-error, `strict=False` liefert `None`. Kein Verhaltenswechsel. Ausserdem neuer `format_ts()`-Helper fuer lesbare Zeitstempel. (CR4416)

### 1.20.1

- **google-search-console: schreibende Sitemap-Operationen `submit-sitemap`/`delete-sitemap`.** Der Skill war bisher rein lesend (Scope `webmasters.readonly`). Neu: `submit-sitemap <-S siteUrl> <feedpath>` (`PUT`) und `delete-sitemap <-S siteUrl> <feedpath>` (`DELETE`). Der Scope wird jetzt **pro Subcommand** gewaehlt — lesende Befehle behalten `webmasters.readonly`, nur die beiden Schreib-Befehle fordern `webmasters` an (Token-Cache pro Scope). Schreib-Endpoint liegt unter `www.googleapis.com/webmasters/v3` (nicht `searchconsole.googleapis.com`); `PUT`/`DELETE` liefern HTTP 204 ohne Body, was `api_call` jetzt abfaengt (leerer Body → `{}`). `siteUrl` und `feedpath` werden voll URL-encodet. Absicherung: beide Befehle zeigen den Vorher-Zustand und fragen interaktiv `[y/N]`; `--yes`/`-y` ueberspringt, ohne TTY (Agent/Script) wird ohne `--yes` mit Exit 2 abgebrochen (kein versehentlicher Write). Verifiziert gegen `sc-domain:globex.com` (siteFullUser): idempotenter Re-Submit liefert HTTP 204 und aktualisiert `lastSubmitted`. Anlass: die in CR4400 noch per Ad-hoc-Script erledigten Sitemap-Writes reproduzierbar machen. (CR4408)

### 1.20.0

- **Neuer Skill `google-search-console` (GSC).** Read-only Datenabfrage der Google Search Console via Service Account (derselbe SA wie GA4, Scope `webmasters.readonly`). Python-Script (stdlib + `cryptography`, JWT-Flow 1:1 aus dem GA4-Skill uebernommen). Subcommands: `setup` (Auth testen, Sites cachen), `sites` (Properties + permissionLevel), `search-analytics` (Klicks/Impressionen/CTR/Position nach query/page/country/device/date/searchAppearance, Zeitraum + `dimension==value`-Filter; relative Datums-Keywords wie `28daysAgo` werden lokal auf ISO-Daten aufgeloest, da die GSC-API nur `YYYY-MM-DD` akzeptiert), `url-inspection` (echter Google-Index-Status je URL: verdict/coverageState/robots/lastCrawlTime/canonical), `sitemaps` (eingereichte Sitemaps + submitted/indexed URL-Zahlen). Trigger `/google-search-console`, `/gsc`. Anlass: empirischer Index-/Ranking-Nachweis fuer duenne Landingpages (CR4403, im Kontext CR4400). (CR4403)

### 1.19.3

- **kimai: `create-project`/`update-project` steuern jetzt `globalActivities`.** Neues Flag `--global-activities 0|1`. Bislang legte `create-project` Projekte implizit mit `globalActivities=false` an — dadurch waren instanzweite (globale) Aktivitaeten wie *IT-Support (SP90)* nicht buchbar und `create-timesheet` schlug mit `400 activity … invalid choice` fehl, was ein manueller Raw-API-PATCH nachziehen musste. `create-project` setzt jetzt **Default `1`** (globale Aktivitaeten erlaubt); `update-project` patcht das Feld nur bei explizitem Flag. (CR4397)

- **swaks: robuster Interpreter-Aufruf + Test-Mail-Footgun geschlossen.** `build_mail.py` wurde in SKILL.md und im Shebang von `python3.11` auf `python3` umgestellt — auf Maschinen ohne `python3.11` (z. B. mom mit `python3` 3.12) schlug der Aufruf sonst mit „command not found" fehl. Kritischer: Das bisher dokumentierte `build_mail.py | swaks --data @-` ist ein Footgun — schlägt der Bau fehl (Exit ≠ 0 oder Interpreter fehlt), läuft `swaks` trotzdem auf leerem STDIN und verschickt seine eingebaute **Default-Test-Mail** (genau so passiert). `set -o pipefail` verhindert das **nicht**, da `swaks` in der Pipe ohnehin startet. Der Standard-Ablauf baut die MIME-DATA jetzt erst in eine Datei und sendet per `&& test -s <datei> && swaks … --data @<datei>` — die `&&`-Kette stoppt vor `swaks`, sobald der Bau fehlschlägt oder die Datei leer ist. Verifiziert: erfolgreicher Bau erzeugt valide Multipart-MIME und passiert den Guard; fehlende Body-Datei (Exit 1) und `python3.11`-not-found (Exit 127, 0-Byte-Datei) stoppen die Kette beide vor `swaks`.

### 1.19.1

- **kanboard: `move-project` erhaelt jetzt den Offen/Geschlossen-Status.** `moveTaskToProject` oeffnet einen geschlossenen Task beim Projektwechsel automatisch wieder (is_active 0 → 1). `move-project` merkt sich den Status vor dem Move und schliesst einen zuvor geschlossenen Task danach wieder (`closeTask`), Rueckgabefeld `reclosed: true`. Ein reines Verschieben aendert damit den Erledigt-Status nicht mehr. Verifiziert: geschlossener Task bleibt nach dem Move geschlossen (richtige Spalte), offener Task bleibt offen.

### 1.19.0

- **kanboard: Projekt-Verwaltung — Projekte anlegen und Mitglieder/Rollen/Owner scriptbar.** Sechs neue Subcommands schliessen die Luecke, dass bisher nur Tasks, aber keine Projekte und keine Projekt-Rechte verwaltet werden konnten: `create-project --name <name> [--owner <username>]` (`createProject`; mit `--owner` wird der User Owner **und** `project-manager`-Mitglied), `list-project-users --project <p>` (`getProjectUsers` + `getProjectUserRole` je User, inkl. Owner), `add-project-user --project <p> --user <u> [--role <rolle>]` (`addProjectUser`, Default-Rolle `project-member`), `set-project-user-role` (`changeProjectUserRole`), `remove-project-user` (`removeProjectUser`) und `set-project-owner` (`updateProject`; ergaenzt den User bei Bedarf zuerst als Mitglied). Rollen validiert gegen `project-manager`/`project-member`/`project-viewer`. Damit ist „Projekt X anlegen, User Y mit gleicher Rolle wie in Projekt Z" ein Einzeiler statt Inline-Python. **API-Stolperfalle dokumentiert:** `updateProject` erwartet den Key `project_id` (nicht `id`) — mit `id` kommt „Missing argument: project_id", mit `name`/`id` ein stummes `False`; und ein Owner muss erst Projektmitglied sein, bevor er gesetzt werden kann. Verifiziert: alle sechs Subcommands live gegen die azedo-Instanz getestet (add/rollenwechsel/remove reversibel, Wegwerf-Projekt angelegt + wieder entfernt), Rollen-Validierung bricht bei ungueltiger Rolle mit Exit ≠ 0 ab.

### 1.18.2

- **swaks/build_mail.py: `--cc`/`--bcc` und Hart-Abbruch bei leerem Body.** `--cc` setzt einen sichtbaren `Cc:`-Header (Adresse zusätzlich in den swaks-Envelope `--to` aufnehmen). `--bcc` setzt **bewusst keinen** Header (sonst wären die Empfänger sichtbar) — die Adresse gehört nur in den swaks-Envelope; ein stderr-Hinweis erinnert daran. Neu: bricht mit Exit ≠ 0 ab, wenn Text *und* HTML leer sind (bzw. die Ausgabe leer wäre), damit swaks nie auf seine eingebaute Default-Test-Mail zurückfällt. SKILL.md um Cc/Bcc/Leer-Body-Hinweise ergänzt. (Enthält außerdem die zuvor lokal offene Multipart-Dokumentation zu `build_mail.py`.)

### 1.18.1

- **kanboard/handoff: robusteres Verhalten, wenn das TaskHandoff-Plugin fehlt.** Ist das Plugin auf der Kanboard-Instanz nicht installiert/aktiviert, liefern `set-handoff`/`get-handoff`/`remove-handoff` den JSON-RPC-Fehler `-32601` „Method not found". Der kanboard-Skill ergänzt bei diesem Code jetzt einen erklärenden Hinweis (Methode wird evtl. von einem nicht installierten Plugin bereitgestellt, z. B. TaskHandoff). Der handoff-Skill dokumentiert den Fallback: schlägt `set-handoff` mit `-32601` fehl, auf die lokale `.md`-Datei zurückfallen und den User informieren.

### 1.18.0

- **kanboard: Handoff-Feld pro Task (`set-handoff` / `get-handoff` / `remove-handoff`).** Ergaenzt das serverseitige Kanboard-Plugin **TaskHandoff** (eigenes Repo/Deployment), das pro Task ein Handoff-Dokument als Volltext-Markdown in einer aufklappbaren „Handoff"-Sektion der Task-Seite speichert (Spalte `content` als `LONGTEXT` — keine Laengengrenze, anders als Task-Metadata mit `VARCHAR(255)`; Bearbeiten per Modal wie „Aufgabe bearbeiten"). Drei neue Subcommands ueber die Plugin-JSON-RPC-Prozeduren `saveTaskHandoff`/`getTaskHandoff`/`removeTaskHandoff`: `set-handoff <task_id> (--file <pfad> | --value <text>)`, `get-handoff <task_id> [--output <pfad>]` (roher Markdown auf stdout oder in Datei), `remove-handoff <task_id>`. Ein Handoff pro Task (Upsert). Verifiziert: API-Round-Trip mit 24 KB Payload (inkl. Umlaute/Emoji) ohne Trunkierung, Skill-Subcommands live getestet. Der handoff-Skill nutzt die Kanboard-Ablage als bewusste **Alternative** zur lokalen `.md`-Datei (Default bleibt die Datei)

### 1.17.0

- **md2pdf-Skill aufgenommen.** Neuer Skill (SKILL.md + gebundeltes bash-Script `md2pdf`) rendert Markdown zu einem "schönen" PDF im Typora-nahen Look. Pipeline: `pandoc` → self-contained HTML (CSS + SVG inline) → headless Chrome `--print-to-pdf` — kein LaTeX nötig, weil Typora selbst über eine Browser-Engine rendert und Chrome praktisch denselben Look samt nativem SVG liefert. Cross-Platform generalisiert (macOS/Linux/FreeBSD): Chrome/Chromium-Discovery je OS mit `MD2PDF_CHROME`-Override, `--headless=new` mit Fallback auf `--headless`, auf Linux/FreeBSD `--no-sandbox --disable-dev-shm-usage` (root/Jail-tauglich), plattformübergreifender Font-Stack (Noto/DejaVu/Liberation). Mermaid-Blöcke (```mermaid) werden via `mmdc` zu SVG gerendert (Puppeteer-Config mit `--no-sandbox` automatisch übergeben); fehlt `mmdc`, bleibt der Block als Code und es gibt eine Warnung (graceful degradation). Optionen `--css <file>` und `--no-mermaid`. `install.sh`-Liste ergänzt

### 1.16.2

- **wp-cli: expliziter Negativ-Hinweis „nie `--allow-root`".** Der Skill zeigte durchgaengig das `sudo -u <wwwuser>`-Muster, sagte aber nirgends ausdruecklich, dass WP-CLI **nicht** als root laufen darf. Warnkasten in Abschnitt „1. Zugriff auf WordPress in Jails" ergaenzt: `--allow-root` vermeiden — triggert u. a. den WPML/WP_Filesystem-FTP-Fatal; immer `sudo -u <wwwuser>`

### 1.16.1

- **handoff + kanboard: aktiver CR-Kontext wird ins Handoff uebernommen.** Ist beim Erstellen eines Uebergabedokuments ein Kanboard-Task als CR-Kontext aktiv (`/kanboard cr <id>`), legt der handoff-Skill jetzt einen eigenen Abschnitt „Aktiver CR-Kontext" an (CR-ID, Titel, Task-URL, aktuelle Spalte/Status; konventionsbasiert aus dem Session-Stand, keine Live-Abfrage) und nimmt `kanboard` in die empfohlenen Skills auf. Der kanboard-Skill verweist im Abschnitt „CR-Kontext" gegenlaeufig darauf. Damit weiss der naechste Agent, an welchem Task gearbeitet wird, und kann ihn mit `/kanboard cr <id>` wiederherstellen
- **install.sh: alte Skill-Verzeichnisse werden beim Update ersetzt.** Bisher uebersprang `install.sh` jeden Skill, dessen Ziel unter `~/.claude/skills/` bereits existierte — eine alte lokale Kopie (echtes Verzeichnis, z.B. das fruehere `handoff/`) blieb so nach einem `git pull` bestehen. Jetzt: bestehende Symlinks werden aufs aktuelle Repo-Ziel umgesetzt; ein echtes Verzeichnis/Datei, das einen Repo-Skill schattet, wird nach `<skill>.pre-azedo-skills` gesichert und durch den Symlink ersetzt (nicht geloescht)

### 1.16.0

- **handoff-Skill aufgenommen.** Reiner Referenz-Skill (nur SKILL.md, kein Script) zum Erstellen von Uebergabedokumenten. Vendorisierter, angepasster Fork von [mattpocock/skills](https://github.com/mattpocock/skills/tree/main/skills/productivity/handoff) @ `386d4ff` (MIT (c) 2026 Matt Pocock, `LICENSE` mitgefuehrt). azedo-Anpassungen gegenueber dem Upstream: Uebersetzung ins Deutsche, Ablage im Projektverzeichnis (`docs/`/Projektstamm) statt OS-Temp, Abschnitt „Einlesen eines bestehenden Handoff-Dokuments", `disable-model-invocation` entfernt. **Neu:** Dateinamens-Konvention — das Argument dient als Fokus **und** Slug (`handoff-<slug>.md`), Argument mit `.md`-Endung als expliziter Dateiname; damit entsteht pro Thema ein eigenes Dokument statt ein stets ueberschriebenes `handoff.md`. `install.sh`-Liste ergaenzt

### 1.15.2

- **kanboard: Neuer Subcommand `move-project` (Task in anderes Projekt verschieben).** `move-task` arbeitet nur projektintern (`moveTaskPosition`) und schlaegt bei einem Projektwechsel fehl. `move-project <task_id> --project <name|id> [--column <name>] [--swimlane <name>]` nutzt `moveTaskToProject` und setzt danach optional Spalte/Swimlane im Zielprojekt (ohne `--column` Kanboard-Standardspalte, ohne `--swimlane` erste aktive Swimlane). Verifiziert: Live-Verschiebung eines realen Tasks ins Zielprojekt/-spalte (`success: true`)

### 1.15.1

- **php-formatting: Leerzeilen um Kontrollstrukturen an Blockgrenzen praezisiert.** Die Ausnahmen-Liste in Abschnitt 2 sagte bisher pauschal „am Anfang/Ende eines Blocks (direkt nach `{` / direkt vor `}`) keine ueberfluessige Leerzeile" — das widersprach der Grundregel, wenn das erste bzw. letzte Statement selbst eine Kontrollstruktur ist. Klargestellt: Regel 2 hat Vorrang, die Leerzeile vor/nach einer Kontrollstruktur gilt konsequent auch an Blockgrenzen (auch direkt nach dem oeffnenden `{` und direkt vor dem schliessenden `}`). Einzige verbleibende Ausnahme bleibt `}`↔`else`/`elseif`/`catch`/`finally`. Beispiel mit verschachtelter Kontrollstruktur als erstes/letztes Statement ergaenzt

### 1.15.0

- **wiki: Read-only-Zugriff auf Wikis anderer Hosts (SSH).** Ein Projekt kann die Wikis eines anderen Hosts nutzen, ohne Sync und ohne je remote ins Wiki zu schreiben. Drei Bausteine: **(1) Remote-Query** — Remotes werden aus `<projekt>/.claude/wiki-remotes.json` (`{name: {host, path, readonly}}`) aufgeloest; `query`/`status` lesen die Dateien per `ssh <host> "cat/grep …"` (User-Shell ist bash, normales Quoting), `ingest`/`compile`/`init` sind fuer Remotes gesperrt (read-only by construction). **(2) Remote-Hints** — Wikilinks `[[<remote>:<slug>]]` gelten im Linter als gueltig, wenn `<remote>` in `.claude/wiki-remotes.json` steht (kein toter Link, keine Waisen-Folgefehler); Default offline-sicher, Flag `--check-remotes` verifiziert die Ziele on demand per SSH-`find`. **(3) Handoff-Note** — Subcommand `<remote>:handoff` liest das Zielschema + `index.md` per SSH, erkennt new-vs-update und erzeugt eine ingest-fertige Note unter `.claude/wiki-outbox/<remote>-<slug>.md`; Transport (Kanboard/scp/Mail) und Ingest auf dem Zielhost sind user-ausgeloest. `lint-wiki.py`: neue `load_remotes()`/`parse_remote_target()`/`check_remote_target()`, `--check-remotes`-Flag. Verifiziert: Regression azedo 99/0 + cris 27/0 unveraendert; SSH-Read + Remote-Pointer + Handoff-Format gegen die reale cris-Wiki getestet

### 1.14.1

- **wiki: Wiki-Basis projekt-relativ (Portabilitaet).** Die Wiki-Root wird nicht mehr home-verankert (`~/azedo.ai/wiki/<name>/`) aufgeloest, sondern **relativ zum Projekt-Root** (`wiki/<name>/`) — konsistent mit der Projekt-`CLAUDE.md` (`wiki/azedo/…`) und portabel fuer Mac, andere Mitarbeiter und abweichende Checkout-Orte. Kein Home-Fallback (waere bei anderem Checkout-Pfad kontraproduktiv). Nur SKILL.md-Anleitung + Hilfetexte im Linter betroffen; `lint-wiki.py` war bereits vollstaendig parametrisch (nimmt die Wiki-Root als Argument). Verifiziert: azedo + cris linten sauber sowohl aus dem Projekt-Root als auch aus einem anderen Verzeichnis (0 Fehler)

### 1.14.0

- **wiki: Multi-Wiki-Support + konfigurierbares Entity-Modell.** Der Skill ist nicht mehr fest auf das Infra-Wiki `azedo` verdrahtet. Ziel-Wiki per Praefix waehlbar: `/wiki <name>:<subcommand>` (z.B. `/wiki cris:query "…"`), ohne Praefix gilt weiterhin `azedo` (rueckwaertskompatibel). Alle hartkodierten `~/azedo.ai/wiki/azedo/`-Pfade laufen ueber `<WIKI_ROOT>`; vor jeder Operation wird `<WIKI_ROOT>/CLAUDE.md` gelesen (jedes Wiki hat sein eigenes Modell und eigene Konventionen). `lint-wiki.py` laedt erlaubte Typen + Pflichtfelder aus `<wiki-root>/wiki-schema.json` (Format: `required_common` + `types`), mit dem bisherigen Infra-Modell als eingebautem Fallback (`DEFAULT_SCHEMA`) — fehlt die Datei, verhaelt sich der Linter wie bisher. `init` legt neben der Verzeichnisstruktur eine Default-`wiki-schema.json` an. Verifiziert: `azedo`-Lint unveraendert (99 Artikel, 0 Fehler, Default-Fallback), neues Projekt-Wiki `cris` (concept/module/integration/procedure/reference/architecture, Pflichtfeld `projekt`) lintet mit eigenem Schema sauber (10 Artikel, 0 Fehler). Die `wiki-schema.json` der einzelnen Wikis liegt im jeweiligen Wiki, nicht im Skill-Repo

### 1.13.0

- **kanboard: Task-Verbindungen (interne Links):** Vier neue Subcommands zum Verwalten von Task-zu-Task-Verknuepfungen ueber die Kanboard-Link-API. `list-links` listet die instanzweit definierten Link-Typen (id, label, opposite_id) — Discovery, um das richtige Label/die richtige ID zu finden. `list-task-links <task_id>` zeigt bestehende Verbindungen eines Tasks. `create-task-link <task_id> <opposite_task_id> --link "<label|id>"` verknuepft zwei Tasks (Label wird case-insensitiv via `getAllLinks` aufgeloest, oder direkt numerische `link_id`); Kanboard legt die Gegenrichtung automatisch an. `remove-task-link <task_link_id>` loescht eine Verbindung. Damit sind interne Verbindungen (z.B. „relates to", „is a child of", „blocks") jetzt scriptbar. Hinweis: die deutsche UI-Bezeichnung „gehört zu" entspricht dem gespeicherten Label „relates to" (link_id 1)

### 1.12.1

- **humanizer-de: Muster 67 „Business-Anglizismen / Denglisch-Jargon" [MEDIUM] (azedo-Erweiterung):** Neue register- und clustergesteuerte Kategorie erkennt deutschen Business-/Consulting-Jargon und Anglizismen („Bullshit-Bingo") und schlaegt deutsche Entsprechungen vor — abgegrenzt von Muster 45 (harte Transfers) und Muster 64 (deutsche KI-Marker). Kuratiertes Lexikon (Begriff→DE) + fixe Negativliste etablierter Fachbegriffe (MVP, SaaS, CRM, KI, …) in `scripts/german_pattern_lint.py`; case-insensitiver Match mit begrenztem Flexions-Suffix (matcht `R&D`, `Plattform-IP`, `instrumentiert`, ohne `Gate`→`Gateway`/`IP`→`ZIP`-Fehltreffer). Schwellen formal ≥1 / sachlich ≥2 / locker ≥4. `humanizer_audit.py` aggregiert die Kategorie ins Preflight; Muster 67 in `patterns.md` (Pass 2) und `SKILL.md` (Modusmatrix, Carve-outs) dokumentiert. Als klar markierte azedo-Erweiterung gekapselt (kein Upstream-Sync)
- **Wording:** „vendorisiert" statt „vendort/vendorter" in SKILL.md, README und Handoff

### 1.12.0

- **humanizer-de-Skill:** Deutscher AI-Text-Humanizer als vendorisierter Fork von `marmbiz/humanizer-de` (@ `a5084f2`, v5.2.0, MIT). Kuratierter Subset (SKILL.md + 6 Referenzen + 7 Python-Linter, stdlib only); Plugin-/Codex-Manifeste, `tests/`, `docs/` und `assets/` weggelassen, da azedo-skills ueber Symlinks statt Marketplace laeuft. Frontmatter an azedo-Konvention angeglichen, Script-Aufrufe auf `$SKILL_DIR`, Herkunft-/Lizenz-Block ergaenzt. `LICENSE` verbatim erhalten (Attribution an `blader/humanizer` und dt. Wikipedia CC BY-SA 4.0)

### 1.11.5

- **wetter: Favoritendatei bei Fehlen anlegen (Workflow):** Fehlt `~/.claude/wetter-favorites.json`, ist das Anlegen jetzt ein verpflichtender Workflow-Schritt (nur bei `forecast`/`nowcast`): `stations <ort>` auflisten, den User die Favoriten waehlen lassen, Datei schreiben — erst dann die eigentliche Abfrage. Zuvor war das nur ein passiver Hinweis. Bei `warnungen` entfaellt der Schritt (nutzen keine Favoriten)

### 1.11.4

- **wetter: Kuratierte Favoritenstationen fuer den Messwert:** Der Messwert-Header nimmt nicht mehr die geografisch naechste Station (oft inoffiziell/ohne aktuelle Daten), sondern ausschliesslich Stationen aus `~/.claude/wetter-favorites.json`. Von diesen die naechste mit **frischen** Daten (veraltete >2 h werden uebersprungen). Fehlt die Datei/liefert kein Favorit Daten, laeuft es ohne Header weiter
- **wetter: Messwert-Header auch im forecast:** `forecast` zeigt denselben Header (aktueller Favoriten-Messwert) wie der Nowcast, oben in der Ausgabe und als `messwert`-Block im `--json`
- **wetter: Neuer Subcommand `stations <ort>`:** listet die naechstgelegenen TAWES-Stationen mit Distanz und aktuellem Wert (bzw. "veraltet"/"keine Daten"), Favoriten mit `*` markiert — zum Auswaehlen der Favoriten
- **wetter: Robustere Stationsabfrage:** Einzelabfrage pro Station statt Batch — die current-API richtet Mehr-Stationen-Requests auf einen gemeinsamen Zeitstempel aus, wodurch veraltete Stationen frische auf null zogen

### 1.11.3

- **wetter: Feuchte in der Stundenvorhersage:** `forecast` zeigt die relative Feuchte (`rF %`) nun in jeder 3-stuendlichen Zeile (Parameter `rh2m` ergänzt) und im `--json`-Output
- **wetter: Echter Messwert im Nowcast:** `nowcast` zeigt oben einen Header mit dem aktuellen Messwert der naechstgelegenen aktiven TAWES-Station (`station/current/tawes-v1-10min`) — Stationsname, Distanz, Temperatur, Feuchte, Taupunkt, Wind. Echter Messwert statt interpoliertem Modellwert; als `messwert`-Block auch im `--json`. Stationsabfrage ist "best effort" (faellt bei Fehler stillschweigend weg)

### 1.11.2

- **wetter: Luftfeuchtigkeit im Nowcast:** Die relative Feuchte (`rh2m`) wird nun in jeder Nowcast-Zeile ausgegeben (`rF NN%`, zwischen Temperatur und Wind) und im `--json`-Output mitgeliefert. Der Parameter wurde bereits abgefragt, aber bisher nicht angezeigt

### 1.11.1

- **Auto-Verlinkung nach `git pull`:** `install.sh` richtet `post-merge`- und `post-rewrite`-Hooks ein, die neue Skills nach jedem Pull (auch `--rebase`) automatisch verlinken. Fremde Hooks bleiben unangetastet, Installation idempotent. Aeltere Installationen einmalig `sh install.sh` ausfuehren, danach greift der Automatismus

### 1.11.0

- **wetter-Skill:** GeoSphere Austria Wetterdaten fuer Oesterreich (Python, stdlib only, keine Auth). Subcommands: forecast (AROME-Stundenvorhersage ~60 h), nowcast (15-Minuten-Schritte, ~3 h), warnungen (amtliche Warn-API). Standort per Ortsname (Nominatim-Geocoding, AT-beschraenkt) oder Koordinaten. Zustand aus Bewoelkung + Niederschlag abgeleitet (kein `sy`-Raten), Zeiten in Europe/Vienna, `--json`-Ausgabe
- **Versionen vereinheitlicht:** alle Skript-`# version`-Marker und die `VERSION`-Datei auf 1.11.0. `image-optimize` hat nun ebenfalls einen Versions-Marker
- **Minor-Version-Unabhaengigkeit geprueft:** alle Scripts laufen unveraendert auf Python 3.9–3.13 (generischer `#!/usr/bin/env python3`-Shebang, keine entfernten Stdlib-Module, keine ungueltigen Escape-Sequenzen). README-Hinweis fuer neue Skills (`install.sh`-Liste) ergaenzt

### 1.10.0

- **google-analytics-Skill:** GA4-Datenabfrage via Service Account (Python, stdlib only). Subcommands: accounts, properties, report, realtime, metadata, setup. Tab-separierte oder JSON-Ausgabe, Custom Dimensions/Metrics, Filter, Sortierung. instance.json fuer Property-ID Lookup
- **wiki-Skill:** LLM Wiki-Verwaltung fuer Server-Infra-Dokumentation. Subcommands: init, ingest, compile, query, lint, status. Frontmatter-Schemas, Cross-Referencing mit Wikilinks, Backlink-Audit, Compile-Checkliste. Lint-Script (lint-wiki.py) prueft Pflichtfelder, tote Links, Konnektivitaet, Namenskonventionen

### 1.9.8

- **MainWP: REST API v2 dokumentiert:** Tag-Verwaltung ueber `mainwp/v2` Endpoint (Consumer Key/Secret Auth, getrennt von Application Password). Neue Abschnitte: Tags verwalten, Clients verwalten, API-Architektur. Pagination-Warnung (>100 Sites, immer page=2 pruefen). v2 Credentials in `.env` (`MAINWP_V2_CONSUMER_KEY`, `MAINWP_V2_CONSUMER_SECRET`)
- **tcsh: iocage exec + sudo -u Pitfall:** `iocage exec <jail> sudo -u <user>` scheitert, weil jexec den `-u` Flag abfaengt. Fix: in `sh -c` wrappen. Unterschied zu `jexec <JID>` (numerisch) dokumentiert. In Entscheidungsmatrix aufgenommen

### 1.9.6

- **wp-pys-Skill:** Neuer Referenz-Skill fuer PixelYourSite Pro Event-Verwaltung in WordPress-(Multi-)Sites. PHP-Snippets fuer list-events, show-config, enable-target, clone-event, set-trigger, verify, backup/restore, list-forms. Dokumentiert Datenmodell, wp_slash()-Fallstrick und Multisite-Stolpersteine
- **install.sh:** Skill-Liste alphabetisch sortiert, wp-pys ergaenzt

### 1.9.5

- **MainWP Auto-Batching:** `--batch-size N` (Default 25) splittet site_ids-basierte Abilities automatisch in Gruppen, um Gateway Timeouts bei vielen Sites zu vermeiden. Bei leerem Array (= alle Sites) werden IDs erst via list-sites geholt. Ergebnisse (synced/errors) werden aggregiert

### 1.9.4

- **install.sh:** tcsh-Skill in Skill-Liste ergaenzt — kuenftige Installs registrieren den Symlink automatisch

### 1.9.3

- **tcsh-Skill:** Neuer Referenz-Skill fuer tcsh-basierte Remote-Administration auf FreeBSD. Entscheidungsmatrix (tcsh nativ vs. sh -c), Syntax-Kurzreferenz, Bash→tcsh Uebersetzungstabelle, FreeBSD-Admin-Patterns, Quoting-Regeln, bekannte Fallen
- **wp-cli: Custom-Tabellen bei Multisite:** Hinweis ergaenzt — `--url` erfasst nur Standard-Tabellen mit Site-Prefix, Custom-Tabellen (z.B. WPML `wp_*_icl_strings`) erfordern `--all-tables`

### 1.9.2

- **Kanboard: Bessere Fehlerbehandlung:** `rpc_call` und `rpc_try` fangen jetzt HTTP-Fehler und nicht-JSON-Antworten sauber ab (z.B. ModSecurity-Blocks), statt mit einem Traceback abzubrechen. Zeigt HTTP-Statuscode und Response-Body (max 500 Zeichen)

### 1.9.1

- **MainWP Bugfixes:** API-Request-Format korrigiert (input-Envelope, Array-Parameter mit indizierter Notation). `_coerce_value` erkennt jetzt JSON-Arrays/Objects in `--param` Werten. SKILL.md dokumentiert `per_page=100` und `search=` fuer list-sites

### 1.9.0

- **MainWP-Skill:** Neuer Skill fuer MainWP Dashboard — generischer Abilities-Executor mit 5 Subcommands (setup, ping, list, info, run). Dynamische Erkennung aller verfuegbaren Abilities via WP Abilities API. Destruktive Operationen erfordern --confirm, --dry-run fuer Vorschau

### 1.8.0

- **Swaks: Kontakt-Shortcuts:** Empfaenger-Lookup ueber `.claude/swaks-contacts.tsv` im Arbeitsverzeichnis (TSV: `kurzname<TAB>email`). Namen statt E-Mail-Adressen verwenden, neue Kontakte werden automatisch ergaenzt
- **Swaks: Default-Signatur:** Optionale Signatur aus `.claude/swaks-signature.txt` wird automatisch an den Mail-Body angehaengt (unterdrueckbar per "ohne Signatur" oder bei anderem Absender)

### 1.7.0

- **wp-sync-dev-Skill:** Neuer Referenz-Skill fuer bidirektionalen WordPress-Plugin/Theme-Sync zwischen Prod-Jails und DEV. Pfad-Schema (iocage/ezjail), rsync, Permissions, Artefakt-Bereinigung

### 1.6.0

- **wp-cli-Skill:** Neuer Referenz-Skill fuer WordPress-Administration via WP-CLI in FreeBSD-Jails. Zugriffsmuster (ezjail/iocage), DB-Operationen (wp db + $wpdb-Workaround), Code-Ausfuehrung (wp eval/eval-file), Quick Reference, Safety-Workflow, Troubleshooting

### 1.5.2

- **Kimai `log` Bugfix:** Timezone-Suffix der API-Antwort (`+0200`, `+02:00`, `Z`) wird jetzt generisch per Regex abgestreift — `fromisoformat()` schlug bei `+0200` (ohne Doppelpunkt) fehl

### 1.5.1

- **Kimai `log` Subcommand:** One-Shot-Buchung — Shortcut-Aufloesung, Zeitberechnung und Timesheet-Anlage in einem Call. Akzeptiert `--shortcut` oder `--project`/`--activity`. Duration-Formate: Dezimalstunden (`0.5`), Minuten (`30m`), gemischt (`1h30m`)
- **Kimai Shortcuts:** Format umgestellt auf flaches JSON (`"key": [pid, aid, "Label"]`, eine Zeile pro Eintrag). Workflow nutzt grep statt Voll-Read. Migrationshinweis fuer bestehende Installationen

### 1.5.0

- **PHP-Formatting-Skill:** Neuer Skill fuer PHP-Code-Formatierung nach PSR-2 mit azedo-Anpassungen (Tabs, Leerzeilen um Kontrollstrukturen/Kommentarbloecke/Methoden)

### 1.4.3

- **Kimai SKILL.md:** Aufbau von `kimai-shortcuts.json` dokumentiert (Keys, Felder, Beispiel) — verhindert Raten auf neuen Installationen

### 1.4.1

- **Kimai Shortcuts:** Pfad von `kimai-shortcuts.json` nach `.claude/kimai-shortcuts.json` verschoben (konsistent mit projektspezifischer `.claude/`-Konfiguration)

### 1.4.0

- **Kimai Shortcuts:** Projekt/Aktivitaets-Lookup ueber `.claude/kimai-shortcuts.json` im Arbeitsverzeichnis statt vollstaendiger `instance.json`. Haeufige Kombinationen werden als kompakte Key-Value-Paare gespeichert, neue Kombinationen automatisch ergaenzt. Fallback auf `instance.json` bei unbekannten Projekten.

### 1.3.2

- **Kanboard SKILL.md:** Hinweis ergaenzt — "erledigt" = move-task in Spalte "erledigt", close-task nur nach Rueckfrage

### 1.3.0

- **Ripgrep-Skill:** Referenz-Skill fuer `rg` uebernommen von [ratacat/claude-skills](https://github.com/ratacat/claude-skills). Quick Reference, Regex-Patterns, Common Patterns, Performance-Tipps.

### 1.2.0

- **Envato-Skill:** Neuer Skill fuer Envato Market (ThemeForest, CodeCanyon) — Kaeufe auflisten, Items herunterladen, suchen, Details anzeigen (8 Subcommands)
- **CR-Kontext:** Kanboard `cr` Subcommand laedt Tasks als aktiven Kontext, Commit-Messages und Kimai-Beschreibungen werden mit `CR{id}: ` prefixed
- **.env Fallback:** Kanboard und Kimai suchen `.env` jetzt auch im Home-Verzeichnis (`~/.env`) als Fallback
- **Kimai:** Neue Eintraege werden zeitlich an den letzten heutigen Eintrag angeschlossen

### 1.1.0

- **Non-Admin-Support:** Kanboard und Kimai funktionieren jetzt mit persoenlichen API-Tokens (ohne Admin-Rechte)
- **Kanboard:** Auth-User konfigurierbar via `KANBOARD_USER` in `.env` (Default: `jsonrpc`)
- **Kanboard:** `setup` erkennt die Benutzerrolle (`getMe`) und speichert sie in `instance.json`
- **Kanboard:** Non-Admins: `getMyProjects` statt `getAllProjects`, Projektmitglieder via `getProjectUsers`
- **Kanboard:** `resolve_user` nutzt `instance.json`-Cache statt Admin-API-Call `getUserByName`
- **Kimai:** `setup` erkennt Admin-Rolle via `/users/me` und speichert `is_admin` in `instance.json`
- **Kimai:** Non-Admins: `GET /users/me` statt `GET /users`
- **Versionierung** eingefuehrt: `VERSION`-Datei im Repo-Root, `# version` Kommentar in Scripts

**Update:** Nach `git pull` einmal `setup` fuer Kanboard und Kimai ausfuehren. Die Setup-Befehle muessen aus dem Arbeitsverzeichnis mit der `.env` ausgefuehrt werden:

```bash
cd ~/.claude/azedo-skills && git pull
cd /pfad/zum/arbeitsverzeichnis   # dort wo die .env liegt
python3 ~/.claude/skills/kanboard/kanboard setup --default-user <username>
python3 ~/.claude/skills/kimai/kimai setup
```

### 1.0.0

Initiale Version mit Kanboard, Kimai, Swaks und Image-Optimize Skills.
