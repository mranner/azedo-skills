# mail-as-me - Profil anlegen und nachschaerfen

**Inhalt:** `setup` (Profil aus echten Mails bauen oder erweitern) · `learn` (Korrekturen einer gesendeten Mail ins Profil zurueckspielen)

## setup - Profil bauen/erweitern (Auto + kurzes Interview)

```bash
python3 "$SKILL_DIR/extract.py" --input <ordner|datei> \
  --out ~/.claude/mail-as-me/<profil>/corpus \
  --config ~/.claude/mail-as-me/<profil>/config.json
```

1. **Samples einsammeln.** No-privilege-Weg fuer Mitarbeiter: in Thunderbird Mails
   markieren → „Speichern als" bzw. herausziehen → `.eml` in einen Ordner. Auch
   `.mbox` (ganzer Ordner-Export) oder ein Maildir/Cyrus-Verzeichnis moeglich.
   Ausgewaehlt werden nur selbstverfasste Mails mit substanziellem Eigentext,
   Register gestreut (formell + locker), moeglichst aelter als vier Wochen - so
   rutschen keine KI-generierten Fassungen in den Korpus, die das Profil auf
   genau den Stil zurueckziehen wuerden, den es vermeiden soll. Anhaenge werden
   ignoriert.
2. **Auto-Extraktion.** `extract.py` strippt Zitat + Signatur, schlaegt je Mail
   `bucket` (Register) und `dialekt_auto` vor.
3. **Kurzes Interview** - nur was die Samples nicht sicher hergeben; den
   Auto-Vorschlag zeigen, der Mensch bestaetigt oder korrigiert. Der Auto-Detect
   liegt beim Dialekt gelegentlich daneben, deshalb ist er hier nur ein Vorschlag:
   - Sign-off je Register samt Sonderfaellen (z.B. „Mike nur bei Empfaengern, die
     mich selbst so nennen").
   - Du/Sie-Zuordnung.
   - Dialekt (z.B. de-AT: „eh", „Jänner", „schlimmster Fall").
   - Empfaenger/Domain → Register (`register_map`).
   - Versand-Identitaet: eigene Absenderadresse und die imap-Konten fuer
     Gesendet und Entwuerfe (`send.from`, `send.account`, `draft.account`;
     ohne IMAP-Konto `send.bcc`, siehe [versand.md](versand.md)).
4. **Profil schreiben.** `config.json` aus dem Interview, `referenz.md` aus
   `templates/referenz.template.md` mit den abgeleiteten Markern + Beispiel-Index
   fuellen. Ein erneuter Lauf erweitert den Korpus, bestehende `clean/` bleiben.

Einzelne Datei nur pruefen (nichts schreiben): `extract.py --analyze <datei>`.

## learn - Feedback-Loop (Konvergenz)

```
--draft <entwurf> --sent <tatsaechlich_gesendet>
```

Beide Fassungen kommen typischerweise als Dateien aus einem vom Nutzer genannten
Projektordner (Entwurf + tatsaechlich gesendete Fassung nebeneinander). Diff der
beiden bilden, die Korrekturen als neue Anti-Patterns/Beispiele an `referenz.md`
anhaengen - dabei generelle Stilregeln von inhaltlichen Einzelfall-Aenderungen
trennen, sonst wird eine einmalige Sachkorrektur zur Stilregel. So wird jede
korrigierte Mail zum Trainingssignal; die Korrekturen pro Mail nehmen mit der Zeit
ab. Ein aktiver CR-Kontext (kanboard/handoff) kann als Herkunft der Korrektur
mitgeschrieben werden.
