# wp-pys: Operationen (PHP-Snippets)

Die Snippets zu Abschnitt 3 der [SKILL.md](../SKILL.md). Ausgefuehrt werden sie
per `wp eval-file` wie dort in Abschnitt 2 beschrieben; Datenmodell und
Fallstricke (Abschnitt 1 und 4) setzen sie voraus.

**Inhalt:**
- 3.1 Events auflisten (list-events) - read
- 3.2 Plugin-Config lesen (show-config) - read
- 3.3 Pixel-Ziel aktivieren (enable-target) - write
- 3.4 Event klonen (clone-event) - write
- 3.5 Trigger aendern (set-selector / set-forms) - write
- 3.6 Verifizieren (verify) - read
- 3.7 Backup / Restore

## 3.1 Events auflisten (list-events)

```php
<?php
// pys-list-events.php — via: wp eval-file pys-list-events.php --url=<subsite>

$events = get_posts([
    'post_type'   => 'pys_event',
    'post_status' => 'any',
    'numberposts' => -1,
]);

foreach ($events as $ev) {
    $data     = get_post_meta($ev->ID, '_pys_event_data', true);
    $triggers = get_post_meta($ev->ID, '_pys_event_triggers', true);
    $state    = get_post_meta($ev->ID, '_pys_event_state', true);

    $triggers_arr = $triggers ? unserialize($triggers) : [];

    $trigger_info = [];
    if (is_array($triggers_arr)) {
        foreach ($triggers_arr as $t) {
            $type = $t->trigger_type ?? '?';
            if ($type === 'css_click') {
                $sel = array_map(fn($e) => ((array) $e)['value'] ?? '?', (array)($t->triggers ?? []));
                $trigger_info[] = "css_click: " . implode(', ', $sel);
            } elseif ($type === 'ninjaform') {
                $trigger_info[] = "ninjaform: " . implode(', ', (array)($t->forms ?? []));
            } else {
                $trigger_info[] = $type;
            }
        }
    }

    // GA4 laeuft ueber ga_ads (SKILL.md, Abschnitt 1), ga_* ist dort false
    $targets = [];
    if (!empty($data['ga_ads_enabled']))   $targets[] = 'GA4(ga_ads)';
    if (!empty($data['ga_enabled']))       $targets[] = 'ga';
    if (!empty($data['facebook_enabled'])) $targets[] = 'Facebook';
    if (!empty($data['gtm_enabled']))      $targets[] = 'GTM';

    $ga_name = $data['ga_ads_custom_event_action'] ?? $data['ga_custom_event_action'] ?? '-';

    printf("ID:%d | %s | state:%s | targets:%s | ga_name:%s | triggers:%s\n",
        $ev->ID,
        $ev->post_title,
        $state ?: 'inactive',
        implode(',', $targets) ?: 'none',
        $ga_name,
        implode('; ', $trigger_info) ?: 'none'
    );
}
```

## 3.2 Plugin-Config lesen (show-config)

```php
<?php
// pys-show-config.php — via: wp eval-file pys-show-config.php --url=<subsite>

global $wpdb;
$table = $wpdb->prefix . 'pys_options';

$rows = $wpdb->get_results("SELECT * FROM $table WHERE option_name IN ('pys_ga', 'pys_gtm', 'pys_facebook', 'pys_google_ads', 'pys_core')");

foreach ($rows as $row) {
    $val = maybe_unserialize($row->option_value);
    echo "=== {$row->option_name} ===\n";
    print_r($val);
    echo "\n";
}
```

## 3.3 Pixel-Ziel aktivieren (enable-target)

```php
<?php
// pys-enable-target.php — via: wp eval-file pys-enable-target.php <event_id> <ga4_name> --url=<subsite>
// $args[0] = Event-Post-ID, $args[1] = GA4-Event-Name (z.B. "kuendigung_abgesendet")

$event_id = (int) $args[0];
$ga_name  = $args[1];

$data = get_post_meta($event_id, '_pys_event_data', true);
if (!is_array($data)) {
    echo "FEHLER: _pys_event_data nicht gefunden oder kein Array\n";
    exit(1);
}

// GA4 laeuft ueber den Kanal ga_ads (SKILL.md, Abschnitt 1), ga_* bleibt unberuehrt
$data['ga_ads_enabled'] = true;
$data['ga_ads_event_action'] = 'CustomEvent';
$data['ga_ads_event_action_group'] = 'Custom Event';
$data['ga_ads_custom_event_action'] = $ga_name;

update_post_meta($event_id, '_pys_event_data', $data);

echo "OK: Event $event_id — GA4 (ga_ads) aktiviert, Name: $ga_name\n";
```

