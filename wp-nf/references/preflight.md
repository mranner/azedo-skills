# Preflight/Verify

Das Ausfuehrungsrezept zur Verifikationsregel aus Abschnitt 2 der
[SKILL.md](../SKILL.md): vor jedem Write und nach jedem Write laufen lassen.

## Drift ueber alle vier Ablagen — plus Zuordnung

Vor Read-Interpretation, **vor jedem Write** und **nach jedem Write** klaeren, ob
die vier Ablagen aus Abschnitt 2 der [SKILL.md](../SKILL.md) denselben Wert
fuehren. Eine Drift ist exakt die Signatur der beiden stillen Fehler: „geaendert, aendert sich nichts" (Cache stale)
und „geaendert, steht aber noch alt da" (Legacy-Spalte bzw. WPML-Quellstring).

Als **fuenfte Pruefgroesse** kommen `parent_id` und die Feldzahl des Formulars
dazu. Sie sind keine Wertablage, sondern die Stelle, an der ein Write auf einer
WPML-Site danebengeht ([wpml-writes.md](wpml-writes.md)): der Wert stimmt dann in
allen vier Ablagen, das Feld haengt aber am falschen Formular. Die Feldzahl hat keinen Sollwert in
der DB — sie wird gegen den `.nff`-Export von **vor** dem Write gehalten
([export-import.md](export-import.md)).

```php
<?php
// nf-preflight.php <form_id> <field_id> <setting_key>
//   wp eval-file nf-preflight.php <form_id> <field_id> default --url=<subsite>
$form_id  = intval( $args[0] );
$field_id = intval( $args[1] );
$key      = $args[2];

global $wpdb;
$meta_table = $wpdb->prefix . 'nf3_field_meta';

// Struktur-Check: existiert wirklich keine settings-Spalte? (Version-agnostisch)
$has_settings_col = $wpdb->get_var(
    "SHOW COLUMNS FROM {$wpdb->prefix}nf3_fields LIKE 'settings'" );
echo "nf3_fields.settings-Spalte: " . ( $has_settings_col ? "JA (aelteres Layout!)" : "nein" ) . "\n";

// 1. nf3_field_meta — Quelle beim Lesen
$meta_val = $wpdb->get_var( $wpdb->prepare(
    "SELECT value FROM $meta_table WHERE parent_id=%d AND `key`=%s", $field_id, $key ) );

// 2. Form-Cache — Render-Quelle (get_nf_cache() unserialisiert selbst, kein json_decode!)
$cache     = WPN_Helper::get_nf_cache( $form_id );
$cache_val = null;
if ( is_array( $cache ) && ! empty( $cache['fields'] ) ) {
    foreach ( $cache['fields'] as $cf ) {
        if ( $cf['id'] == $field_id ) { $cache_val = $cf['settings'][ $key ] ?? null; break; }
    }
}

// 3. Spalte in nf3_fields — bei `default` ist die Spalte die alte Seite,
//    bei `label` die Meta-Zeile (SKILL.md, Abschnitt 2); verglichen wird so oder so
$col_map = array( 'default' => 'default_value', 'label' => 'label' );
$col_val = isset( $col_map[ $key ] )
    ? $wpdb->get_var( $wpdb->prepare(
        "SELECT `{$col_map[$key]}` FROM {$wpdb->prefix}nf3_fields WHERE id=%d", $field_id ) )
    : null;

// 4. WPML-Quellstring — rendert als Fallback, solange keine Uebersetzung existiert
$icl      = $wpdb->prefix . 'icl_strings';
$has_wpml = $wpdb->get_var( "SHOW TABLES LIKE '$icl'" ) === $icl;
$icl_val  = $has_wpml ? $wpdb->get_var( $wpdb->prepare(
    "SELECT value FROM $icl WHERE context=%s AND name=%s",
    "ninja-forms-$form_id", "default-$field_id" ) ) : null;

// 5. Zuordnung: haengt das Feld noch am erwarteten Formular, und wie viele
//    Felder hat dieses Formular jetzt? (Sollwert: der .nff-Export von vorher)
$parent_id   = $wpdb->get_var( $wpdb->prepare(
    "SELECT parent_id FROM {$wpdb->prefix}nf3_fields WHERE id=%d", $field_id ) );
$field_count = $wpdb->get_var( $wpdb->prepare(
    "SELECT COUNT(*) FROM {$wpdb->prefix}nf3_fields WHERE parent_id=%d", $form_id ) );

printf( "1 meta         : %s\n", var_export( $meta_val,  true ) );
printf( "2 cache        : %s\n", var_export( $cache_val, true ) );
printf( "3 %-12s: %s\n", $col_map[ $key ] ?? 'spalte',
    isset( $col_map[ $key ] ) ? var_export( $col_val, true ) : '(nur fuer key=default|label)' );
printf( "4 icl_strings  : %s\n", $has_wpml ? var_export( $icl_val, true ) : '(kein WPML)' );
printf( "5 parent_id    : %s (erwartet %d) | Felder in Form %d: %d\n",
    var_export( $parent_id, true ), $form_id, $form_id, $field_count );

$drift = array();
if ( $meta_val !== $cache_val )                       { $drift[] = 'cache'; }
if ( $col_val !== null && $col_val !== $meta_val )    { $drift[] = $col_map[ $key ]; }
if ( $icl_val !== null && $icl_val !== $meta_val )    { $drift[] = 'icl_strings'; }
if ( (int) $parent_id !== $form_id )                  { $drift[] = 'parent_id'; }

echo $drift
    ? 'DRIFT gegen meta: ' . implode( ', ', $drift ) . "\n"
    : "OK: konsistent\n";
```

Meldet der Lauf `cache`, fehlt `delete_nf_cache()`/`build_nf_cache()` (SKILL.md,
Abschnitt 4).
Meldet er `parent_id`, ist der Write auf einer WPML-Site ins Quellformular
gelaufen — Reparatur in [wpml-writes.md](wpml-writes.md), und zwar bevor weitere Felder geschrieben
werden. Meldet er `default_value`, `label` oder `icl_strings`, sind das die
Ablagen, die die Model-API nicht mitschreibt — gezielt nachziehen:

```php
// 3. Legacy-Spalte
$wpdb->update( "{$wpdb->prefix}nf3_fields",
    array( 'default_value' => $neu ), array( 'id' => $field_id ) );

// 3b. Meta-Zeile bei key=label (dort ist die Spalte die frische Seite)
$wpdb->update( "{$wpdb->prefix}nf3_field_meta",
    array( 'value' => $neu, 'meta_value' => $neu ),
    array( 'parent_id' => $field_id, 'key' => 'label' ) );

// 4. WPML-Quellstring
$wpdb->update( "{$wpdb->prefix}icl_strings",
    array( 'value' => $neu ),
    array( 'context' => "ninja-forms-$form_id", 'name' => "default-$field_id" ) );
```

Danach den Preflight erneut laufen lassen. Die Alternative ohne SQL ist, das
Formular einmal ueber das Admin-UI zu speichern — das schreibt beide Ablagen mit,
ist auf einer Multisite aber je Subsite ein Handgriff.

Zurueck zur Uebersicht: [SKILL.md](../SKILL.md).
