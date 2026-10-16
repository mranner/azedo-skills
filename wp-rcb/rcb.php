<?php

/*
 * wp-rcb: Real Cookie Banner per WP-CLI.
 * Aufruf: wp eval-file - <befehl> [argumente] (Code über STDIN), Ausgabe JSON.
 */

use DevOwl\RealCookieBanner\Cache;
use DevOwl\RealCookieBanner\import\Export;
use DevOwl\RealCookieBanner\import\Import;

// Wird von `rcb php --input <datei>` ersetzt

$rcb_input = null;

const RCB_CODE_FIELDS = ['codeOptIn', 'codeOptOut', 'codeOnPageLoad'];

function rcb_out($data)
{
	echo json_encode($data, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE), "\n";
}

function rcb_fail($message)
{
	fwrite(STDERR, "wp-rcb: $message\n");
	exit(1);
}

function rcb_opts($args)
{
	$opts = [];

	foreach ($args as $arg) {

		if (strpos($arg, '=') !== false) {
			list($k, $v) = explode('=', $arg, 2);
			$opts[$k] = $v;
		} else {
			$opts[$arg] = true;
		}

	}

	return $opts;
}

function rcb_lang($id)
{
	$details = apply_filters('wpml_post_language_details', null, $id);

	return is_array($details) ? $details['language_code'] : null;
}

function rcb_posts($type)
{
	return get_posts([
		'post_type' => $type,
		'post_status' => 'any',
		'numberposts' => -1,
		'orderby' => ['menu_order' => 'ASC', 'ID' => 'ASC'],
		'suppress_filters' => true,
	]);
}

function rcb_json_meta($id, $key)
{
	$value = get_post_meta($id, $key, true);
	$decoded = is_string($value) ? json_decode($value, true) : null;

	return $decoded === null ? $value : $decoded;
}

function rcb_hosts($id)
{
	$defs = rcb_json_meta($id, 'technicalDefinitions');

	if (!is_array($defs)) {
		return [];
	}

	return array_values(array_unique(array_filter(array_column($defs, 'host'))));
}

function rcb_group($id)
{
	$terms = wp_get_object_terms($id, 'rcb-cookie-group', ['fields' => 'slugs']);

	return is_wp_error($terms) || !$terms ? null : $terms[0];
}

function rcb_find_service($needle)
{
	if (ctype_digit((string) $needle)) {
		$post = get_post((int) $needle);

		if ($post && $post->post_type === 'rcb-cookie') {
			return $post;
		}

		rcb_fail("kein Dienst mit ID $needle");
	}

	$hits = [];

	foreach (rcb_posts('rcb-cookie') as $post) {

		if ($post->post_name === $needle) {
			return $post;
		}

		if (stripos($post->post_title, $needle) !== false) {
			$hits[] = $post;
		}

	}

	if (count($hits) !== 1) {
		$names = array_map(function ($p) {
			return "$p->ID $p->post_title (" . rcb_lang($p->ID) . ')';
		}, $hits);
		rcb_fail(count($hits) . " Treffer für '$needle'" . ($names ? ': ' . implode(', ', $names) : ''));
	}

	return $hits[0];
}

function rcb_export()
{
	$data = Export::instance()
		->appendSettings()
		->appendBannerLinks()
		->appendCookieGroups()
		->appendCookies()
		->appendBlocker()
		->appendTcfVendorConfigurations()
		->appendCustomizeBanner()
		->finish();
	$data['_meta'] = rcb_info();

	return $data;
}

function rcb_info()
{
	return [
		'rcb_version' => defined('RCB_VERSION') ? RCB_VERSION : null,
		'pro' => defined('RCB_PRO_VERSION') || is_dir(WP_PLUGIN_DIR . '/real-cookie-banner-pro'),
		'home' => home_url(),
		'blog_id' => get_current_blog_id(),
		'locale' => get_locale(),
		'languages' => array_keys((array) apply_filters('wpml_active_languages', null, [])),
		'created' => gmdate('c'),
	];
}

