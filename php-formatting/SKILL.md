---
name: php-formatting
description: >
  PHP-Code-Formatierung nach PSR-2 mit azedo-spezifischen Anpassungen,
  inklusive Reihenfolge neuer Methoden und Hook-Registrierungen.
  Wende diesen Skill IMMER automatisch an, wenn du PHP-Code schreibst oder änderst —
  auch ohne expliziten Aufruf. Der User kann den Skill auch manuell auslösen mit
  /php-formatting oder "formatiere den PHP Code".
  Trigger: /php-formatting, jede PHP-Datei die erstellt oder bearbeitet wird.
allowed-tools: [Read, Edit, Write]
---

# php-formatting – PHP Code-Stil

Basiert auf PSR-2, mit azedo-spezifischen Anpassungen (siehe Abweichungen).

**Automatische Anwendung:** Gilt für jede PHP-Datei die du erstellst oder änderst.
Bei manuellem Aufruf (/php-formatting) die genannte Datei oder den sichtbaren
PHP-Code komplett nach diesen Regeln formatieren.

## PSR-2 Grundregeln (gelten unverändert)

- Dateien MÜSSEN Unix-Zeilenenden (LF) verwenden
- Dateien MÜSSEN mit einer einzelnen Leerzeile enden
- Der schließende `?>` Tag MUSS in reinen PHP-Dateien weggelassen werden
- Zeilen SOLLEN maximal 80 Zeichen lang sein, Soft-Limit 120 Zeichen
- Pro Zeile maximal ein Statement
- Kein Whitespace am Zeilenende
- Eine Leerzeile nach der `namespace`-Deklaration
- Ein `use`-Keyword pro Deklaration, eine Leerzeile nach dem `use`-Block
- `extends`/`implements` auf derselben Zeile wie der Klassenname
- Öffnende geschweifte Klammer von Klassen auf eigener Zeile
- Öffnende geschweifte Klammer von Methoden auf eigener Zeile
- Alle Properties und Methoden MÜSSEN Sichtbarkeit deklarieren (`public`, `protected`, `private`)
- `abstract`/`final` vor der Sichtbarkeit, `static` nach der Sichtbarkeit
- PHP-Keywords in Kleinbuchstaben (`true`, `false`, `null`)
- Kontrollstruktur-Keywords mit einem Leerzeichen danach
- Kein Leerzeichen nach öffnender / vor schließender Klammer bei Kontrollstrukturen
- Öffnende geschweifte Klammer von Kontrollstrukturen auf derselben Zeile
- `case` einmal eingerückt gegenüber `switch`
- Closures: Leerzeichen nach `function` und vor/nach `use`

## Abweichungen von PSR-2

### 1. Einrückung: Tabs bevorzugt

Wir verwenden **Tabs** für die Einrückung (nicht 4 Spaces).

**Ausnahme:** Wenn die bestehende Datei bereits durchgehend Spaces für die
Einrückung verwendet, dann die 4-Spaces-Regel von PSR-2 beibehalten —
nicht auf Tabs umstellen.

Regel: Bestehenden Stil der Datei erkennen und beibehalten. Neue Dateien → Tabs.

### 2. Leerzeilen um Kontrollstrukturen

Vor der Zeile mit dem Kontrollstruktur-Keyword (`if`, `else if`, `for`, `foreach`,
`while`, `do`, `switch`, `try`) und nach der schließenden `}` jeweils eine
**Leerzeile** einfügen.

Ausnahmen:
- Zwischen `}` und unmittelbar folgendem `else`, `elseif`, `catch`, `finally`
  **keine** zusätzliche Leerzeile (die gehören zusammen).
- Am Anfang/Ende eines Blocks (direkt nach `{` / direkt vor `}`) keine
  überflüssige Leerzeile — **außer** die erste bzw. letzte Anweisung im Block
  ist selbst eine Kontrollstruktur. Dann hat Regel 2 Vorrang: Leerzeile **vor**
  der Kontrollstruktur (auch direkt nach dem öffnenden `{`) und **nach** ihrer
  schließenden `}` (auch direkt vor dem schließenden `}` des umschließenden
  Blocks). Die Leerzeile vor/nach Kontrollstrukturen gilt also konsequent, auch
  an Blockgrenzen.

Beispiel (verschachtelte Kontrollstruktur als erstes/letztes Statement):

