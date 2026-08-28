---
name: wp-pys
description: >
  PixelYourSite Pro in WordPress-(Multi-)Sites per WP-CLI: Events auslesen,
  Pixel-Ziele aktivieren, Trigger ändern, Events klonen - reproduzierbar
  statt über das Admin-UI. Auch bei "PixelYourSite", "PYS-Event", "GA4-Event
  anlegen", "Tracking-Event", "CSS-Click-Event".
  Trigger: /wp-pys.
---

# wp-pys — PixelYourSite Pro Event-Verwaltung

Referenz fuer die Verwaltung von PixelYourSite-Pro-Events (Custom Events, Trigger, Pixel-Ziele) in WordPress-(Multi-)Sites per WP-CLI.

Besonders nuetzlich, um Tracking-Setups zwischen mehreren Subsites (z.B. DE/FR/IT) konsistent zu halten.

---

## 1. Datenmodell

### PYS-Settings (Plugin-Konfiguration)

Liegen in **eigener Tabelle** `wp_{blog_id}_pys_options` (NICHT in `wp_options` oder `wp_sitemeta`).

Relevante Options:

| Option | Inhalt |
|--------|--------|
| `pys_core` | Core-Settings (Features, Consent-Modus) |
| `pys_ga` | GA4: `tracking_id`, `main_pixel_enabled` |
| `pys_gtm` | GTM: Container-ID |
| `pys_facebook` | Facebook Pixel |
| `pys_google_ads` | Google Ads Conversion |

### Events (Custom Post Type)

CPT `pys_event` mit folgenden Post-Meta-Feldern:

| Meta Key | Format | Inhalt |
|----------|--------|--------|
| `_pys_event_data` | serialisiertes Array (~91-94 Keys) | Pixel-Ziele (`ga_enabled`, `ga_ads_enabled`), Event-Namen (`ga_ads_custom_event_action`), GTM-dataLayer-Name |
| `_pys_event_triggers` | serialisierter String | Array von `PixelYourSite\TriggerEvent`-Objekten: `trigger_type` (`css_click`, `ninjaform`), `forms`, `selectors`, `form_submit_mode` |
| `_pys_event_conditions` | serialisiert | Bedingungen (Seiten, URLs) |
| `_pys_event_state` | String | `active` oder leer |

### Pixel-ID-Aufloesung

`"all"` + `enable_all_tracking_ids=1` → Event ohne harte Pixel-ID loest automatisch auf die GA4-Property der jeweiligen Subsite auf. Empfohlener Standard bei Multisite.

---

## 2. Zugang / Ausfuehrung

WP-CLI in Jails — siehe auch `/wp-cli` Skill fuer allgemeine Jail-Zugriffsmuster.

```sh
# Allgemeines Muster (iocage):
sudo ssh -C root@<jailhost> "iocage exec <jail> sudo -u <wwwuser> wp --path=<docroot> <cmd> --url=<subsite>"

# Beispiel:
sudo ssh -C root@jailer.example.com "iocage exec wordpress1 sudo -u wwwexample wp --path=/www/home/wwwexample/example.com eval-file /tmp/pys-list.php --url=https://sub.example.com"
```

### PHP-Logik ausfuehren

Fuer komplexere Operationen `wp eval-file` verwenden:

```sh
# Script auf den Server kopieren:
cat script.php | sudo ssh -C root@<jailhost> "iocage exec <jail> sh -c 'cat > /tmp/pys-script.php'"

# Ausfuehren:
sudo ssh -C root@<jailhost> "iocage exec <jail> sudo -u <wwwuser> wp --path=<docroot> eval-file /tmp/pys-script.php <arg1> --url=<subsite>"
```

**Wichtig:** Argumente als `$args[0]`, `$args[1]` etc. uebergeben — NICHT als Env-Variablen (`sudo` strippt die Umgebung).

---

## 3. Operationen

### 3.1 Events auflisten (list-events)

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
                $trigger_info[] = "css_click: " . implode(', ', (array)($t->selectors ?? []));
            } elseif ($type === 'ninjaform') {
                $trigger_info[] = "ninjaform: " . implode(', ', (array)($t->forms ?? []));
            } else {
                $trigger_info[] = $type;
            }
        }
    }

    $targets = [];
    if (!empty($data['ga_enabled']))      $targets[] = 'GA4';
    if (!empty($data['ga_ads_enabled']))   $targets[] = 'GoogleAds';
    if (!empty($data['facebook_enabled'])) $targets[] = 'Facebook';
    if (!empty($data['gtm_enabled']))      $targets[] = 'GTM';

    $ga_name = $data['ga_custom_event_action'] ?? $data['ga_ads_custom_event_action'] ?? '-';

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

### 3.2 Plugin-Config lesen (show-config)

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

### 3.3 Pixel-Ziel aktivieren (enable-target)

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

// GA4 aktivieren
$data['ga_enabled'] = true;
$data['ga_event_action'] = 'CustomEvent';
$data['ga_event_action_group'] = 'Custom Event';
$data['ga_custom_event_action'] = $ga_name;

// Google Ads aktivieren (optional — gleichen Event-Name verwenden)
$data['ga_ads_enabled'] = true;
$data['ga_ads_event_action'] = 'CustomEvent';
$data['ga_ads_event_action_group'] = 'Custom Event';
$data['ga_ads_custom_event_action'] = $ga_name;

update_post_meta($event_id, '_pys_event_data', $data);

