---
name: wp-rcb
description: >
  Real Cookie Banner (devowl, auch Pro) per WP-CLI: Dienste, Content Blocker,
  Banner-Links, Einstellungen und Revisionen lesen, ausgelieferten Dienst-Code
  im Frontend prüfen, Einrichtung exportieren, zwischen Sites vergleichen und
  importieren, Content Blocker anlegen, Code-Felder, Cookie-Definitionen,
  Rechtsgrundlage und Einstellungen setzen, per Browser-Test prüfen, was vor
  der Einwilligung lädt. Auch bei "welche Dienste hat der Cookie-Banner",
  "liefert RCB den Code ohne Einwilligung aus",
  "übertrag den Cookie-Banner auf die andere Seite", "vergleich die
  RCB-Einstellungen". Trigger: /wp-rcb.
allowed-tools: [Bash, Read]
---

# wp-rcb -- Real Cookie Banner per WP-CLI

RCB bringt keine eigenen WP-CLI-Befehle mit. `rcb.php` ruft seine PHP-Klassen
(Export, Import, Cache) direkt auf und liefert JSON. Es läuft **auf dem Server**
per `wp eval-file -` über STDIN; lokal braucht es nur `python3`.

Das Zusammenspiel mit PixelYourSite (Consent-Kopplung, `optimized-assets`,
MU-Plugin) steht nicht hier, sondern in der Wiki-Procedure
`wp-pys-rcb-integration`. Die DSGVO-Bewertung bleibt beim Menschen.

## Aufruf

Host, Jail, Docroot und wwwuser der Site kommen aus dem Infra-Wiki, die
Aufrufform aus dem Skill `wp-cli` (iocage: `iocage exec -U <wwwuser>`, ezjail:
`jexec <jail> sh -c "cd <docroot> && sudo -u <wwwuser> wp …"`). An die Stelle
des WP-CLI-Befehls tritt `wp eval-file - <befehl> [argumente]`:

```bash
cat "$SKILL_DIR/rcb.php" | sudo ssh -C root@<host> \
  "jexec <jail> sh -c 'cd <docroot> && sudo -u <wwwuser> wp eval-file - services'"
```

Bei Multisite gehört `--url=<site-url>` vor `eval-file`. Befehle, die eine
Datei brauchen (`import`, `set-code`, `create-blocker`, Zweck bei
`set-cookie`), bekommen sie über das lokale Script, das den Inhalt in die
Payload einbettet:

```bash
python3 "$SKILL_DIR/rcb" php --input <datei> | sudo ssh -C root@<host> "… wp eval-file - import"
```

Argumente sind Wörter oder `name=wert` (`revisions grep=office@ limit=5`) -
WP-CLI nimmt `--optionen` hinter `eval-file` nicht an. Ein Wert mit
Leerzeichen oder Sonderzeichen (`set-setting`, `set-code`, Zweck bei
`set-cookie`) geht über `--input`, nie als Argument: SSH, tcsh und `sh -c`
zerlegen ihn sonst.

PHP-Warnungen von Plugins landen auf stderr, das JSON auf stdout - beim
Weiterverarbeiten nur stdout lesen (`2>/dev/null` oder in eine Datei).

## Befehle (rcb.php, auf dem Server)

| Befehl | Zweck |
|---|---|
| `info` | RCB-Version, Pro, Home-URL, Blog-ID, Sprachen |
| `services` | Dienste mit Gruppe, Vorlage/Version, Rechtsgrundlage, Sprache, befüllten Code-Feldern, Cookie-Hosts |
| `service <id\|post_name\|titel>` | ein Dienst mit allen Metas, Code-Felder im Klartext |
| `blockers` | Content Blocker mit verbundenen Diensten und Regeln |
| `banner-links` | Datenschutz/Impressum/… mit Sprache und Ziel-URL |
| `settings [all]` | die funktionalen RCB-Einstellungen; `all`: alle `rcb-*`-Optionen ohne Caches |
| `revisions [grep=<text>] [limit=<n>]` | öffentliche Revision je Kontext und die letzten Einträge |
| `check-groups` | je Gruppe Term-`count` gegen die veröffentlichten Dienste; Abweichung siehe Fallstricke |
| `export` | komplette Einrichtung samt `_meta` (Version, Home-URL) |
| `import [yes] [group=<slug>]` | Export einspielen; ohne `yes` nur Vorschau |
| `create-blocker <titel> services=<post_name,…> [yes]` | Content Blocker anlegen, Regeln zeilenweise per `--input`; läuft über den Import |
| `set-code <dienst> <feld> [empty] [yes]` | `codeOptIn`, `codeOptOut` oder `codeOnPageLoad` setzen bzw. leeren |
| `set-cookie <dienst> <name> [host=…] [type=…] [duration=<n>] [unit=s\|m\|h\|d\|mo\|y] [session[=0]] [purpose=…] [remove] [yes]` | Cookie-Definition (`technicalDefinitions`) eines Dienstes anlegen, ändern oder entfernen |
| `set-legal-basis <dienst> consent\|legitimate-interest\|legal-requirement [yes]` | Rechtsgrundlage (`legalBasis`) eines Dienstes setzen, unter WPML in allen Sprach-Posts |
| `set-setting <option> <wert\|empty> [yes]` | eine RCB-Einstellung setzen |
| `clear-cache` | RCB-Cache und WP Rocket leeren |

