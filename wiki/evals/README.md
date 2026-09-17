# evals — Trigger-Testfaelle

`evals.json` im Schema des Anthropic-`skill-creator` (Feld `expectations` =
pruefbare Aussagen je Fall). Die Faelle zielen auf das **Triggering**: ob der
Skill geladen wird, wenn er gebraucht wird - und ob er wegbleibt, wenn nicht.

- **1, 2** — handlungsbezogener Trigger: ein Eingriff an einem dokumentierten
  Server, ohne dass das Wort „Wiki" faellt. Genau der Fall, der bis 1.59.0 nicht
  ausgeloest hat.
- **3, 4, 5** — die klassischen Wege: fragen, eintragen, Remote-Config.
- **6, 7** — Negativfaelle. Ein Skill, der auf jede Dateiaenderung anspringt, ist
  so unbrauchbar wie einer, der nie anspringt.

Ausgefuehrt werden sie mit dem `skill-creator`-Skill (je Fall ein Lauf mit und
einer ohne Skill, danach graden). Die Erwartungen zum Triggering liest man aus
dem Transkript ab, nicht aus einer Ausgabedatei.
