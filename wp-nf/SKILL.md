---
name: wp-nf
description: >
  Ninja Forms in WordPress-(Multi-)Sites per WP-CLI im FreeBSD-Jail:
  Formulare auflisten, Felder und Settings auslesen, CSS-Klassen
  (element_class) für Click-Tracking setzen, Formulare exportieren und
  importieren (Backup, Klonen) - reproduzierbar statt über das Admin-UI;
  kennt die vier Ablagen eines Feldwerts (Meta, Form-Cache, Legacy-Spalte,
  WPML-Quellstring). Auch bei "Ninja Forms", "NF-Formular", "nf3_fields",
  "Formular exportieren".
  Trigger: /wp-nf.
allowed-tools: [Bash, Read, Write]
---

# wp-nf — Ninja-Forms-Administration via WP-CLI

Referenz fuer das Auslesen und gezielte Aendern von **Ninja-Forms**-Formularen in
WordPress-(Multi-)Sites per `wp` CLI im FreeBSD-Jail. **Read-first**: Formulare und
Felder auslesen ist der Regelfall; Writes (z.B. `element_class` setzen) sind wenige,
sorgfaeltige Operationen mit Backup + Cache-Invalidierung + Verify.

Grenzt an zwei Nachbar-Skills und dupliziert deren Wissen bewusst **nicht**:

- **[[wp-cli]]** — Jail-Zugriff, `wp eval-file`, csh-Quoting, DB-Ops. wp-nf setzt das
  voraus und verweist darauf statt es zu wiederholen.
- **[[wp-pys]]** — PixelYourSite-Event-/Trigger-Config. Die Verbindung ist das
  CSS-Click-Tracking: PYS liefert den **Selektor**, das NF-Feld die **Klasse**
  (`element_class`). Siehe Abschnitt 6.

Belegte Evidenzbasis: CR4266 (Kundenprojekt, GA4-CSS-Click-Events auf einem Shared-Webhost),
CR4630/CR4633 (Bild-URLs in HTML-Feldern einer mehrsprachigen Multisite).
Verifiziert gegen **Ninja Forms 3.14.8** auf apache1.acme.com.

---

## 1. Zugriff

Kein eigener Zugriffsweg — es gilt der aus **[[wp-cli]]** (Jail → `wp eval-file`).
Bei komplexem Quoting das PHP-Script ins Jail legen und dort ausfuehren (csh-Fallstricke,
siehe [[freebsd-shell-pitfalls]]).

Beispiel (Multisite; Form-IDs sind **subsite-spezifisch**):

```
sudo ssh -C root@jailer.acme.com "iocage exec apache1.acme.com sh -c \
  'sudo -u wwwcustomer wp \
   --path=/www/home/wwwcustomer/www.example.com \
   eval-file /tmp/<script>.php --url=<subsite>'"
```

`--url=<subsite>` waehlt die Subsite (bestimmt das Tabellen-Prefix `wp_{blog}_nf3_*`).

### Native `wp ninja-forms`-Extension

Ninja Forms bringt eine eigene WP-CLI-Extension mit (`wp ninja-forms <sub>`, registriert
in `ninja-forms.php`). Sie deckt nur Grundlegendes ab — fuer Settings-Detail,
`element_class`-Writes und Export/Import ist weiterhin `eval-file` (Abschnitte 4/5/8)
noetig:

| Subcommand | Zweck |
|---|---|
| `wp ninja-forms list` | Formulare auflisten (`#id - Titel`) |
| `wp ninja-forms get <id>` | Formular + Feld-`key`/`label` (**keine** Settings-Details) |
| `wp ninja-forms form "<Titel>"` | leeres Formular anlegen |
| `wp ninja-forms delete form <id>` | Formular loeschen (Rueckfrage; `--yes` unterdrueckt) |
| `wp ninja-forms info` | NF-Version / Pfade |

**Nicht enthalten:** Export/Import, Feld-Settings lesen/schreiben, Cache-Handling — genau
das liefert dieser Skill.

---

## 2. Datenmodell (verifiziert an NF 3.14.8)

