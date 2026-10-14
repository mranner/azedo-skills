# Skill-Mechanik

Was sich ändert, wenn das Dokument ein Skill ist. Alles andere steht in [SKILL.md](../SKILL.md).

## Aufruf durch Modell oder User

Zwei Wege, die zwei verschiedene Lasten tragen:

- **Vom Modell aufrufbar:** Der Skill hat eine `description`, der Agent kann ihn selbst laden, und andere Skills können ihn erreichen. Per `/name` aufrufbar bleibt er trotzdem. Die `description` ist ein Pointer, der immer im Kontext liegt: dauerhafte Kontextlast gegen Auffindbarkeit. Ein reiner Referenz-Skill dieser Art ist auch der Ort für Referenz, die mehrere Skills brauchen.
- **Nur vom User aufrufbar** (`disable-model-invocation: true`): keine Kontextlast, aber Merklast - der Mensch muss wissen, dass es den Skill gibt. Die `description` wird zur einzeiligen Zusammenfassung für den Menschen, ohne Trigger-Liste. Kein anderer Skill kann ihn auslösen.

Vom Modell aufrufbar nur dann, wenn der Agent den Skill selbst finden muss oder ein anderer Skill ihn braucht. Läuft er nur auf Zuruf, nur vom User aufrufbar.

Referenz, die zwei nur vom User aufrufbare Skills brauchen, kann in keinem der beiden liegen. Sie gehört in eine eigene Datei außerhalb, auf die beide zeigen.

## Aufteilen nach Aufruf

Einen Teil als eigenen, vom Modell aufrufbaren Skill abspalten, wenn er einen eigenen Trigger hat, den der User tatsächlich verwendet, oder ein anderer Skill ihn erreichen muss. Die neue `description` kostet dauerhaft Kontext - die eigene Erreichbarkeit muss das wert sein.

Aufteilen nach Ablauf (spätere Schritte verleiten zum Hetzen): siehe [SKILL.md](../SKILL.md), Abschnitt „Schritte und Abschlusskriterien".

## Router-Skills

Werden die nur vom User aufrufbaren Skills zu viele, um sie im Kopf zu behalten, hilft ein **Router-Skill**: ein einzelner, nur vom User aufrufbarer Skill, der die anderen nennt und sagt, wann welcher dran ist. Er kann nur hinweisen, nicht auslösen.
