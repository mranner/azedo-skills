---
name: php-formatting
description: >
  PHP-Code-Formatierung nach PSR-2 mit azedo-spezifischen Anpassungen.
  Wende diesen Skill IMMER automatisch an, wenn du PHP-Code schreibst oder aenderst —
  auch ohne expliziten Aufruf. Der User kann den Skill auch manuell ausloesen mit
  /php-formatting oder "formatiere den PHP Code".
  Trigger: /php-formatting, jede PHP-Datei die erstellt oder bearbeitet wird.
---

# php-formatting – PHP Code-Stil

Basiert auf PSR-2, mit azedo-spezifischen Anpassungen (siehe Abweichungen).

**Automatische Anwendung:** Gilt fuer jede PHP-Datei die du erstellst oder aenderst.
Bei manuellem Aufruf (/php-formatting) die genannte Datei oder den sichtbaren
PHP-Code komplett nach diesen Regeln formatieren.

## PSR-2 Grundregeln (gelten unveraendert)

- Dateien MUESSEN Unix-Zeilenenden (LF) verwenden
- Dateien MUESSEN mit einer einzelnen Leerzeile enden
- Der schliessende `?>` Tag MUSS in reinen PHP-Dateien weggelassen werden
- Zeilen SOLLEN maximal 80 Zeichen lang sein, Soft-Limit 120 Zeichen
- Pro Zeile maximal ein Statement
- Kein Whitespace am Zeilenende
- Eine Leerzeile nach der `namespace`-Deklaration
- Ein `use`-Keyword pro Deklaration, eine Leerzeile nach dem `use`-Block
- `extends`/`implements` auf derselben Zeile wie der Klassenname
- Oeffnende geschweifte Klammer von Klassen auf eigener Zeile
- Oeffnende geschweifte Klammer von Methoden auf eigener Zeile
- Alle Properties und Methoden MUESSEN Sichtbarkeit deklarieren (`public`, `protected`, `private`)
- `abstract`/`final` vor der Sichtbarkeit, `static` nach der Sichtbarkeit
- PHP-Keywords in Kleinbuchstaben (`true`, `false`, `null`)
- Kontrollstruktur-Keywords mit einem Leerzeichen danach
- Kein Leerzeichen nach oeffnender / vor schliessender Klammer bei Kontrollstrukturen
- Oeffnende geschweifte Klammer von Kontrollstrukturen auf derselben Zeile
- `case` einmal eingerueckt gegenueber `switch`
- Closures: Leerzeichen nach `function` und vor/nach `use`

## Abweichungen von PSR-2

### 1. Einrueckung: Tabs bevorzugt

Wir verwenden **Tabs** fuer die Einrueckung (nicht 4 Spaces).

**Ausnahme:** Wenn die bestehende Datei bereits durchgehend Spaces fuer die
Einrueckung verwendet, dann die 4-Spaces-Regel von PSR-2 beibehalten —
nicht auf Tabs umstellen.

Regel: Bestehenden Stil der Datei erkennen und beibehalten. Neue Dateien → Tabs.

### 2. Leerzeilen um Kontrollstrukturen

Vor der Zeile mit dem Kontrollstruktur-Keyword (`if`, `else if`, `for`, `foreach`,
`while`, `do`, `switch`, `try`) und nach der schliessenden `}` jeweils eine
**Leerzeile** einfuegen.

Ausnahmen:
- Zwischen `}` und unmittelbar folgendem `else`, `elseif`, `catch`, `finally`
  **keine** zusaetzliche Leerzeile (die gehoeren zusammen).
- Am Anfang/Ende eines Blocks (direkt nach `{` / direkt vor `}`) keine
  ueberfluessige Leerzeile — **ausser** die erste bzw. letzte Anweisung im Block
  ist selbst eine Kontrollstruktur. Dann hat Regel 2 Vorrang: Leerzeile **vor**
  der Kontrollstruktur (auch direkt nach dem oeffnenden `{`) und **nach** ihrer
  schliessenden `}` (auch direkt vor dem schliessenden `}` des umschliessenden
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

Nach der schliessenden `}` einer Methode oder Funktion immer eine **Leerzeile**
einfuegen — ausser es folgt direkt die schliessende `}` der Klasse.

### 4. Leerzeilen um Kommentarbloecke

Vor `/*` und nach `*/` (mehrzeilige Kommentare, inkl. DocBlocks `/** ... */`)
jeweils eine **Leerzeile** einfuegen — auch zwischen `*/` und der darauf
folgenden Funktions-/Methodendeklaration. Ausnahme: am Blockanfang/Ende
keine ueberfluessige Leerzeile.

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
	 * Alle User eines Teams zurueckgeben.
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
- **Tabs** fuer Einrueckung
- **Leerzeile vor** `if`, `foreach` und **nach** deren schliessendem `}`
- **Leerzeile nach** jeder Methoden-`}` (auch vor der Klassen-`}`)
- **Keine Leerzeile** zwischen `}` und `else` (gehoeren zusammen)
- **Leerzeile vor** `/*` und **nach** `*/` (auch zwischen DocBlock und Funktion/Property)
- Klassen-/Methoden-Klammern auf eigener Zeile (PSR-2)
- Kontrollstruktur-Klammern auf derselben Zeile (PSR-2)
