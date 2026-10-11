---
name: wp-pys
description: >
  PixelYourSite Pro in WordPress-(Multi-)Sites per WP-CLI: Events auslesen,
  Pixel-Ziele aktivieren, Trigger ändern, Events klonen - reproduzierbar
  statt über das Admin-UI. Auch bei "PixelYourSite", "PYS-Event", "GA4-Event
  anlegen", "Tracking-Event", "CSS-Click-Event".
  Trigger: /wp-pys.
allowed-tools: [Bash, Read]
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
| `pys_ga` | GA4: `tracking_id` (**Array** von Mess-IDs, kein String), `main_pixel_enabled` |
| `pys_gtm` | GTM: Container-ID |
| `pys_facebook` | Facebook Pixel |
| `pys_google_ads` | Google Ads Conversion |

### Events (Custom Post Type)

CPT `pys_event` mit folgenden Post-Meta-Feldern:

| Meta Key | Format | Inhalt |
|----------|--------|--------|
| `_pys_event_data` | **einfach** serialisiert — `get_post_meta()` liefert das Array (~91-94 Keys) | Pixel-Ziele (`ga_ads_enabled`, `ga_enabled`), Event-Namen (`ga_ads_custom_event_action`), Pixel-ID (`ga_ads_pixel_id`), GTM-dataLayer-Name |
| `_pys_event_triggers` | **doppelt** serialisiert — `get_post_meta()` liefert einen String, erst `unserialize()` das Array | Array von `PixelYourSite\TriggerEvent`-Objekten: `trigger_type` (`css_click`, `ninjaform`), `forms` (ninjaform), `triggers` (css_click, siehe unten), `form_submit_mode` |
| `_pys_event_conditions` | serialisiert | Bedingungen (Seiten, URLs) |
| `_pys_event_state` | String | `active` oder leer |

### GA4 laeuft ueber den Kanal `ga_ads`

GA4-Events haengen am Kanal **`ga_ads`**: `ga_ads_enabled`,
`ga_ads_custom_event_action` (Event-Name), `ga_ads_pixel_id`. `ga_enabled` steht
bei diesen Events auf `false`. Wer nur `ga_*` liest, haelt ein feuerndes
GA4-Event fuer inaktiv.

### css_click-Selektoren stehen in `triggers`

Die Selektoren eines `css_click`-Triggers liegen in der TriggerEvent-Property
**`triggers`** als Liste von `{rule, value}` — `value` ist der Selektor. Eine
Property `selectors` gibt es dort nicht; ein Lesen ueber `selectors` liefert
still eine leere Liste.

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

### Ablauf und Snippets

Die PHP-Snippets liegen in **[references/snippets.md](references/snippets.md)**
und werden erst beim Ausfuehren gebraucht:

| Nr. | Operation | Art |
|---|---|---|
| 3.1 | Events auflisten (`list-events`) - Ziele, GA4-Name, Trigger je Event | read |
| 3.2 | Plugin-Config lesen (`show-config`) - `pys_ga`, `pys_gtm` u.a. aus `pys_options` | read |
| 3.3 | Pixel-Ziel aktivieren (`enable-target`) - setzt den Kanal `ga_ads` | write |
| 3.4 | Event klonen (`clone-event`) - Meta als Rohwert, Byte-Vergleich | write |
| 3.5 | Trigger aendern (`set-trigger`) - css-Selektor oder NF-Formulare | write |
| 3.6 | Verifizieren (`verify`) - Trigger-Deserialisierung und Pixel-Ziele | read |
| 3.7 | Backup / Restore - Meta base64-codiert sichern und zurueckschreiben | write |

Vor jedem Write 3.7 (Backup), danach 3.6 (Verify) - siehe Abschnitt 5.

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

### Klonen: Rohwert per SQL, nicht ueber add_/update_post_meta

`add_post_meta()`/`update_post_meta()` mit dem Rohwert aus der DB (auch mit
`wp_slash()`) laufen durch `maybe_serialize()`: ein schon serialisierter String
wird **nochmals** serialisiert. Der Klon fuehrt dann einen anderen Wert als die
Quelle, ohne Fehlermeldung.

**Regel:** Beim Klonen den Rohwert per `$wpdb->insert` in `postmeta` schreiben,
danach `wp_cache_delete($id, 'post_meta')` und Quelle gegen Klon byteweise
vergleichen — so in 3.4 ([references/snippets.md](references/snippets.md)). Danach Trigger oder Formulare per 3.5 anpassen, nicht
per `str_replace` im serialisierten String.

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
