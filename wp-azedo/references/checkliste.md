# Abnahme-Checkliste Block-Theme

Jeder Punkt stammt aus einem Fehler, der in einem Projekt tatsächlich passiert ist.

## Aufbau

- [ ] Grundgerüst nicht von Hand: „Create Block Theme" oder Export, siehe `wp-block-themes`.
- [ ] `screenshot.png` (1200×900) im Theme - sonst leere Kachel unter Design → Themes.
- [ ] Templates vollständig: `index`, `front-page` bzw. `home`, `page`, `single`, `archive`, `search`, `404`. Fehlende fallen auf `index.html` zurück und zeigen dann oft eine leere Seite.
- [ ] Nicht benötigte Archive (Autor, Taxonomien ohne eigene Seite) abschalten, statt sie leer auszuliefern. Autorenarchive verraten Benutzernamen.
- [ ] Jede PHP-Datei im Theme und im mu-plugin beginnt mit `defined('ABSPATH') || exit;`.

## Gestaltung

- [ ] Farben, Schatten, Schriften nur aus `theme.json`-Presets; im CSS keine festen Hex-Werte.
- [ ] Schriften lokal über `fontFace`, keine Anfrage an Google Fonts.
- [ ] Header und Footer aus Core-Blöcken, nicht als `wp:html`.
- [ ] `blockGap` nicht pauschal auf 0 setzen - nimmt Absätzen in Gruppen die Ränder.
- [ ] `add_editor_style('style.css')`, damit der Editor wie das Frontend aussieht.
- [ ] Stylesheet-Version am Änderungsdatum (`filemtime`), nicht an der Theme-Version - sonst sieht ein Browser alte Stände.

## Navigation

- [ ] Menüs als `wp_navigation` mit Seiten-Links (folgen Slug-Änderungen), keine festen URLs im Pattern.
- [ ] Im Pattern das Menü über seinen Slug finden (`get_page_by_path($slug, OBJECT, 'wp_navigation')`), nicht über die ID.
- [ ] Eigene Regeln für das Overlay-Menü brauchen mindestens Spezifität (0,3,1); core setzt manche Werte mit dreifacher Klasse.
- [ ] Navigationsblock mit Textfarbe, sonst färbt core das offene Menü schwarz.
- [ ] Handy-Menü geöffnet geprüft, nicht nur geschlossen.

## Blöcke

- [ ] `block.json`: `apiVersion` 3, `textdomain`, `example`; Frontend-Script als `viewScriptModule`, wo möglich.
- [ ] Assets je Block über `block.json` (`style`, `viewScript…`), damit sie nur bei Bedarf laden.

## Prüfung

- [ ] Frontend am Desktop und am Handy gegen den freigegebenen Entwurf, per Screenshot.
- [ ] Startseite und mindestens eine Seite im Editor geöffnet: keine ungültigen Blöcke, Gestaltung sichtbar. Nichts speichern.
- [ ] Interaktives (Filter, Menü, Formular) im echten Browser geklickt, Konsole ohne Fehler.
- [ ] Formular: Testanfrage abgeschickt, Zustellung im Mail-Log gesehen.
- [ ] DEV steht auf „Suchmaschinen davon abhalten“ (`blog_public=0`).
