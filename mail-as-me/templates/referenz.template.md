# Few-shot-Referenz: Mail-Stil {{NAME}}

Zweck: Wird beim **Entwerfen einer Mail** geladen, damit der Entwurf nach {{NAME}}
klingt. Aufbau: (1) Register-Matrix, (2) Stilmarker, (3) Anti-Patterns, (4) Beispiele.

Grundlage: selbstverfasste Mails (Korpus in `corpus/clean/`) + laufende Korrekturen
(Feedback-Loop via `learn`).

**Beim Entwerfen:** Empfängertyp bestimmen → passende Zeile der Register-Matrix +
1-2 Beispiele desselben Registers heranziehen → Anti-Patterns prüfen.

---

## 1. Register-Matrix

Achse: formell ↔ informell, festgemacht am Empfänger (siehe `config.json.register_map`).

| Empfängertyp | Anrede | Anrede-Form | Sign-off | Beleg |
|---|---|---|---|---|
| {{FORMELL_TYP}} | {{FORMELL_ANREDE}} | Sie/Ihnen | {{FORMELL_SIGNOFF}} | {{FORMELL_BELEG}} |
| {{PARTNER_TYP}} | {{PARTNER_ANREDE}} | Du/Dir (groß) | {{PARTNER_SIGNOFF}} | {{PARTNER_BELEG}} |

Sign-off-Sonderfälle: {{SIGNOFF_CONDITIONS}}

---

## 2. Stilmarker (nachahmen)

Aus dem Korpus abgeleitete, belegte Gewohnheiten — je Punkt eine Mail-Referenz:

- **Einstieg/Aufbau:** {{MARKER_AUFBAU}}
- **Konkretheit:** {{MARKER_KONKRET}}
- **Ton/Hedging:** {{MARKER_TON}}
- **ich vs. wir:** {{MARKER_ICH_WIR}}
- **Dialekt ({{DIALEKT}}):** {{MARKER_DIALEKT}}

---

## 3. Anti-Patterns (vermeiden)

Geprüft über den **humanizer-de**-Skill; hier nur als Checkliste mit persönlichem
Bezug. Standard-KI-Tells: Gedankenstrich (— → `-`), Nominalkomposita auflösen,
elliptische Antithese, erfundene Zusagen/Deadlines, Anführungszeichen um Paraphrasen,
Absolutheit ohne Hedge, Bestätigungsfloskeln. Echte Umlaute, gerade Anführungszeichen.

Persönliche Zusätze (aus `learn`): {{ANTI_PERSOENLICH}}

---

## 4. Beispiele

### Index (alle in `corpus/clean/<id>.md`)

{{BEISPIEL_INDEX}}

### Eingebettete Exemplare

{{EXEMPLARE}}
