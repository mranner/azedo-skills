# Reads: Formulare auflisten, Felder + Settings dumpen

Die beiden Standard-Reads des Skills. Harmlos — sie aendern nichts und sind der
uebliche erste Schritt vor jedem Write.

## Formulare auflisten + Titel→ID-Mapping

Form-IDs sind subsite-spezifisch — **nie raten, immer nachschlagen** und ueber den
Formular-**Titel** mappen.

Schnellster Weg (native Extension, Abschnitt 1 der [SKILL.md](../SKILL.md)):

```
wp ninja-forms list --url=<subsite>
```

Falls die Extension nicht geladen ist oder maschinenlesbare Ausgabe gebraucht wird,
das Snippet (mit Tabellen-Guard):

```php
<?php
// nf-list-forms.php — wp eval-file nf-list-forms.php --url=<subsite>
global $wpdb;
$table = $wpdb->prefix . 'nf3_forms';

if ( $wpdb->get_var( "SHOW TABLES LIKE '$table'" ) !== $table ) {
    echo "Tabelle $table existiert nicht (Ninja Forms auf dieser Subsite aktiv?)\n";
    exit( 0 );
}

foreach ( $wpdb->get_results( "SELECT id, title FROM $table ORDER BY id" ) as $f ) {
    echo "ID:{$f->id} | {$f->title}\n";
}
```

---

## Felder + Settings eines Formulars auslesen

Fuer Reads die **Model-API** nutzen, nicht die Rohtabellen: `get_settings()` merged
Spalten + Meta und deserialisiert `options` selbst — damit umgeht man die
Meta-Footguns aus Abschnitt 2 der [SKILL.md](../SKILL.md) vollstaendig.

```php
<?php
// nf-dump-fields.php <form_id> — wp eval-file nf-dump-fields.php <form_id> --url=<subsite>
$form_id = intval( $args[0] );
$fields  = Ninja_Forms()->form( $form_id )->get_fields();

foreach ( $fields as $field ) {
    $s = $field->get_settings();
    printf( "#%d  key=%s  type=%s  label=%s\n",
        $field->get_id(), $s['key'] ?? '', $s['type'] ?? '', $s['label'] ?? '' );
    printf( "     element_class=%s  container_class=%s\n",
        $s['element_class'] ?? '', $s['container_class'] ?? '' );

    if ( isset( $s['default'] ) && $s['default'] !== '' ) {
        printf( "     default(HTML)=%s\n", trim( $s['default'] ) );
    }
    if ( isset( $s['options'] ) && is_array( $s['options'] ) ) {
        foreach ( $s['options'] as $o ) {
            printf( "     option: label=%s value=%s\n", $o['label'] ?? '', $o['value'] ?? '' );
        }
    }
}
```

Zurueck zur Uebersicht: [SKILL.md](../SKILL.md).