function rcb_cmd_services()
{
	$rows = [];

	foreach (rcb_posts('rcb-cookie') as $post) {
		$code = [];

		foreach (RCB_CODE_FIELDS as $field) {

			if (trim((string) get_post_meta($post->ID, $field, true)) !== '') {
				$code[] = $field;
			}

		}

		$rows[] = [
			'id' => $post->ID,
			'title' => $post->post_title,
			'post_name' => $post->post_name,
			'status' => $post->post_status,
			'group' => rcb_group($post->ID),
			'preset' => get_post_meta($post->ID, 'presetId', true) ?: null,
			'preset_version' => get_post_meta($post->ID, 'presetVersion', true) ?: null,
			'legal_basis' => get_post_meta($post->ID, 'legalBasis', true),
			'lang' => rcb_lang($post->ID),
			'code' => $code,
			'hosts' => rcb_hosts($post->ID),
		];
	}

	return $rows;
}

function rcb_cmd_service($needle)
{
	$post = rcb_find_service($needle);
	$metas = [];

	foreach (array_keys(get_post_meta($post->ID)) as $key) {
		$metas[$key] = rcb_json_meta($post->ID, $key);
	}

	ksort($metas);

	return [
		'id' => $post->ID,
		'title' => $post->post_title,
		'post_name' => $post->post_name,
		'status' => $post->post_status,
		'group' => rcb_group($post->ID),
		'lang' => rcb_lang($post->ID),
		'metas' => $metas,
	];
}

function rcb_cmd_blockers()
{
	$rows = [];

	foreach (rcb_posts('rcb-blocker') as $post) {
		$services = array_filter(array_map('intval', explode(',', (string) get_post_meta($post->ID, 'services', true))));
		$rules = array_values(array_filter(array_map('trim', explode("\n", (string) get_post_meta($post->ID, 'rules', true)))));
		$rows[] = [
			'id' => $post->ID,
			'title' => $post->post_title,
			'status' => $post->post_status,
			'preset' => get_post_meta($post->ID, 'presetId', true) ?: null,
			'lang' => rcb_lang($post->ID),
			'services' => array_map(function ($id) {
				$p = get_post($id);

				return $p ? "$id $p->post_title" : "$id (fehlt)";
			}, array_values($services)),
			'criteria' => get_post_meta($post->ID, 'criteria', true),
			'visual' => (bool) get_post_meta($post->ID, 'isVisual', true),
			'rules' => $rules,
		];
	}

	return $rows;
}

function rcb_cmd_banner_links()
{
	$rows = [];

	foreach (rcb_posts('rcb-banner-link') as $post) {
		$pageId = (int) get_post_meta($post->ID, 'pageId', true);
		$external = (bool) get_post_meta($post->ID, 'isExternalUrl', true);
		$rows[] = [
			'id' => $post->ID,
			'title' => $post->post_title,
			'status' => $post->post_status,
			'type' => get_post_meta($post->ID, 'pageType', true),
			'lang' => rcb_lang($post->ID),
			'url' => $external ? get_post_meta($post->ID, 'externalUrl', true) : ($pageId ? get_permalink($pageId) : null),
			'page_id' => $external ? null : $pageId,
		];
	}

	return $rows;
}

function rcb_settings_map()
{
	return Import::instance([])->optionsMap(true);
}

function rcb_cmd_settings($opts)
{
	global $wpdb;

	$result = [];

	if (empty($opts['all'])) {

		foreach (rcb_settings_map() as $name) {
			$result[$name] = get_option($name);
		}

		ksort($result);

		return $result;
	}

	// Caches, Template-Kopien und interne Zustände ändern sich ohne Zutun

	$skip = '/-(templates|presets)-|-expire$|^rcb-cloud-data-source|^rcb-notice-states$|^rcb-migration|^rcb-installation-date$|^rcb_db_/';

	foreach ($wpdb->get_col("SELECT option_name FROM {$wpdb->options} WHERE option_name LIKE 'rcb%' ORDER BY option_name") as $name) {

		if (!preg_match($skip, $name)) {
			$result[$name] = get_option($name);
		}

	}

	return $result;
}