## 3.4 Event klonen (clone-event)

```php
<?php
// pys-clone-event.php — via: wp eval-file pys-clone-event.php <source_id> <new_title> --url=<subsite>
// $args[0] = Quell-Event-ID, $args[1] = Titel des neuen Events

$source_id = (int) $args[0];
$new_title = $args[1];

$source = get_post($source_id);
if (!$source || $source->post_type !== 'pys_event') {
    echo "FEHLER: Quell-Event $source_id nicht gefunden\n";
    exit(1);
}

// Post klonen
$new_id = wp_insert_post([
    'post_type'   => 'pys_event',
    'post_title'  => $new_title,
    'post_status' => 'publish',
]);

if (is_wp_error($new_id)) {
    echo "FEHLER: " . $new_id->get_error_message() . "\n";
    exit(1);
}

// Meta als Rohwert kopieren - NICHT ueber add_/update_post_meta (SKILL.md, Abschnitt 4)
global $wpdb;
$keys = ['_pys_event_data', '_pys_event_triggers', '_pys_event_conditions', '_pys_event_state'];
$raw  = fn($id, $key) => $wpdb->get_var($wpdb->prepare(
    "SELECT meta_value FROM {$wpdb->postmeta} WHERE post_id = %d AND meta_key = %s", $id, $key));

foreach ($keys as $key) {
    $value = $raw($source_id, $key);
    if ($value === null) continue;
    $wpdb->insert($wpdb->postmeta, ['post_id' => $new_id, 'meta_key' => $key, 'meta_value' => $value]);
}
wp_cache_delete($new_id, 'post_meta');

// Byte-Vergleich Quelle <-> Klon
$ok = true;
foreach ($keys as $key) {
    if ($raw($source_id, $key) !== $raw($new_id, $key)) {
        echo "FEHLER: $key weicht von der Quelle ab\n";
        $ok = false;
    }
}

echo $ok ? "OK: Event $new_id erstellt (Klon von $source_id, Meta byte-gleich)\n" : "FEHLER: Klon $new_id pruefen\n";
```

## 3.5 Trigger aendern (set-selector / set-forms)

```php
<?php
// pys-set-trigger.php — via: wp eval-file pys-set-trigger.php <event_id> <type> <value> --url=<subsite>
// $args[0] = Event-ID
// $args[1] = "css_click" oder "ninjaform"
// $args[2] = Selektor (z.B. ".cancel-submit") oder Form-IDs kommasepariert (z.B. "3,5")

$event_id = (int) $args[0];
$type     = $args[1];
$value    = $args[2];

$raw = get_post_meta($event_id, '_pys_event_triggers', true);
$triggers = $raw ? unserialize($raw) : [];

if (!is_array($triggers) || empty($triggers)) {
    echo "FEHLER: Keine Trigger gefunden — Event hat keine gueltige Trigger-Konfiguration\n";
    exit(1);
}

$trigger = $triggers[0]; // Erster (meist einziger) Trigger

if ($type === 'css_click') {
    // Selektor steht in triggers[] als {rule, value} (SKILL.md, Abschnitt 1); rule aus dem Bestand uebernehmen
    $entries = (array)($trigger->triggers ?? []);
    if (($trigger->trigger_type ?? '') !== 'css_click' || empty($entries)) {
        echo "FEHLER: Kein css_click-Eintrag als Vorlage - Event mit css_click-Trigger klonen (3.4)\n";
        exit(1);
    }
    $entry = reset($entries);
    if (is_array($entry)) { $entry['value'] = $value; } else { $entry->value = $value; }
    $trigger->triggers = [$entry];
} elseif ($type === 'ninjaform') {
    $trigger->trigger_type = 'ninjaform';
    $trigger->forms = array_map('intval', explode(',', $value));
} else {
    echo "FEHLER: Unbekannter Typ '$type' — erlaubt: css_click, ninjaform\n";
    exit(1);
}

$triggers[0] = $trigger;
$serialized = serialize($triggers);

// KRITISCH: wp_slash() verwenden!
update_post_meta($event_id, '_pys_event_triggers', wp_slash($serialized));

echo "OK: Trigger von Event $event_id auf $type=$value gesetzt\n";
```

