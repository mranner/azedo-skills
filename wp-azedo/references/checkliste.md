# Abnahme-Checkliste Block-Theme

Jeder Punkt stammt aus einem Fehler, der in einem Projekt tatsächlich passiert ist.

## Aufbau

- [ ] Grundgerüst nicht von Hand: „Create Block Theme" oder Export, siehe `wp-block-themes`.
- [ ] `screenshot.png` (1200×900) im Theme - sonst leere Kachel unter Design → Themes.
- [ ] Templates vollständig: `index`, `front-page` bzw. `home`, `page`, `single`, `archive`, `search`, `404`. Fehlende fallen auf `index.html` zurück und zeigen dann oft eine leere Seite.
- [ ] Nicht benötigte Archive (Autor, Taxonomien ohne eigene Seite) abschalten, statt sie leer auszuliefern. Autorenarchive verraten Benutzernamen.
- [ ] `/wp-json/wp/v2/users` für Gäste sperren (`rest_pre_dispatch`, 401). Das Abschalten der Autorenarchive allein reicht nicht, der Endpunkt nennt Slug und Autoren-URL.
- [ ] DEV: `WP_DEVELOPMENT_MODE` auf `theme`. Sonst cacht WordPress die Liste der Pattern-Dateien: eine neue Datei unter `patterns/` erscheint erst nach `wp_get_theme()->delete_pattern_cache()`, bis dahin rendert `wp:pattern` nichts.
- [ ] Jede PHP-Datei im Theme und im mu-plugin beginnt mit `defined('ABSPATH') || exit;`.

## Gestaltung

- [ ] Farben, Schatten, Schriften nur aus `theme.json`-Presets; im CSS keine festen Hex-Werte.
- [ ] Schriften lokal über `fontFace`, keine Anfrage an Google Fonts.
- [ ] Header und Footer aus Core-Blöcken, nicht als `wp:html`.
- [ ] `blockGap` nicht pauschal auf 0 setzen - nimmt Absätzen in Gruppen die Ränder.
- [ ] `add_editor_style('style.css')`, damit der Editor wie das Frontend aussieht.
- [ ] Stylesheet-Version am Änderungsdatum (`filemtime`), nicht an der Theme-Version - sonst sieht ein Browser alte Stände.

## Navigation

- [ ] Menüs als `wp_navigation` mit Seiten-Links, keine festen URLs im Pattern. Auch der Seiten-Link speichert die URL fest und folgt einer Slug-Änderung nicht - erst das Binding `"metadata":{"bindings":{"url":{"source":"core/post-data","args":{"field":"link"}}}}` (ab WP 6.9) rendert den aktuellen Permalink zur `id`.
- [ ] Ein eigener `render_block_core/navigation-link`-Filter liest gebundene Werte aus `$instance->attributes` (3. Parameter), nicht aus `$block['attrs']` - dort steht weiter die gespeicherte URL, ein Vergleich etwa für `aria-current` trifft nach einer Slug-Änderung still nicht mehr.
- [ ] Im Pattern das Menü über seinen Slug finden (`get_page_by_path($slug, OBJECT, 'wp_navigation')`), nicht über die ID.
- [ ] Eigene Regeln für das Overlay-Menü brauchen mindestens Spezifität (0,3,1); core setzt manche Werte mit dreifacher Klasse.
- [ ] Navigationsblock mit Textfarbe, sonst färbt core das offene Menü schwarz.
- [ ] Handy-Menü geöffnet geprüft, nicht nur geschlossen.

## Blöcke

- [ ] `block.json`: `apiVersion` 3, `textdomain`, `example`; Frontend-Script als `viewScriptModule`, wo möglich.
- [ ] Assets je Block über `block.json` (`style`, `viewScript…`), damit sie nur bei Bedarf laden.
- [ ] `get_block_wrapper_attributes()` am äußersten Element jeder `render.php`, sonst kommen Zusatzklasse und Anker aus dem Editor im Frontend nicht an. ACF-Blöcke dazu mit `"align": false` in `supports`, sonst setzt core eine leere Klasse `align`.
- [ ] Version in `view.asset.php` per `filemtime(__DIR__ . '/view.js')`, nicht fest `'1'`.

## Prüfung

- [ ] Frontend am Desktop und am Handy gegen den freigegebenen Entwurf, per Screenshot.
- [ ] Startseite und mindestens eine Seite im Editor geöffnet: keine ungültigen Blöcke, Gestaltung sichtbar. Nichts speichern.
- [ ] Interaktives (Filter, Menü, Formular) im echten Browser geklickt, Konsole ohne Fehler.
- [ ] Formular: Testanfrage abgeschickt, Zustellung im Mail-Log gesehen.
- [ ] DEV steht auf „Suchmaschinen davon abhalten“ (`blog_public=0`).
