# Export / Import (Backup & Klonen)

**Inhalt:** Export · Import per `import_form()` - nicht per CLI · Anlegen aus Definition · Merke

Der Export ist zugleich das **Backup vor jedem Write** (Abschnitt 4 der
[SKILL.md](../SKILL.md)) und der Sollwert, gegen den der Preflight die Feldzahl
je Formular haelt.

Entspricht dem Backend-Import/Export (`.nff`-Datei = **utf8-kodiertes JSON**). Als
WP-CLI-Subcommand **nicht** verfuegbar → via `eval-file` ueber die Form-API
(`export_form()`, Anlegen ueber die Model-API). Ein Export enthaelt **nur die Definition**
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

**Import per `import_form()` - nicht per CLI.** `import_form()` legt Formular und
Actions korrekt an, die **Felder aber leer**: `NF_Database_Models_Form::import()`
speichert jedes Feld zuerst ohne Settings und reicht die Werte an den
Hintergrundprozess `update-fields` weiter. Der laeuft nur aus dem Backend an, vom
CLI aus nicht. Die Werte stehen danach einzig im Form-Cache - und ein spaeteres
`build_nf_cache()` ueberschreibt ihn mit den leeren Feldern. Ueber das Backend-UI
importiert, ist eine `.nff` dagegen in Ordnung.

**Anlegen aus Definition** (Klonen und Wiederherstellen per CLI): das Formular aus
der `.nff` ueber die Model-API aufbauen, Felder und Actions einzeln mit ihren
Settings. `save()` fuellt dabei die Spalten `nf3_fields.order`, `required` und
`label_pos` nicht (nur die Meta-Zeilen) - das Snippet zieht sie per `UPDATE` nach.
Es legt **immer ein neues Formular** an und gibt die neue ID aus:

```php
<?php
// nf-create-form.php <quelle.nff>
//   wp eval-file nf-create-form.php /tmp/form.nff --url=<ziel-subsite>
$infile = $args[0];
if ( ! is_readable( $infile ) ) { echo "Datei nicht lesbar: $infile\n"; exit( 1 ); }

// Dekodierung wie import_form(): JSON, danach utf8_decode
$data = WPN_Helper::utf8_decode( json_decode( WPN_Helper::json_cleanup( file_get_contents( $infile ) ), true ) );
if ( ! is_array( $data ) || empty( $data['settings'] ) ) { echo "Keine gueltige .nff: $infile\n"; exit( 1 ); }

$now  = current_time( 'mysql' );
$form = Ninja_Forms()->form()->get();
$form->update_settings( $data['settings'] );
$form->update_setting( 'created_at', $now );
$form->save();
$form_id = $form->get_id();

foreach ( $data['fields'] as $s ) {
    unset( $s['id'] );
    $s['parent_id']  = $form_id;
    $s['created_at'] = $now;
    Ninja_Forms()->form( $form_id )->field()->get()->update_settings( $s )->save();
}
foreach ( $data['actions'] as $s ) {
    unset( $s['id'] );
    $s['parent_id']  = $form_id;
    $s['created_at'] = $now;
    Ninja_Forms()->form( $form_id )->action()->get()->update_settings( $s )->save();
}

// save() fuellt order, required und label_pos nur in der Meta - Spalten nachziehen
global $wpdb;
$f = $wpdb->prefix . 'nf3_fields';
$m = $wpdb->prefix . 'nf3_field_meta';
$wpdb->query( $wpdb->prepare( "UPDATE $f f JOIN $m m ON m.parent_id = f.id AND m.`key` = 'order'
    SET f.`order` = CAST( m.value AS SIGNED ) WHERE f.parent_id = %d", $form_id ) );
$wpdb->query( $wpdb->prepare( "UPDATE $f f JOIN $m m ON m.parent_id = f.id AND m.`key` = 'label_pos'
    SET f.label_pos = m.value WHERE f.parent_id = %d", $form_id ) );
$wpdb->query( $wpdb->prepare( "UPDATE $f f LEFT JOIN $m m ON m.parent_id = f.id AND m.`key` = 'required'
    SET f.required = ( COALESCE( m.value, '' ) = '1' ) WHERE f.parent_id = %d", $form_id ) );

$n = $wpdb->get_var( $wpdb->prepare( "SELECT COUNT(*) FROM $f WHERE parent_id = %d", $form_id ) );
echo "OK: Formular #$form_id angelegt, $n von " . count( $data['fields'] ) . " Feldern, "
    . count( $data['actions'] ) . " Actions\n";
echo "Jetzt Cache neu bauen (eigener Aufruf): nf-rebuild-cache.php $form_id\n";
```

Danach den Cache in einem **eigenen Aufruf** neu bauen (`nf-rebuild-cache.php`,
Abschnitt 4 der [SKILL.md](../SKILL.md)) - im selben Lauf haetten die Modelle den
Stand vor dem `UPDATE`. Anschliessend den Preflight (Verifikationsregel in Abschnitt 2 der SKILL.md)
gegen das Quellformular fahren; Feldzahl und Feldwerte muessen uebereinstimmen.

Merke:
- Es wird **nichts ueberschrieben** - es entsteht ein neues Formular mit neuer ID.
  „Restore" = neu anlegen, das alte danach ggf. per `wp ninja-forms delete form <id>`
  entfernen. Zum **Klonen** (z.B. DE→FR): auf der Quelle exportieren, auf der
  Ziel-Subsite anlegen.
- Form-IDs im Export sind die der Quelle; beim Anlegen neu vergeben → Referenzierung
  weiter ueber den Titel (Lese-Snippets laut SKILL.md).
- Die `.nff` ins Jail-`/tmp` schreiben, fuer ein echtes Backup vom Host abholen, danach im
  Jail aufraeumen.

Zurueck zur Uebersicht: [SKILL.md](../SKILL.md).