## 3.6 Verifizieren (verify)

Geprueft wird serverseitig (Meta-Daten) — das gerenderte Frontend ist bei login-gated Formularen nicht anonym abrufbar.

```php
<?php
// pys-verify.php — via: wp eval-file pys-verify.php <event_id> --url=<subsite>

$event_id = (int) $args[0];

$data     = get_post_meta($event_id, '_pys_event_data', true);
$triggers = get_post_meta($event_id, '_pys_event_triggers', true);
$state    = get_post_meta($event_id, '_pys_event_state', true);

echo "=== Event $event_id ===\n";
echo "State: " . ($state ?: 'inactive') . "\n";

// Data check
if (!is_array($data)) {
    echo "WARNUNG: _pys_event_data ist kein Array!\n";
} else {
    // GA4 laeuft ueber ga_ads (SKILL.md, Abschnitt 1)
    echo "GA4 (ga_ads): " . (!empty($data['ga_ads_enabled']) ? 'aktiv' : 'inaktiv');
    echo " | Name: " . ($data['ga_ads_custom_event_action'] ?? '-') . "\n";
    echo "ga_enabled: " . (!empty($data['ga_enabled']) ? 'true' : 'false') . "\n";
    echo "Pixel-ID: " . ($data['ga_ads_pixel_id'] ?? 'all') . "\n";
    echo "enable_all_tracking_ids: " . ($data['enable_all_tracking_ids'] ?? '0') . "\n";
}

// Trigger check
echo "\n--- Trigger ---\n";
$t_arr = $triggers ? unserialize($triggers) : false;
if ($t_arr === false) {
    echo "FEHLER: unserialize() fehlgeschlagen — vermutlich wp_slash() vergessen!\n";
} elseif (!is_array($t_arr)) {
    echo "WARNUNG: Trigger ist kein Array (Typ: " . gettype($t_arr) . ")\n";
} else {
    foreach ($t_arr as $i => $t) {
        $class = get_class($t);
        echo "[$i] class=$class type={$t->trigger_type}";
        if ($t->trigger_type === 'css_click') {
            foreach ((array)($t->triggers ?? []) as $e) {
                $e = (array) $e;
                echo " [rule=" . ($e['rule'] ?? '?') . " value=" . ($e['value'] ?? '?') . "]";
            }
        } elseif ($t->trigger_type === 'ninjaform') {
            echo " forms=" . implode(',', (array)($t->forms ?? []));
        }
        echo "\n";
    }
}
```

## 3.7 Backup / Restore

```php
<?php
// pys-backup.php — via: wp eval-file pys-backup.php <event_id> --url=<subsite>
// Gibt base64-encodierte Meta-Werte aus — zum Wiederherstellen aufbewahren

global $wpdb;
$event_id = (int) $args[0];

foreach (['_pys_event_data', '_pys_event_triggers', '_pys_event_conditions', '_pys_event_state'] as $key) {
    $raw = $wpdb->get_var($wpdb->prepare(
        "SELECT meta_value FROM {$wpdb->postmeta} WHERE post_id = %d AND meta_key = %s",
        $event_id, $key
    ));
    echo "$key=" . base64_encode($raw ?? '') . "\n";
}
echo "OK: Backup von Event $event_id\n";
```

```php
<?php
// pys-restore.php — via: wp eval-file pys-restore.php <event_id> <key> <base64> --url=<subsite>
// $args[0] = Event-ID, $args[1] = Meta-Key, $args[2] = base64-Wert

$event_id = (int) $args[0];
$key      = $args[1];
$value    = base64_decode($args[2]);

global $wpdb;
$wpdb->update(
    $wpdb->postmeta,
    ['meta_value' => $value],
    ['post_id' => $event_id, 'meta_key' => $key]
);

echo "OK: $key von Event $event_id wiederhergestellt\n";
```

Zurueck zur Uebersicht: [SKILL.md](../SKILL.md).