## Befehle (rcb, lokal)

| Befehl | Zweck |
|---|---|
| `rcb php [--input <datei>]` | Payload für `wp eval-file -` ausgeben |
| `rcb frontend <url>… [--full]` | welche Dienste die Seite ausliefert und mit welchem Code (dekodiert) |
| `rcb diff <a.json> <b.json>` | zwei Exporte oder `settings`-Ausgaben vergleichen, Listen per Slug |

## Consent-Test (consent-test.mjs, lokal)

Was die Seite **tatsächlich anfragt**, nicht nur, was im HTML steht: drei
Durchläufe in frischen Browser-Kontexten - ohne Einwilligung, nach "nur
essenzielle", nach "alle akzeptieren" - mit den fremden Hosts, den
`gcs=`-Werten (GA4 Consent Mode) und fremden Cookies je Durchlauf.

```bash
node "$SKILL_DIR/consent-test.mjs" <url> [<unterseite>…] [--groups Statistik,Marketing]
```

`--groups` fügt den Durchlauf "auswahl" hinzu: individuelle Einstellungen
öffnen, die genannten Gruppen anhaken (Namen wie im Banner), speichern. Nicht
genannte Gruppen behalten den RCB-Vorgabewert. `Gruppen angehakt` zeigt je
Gruppe, ob die Checkbox danach gesetzt war.

- Braucht Playwright mit Chromium, das es für FreeBSD nicht gibt: läuft am
  Mac oder unter Linux. Fehlt es, nennt das Script die Installationsbefehle
  (einmalig nach `~/.cache/wp-rcb`).
- Läuft ohne Fenster mit normalem User-Agent. `--headed`, wenn GA4-Hits
  ankommen müssen - GA4 verwirft Hits von Headless-Chrome.
- Fremde Hosts im ersten oder zweiten Durchlauf sind der Befund: dort lädt etwas
  ohne die passende Einwilligung. `gcs=G111` vor der Einwilligung heißt, GA
  sendet ohne. Ob ein Host essenziell ist, entscheidet der Mensch.
- **Gültig ist ein Durchlauf nur mit `Einwilligung gespeichert: true`.** Das
  Script wartet nach dem Klick auf das Cookie `real_cookie_banner*`; ohne
  dieses Cookie misst die Phase dasselbe wie "ohne Einwilligung".
- `Klick: false` heißt, der Banner-Button wurde nicht gefunden. Die Defaults
  passen auf deutsche und englische RCB-Texte ("Weiter ohne Einwilligung",
  "Alle akzeptieren"); sonst `--accept`/`--essential` mit dem Buttontext.
- Ist die Site per Passwort geschützt (DEV hinter Hide My WP, Basic Auth),
  kommt der Test nicht bis zum Banner.

Sites vergleichen: `export` bzw. `settings all` auf beiden Seiten nach `.tmp/`
schreiben, dann `rcb diff`. Ein leeres `rcb-banner-active` zeigt nur der
Vergleich der Einstellungen, nicht der Blick auf die Dienste.

## Schreiben

1. Ohne `yes` aufrufen und die Vorschau lesen: alter und neuer Wert, beim
   Import der Plan je Gruppe, Dienst, Blocker und Einstellung.
2. Erst nach Freigabe mit `yes`. Die Ausgabe enthält unter `backup` den Export
   **vor** der Änderung - sie gehört nach `.tmp/rcb-<site>-<befehl>-<zeit>.json`
   (`| tee …`), sonst ist die Sicherung weg.
3. Danach mit `service`/`settings` gegenlesen und `rcb frontend` gegen die
   Seite laufen lassen; bei Seiten-Cache vorher `clear-cache`.