function rcb_cmd_revisions($opts)
{
	global $wpdb;

	$table = $wpdb->prefix . 'rcb_revision';
	$current = [];

	foreach ($wpdb->get_col("SELECT option_name FROM {$wpdb->options} WHERE option_name LIKE 'rcb-revision-current-hash%'") as $name) {
		$parts = explode(':', (string) get_option($name));
		$current[$name] = [
			'hash' => $parts[0],
			'since' => isset($parts[1]) ? gmdate('c', (int) $parts[1]) : null,
		];
	}

	$hashes = array_column($current, 'hash');
	$limit = isset($opts['limit']) ? (int) $opts['limit'] : 10;
	$where = '';

	if (!empty($opts['grep'])) {
		$where = $wpdb->prepare('WHERE json_revision LIKE %s', '%' . $wpdb->esc_like($opts['grep']) . '%');
	}

	$rows = $wpdb->get_results("SELECT id, hash, created FROM $table $where ORDER BY id DESC LIMIT $limit", ARRAY_A);

	foreach ($rows as &$row) {
		$row['public'] = in_array($row['hash'], $hashes, true);
	}

	return ['current' => $current, 'revisions' => $rows];
}

/*
 * Import-Vorschau. RCB legt Dienste und Blocker nur neu an - bestehende
 * (gleicher post_name) überspringt es, Gruppen gleicht es per Slug ab.
 */

function rcb_import_plan($json)
{
	$here = rcb_info();
	$there = isset($json['_meta']) ? $json['_meta'] : [];
	$plan = ['source' => $there, 'target' => $here, 'problems' => [], 'warnings' => []];

	if (empty($there['rcb_version'])) {
		$plan['problems'][] = 'Datei ohne _meta.rcb_version - nicht mit wp-rcb exportiert';
	} elseif ($there['rcb_version'] !== $here['rcb_version']) {
		$plan['problems'][] = "RCB-Version weicht ab: Quelle {$there['rcb_version']}, Ziel {$here['rcb_version']}";
	}

	$existing = function ($type) {
		return array_map(function ($p) {
			return $p->post_name;
		}, rcb_posts($type));
	};
	$services = $existing('rcb-cookie');
	$blockers = $existing('rcb-blocker');
	$current = Export::instance()->appendCookieGroups()->appendCustomizeBanner()->finish();
	$groups = array_column($current['cookieGroups'], 'slug', 'term_id');
	$groupNames = array_column($current['cookieGroups'], 'name', 'term_id');
	$groupRows = array_column($current['cookieGroups'], null, 'slug');

	foreach ((array) ($json['cookieGroups'] ?? []) as $g) {
		$other = array_search($g['name'], $groupNames, true);

		if (isset($groupRows[$g['slug']])) {
			$row = $groupRows[$g['slug']];
			$same = $row['name'] === $g['name'] && $row['description'] === $g['description'];
			$plan['groups'][$g['slug']] = $same ? 'unverändert' : 'Name/Beschreibung überschreiben';
		} elseif ($other !== false) {
			$plan['groups'][$g['slug']] = "anlegen - DUPLIKAT: Name existiert als {$groups[$other]}";
			$plan['problems'][] = "Gruppe '{$g['name']}' gibt es schon unter anderem Slug";
		} else {
			$plan['groups'][$g['slug']] = 'anlegen';
			$plan['warnings'][] = "neue Gruppe '{$g['name']}' ({$g['slug']}) - vorhanden: " . implode(', ', $groups);
		}

	}

	// RCB gleicht nur per post_name ab - gleicher Titel unter anderem Slug wird ein Duplikat

	$titles = [];

	foreach (rcb_posts('rcb-cookie') as $p) {
		$titles[$p->post_title] = $p->post_name;
	}

	foreach ((array) ($json['cookies'] ?? []) as $c) {

		if (in_array($c['post_name'], $services, true)) {
			$plan['services'][$c['post_name']] = 'überspringen (existiert)';
		} elseif (isset($titles[$c['post_title']])) {
			$plan['services'][$c['post_name']] = "anlegen - DUPLIKAT: Titel existiert als {$titles[$c['post_title']]}";
			$plan['problems'][] = "Dienst '{$c['post_title']}' gibt es schon unter anderem Slug";
		} else {
			$plan['services'][$c['post_name']] = 'anlegen';
		}

	}

	foreach ((array) ($json['blocker'] ?? []) as $b) {
		$plan['blockers'][$b['post_name']] = in_array($b['post_name'], $blockers, true) ? 'überspringen (existiert)' : 'anlegen';
	}

	$map = rcb_settings_map();

	foreach ((array) ($json['settings'] ?? []) as $key => $value) {

		if (isset($map[$key]) && is_scalar($value) && get_option($map[$key]) != $value) {
			$plan['settings'][$map[$key]] = ['alt' => get_option($map[$key]), 'neu' => $value];
		}

	}

	// Banner-Texte und -Design überschreibt RCB ohne Rückfrage

	if (isset($json['customizeBanner'])) {
		$plan['banner'] = rcb_changed_keys($current['customizeBanner'], $json['customizeBanner']);
	}

	$from = rcb_bare_host($there['home'] ?? '');
	$to = rcb_bare_host($here['home']);

	if ($from && $from !== $to) {
		$plan['hosts'] = "Cookie-Hosts werden von $from auf $to umgeschrieben";
	}

	// Ein DEV-Klon trägt oft noch die Live-Domain in den Hosts - das Umschreiben greift dann nicht

	foreach ((array) ($json['cookies'] ?? []) as $c) {

		if ($plan['services'][$c['post_name']] === 'überspringen (existiert)') {
			continue;
		}

		foreach ((array) ($c['metas']['technicalDefinitions'] ?? []) as $def) {
			$host = $def['host'] ?? '';

			if (strpos($host, '.') !== false && strpos($host, $from) === false && strpos($host, $to) === false) {
				$plan['warnings'][] = "Host '$host' von '{$c['post_title']}' passt weder zu $from noch zu $to";
			}

		}

	}

	return $plan;
}

