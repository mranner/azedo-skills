---
name: wp-rest
description: >
  WordPress-Inhalte über die REST-API pflegen, mit Application Password statt
  Shell-Zugang: Beiträge, Seiten und wiederverwendbare Blöcke anlegen und
  ändern, Medien hochladen samt Alt-Text und Slug, Kategorien und Schlagworte
  setzen, Templates und Global Styles von Block-Themes bearbeiten, dazu
  WooCommerce über /wc/v3/. Mehrere Sites über benannte Profile. Nicht
  zuständig für Cache, Plugins, Datenbank und Theme-Dateien - das bleibt
  wp-cli. Auch bei "leg einen Beitrag an", "lad das Bild hoch", "ändere den
  Text der Seite", "setz die Seite auf publish", "Produkt in WooCommerce".
  Trigger: /wp-rest.
---

# wp-rest -- WordPress-Inhalte über die REST-API

Pflegt Inhalte auf WordPress-Sites über `/wp-json/wp/v2/` und WooCommerce über
`/wp-json/wc/v3/`. Authentifiziert wird mit einem **Application Password** -
kein SSH, kein sudo, kein PHP-Eval. Das Passwort ist einzeln widerrufbar und
trägt nur die Rechte seines Benutzers.

**Aufruf:** `python3 "$SKILL_DIR/wp-rest" <subcommand> [options]`

`$SKILL_DIR` ist das Base Directory dieses Skills.

## Abgrenzung zu den anderen WordPress-Skills

| Skill | Zuständig für |
|---|---|
| **wp-rest** | Inhalte: Beiträge, Seiten, Medien, Terms, Blöcke, Templates, Global Styles, WooCommerce |
| `wp-cli` | Administration per SSH im Jail: Cache, Plugins, Themes, Datenbank, search-replace |
| `wordpress-pro` | Entwicklung eigener Endpunkte, Blöcke, Hardening |
| `wp-nf`, `wp-pys` | Ninja Forms, PixelYourSite |
| `mainwp` | Dashboard, Updates netzwerkübergreifend |
| `novamira` | voller PHP-/Dateisystemzugriff, nur für DEV/Staging |

**Was die REST-API nicht kann** - dafür bleibt `wp-cli` zuständig:
Theme-Dateien schreiben, Plugins aktivieren, Cache leeren, Datenbank-Operationen,
und das Customizer-CSS von Classic-Themes (siehe unten).

## Konfiguration

Profile kommen aus einer `.env` - Reihenfolge: `WP_REST_ENV` (voller Pfad),
sonst `.env` im aktuellen Arbeitsverzeichnis, sonst `~/.env`. Pro Instanz drei
Werte, der Name zwischen den Unterstrichen ist der Profilname:

```
WP_<INSTANZ>_URL=https://www.example.org
WP_<INSTANZ>_USER=<username>
WP_<INSTANZ>_APP_PASSWORD="xxxx xxxx xxxx xxxx xxxx xxxx"   # gequotet, enthält Leerzeichen
```

Optional:

```
WP_DEFAULT_INSTANCE=<instanz>          # sonst --instance nötig (außer bei genau einem Profil)
WP_<INSTANZ>_WC_KEY=ck_...             # eigene WooCommerce-Consumer-Keys,
WP_<INSTANZ>_WC_SECRET=cs_...          # sonst wird das App Password auch für /wc/v3 verwendet
```

`instances` zeigt, was gefunden wurde (ohne das Passwort auszugeben), `whoami`
prüft Zugang und Rechte gegen die Site.

**Sicherheitsregel:** Application Passwords nie auf der Kommandozeile übergeben,
nie in Logs oder Kommentare schreiben - ausschließlich aus der `.env` lesen.

## Subcommands

`python3 "$SKILL_DIR/wp-rest" <subcommand> --help` listet die Optionen direkt
aus dem Script.

### Zugang

| Subcommand | Zweck |
|---|---|
| `instances` | konfigurierte Profile auflisten |
| `whoami` | Zugang und Rechte des App-Passworts prüfen |

### Beiträge, Seiten, wiederverwendbare Blöcke

Alle Befehle dieses Abschnitts wählen den Post-Type über
`--type post|page|wp_block|media` (Default `post`); für alles andere unter
`wp/v2` gibt es `--endpoint <pfad>`.

| Subcommand | Zweck |
|---|---|
| `list-posts` | filtern nach Status, Suchbegriff, Kategorie, Elternseite |
| `get-post <id>` | Inhalt anzeigen oder mit `--output` in eine Datei schreiben |
| `create-post` | Titel, Inhalt, Status, Datum, Elternseite, Beitragsbild |
| `update-post <id>` | nur die übergebenen Felder, der Rest bleibt stehen |
| `set-status <id> <status>` | publish, draft, pending, private |
| `delete-post <id>` | Papierkorb, mit `--force` endgültig; `--yes` nötig |

