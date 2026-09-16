# Writes auf WPML-Uebersetzungsformularen

Gilt nur auf mehrsprachigen Sites mit `wpml-ninja-forms`. Auf einer Site ohne
WPML ist nichts davon noetig — dort gilt der Write-Ablauf aus Abschnitt 4 der
[SKILL.md](../SKILL.md) unveraendert.

## Ein Write kann das Feld in ein anderes Formular verschieben

Auf Sites mit `wpml-ninja-forms` aendert `$field->save()` unter Umstaenden die
**`parent_id`** des Feldes — das Feld wandert vom Uebersetzungs- ins
Quellformular. Betroffen sind nur Felder, deren Formular eine WPML-Uebersetzung
eines anderen Formulars ist; Felder normaler Formulare bleiben im selben Lauf
korrekt zugeordnet. Verdacht: ein Hook des Uebersetzungs-Plugins im
Save-Vorgang. Im Quellcode nicht abschliessend verifiziert.

Die Verifikation ueber die vier Ablagen deckt das **nicht** auf: der Wert steht
ueberall richtig, nur haengt das Feld am falschen Formular. Sichtbar wird es
erst, wenn im Frontend ein Feld fehlt — im belegten Fall (CR4656) der
Absende-Button des italienischen Login-Formulars, der in der deutschen Fassung
ein zweites Mal auftauchte.

Deshalb auf WPML-Sites die `parent_id` vor und nach **jedem** Write festhalten,
vergleichen und im Fall der Faelle sofort zurueckschreiben — per direktem
`UPDATE`, weil in der Model-API genau der ausloesende Hook sitzt:

```php
<?php
// Ergaenzung zum Write oben — nur die parent_id-Klammer
global $wpdb;
$ftab = $wpdb->prefix . 'nf3_fields';

$before = $wpdb->get_row( $wpdb->prepare(
    "SELECT parent_id, `order` FROM $ftab WHERE id=%d", $field_id ) );

// … update_setting() + save() wie oben …

$after = $wpdb->get_row( $wpdb->prepare(
    "SELECT parent_id, `order` FROM $ftab WHERE id=%d", $field_id ) );

if ( (int) $before->parent_id !== (int) $after->parent_id ) {
    printf( "ACHTUNG: Feld %d von Form %s nach Form %s gewandert — setze zurueck\n",
        $field_id, $before->parent_id, $after->parent_id );

    $wpdb->update( $ftab,
        array( 'parent_id' => $before->parent_id, 'order' => $before->order ),
        array( 'id' => $field_id ) );

    // Caches BEIDER Formulare neu bauen — das Feld fehlt im einen und steht zuviel im anderen
    foreach ( array( $before->parent_id, $after->parent_id ) as $fid ) {
        WPN_Helper::delete_nf_cache( $fid );
        WPN_Helper::build_nf_cache( $fid );
    }
}
```

Bei einem Lauf ueber mehrere Felder die `parent_id` je Feld pruefen, nicht erst
am Ende: der zweite Write laeuft sonst bereits gegen ein Formular, dessen
Feldbestand nicht mehr stimmt.

## Model-API oder direktes SQL auf Uebersetzungsformularen?

Naheliegend waere, Writes auf Uebersetzungsformularen grundsaetzlich per
`UPDATE` zu fahren — dann laeuft kein Hook mit und die `parent_id` bleibt
unberuehrt. Der Preis steht in Abschnitt 2 der [SKILL.md](../SKILL.md):
`nf3_field_meta` fuehrt `key`/`value` **und** `meta_key`/`meta_value`, beide Paare muss das eigene SQL dann konsistent
halten, und eine noch gar nicht existierende Meta-Zeile legt kein `UPDATE` an.

| | Model-API + parent_id-Guard | direktes SQL |
|---|---|---|
| Spaltenpaare in `nf3_field_meta` | schreibt das Plugin | selbst konsistent halten |
| Setting noch ohne Meta-Zeile | wird angelegt | `INSERT` selbst bauen |
| `parent_id` | kann wandern → Guard noetig | bleibt unberuehrt |
| Cache | `delete`/`build` noetig | `delete`/`build` noetig |

**Empfehlung:** bei der Model-API bleiben und den Guard mitlaufen lassen — er
kostet zwei `SELECT`s und faengt den Fall vollstaendig ab. Direktes SQL nur dort,
wo ausschliesslich **vorhandene** Meta-Zeilen zu aendern sind und ein Lauf viele
Felder eines Uebersetzungsformulars trifft; dann beide Spaltenpaare in einem
`UPDATE` setzen:

```php
$wpdb->update( "{$wpdb->prefix}nf3_field_meta",
    array( 'value' => $neu, 'meta_value' => $neu ),
    array( 'parent_id' => $field_id, 'key' => $key ) );
```

Der Cache-Schritt entfaellt dabei nicht — er haengt am Formular, nicht am
Schreibweg.

Zurueck zur Uebersicht: [SKILL.md](../SKILL.md).