function rcb_changed_keys($old, $new, $path = '')
{
	$changed = [];

	foreach ((array) $new as $key => $value) {
		$sub = $path === '' ? $key : "$path.$key";

		if (is_array($value) && isset($old[$key]) && is_array($old[$key])) {
			$changed = array_merge($changed, rcb_changed_keys($old[$key], $value, $sub));
		} elseif (!array_key_exists($key, (array) $old) || $old[$key] !== $value) {
			$changed[] = $sub;
		}

	}

	return $changed;
}

function rcb_bare_host($url)
{
	$host = (string) parse_url($url, PHP_URL_HOST);

	return preg_replace('/^www\./', '', $host);
}

// Hosts in technicalDefinitions tragen die Domain der Quell-Site, RCB schreibt sie nicht um

function rcb_rehost(&$json, $from, $to)
{
	foreach ($json['cookies'] as &$cookie) {

		if (empty($cookie['metas']['technicalDefinitions'])) {
			continue;
		}

		foreach ($cookie['metas']['technicalDefinitions'] as &$def) {

			if (!empty($def['host'])) {
				$def['host'] = str_replace($from, $to, $def['host']);
			}

		}

	}
}

function rcb_cmd_import($json, $opts)
{
	if (!is_array($json)) {
		rcb_fail('import braucht die Exportdatei: rcb php --input <datei>');
	}

	$plan = rcb_import_plan($json);

	if (empty($opts['yes'])) {
		return ['dry_run' => true] + $plan;
	}

	if ($plan['problems']) {
		rcb_fail('Import abgebrochen: ' . implode('; ', $plan['problems']));
	}

	$from = rcb_bare_host($plan['source']['home']);
	$to = rcb_bare_host($plan['target']['home']);

	if ($from !== $to) {
		rcb_rehost($json, $from, $to);
	}

	$groups = get_terms(['taxonomy' => 'rcb-cookie-group', 'hide_empty' => false, 'fields' => 'id=>slug']);
	$fallback = isset($opts['group']) ? array_search($opts['group'], $groups, true) : array_key_first($groups);

	if (!$fallback) {
		rcb_fail("Gruppe '{$opts['group']}' gibt es nicht: " . implode(', ', $groups));
	}

	$backup = rcb_export();
	unset($json['_meta']);
	$import = Import::instance($json);
	$import->setCookieGroup($fallback);
	$import->import();
	Cache::getInstance()->invalidate();

	return ['plan' => $plan, 'messages' => $import->getMessages(), 'backup' => $backup];
}