**`set-cookie`:** Ein neues Cookie braucht `host=` und `duration=`/`unit=`
(oder `session`), `type` ist ohne Angabe `http`. Ein bestehendes wird über den
Namen gefunden; steht der Name mit mehreren Hosts im Dienst, wählt `host=` den
Eintrag. Geändert werden nur die angegebenen Felder. Der Zweck kommt über
`--input`, sobald er Leerzeichen enthält. Den Dienst ändert man in einer Sprache,
RCB kopiert die Definitionen unter WPML auf die übrigen Sprachversionen.
`posts` in der Ausgabe zeigt das Cookie je Sprach-Post - nach `yes` muss es
überall stehen.

Schreibbefehle verlangen **keine** neue Einwilligung der Besucher. RCB rechnet
die Revision neu und zeigt im Admin einen Hinweis; ob neu eingewilligt werden
muss, entscheidet der Mensch dort ("Neue Einwilligung anfordern").

## Import - was RCB tut und was nicht

- **Legt nur an.** Dienste und Blocker mit bestehendem `post_name` werden
  übersprungen, nie aktualisiert. Zum Angleichen einer bestehenden Site
  `set-code`/`set-setting` verwenden.
- **Abgleich nur per Slug.** Heißt derselbe Dienst oder dieselbe Gruppe auf der
  Ziel-Site anders (`statistik` vs. `statistiken`), entsteht ein Duplikat. Die
  Vorschau meldet gleiche Titel unter anderem Slug als Problem und jede neue
  Gruppe als Warnung.
- **Version muss gleich sein.** RCB selbst prüft das nicht; `rcb.php` bricht
  mit `yes` ab, solange `problems` nicht leer ist.
- **Cookie-Hosts** tragen die Domain der Quell-Site; `rcb.php` schreibt sie beim
  Import auf die Ziel-Domain um. Hosts, die zu keiner der beiden passen (ein
  DEV-Klon trägt oft noch die Live-Domain), meldet die Vorschau als Warnung.
- **Nicht importiert** (nur Meldung): Einstellungen mit Seiten-IDs
  (Kontaktformular, Cookie-Richtlinie, ausgeblendete Seiten), Consent-Forwarding,
  TCF, Geo-Restriction. Diese per `set-setting` nachziehen.
- **Überschreibt ohne Rückfrage** die Banner-Texte und das Design
  (`customizeBanner`) sowie Name und Beschreibung bestehender Gruppen. Die
  Vorschau listet die betroffenen Felder unter `banner` und `groups`; soll nur
  ein Teil übertragen werden, die Exportdatei vorher auf diese Schlüssel kürzen.
- `group=<slug>` ist nur die Ersatzgruppe für Dienste, deren Gruppe fehlt.

**Zurücknehmen:** `backup` aus der Import-Ausgabe als eigene Datei speichern und
mit `import yes` wieder einspielen - das stellt Einstellungen, Banner und
Gruppen her. Neu angelegte Dienste, Blocker und Gruppen bleiben dabei stehen;
sie per `wp post delete <id> --force` bzw. `wp term delete rcb-cookie-group
<slug> --by=slug` entfernen. Abschluss: neuer `export`, `rcb diff` gegen die
Sicherung zeigt 0 Unterschiede.

## Multisite und WPML

RCB-Optionen und -Tabellen liegen je Blog - `--url` wählt ihn. Unter WPML hat
jeder Dienst und jeder Banner-Link je Sprache einen eigenen Post (Feld `lang`).
Die Einwilligung gilt je Sprachdomain: `rcb frontend` je Domain aufrufen.

Eine Kontaktseiten-ID in `rcb-operator-contact-form-id` ist die der
Hauptsprache; RCB löst die Übersetzung über WPML selbst auf.

## Fallstricke

- **Gruppe fehlt im Frontend:** RCB liefert eine nicht-essenzielle Gruppe mit
  Term-`count` 0 nicht aus, auch wenn ihr Dienste zugeordnet sind; PYS-Pixel
  laden dann ohne Einwilligung. `check-groups` zeigt das als `ok: false`,
  behoben mit `wp term recount rcb-cookie-group` und `clear-cache`.
- **`blockers` leer** ist kein Fehler, wenn die Sperre über die
  PixelYourSite-Kopplung läuft (siehe `wp-pys-rcb-integration`).
- **`frontend` braucht einen normalen User-Agent** - Headless-Browsern zeigt RCB
  keinen Banner. Das Script setzt ihn; mit `curl` von Hand ebenso.
- Ausgelieferter Code steht im HTML als `base64-encoded:…`; `rcb frontend`
  dekodiert ihn, `--full` zeigt ihn ganz.
