# imap - Header und Rohnachricht

**Inhalt:** wofür `--headers` und `--raw` gebraucht werden · was sie ausgeben · Kosten

## Header lesen (`--headers` / `--raw`)

Die Standardausgabe von `read` zeigt bewusst nur `From`, `To`, `Subject`, `Date`
und Anhänge -- für die Triage ist alles andere Rauschen. Bei Mail-Problemen ist
aber genau der Rest die Aussage:

- **Zustellweg** -- die `Received`-Kette: welcher Smarthost war beteiligt, wo
  wurde der Absender umgeschrieben
- **SPF/DKIM/DMARC** -- `Authentication-Results`, wenn Mails im Spam landen
- **Bcc-Verhalten** -- ob ein `Bcc`-Header in der zugestellten Mail stehen blieb
  und die Adresse damit an den To-Empfänger leakt
- **Newsletter-Triage** -- `List-Id` / `List-Unsubscribe`
- **Dubletten** -- `Message-ID` als Gegenprobe zum kontoübergreifenden `batch`

`--headers` liefert **alle** Header in Originalreihenfolge; Mehrfach-Header wie
`Received` bleiben einzeln stehen, sonst wäre die Kette nicht mehr lesbar. Die
Zeilenfaltung wird aufgelöst, der Wert sonst nicht angefasst -- insbesondere
**kein** RFC-2047-Decoding, weil bei einer Header-Analyse der Rohwert zählt. Im
`--json` steht das als Feld `headers` (Liste aus `[name, value]`).

`--raw` gibt die Nachricht komplett und ungeparst aus (Header + Body) -- die
Wahl bei MIME-Problemen. In der Textausgabe ersetzt `--raw` die Aufbereitung; per
Pipe an `less`/`grep` ist das der übliche Weg.

Beides kostet **keinen** zusätzlichen IMAP-Roundtrip: `BODY.PEEK[]` holt ohnehin
die vollständige Rohnachricht; `--headers`/`--raw` geben nur mehr davon aus. `BODY.PEEK`
gilt unverändert -- auch mit `--headers`/`--raw` bleibt der Ungelesen-Status.
