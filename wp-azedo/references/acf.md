# ACF bei azedo

- **Local JSON** im Theme unter `acf-json/` - CPTs, Taxonomien und Feldgruppen liegen damit in Git. Der Ordner muss für den Webserver-User schreibbar sein, sonst speichert die ACF-Oberfläche nur in die DB.
- **JSON nicht von Hand schreiben:** mit ACFs eigener Validierung und Export erzeugen (`acf_get_internal_post_type_instance(...)->validate_post()`, `acf_get_valid_field()`, `acf_prepare_internal_post_type_for_export()`, `acf_json_encode()`), per `wp eval-file -` ausgeführt.
- **Feldnamen englisch, Beschriftungen deutsch.** URLs dürfen deutsch sein.
- **Standardfelder nutzen, wo es sie gibt:** Beitragsbild statt eigenem Bildfeld, Auszug statt eigenem Kurztext.
- **Eigene URLs** für CPTs (`no_permalink` in der JSON) plus Regeln über `rewrite_rules_array` im mu-plugin; beim Speichern nur `rewrite_rules` löschen, der Neuaufbau läuft beim nächsten Request.
- **ACF Blocks:** ab WP 7.1 ist Blockversion 3 Standard; ein `blockVersion` in `block.json` pinnt nur eine ältere Version (ACF 6.8.10, `pro/blocks.php`). `block.json` mit `acf.renderTemplate`, Daten aus dem aktuellen Beitrag in `render.php`; ohne passenden Beitrag im Editor mit `$is_preview` einen Hinweis ausgeben.
- **Lizenz** per `acf_pro_activate_license($key, true)` aus `wp eval-file -` (zweiter Parameter `$silent`); den Schlüssel nicht in den Chat und nicht ins Repo.
