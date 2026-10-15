#!/usr/bin/env node
// wp-rcb consent-test: welche fremden Hosts eine Seite ohne Einwilligung, nach
// "nur essenzielle" und nach "alle akzeptieren" anfragt. Braucht Playwright
// (Chromium) - nicht auf FreeBSD verfügbar, also am Mac oder unter Linux.

import { createRequire } from 'node:module';
import { homedir } from 'node:os';
import { join } from 'node:path';

const PW_DIR = process.env.RCB_PLAYWRIGHT_DIR || join(homedir(), '.cache', 'wp-rcb');

// RCB zeigt Headless-Browsern keinen Banner, GA4 verwirft deren Hits

const USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
	+ '(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36';

const PHASES = ['ohne', 'essenziell', 'alle'];

function usage() {
	console.error(`Aufruf: node consent-test.mjs <url> [<url>…] [Optionen]
  --headless            ohne Fenster (GA4 kann Hits dann verwerfen)
  --wait <ms>           Wartezeit nach 'load', Default 2500
  --locale <code>       Default de-DE
  --accept <regex>      Text des Buttons "alle akzeptieren"
  --essential <regex>   Text des Buttons "nur essenzielle"
  --json`);
	process.exit(1);
}

function parseArgs(argv) {
	const opts = {
		urls: [], headless: false, wait: 2500, locale: 'de-DE', json: false,
		accept: /alle akzeptieren|accept all/i,
		// RCB nennt den Button oft "Weiter ohne Einwilligung", nicht "nur essenzielle"
		essential: /ohne Einwilligung|nur essenziell|without consent|essential only/i,
	};

	for (let i = 0; i < argv.length; i++) {
		const a = argv[i];

		if (a === '--headless') opts.headless = true;
		else if (a === '--json') opts.json = true;
		else if (a === '--wait') opts.wait = Number(argv[++i]);
		else if (a === '--locale') opts.locale = argv[++i];
		else if (a === '--accept') opts.accept = new RegExp(argv[++i], 'i');
		else if (a === '--essential') opts.essential = new RegExp(argv[++i], 'i');
		else if (a.startsWith('--')) usage();
		else opts.urls.push(a);
	}

	if (!opts.urls.length) usage();

	return opts;
}

function loadPlaywright() {
	try {
		return createRequire(join(PW_DIR, 'package.json'))('playwright');
	} catch {
		console.error(`Playwright fehlt in ${PW_DIR}. Einmalig installieren:
  npm install --prefix ${PW_DIR} playwright
  ${join(PW_DIR, 'node_modules', '.bin', 'playwright')} install chromium`);
		process.exit(1);
	}
}

const bare = (host) => host.replace(/^www\./, '');

// Banner liegt im Shadow-DOM - getByRole/getByText durchdringen es, CSS-Selektoren nicht

async function click(page, re) {
	for (const loc of [page.getByRole('button', { name: re }), page.getByText(re)]) {
		try {
			await loc.first().click({ timeout: 8000 });
			return true;
		} catch {
			// nächster Locator
		}
	}

	return false;
}

// Ein Reload direkt nach dem Klick verwirft die Einwilligung - erst das RCB-Cookie abwarten

async function consentStored(context) {
	for (let i = 0; i < 20; i++) {
		const cookies = await context.cookies();

		if (cookies.some((c) => c.name.startsWith('real_cookie_banner'))) return true;

		await new Promise((resolve) => setTimeout(resolve, 500));
	}

	return false;
}

async function visit(page, url, wait) {
	// networkidle läuft auf Seiten mit Dauer-Pings in den Timeout
	await page.goto(url, { waitUntil: 'load', timeout: 60000 });
	await page.waitForTimeout(wait);
}

async function runPhase(browser, phase, opts) {
	const site = bare(new URL(opts.urls[0]).hostname);
	const context = await browser.newContext({ userAgent: USER_AGENT, locale: opts.locale });
	const page = await context.newPage();
	const hosts = {};
	const gcs = new Set();
	let recording = phase === 'ohne';
	const result = { phase, banner: null, clicked: null, stored: null };

	page.on('request', (req) => {
		if (!recording) return;

		const u = new URL(req.url());

		if (!u.protocol.startsWith('http') || bare(u.hostname).endsWith(site)) return;

		hosts[u.hostname] = (hosts[u.hostname] || 0) + 1;

		const value = u.searchParams.get('gcs') || new URLSearchParams(req.postData() || '').get('gcs');

		if (value) gcs.add(value);
	});

	await visit(page, opts.urls[0], opts.wait);
	result.banner = await page.getByRole('button', { name: opts.accept }).first().isVisible().catch(() => false);

	if (phase !== 'ohne') {
		result.clicked = await click(page, phase === 'alle' ? opts.accept : opts.essential);
		result.stored = result.clicked && await consentStored(context);
		recording = true;
		await visit(page, opts.urls[0], opts.wait);
	}

	for (const url of opts.urls.slice(1)) {
		await visit(page, url, opts.wait);
	}

	const cookies = await context.cookies();
	await context.close();

	return {
		...result,
		hosts: Object.fromEntries(Object.entries(hosts).sort((a, b) => b[1] - a[1])),
		gcs: [...gcs],
		cookies_fremd: cookies.filter((c) => !bare(c.domain.replace(/^\./, '')).endsWith(site))
			.map((c) => `${c.domain} ${c.name}`),
	};
}

function report(results) {
	const before = new Set();

	for (const r of results) {
		const consent = r.clicked === null ? '' : `, Klick: ${r.clicked}, Einwilligung gespeichert: ${r.stored}`;
		console.log(`\n== ${r.phase}  (Banner sichtbar: ${r.banner}${consent})`);

		for (const [host, n] of Object.entries(r.hosts)) {
			console.log(`  ${String(n).padStart(4)}  ${host}`);

			if (r.phase !== 'alle') before.add(host);
		}

		if (r.gcs.length) console.log(`  gcs: ${r.gcs.join(', ')}`);
		if (r.cookies_fremd.length) console.log(`  fremde Cookies: ${r.cookies_fremd.join(', ')}`);
		if (r.clicked === false) console.log('  ACHTUNG: Banner-Button nicht getroffen - --accept/--essential prüfen');
		if (r.clicked && !r.stored) console.log('  ACHTUNG: kein RCB-Cookie nach dem Klick - die Phase misst dasselbe wie "ohne"');
	}

	if (before.size) {
		console.log(`\nVor bzw. ohne volle Einwilligung angefragt: ${[...before].join(', ')}`);
	}
}

const opts = parseArgs(process.argv.slice(2));
const { chromium } = loadPlaywright();
const browser = await chromium.launch({ headless: opts.headless });
const results = [];

for (const phase of PHASES) {
	results.push(await runPhase(browser, phase, opts));
}

await browser.close();

if (opts.json) {
	console.log(JSON.stringify(results, null, 2));
} else {
	report(results);
}
