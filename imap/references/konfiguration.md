# imap - Konfiguration

**Inhalt:** Zugangsdaten aus der muttrc · Keystore statt Klartext · Kontoname

## Zugangsdaten aus der muttrc

Zugangsdaten stehen in `~/.muttrc` und werden von mutt und diesem Script
gemeinsam genutzt. Es gibt bewusst **keine** zweite Credential-Datei.

```
set folder    = "imaps://mail.example.at/"
set imap_user = "<username>"
set imap_pass = "..."

account-hook imaps://mail.example.at/   'set imap_user="<username>" imap_pass="..."'
account-hook imaps://office.example.at/ 'set imap_user="<username>" imap_pass="..."'
```

Ausgewertet wird eine Teilmenge der muttrc-Syntax: `set`, `account-hook`,
`source` (auch `source "cmd |"`) und Backtick-Substitution. Damit funktioniert
auch ein Keystore statt Klartext:

```
account-hook imaps://mail.example.at/ 'set imap_user="<username>" imap_pass=`pass show mail/example`'
```

Anderer Pfad per `--muttrc /pfad/zur/datei`. Fehlen User oder Passwort für ein
Konto, wird es **übersprungen** statt geraten.

**Kontoname** ist das erste Label des Hostnamens: `mail.example.at` -> `mail`,
`office.example.at` -> `office`. Ohne `--account` gilt das Konto aus `set folder`
als Default; `list` ohne `--account` fragt **alle** Konten ab.

**Der Kontoname hier ist nicht der aus Thunderbird.** Dort steht ein frei
vergebener Anzeigename ("Arbeit", "privat", der eigene Nachname), hier das erste
Label des Hostnamens -- eine Mail, die aus Thunderbird als Text herauskopiert
wurde, nennt also ein Konto, das dieser Skill nicht kennt. Statt zu raten oder
ein Mapping zu pflegen: `find` fragt ohne `--account` ohnehin alle Konten ab und
liefert den richtigen Namen mit. Wer das Mapping trotzdem festhalten will,
schreibt es in `~/.claude/imap-triage.md` (persönliche Datei, siehe SKILL.md) --
nicht in diesen Skill.