| Tabelle | Inhalt |
|---|---|
| `wp_{blog}_nf3_forms` | Formulare: `id`, `title`. **IDs subsite-spezifisch** → Mapping ueber Titel. |
| `wp_{blog}_nf3_fields` | Felder: `id`, `label`, `key`, `type`, `parent_id` (=Form-ID), `order`, `required`, `default_value`, `label_pos` u.a. |
| `wp_{blog}_nf3_field_meta` | Feld-Settings als key/value: **`element_class`**, `container_class`, `default` (HTML-Inhalt), `value`, `options` (serialisiert). |
| `wp_{blog}_nf3_upgrades` | **Form-Cache** (Spalte `cache`, **PHP-serialisiert**) — die Render-Quelle. Siehe unten. |
| `wp_{blog}_icl_strings` | Nur mit WPML: **Quellstring** je Feld (Kontext `ninja-forms-<form_id>`, Name `default-<field_id>`) — rendert als Fallback ohne Uebersetzung. |

### Wo Settings wirklich liegen — und was rendert

Dies ist der zentrale Footgun. Fuer NF **3.14.8** gilt (aus dem Plugin-Quellcode
`includes/Abstracts/Model.php` + `includes/Helper.php` verifiziert):

- **`element_class` und die meisten Feld-Settings liegen in `nf3_field_meta`** —
  als key/value-Zeilen. **`nf3_fields` hat KEINE `settings`-Spalte** (nur die oben
  gelisteten Spalten). Die aeltere Annahme „Settings serialisiert in `nf3_fields.settings`"
  trifft auf 3.14.8 **nicht** zu; sie stammt aus einem frueheren DB-Layout. → Vor
  Annahmen immer die tatsaechliche Struktur pruefen (`SHOW COLUMNS`), nicht die Version
  raten.
- **Gerendert wird aus dem Form-Cache, nicht aus `nf3_field_meta`.**
  `WPN_Helper::use_cache()` liefert hart `true` → der Cache ist **immer** massgeblich
  fuer das, was das Frontend anzeigt. Er liegt serialisiert in `nf3_upgrades.cache`
  (Fallback: Option `nf_form_{id}`) und enthaelt je Feld eine **Kopie** des
  `settings`-Arrays.
- **Praezedenz beim Lesen (`get_settings()`):** zuerst `nf3_field_meta`, der Cache nur
  als Fallback wenn Meta leer. Ein Model-/DB-**Read** sieht eine Meta-Aenderung also
  sofort — das gerenderte Formular aber erst nach Cache-Neuaufbau.