```php
foreach ($files as $file) {

	if (preg_match('/(\d{4}-\d{2}-\d{2})/', basename($file), $m)) {
		$dated[] = $file;
	}

}
```

### 3. Leerzeilen nach Methoden-/Funktionsdeklarationen

Nach der schließenden `}` einer Methode oder Funktion immer eine **Leerzeile**
einfügen — außer es folgt direkt die schließende `}` der Klasse.

### 4. Leerzeilen um Kommentarblöcke

Vor `/*` und nach `*/` (mehrzeilige Kommentare, inkl. DocBlocks `/** ... */`)
jeweils eine **Leerzeile** einfügen — auch zwischen `*/` und der darauf
folgenden Funktions-/Methodendeklaration. Ausnahme: am Blockanfang/Ende
keine überflüssige Leerzeile.

## Kommentare: Inhalt und Umfang

Die Regeln oben betreffen die Formatierung von Kommentaren, diese ihren Inhalt.

Ein Kommentar steht nur dort, wo er etwas trägt, das der Code nicht selbst sagt:
eine Falle, eine belegte Eigenheit eines Fremdsystems, ein bewusst gewählter
Sonderweg. Doc-Block am Klassen- oder Methodenkopf höchstens zwei Zeilen,
Inline-Kommentar einer.

Nicht kommentieren, was ohnehin dasteht — den Methodennamen in Worten,
Aufzählungen verwandter Klassen, Verweise auf Code drei Zeilen weiter, die
Signatur als Prosa.

Beim Verschieben von Code gehören geerbte Kommentare auf denselben Prüfstand:
mitkürzen, nicht ungeprüft mitschleppen.

Gilt nicht für PHPDoc-Annotationen (`@param`, `@return`, `@var`) — die sind
Schnittstellenbeschreibung, kein Prosa-Kommentar.

## Reihenfolge von Methoden und Hooks

**Neue Methoden** alphabetisch zwischen die bestehenden Nachbarn einsortieren:
an die erste Stelle, deren Vorgänger alphabetisch davor und deren Nachfolger
danach liegt. Bestehende Methoden bleiben, wo sie sind, auch wenn die Klasse
insgesamt nicht sortiert ist. Beispiel: Bestand `init()`, `save()`, `delete()`,
neue Methode `render()` kommt zwischen `init()` und `save()`.

**Hook-Registrierungen** (`add_action`/`add_filter`) im Konstruktor nach
Hook-Namen sortieren, Actions und Filter gemeinsam:

```php
public function __construct()
{
	add_action('admin_init', [$this, 'registerSettings']);
	add_action('init', [$this, 'registerPostType']);
	add_filter('the_content', [$this, 'appendNotice']);
}
```

## Beispiel

```php
<?php

namespace App\Service;

use App\Repository\UserRepository;
use App\Model\User;

class UserService
{
	/**
	 * @var UserRepository
	 */

	private $repository;

	/**
	 * @param UserRepository $repository
	 */

	public function __construct(UserRepository $repository)
	{
		$this->repository = $repository;
	}

	/**
	 * Aktiven User anhand der E-Mail-Adresse suchen.
	 *
	 * @param string $email
	 * @return User|null
	 */

	public function findActiveByEmail($email)
	{
		$email = trim($email);

		if (empty($email)) {
			return null;
		}

		/* Suche in der Datenbank */

		$user = $this->repository->findByEmail($email);

		if ($user !== null && $user->isActive()) {
			return $user;
		} else {
			return null;
		}

		return null;
	}

	/**
	 * Alle User eines Teams zurückgeben.
	 *
	 * @param int $teamId
	 * @return User[]
	 */

	public function getTeamMembers($teamId)
	{
		$members = [];

		foreach ($this->repository->findByTeam($teamId) as $user) {
			$members[] = $user;
		}

		return $members;
	}

}
```

Beachte im Beispiel:
- **Tabs** für Einrückung
- **Leerzeile vor** `if`, `foreach` und **nach** deren schließendem `}`
- **Leerzeile nach** jeder Methoden-`}` (auch vor der Klassen-`}`)
- **Keine Leerzeile** zwischen `}` und `else` (gehören zusammen)
- **Leerzeile vor** `/*` und **nach** `*/` (auch zwischen DocBlock und Funktion/Property)
- Klassen-/Methoden-Klammern auf eigener Zeile (PSR-2)
- Kontrollstruktur-Klammern auf derselben Zeile (PSR-2)