function rcb_cmd_set_code($needle, $field, $opts, $input)
{
	if (!in_array($field, RCB_CODE_FIELDS, true)) {
		rcb_fail("Feld '$field' unbekannt: " . implode(', ', RCB_CODE_FIELDS));
	}

	if (empty($opts['empty']) && !is_string($input)) {
		rcb_fail('Wert fehlt: rcb php --input <datei> oder Argument empty');
	}

	$post = rcb_find_service($needle);
	$old = get_post_meta($post->ID, $field, true);
	$new = empty($opts['empty']) ? $input : '';

	if (empty($opts['yes'])) {
		return ['dry_run' => true, 'id' => $post->ID, 'title' => $post->post_title, 'field' => $field, 'alt' => $old, 'neu' => $new];
	}

	$backup = rcb_export();
	update_post_meta($post->ID, $field, wp_slash($new));
	Cache::getInstance()->invalidate();

	return ['id' => $post->ID, 'title' => $post->post_title, 'field' => $field, 'alt' => $old, 'neu' => get_post_meta($post->ID, $field, true), 'backup' => $backup];
}

// Unter WPML hat jeder Dienst je Sprache einen Post, RCB kopiert technicalDefinitions selbst

function rcb_translations($post)
{
	$type = 'post_' . $post->post_type;
	$trid = apply_filters('wpml_element_trid', null, $post->ID, $type);

	if (!$trid) {
		return [$post->ID];
	}

	return array_values(array_map(function ($t) {
		return (int) $t->element_id;
	}, (array) apply_filters('wpml_get_element_translations', null, $trid, $type)));
}

function rcb_cookie_posts($ids, $name, $host)
{
	return array_map(function ($id) use ($name, $host) {
		$hits = array_values(array_filter((array) rcb_json_meta($id, 'technicalDefinitions'), function ($d) use ($name, $host) {
			return $d['name'] === $name && ($host === null || $d['host'] === $host);
		}));

		return ['id' => $id, 'lang' => rcb_lang($id), 'cookie' => $hits ?: null];
	}, $ids);
}

function rcb_cmd_set_cookie($needle, $name, $opts, $input)
{
	$units = ['s', 'm', 'h', 'd', 'mo', 'y'];

	if (isset($opts['unit']) && !in_array($opts['unit'], $units, true)) {
		rcb_fail("Einheit '{$opts['unit']}' unbekannt: " . implode(', ', $units));
	}

	$post = rcb_find_service($needle);
	$defs = (array) rcb_json_meta($post->ID, 'technicalDefinitions');
	$host = $opts['host'] ?? null;
	$hits = array_keys(array_filter($defs, function ($d) use ($name, $host) {
		return $d['name'] === $name && ($host === null || $d['host'] === $host);
	}));

	if (count($hits) > 1) {
		rcb_fail("'$name' steht mehrfach im Dienst, host= angeben: " . implode(', ', array_map(function ($i) use ($defs) {
			return $defs[$i]['host'];
		}, $hits)));
	}

	$index = $hits ? $hits[0] : null;
	$old = $index === null ? null : $defs[$index];

	if (!empty($opts['remove'])) {

		if ($index === null) {
			rcb_fail("'$name' steht nicht im Dienst $post->ID");
		}

		array_splice($defs, $index, 1);

		foreach ($defs as $i => &$d) {
			$d['orderPosition'] = $i;
		}

		unset($d);
		$new = null;
	} else {

		if ($index === null && ($host === null || (!isset($opts['duration'], $opts['unit']) && !isset($opts['session'])))) {
			rcb_fail("'$name' ist neu: host= und duration=/unit= (oder session) angeben");
		}

		$new = $old ?: [
			'language' => $defs ? $defs[0]['language'] : get_locale(),
			'purpose' => null,
			'purposeTranslationFlags' => [],
			'type' => 'http',
			'name' => $name,
			'host' => $host,
			'duration' => 1,
			'durationUnit' => 'y',
			'isSessionDuration' => false,
			'orderPosition' => count($defs),
		];

		foreach (['host' => 'host', 'type' => 'type', 'unit' => 'durationUnit'] as $opt => $key) {

			if (isset($opts[$opt])) {
				$new[$key] = $opts[$opt];
			}

		}

		if (isset($opts['duration'])) {
			$new['duration'] = (int) $opts['duration'];
		}

		if (isset($opts['session'])) {
			$new['isSessionDuration'] = filter_var($opts['session'], FILTER_VALIDATE_BOOLEAN);
		}

		if (is_string($input) || isset($opts['purpose'])) {
			$new['purpose'] = is_string($input) ? trim($input) : $opts['purpose'];
		}

		$defs[$index ?? count($defs)] = $new;
	}

	$result = ['id' => $post->ID, 'title' => $post->post_title, 'lang' => rcb_lang($post->ID), 'alt' => $old, 'neu' => $new];
	$ids = rcb_translations($post);

	if (empty($opts['yes'])) {
		return ['dry_run' => true] + $result + ['posts' => rcb_cookie_posts($ids, $name, $host)];
	}

	$backup = rcb_export();
	update_post_meta($post->ID, 'technicalDefinitions', wp_slash(json_encode(array_values($defs))));
	Cache::getInstance()->invalidate();

	return $result + ['posts' => rcb_cookie_posts($ids, $name, $host), 'backup' => $backup];
}