- **Daraus der Write-Footgun** („geaendert, aendert sich aber nichts"): Ein direkter
  Write in `nf3_field_meta` aktualisiert die Quelle, laesst aber `nf3_upgrades` **stale**
  → Frontend zeigt weiter den alten Wert. **Immer Cache invalidieren** (Abschnitt 5).
- **Dual-Column-Quirk:** `nf3_field_meta` fuehrt `key`/`value` **und** `meta_key`/`meta_value`;
  das Plugin schreibt beide Paare. Raw-SQL muss beide konsistent halten → besser die
  Model-API nutzen (Abschnitt 5).

### Ein Feldwert liegt an bis zu vier Stellen

Meta und Cache sind nur zwei davon. Wer nur diese beiden gegenliest, haelt eine
Aenderung fuer erledigt, waehrend zwei Kopien des alten Werts stehenbleiben:

| # | Ablage | Schreibt die Model-API mit? | Wirkung |
|---|---|---|---|
| 1 | `nf3_field_meta` | ja | Quelle beim Lesen ueber `get_settings()` |
| 2 | `nf3_upgrades.cache` | erst nach `delete_nf_cache()`/`build_nf_cache()` | Render-Quelle des Frontends |
| 3 | `nf3_fields.default_value` | **nein** | rendert nicht, ist aber die sichtbarste Stelle bei jeder direkten DB-Suche |
| 4 | `icl_strings` (WPML) | **nein** | rendert als Fallback, solange fuer die Sprache keine Uebersetzung existiert |

- **`nf3_fields.default_value`** — die Legacy-Spalte. `update_setting()` / `save()`
  fassen sie nicht an. Der Wert dort ist nach jedem Write veraltet und produziert
  beim naechsten `SELECT … FROM nf3_fields` den Fehlbefund „ist ja gar nicht
  geaendert".
- **WPML-Quellstring** — auf mehrsprachigen Sites registriert `wpml-ninja-forms`
  den Feldinhalt als Quellstring: Kontext `ninja-forms-<form_id>`, Name
  `default-<field_id>`. Gibt es fuer die aktuelle Sprache keine Uebersetzung,
  rendert dieser Quellstring als Fallback — also weiter der alte Wert. Die
  Registrierung laeuft nur beim Speichern ueber das Admin-UI erneut; eine
  Aenderung ueber die Model-API erreicht sie nicht. (Vorhandene Uebersetzungen
  liegen daneben in `icl_string_translations` und sind eigene Kopien.)

**Verifikationsregel:** Nach einem Write **alle vier** Ablagen gegenlesen, nicht
nur Meta und Cache — Snippet in Abschnitt 7. Ablage 3 und 4 anschliessend per
gezieltem `UPDATE` nachziehen (ebenfalls Abschnitt 7); auf einer Site ohne WPML
entfaellt Ablage 4, die Tabelle existiert dann nicht.

Beleg (CR4630/CR4633): Nach einem Fix an sechs HTML-Feldern standen Meta und
Cache auf dem neuen Wert, `default_value` und der WPML-Quellstring weiterhin auf
dem alten. Die Verifikation „Meta plus Cache" hat den halb wirkungslosen Fix
nicht gezeigt.

### Der Form-Cache ist PHP-serialisiert, nicht JSON

`nf3_upgrades.cache` enthaelt `serialize()`-Ausgabe (`a:4:{s:2:"id";…}`). Ein
`json_decode()` darauf liefert stillschweigend `null`, und die anschliessende
Pruefung meldet dann fuer **jedes** Feld eine Abweichung — ein Fehlalarm, der wie
ein defekter Cache aussieht. Richtig ist `unserialize()`;
`WPN_Helper::get_nf_cache( $form_id )` erledigt das selbst, der Fallstrick trifft
nur den Weg ueber rohes SQL.

Struktur zur Orientierung:

- oberste Keys: `id`, `fields`, `actions`, `settings`
- Eintrag in `fields`: Feld-ID unter `['id']`, die Werte unter `['settings']`
- Eintrag in `actions`: `{ settings: {…}, id: <n> }`

### Weitere Footguns

- `options` (z.B. bei `listradio`/`checkbox`) ist ein **serialisiertes Array**; jede
  Option hat `label` + `value`.
- HTML-Feld-Inhalt (Feldtyp `html`) steht im Meta-Key **`default`** — dort sitzt z.B.
  ein Link mit/ohne CSS-Klasse.
- **Submissions/Entries** liegen grundsaetzlich als CPT `nf_sub` vor — koennen aber
  **leer** sein (im belegten Fall gingen Formulare direkt an ein externes CRM, `nf_sub` ist ueber
  alle Zeiten leer). Ein Abgleich „Einreichungen vs. Events" ist dann ueber die WP-DB
  **nicht** moeglich. Vor Auswertung pruefen, ob lokal ueberhaupt gespeichert wird.

---

## 3. Formulare auflisten + Titel→ID-Mapping

Form-IDs sind subsite-spezifisch — **nie raten, immer nachschlagen** und ueber den
Formular-**Titel** mappen.

Schnellster Weg (native Extension, Abschnitt 1):

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

## 4. Felder + Settings eines Formulars auslesen

Fuer Reads die **Model-API** nutzen, nicht die Rohtabellen: `get_settings()` merged
Spalten + Meta und deserialisiert `options` selbst — damit umgeht man die
Meta-Footguns aus Abschnitt 2 vollstaendig.

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

---

## 5. Write: `element_class` / HTML-Link-Klasse setzen

Wenige, sorgfaeltige Writes — immer nach dem Muster **Backup → Write → Cache
invalidieren → Verify ueber alle vier Ablagen** (Abschnitt 2). Als **Backup** vor dem Write das ganze Formular exportieren
(Abschnitt 8, `nf-export-form.php`) — ein vollstaendiger, wiederherstellbarer Stand statt
nur des alten Einzelwerts. Der Cache-Schritt ist nicht optional (Abschnitt 2): ohne ihn
rendert das Frontend weiter den alten Wert.

Bevorzugt ueber die Model-API (schreibt `nf3_field_meta` konsistent inkl. beider
Spaltenpaare):

```php
<?php
// nf-set-class.php <form_id> <field_id> <element_class>
//   wp eval-file nf-set-class.php <form_id> <field_id> <klasse> --url=<subsite>
$form_id  = intval( $args[0] );
$field_id = intval( $args[1] );
$class    = $args[2];

$field = Ninja_Forms()->form()->field( $field_id )->get();
if ( ! $field || ! $field->get_id() ) { echo "Feld $field_id nicht gefunden\n"; exit( 1 ); }

// Alten Wert protokollieren (echtes Backup = Form-Export, Abschnitt 8)
$old = $field->get_setting( 'element_class' );
echo "alt : " . var_export( $old, true ) . "\n";

// Write ueber die Model-API
$field->update_setting( 'element_class', $class );
$field->save();

// Cache invalidieren + neu aufbauen (sonst bleibt das Frontend stale)
WPN_Helper::delete_nf_cache( $form_id );
WPN_Helper::build_nf_cache( $form_id );

// Verify aus frischem Objekt
$verify = Ninja_Forms()->form()->field( $field_id )->get()->get_setting( 'element_class' );
echo "neu : " . var_export( $verify, true ) . "\n";
echo ( $verify === $class ) ? "OK\n" : "FEHLER: Wert nicht gesetzt\n";
```

> [!warning] Vor dem ersten produktiven Einsatz an einem **Testfeld** verifizieren.
> Die Read-Snippets (Abschnitt 3/4/7) sind harmlos; dieser Write ist der einzige
> heikle Teil und noch nicht gegen einen realen Fall gefahren. Immer zuerst
> Abschnitt 7 (Preflight) laufen lassen, um Ausgangswert und Cache-Zustand zu kennen.

Das `echo "OK"` am Ende belegt nur die Ablagen 1 und 2: `nf3_fields.default_value`
und der WPML-Quellstring bleiben auf dem alten Wert, weil `update_setting()`/`save()`
sie nicht mitschreiben — bei Feldtyp `html` auf einer mehrsprachigen Site ist der Fix
damit zur Haelfte wirkungslos. Nach dem Write deshalb **immer** Abschnitt 7 fahren und
die beiden Ablagen bei Bedarf nachziehen.

HTML-Feld-Link-Klasse (Feldtyp `html`) sitzt im Setting **`default`** (der HTML-Markup) —
dort per gezieltem String-Ersatz die Klasse am `<a>` ergaenzen, dann derselbe
Cache-/Verify-Ablauf.

---

## 6. Diagnose-Muster: PYS-CSS-Click ↔ NF-`element_class`

Ob ein PixelYourSite-`css_click`-Event feuert, haengt an **zwei** Stellen: dem
PYS-Selektor **und** der CSS-Klasse im Ziel-Formularfeld.

**Merksatz:** Beim Subsite-Vergleich von PYS-CSS-Click-Tracking immer **beides**
pruefen — die PYS-Selektoren (→ [[wp-pys]], `_pys_event_triggers`) **und** die
NF-Feld-Klassen (`element_class` bzw. die Klasse im HTML-Feld). Der Bug sitzt oft im
NF-Feld, nicht in der Tracking-Config.

Worked Example (CR4266): Auf webhost1 feuerte `support_cancelled` nicht, weil im
Kuendigungsformular die Klassen fehlten (`submit` ohne `cancel-submit`, HTML-Link ohne
`cancellation-edit`) — obwohl die PYS-Config byte-identisch zu sgb-fss war. Klassen
ergaenzt → Event feuerte.

Ein Subsite-Vergleich braucht keinen eigenen Befehl: Abschnitt 3 (Forms/IDs je Subsite)
+ Abschnitt 4 (Felder dumpen) nebeneinanderlegen.

---

## 7. Preflight/Verify: Drift ueber alle vier Ablagen

Vor Read-Interpretation, **vor jedem Write** und **nach jedem Write** klaeren, ob
die vier Ablagen aus Abschnitt 2 denselben Wert fuehren. Eine Drift ist exakt die
Signatur der beiden stillen Fehler: „geaendert, aendert sich nichts" (Cache stale)
und „geaendert, steht aber noch alt da" (Legacy-Spalte bzw. WPML-Quellstring).

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

// 3. nf3_fields.default_value — Legacy-Spalte, von der Model-API nicht mitgeschrieben
$col_val = ( $key === 'default' )
    ? $wpdb->get_var( $wpdb->prepare(
        "SELECT default_value FROM {$wpdb->prefix}nf3_fields WHERE id=%d", $field_id ) )
    : null;

// 4. WPML-Quellstring — rendert als Fallback, solange keine Uebersetzung existiert
$icl      = $wpdb->prefix . 'icl_strings';
$has_wpml = $wpdb->get_var( "SHOW TABLES LIKE '$icl'" ) === $icl;
$icl_val  = $has_wpml ? $wpdb->get_var( $wpdb->prepare(
    "SELECT value FROM $icl WHERE context=%s AND name=%s",
    "ninja-forms-$form_id", "default-$field_id" ) ) : null;

printf( "1 meta         : %s\n", var_export( $meta_val,  true ) );
printf( "2 cache        : %s\n", var_export( $cache_val, true ) );
printf( "3 default_value: %s\n", ( $key === 'default' ) ? var_export( $col_val, true ) : '(nur fuer key=default)' );
printf( "4 icl_strings  : %s\n", $has_wpml ? var_export( $icl_val, true ) : '(kein WPML)' );

$drift = array();
if ( $meta_val !== $cache_val )                       { $drift[] = 'cache'; }
if ( $col_val !== null && $col_val !== $meta_val )    { $drift[] = 'default_value'; }
if ( $icl_val !== null && $icl_val !== $meta_val )    { $drift[] = 'icl_strings'; }

echo $drift
    ? 'DRIFT gegen meta: ' . implode( ', ', $drift ) . "\n"
    : "OK: konsistent\n";
```

Meldet der Lauf `cache`, fehlt `delete_nf_cache()`/`build_nf_cache()` (Abschnitt 5).
Meldet er `default_value` oder `icl_strings`, sind das die beiden Ablagen, die die
Model-API nicht mitschreibt — gezielt nachziehen:

```php
// 3. Legacy-Spalte
$wpdb->update( "{$wpdb->prefix}nf3_fields",
    array( 'default_value' => $neu ), array( 'id' => $field_id ) );

// 4. WPML-Quellstring
$wpdb->update( "{$wpdb->prefix}icl_strings",
    array( 'value' => $neu ),
    array( 'context' => "ninja-forms-$form_id", 'name' => "default-$field_id" ) );
```

Danach den Preflight erneut laufen lassen. Die Alternative ohne SQL ist, das
Formular einmal ueber das Admin-UI zu speichern — das schreibt beide Ablagen mit,
ist auf einer Multisite aber je Subsite ein Handgriff.

---

## 8. Export / Import (Backup & Klonen)

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
  ueber den Titel (Abschnitt 3).
- Die `.nff` ins Jail-`/tmp` schreiben, fuer ein echtes Backup vom Host abholen, danach im
  Jail aufraeumen.

---

## Cross-Links

- **[[wp-cli]]** — Jail-Zugriff, `wp eval-file`, DB-Ops, csh-Quoting.
- **[[wp-pys]]** — PYS-Event-/Trigger-Config; NF-ID-Lookup verweist hierher (Abschnitt 3).
- Wiki `wiki/acme/wiki/services/customer-multisite.md` — geloeste GA4-Notiz.
- Kanboard CR4266 (Attachment `handoff-ninja-forms-knowledge.md`), CR4409 (Skill-Entscheidung),
  CR4633 (vier Ablagen + Cache-Format).

## Quellen

- Plugin-Quellcode Ninja Forms 3.14.8, apache1.acme.com:
  `includes/Abstracts/Model.php` (`get_settings`/`_save_setting`),
  `includes/Helper.php` (`get_nf_cache`/`build_nf_cache`/`delete_nf_cache`/`use_cache`).
- DB-Struktur `nf3_fields`/`nf3_field_meta`/`nf3_upgrades` (verifiziert 2026-07-17).
- `nf3_fields.default_value`, WPML-Quellstrings in `icl_strings` und das
  `serialize()`-Format von `nf3_upgrades.cache` (verifiziert 2026-09-11).
