# Export / Import (Backup & Klonen)

Der Export ist zugleich das **Backup vor jedem Write** (Abschnitt 4 der
[SKILL.md](../SKILL.md)) und der Sollwert, gegen den der Preflight die Feldzahl
je Formular haelt.

Entspricht dem Backend-Import/Export (`.nff`-Datei = **utf8-kodiertes JSON**). Als
WP-CLI-Subcommand **nicht** verfuegbar → via `eval-file` ueber die Form-API
(`export_form()`/`import_form()`). Ein Export enthaelt **nur die Definition**
(settings/fields/actions inkl. `element_class`), **keine Submissions**.

**Export** (Backup / Quelle fuers Klonen):

```php
<?php
// nf-export-form.php <form_id> <ziel.nff>
//   wp eval-file nf-export-form.php <form_id> /tmp/form.nff --url=<subsite>
$form_id = intval( $args[0] );
$outfile = $args[1];

$export = Ninja_Forms()->form( $form_id )->export_form( true );
if ( ! is_array( $export ) ) { echo "Export fehlgeschlagen (Form $form_id?)\n"; exit( 1 ); }

// Backend-identisches Format: utf8-kodiertes JSON
$json = json_encode( WPN_Helper::utf8_encode( $export ) );
if ( file_put_contents( $outfile, $json ) === false ) {
    echo "FEHLER: konnte $outfile nicht schreiben (Web-User schreibbar?)\n"; exit( 1 );
}
echo "OK: $outfile (" . strlen( $json ) . " Bytes)\n";
```

**Import** (legt IMMER ein neues Formular an, gibt neue ID zurueck):

```php
<?php
// nf-import-form.php <quelle.nff>
//   wp eval-file nf-import-form.php /tmp/form.nff --url=<ziel-subsite>
$infile = $args[0];
if ( ! is_readable( $infile ) ) { echo "Datei nicht lesbar: $infile\n"; exit( 1 ); }

$json   = file_get_contents( $infile );
$new_id = Ninja_Forms()->form()->import_form( $json );

echo $new_id ? "OK: neues Formular #$new_id angelegt\n" : "Import fehlgeschlagen (JSON gueltig?)\n";
```

Merke:
- Import **ueberschreibt nichts** — es entsteht ein neues Formular mit neuer ID. „Restore"
  = importieren, altes danach ggf. per `wp ninja-forms delete form <id>` entfernen. Zum
  **Klonen** (z.B. DE→FR): auf der Quelle exportieren, auf der Ziel-Subsite importieren.
- Form-IDs im Export sind die der Quelle; beim Import neu vergeben → Referenzierung weiter
  ueber den Titel ([snippets-read.md](snippets-read.md)).
- Die `.nff` ins Jail-`/tmp` schreiben, fuer ein echtes Backup vom Host abholen, danach im
  Jail aufraeumen.

Zurueck zur Uebersicht: [SKILL.md](../SKILL.md).