function rcb_cmd_set_setting($name, $value, $opts, $input)
{
	if (!in_array($name, rcb_settings_map(), true)) {
		rcb_fail("'$name' ist keine RCB-Einstellung - Liste: settings");
	}

	$new = is_string($input) ? $input : ($value === 'empty' ? '' : $value);

	if ($new === null) {
		rcb_fail('Wert fehlt: set-setting <option> <wert|empty>');
	}

	$old = get_option($name);

	if (empty($opts['yes'])) {
		return ['dry_run' => true, 'option' => $name, 'alt' => $old, 'neu' => $new];
	}

	$backup = rcb_export();
	update_option($name, $new);
	Cache::getInstance()->invalidate();

	return ['option' => $name, 'alt' => $old, 'neu' => get_option($name), 'backup' => $backup];
}

function rcb_cmd_clear_cache()
{
	$result = ['rcb' => Cache::getInstance()->invalidate()];

	if (function_exists('rocket_clean_domain')) {
		rocket_clean_domain();
		$result['wp_rocket'] = true;
	}

	return $result;
}

if (!class_exists(Export::class)) {
	rcb_fail('Real Cookie Banner ist auf dieser Site nicht aktiv');
}

$cmd = array_shift($args);
$pos = array_values(array_filter($args, function ($a) {
	return strpos($a, '=') === false && !in_array($a, ['yes', 'all', 'empty', 'remove', 'session'], true);
}));
$opts = rcb_opts($args);

switch ($cmd) {
	case 'info':
		rcb_out(rcb_info());
		break;
	case 'services':
		rcb_out(rcb_cmd_services());
		break;
	case 'service':
		rcb_out(rcb_cmd_service($pos[0] ?? rcb_fail('service <id|post_name|titel>')));
		break;
	case 'blockers':
		rcb_out(rcb_cmd_blockers());
		break;
	case 'banner-links':
		rcb_out(rcb_cmd_banner_links());
		break;
	case 'settings':
		rcb_out(rcb_cmd_settings($opts));
		break;
	case 'revisions':
		rcb_out(rcb_cmd_revisions($opts));
		break;
	case 'export':
		rcb_out(rcb_export());
		break;
	case 'import':
		rcb_out(rcb_cmd_import(is_string($rcb_input) ? json_decode($rcb_input, true) : null, $opts));
		break;
	case 'set-code':
		rcb_out(rcb_cmd_set_code($pos[0] ?? rcb_fail('set-code <dienst> <feld>'), $pos[1] ?? '', $opts, $rcb_input));
		break;
	case 'set-cookie':
		rcb_out(rcb_cmd_set_cookie($pos[0] ?? rcb_fail('set-cookie <dienst> <name>'), $pos[1] ?? rcb_fail('set-cookie <dienst> <name>'), $opts, $rcb_input));
		break;
	case 'set-setting':
		rcb_out(rcb_cmd_set_setting($pos[0] ?? rcb_fail('set-setting <option> <wert>'), $pos[1] ?? ($opts['empty'] ?? false ? 'empty' : null), $opts, $rcb_input));
		break;
	case 'clear-cache':
		rcb_out(rcb_cmd_clear_cache());
		break;
	default:
		rcb_fail('Befehl: info, services, service, blockers, banner-links, settings, revisions, export, import, set-code, set-cookie, set-setting, clear-cache');
}