### Kategorien und Schlagworte

| Subcommand | Zweck |
|---|---|
| `list-terms` | `--taxonomy categories\|tags` |
| `create-term` | Begriff anlegen |
| `set-terms <id>` | zuweisen, Namen oder IDs; `--create` legt fehlende an |

### Medien

| Subcommand | Zweck |
|---|---|
| `upload-media <datei>` | Upload samt `--title`, `--alt`, `--caption`, `--post` |
| `list-media` | Mediathek durchsuchen |
| `update-media <id>` | Titel, Alt-Text, Zuordnung nachziehen |
| `delete-media <id>` | endgültig (Medien haben keinen Papierkorb), `--yes` nötig |

Der **Dateiname wird zum Slug** und landet damit in der URL. Vor dem Upload
sprechenden Namen vergeben (`--filename`), nicht `IMG_4711.jpg` hochladen -
für Skalierung und Umbenennung ist `image-optimize` zuständig.

### Templates und Global Styles (nur Block-Themes)

| Subcommand | Zweck |
|---|---|
| `list-templates` | `--parts` für template-parts |
| `get-template <id>` | Markup anzeigen oder `--output` in eine Datei |
| `update-template <id>` | Markup setzen |
| `get-global-styles` | eigene Einstellungen, `--theme-defaults` für die Theme-Vorgaben, `--css-output` für styles.css allein |
| `set-global-css` | nur `styles.css` ersetzen, der Rest der theme.json-Ebene bleibt |
| `set-global-styles --file` | ganzes Styles-/Settings-JSON setzen |

### WooCommerce

Generisch über den Namespace `wc/v3` - `resource` ist der Endpunkt-Pfad, z.B.
`products`, `orders`, `customers`, `coupons`, `products/categories`.

| Subcommand | Zweck |
|---|---|
| `wc-list <resource>` | auflisten, `--param key=value` für Filter der API |
| `wc-get <resource> <id>` | einzeln anzeigen |
| `wc-create <resource> --file` | anlegen, Felder als JSON-Datei |
| `wc-update <resource> <id> --file` | ändern |
| `wc-delete <resource> <id>` | löschen, `--yes` nötig |

### Escape-Hatch

`request <method> <path>` setzt einen rohen Aufruf ab, `--namespace` wählt den
Namespace (Default `wp/v2`). Damit sind auch `settings`, `block-types`,
`block-patterns/patterns`, `navigation` und `block-renderer/<name>` erreichbar,
ohne dass es dafür eigene Subcommands braucht.

## Block-Markup: der Fallstrick

Die REST-API spricht nicht den Editor an, sondern den Inhalt, den er erzeugt.
Block-Markup ist HTML mit `<!-- wp:… -->`-Kommentaren im Feld `content`.

- **Immer das Roh-Markup lesen.** `get-post` verwendet dafür `context=edit`;
  `--rendered` liefert `content.rendered`, also die Fassung **ohne**
  Block-Kommentare. Wer die zurückschreibt, zerlegt die Blockstruktur.
- **Geschriebenes Markup wird nicht validiert.** Die Block-Validierung passiert
  erst clientseitig - kaputte Delimiter fallen also erst auf, wenn jemand die
  Seite im Editor öffnet („Block enthält unerwarteten Inhalt").
- Der Skill konvertiert **nicht** zwischen HTML und Block-Markup. Sites mit
  Classic Editor bekommen reines HTML, Block-Themes Block-Markup - so, wie es
  gelesen wurde.

## Weiteres zu beachten

- **Kodierung:** Inhalte mit Umlauten über `--content-file` übergeben, nicht
  über `--content` auf der Kommandozeile.
- **Seiten-Cache:** Sites mit WP Super Cache o.ä. liefern nach einer Änderung
  weiterhin die alte Fassung aus. Der Skill kann den Cache nicht leeren; danach
  über `wp-cli` leeren und den Nutzer darauf hinweisen.
- **Custom CSS trennt sich nach Theme-Typ.** Der Customizer-Eintrag
  „Zusätzliches CSS" von Classic-Themes liegt im Post-Type `custom_css`, der in
  Core **ohne** `show_in_rest` registriert ist und über die REST-API weder
  lesbar noch schreibbar ist - dafür `wp-cli` (`wp theme mod get
  custom_css_post_id`, dann `wp post get/update`). Nur Block-Themes haben
  Global Styles.
- **Löschen braucht `--yes`.** Ohne die Option zeigen `delete-post`,
  `delete-media` und `wc-delete` nur, was getroffen wäre.
- Temporäre Dateien (Inhalte, Exporte) gehören ins Projekt-`.tmp/`, nicht ins
  Skill-Verzeichnis.