echo "OK: Event $event_id — GA4+GoogleAds aktiviert, Name: $ga_name\n";
```

### 3.4 Event klonen (clone-event)

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

// Meta kopieren
foreach (['_pys_event_data', '_pys_event_triggers', '_pys_event_conditions', '_pys_event_state'] as $key) {
    $raw = get_post_meta($source_id, $key, true);
    if ($key === '_pys_event_triggers') {
        // KRITISCH: wp_slash() verwenden! Siehe Abschnitt "Fallstricke"
        update_post_meta($new_id, $key, wp_slash($raw));
    } else {
        update_post_meta($new_id, $key, $raw);
    }
}

echo "OK: Event $new_id erstellt (Klon von $source_id)\n";
```

### 3.5 Trigger aendern (set-selector / set-forms)

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
    $trigger->trigger_type = 'css_click';
    $trigger->selectors = [$value];
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

### 3.6 Verifizieren (verify)

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
    echo "GA4: " . ($data['ga_enabled'] ? 'aktiv' : 'inaktiv');
    echo " | Name: " . ($data['ga_custom_event_action'] ?? '-') . "\n";
    echo "GoogleAds: " . ($data['ga_ads_enabled'] ? 'aktiv' : 'inaktiv');
    echo " | Name: " . ($data['ga_ads_custom_event_action'] ?? '-') . "\n";
    echo "Pixel-ID: " . ($data['pixel_id'] ?? $data['ga_pixel_id'] ?? 'all') . "\n";
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
            echo " selectors=" . implode(',', (array)($t->selectors ?? []));
        } elseif ($t->trigger_type === 'ninjaform') {
            echo " forms=" . implode(',', (array)($t->forms ?? []));
        }
        echo "\n";
    }
}
```

### 3.7 Backup / Restore

```php
<?php
// pys-backup.php — via: wp eval-file pys-backup.php <event_id> --url=<subsite>
// Gibt base64-encodierte Meta-Werte aus — zum Wiederherstellen aufbewahren

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

### 3.8 Ninja-Form-IDs ermitteln

Form-IDs sind **site-spezifisch** — nie raten, immer nachschlagen und ueber den
Formular-**Titel** mappen. Das Auflisten und das gesamte NF-Datenmodell liegen im
Skill **[[wp-nf]]** (Abschnitt „Formulare auflisten + Titel→ID-Mapping"); von dort das
`nf-list-forms.php`-Snippet verwenden.

Ergaenzend fuer CSS-Click-Tracking: ob ein `css_click`-Event feuert, haengt nicht nur am
PYS-Selektor, sondern auch an der **CSS-Klasse im NF-Feld** (`element_class`). Zum
Setzen/Pruefen dieser Klasse siehe [[wp-nf]] (Diagnose-Muster PYS ↔ `element_class`).

---

## 4. Fallstricke

### wp_slash() bei Triggers (KRITISCH)

`_pys_event_triggers` enthaelt den Klassennamen **mit Backslash**: `PixelYourSite\TriggerEvent`.

`update_post_meta()` ruft intern `wp_unslash()` auf → ohne `wp_slash()` wird der Backslash entfernt → `unserialize()` liefert `false` → Event feuert nicht + PYS-Warning in `class-custom-event.php:1323` (`foreach over bool`).

**Regel:** Jeden serialisierten Trigger-String vor dem Speichern mit `wp_slash()` wrappen.

### Robustes Trigger-Klonen

Trigger von einem bestehenden, gueltigen Event **derselben Site** klonen und nur das `forms`-Array per `str_replace` tauschen (Arrays haben keine Byte-Laengen-Praefixe → sicher). Dann mit `wp_slash()` speichern.

**NICHT** cross-site kopieren ohne Re-Slash.

### sudo strippt Umgebung

Parameter an `wp eval-file` immer als Positionsargumente (`$args[0]`, `$args[1]`) uebergeben, nicht als Umgebungsvariablen.

### Ninja-Form-IDs sind site-spezifisch

Bei Multisite haben die gleichen Formulare auf verschiedenen Subsites unterschiedliche IDs. Immer nachschlagen und das Mapping ueber den Formular-Titel herstellen — Auflistung via Skill [[wp-nf]].

### Login-gated Formulare

Foerderer-Formulare (z.B. Kuendigungsformulare) sind hinter Login (Einmalcode) versteckt. Trigger-Buttons sind anonym nicht im Markup sichtbar. Echtes Feuern des Events nur im eingeloggten GA4 Tag Assistant verifizierbar.

### Consent (Real Cookie Banner)

GA4-Events werden erst nach Cookie-Consent gesendet. Die Event-Config (`pysOptions`) wird aber serverseitig unabhaengig vom Consent gerendert — serverseitige Verifikation (Abschnitt 3.6) funktioniert also immer.

---

## 5. Workflow

1. **Subsite identifizieren** — Blog-ID, Docroot, WP-User, Jail, Subsite-URL.
2. **Bestehende Events auflisten** (`list-events`) — Ueberblick ueber vorhandenes Setup.
3. **Backup** erstellen, bevor Aenderungen gemacht werden.
4. **Aenderung durchfuehren** — enable-target, set-trigger, clone-event.
5. **Verifizieren** (`verify`) — Trigger-Deserialisierung und Pixel-Ziele pruefen.
6. Bei Multisite: fuer jede Subsite wiederholen, Ninja-Form-IDs pro Site nachschlagen.
