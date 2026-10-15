---
name: meta-ads
description: >
  Meta (Facebook/Instagram) über Graph- und Marketing-API: Token prüfen,
  Datasets (Pixel) auflisten, anlegen und ihre Events abfragen, Test-Events
  per Conversions API senden, Werbe-Insights pro Kampagne abrufen. Mehrere
  Kunden über Profile mit je eigenem Systemnutzer-Token, dazu die Einrichtung
  in der Oberfläche (App, Systemnutzer, Domain-Verifizierung). Auch bei
  "kommen die Pixel-Events an", "leg ein Dataset an", "wie laufen die
  Facebook-Kampagnen", "Systemnutzer-Token". Trigger: /meta-ads.
---

# meta-ads - Meta Graph- und Marketing-API

Zugriff über das gebündelte Script `meta-ads` (Python >=3.11, nur Standardbibliothek).

**Aufruf:** `python3 "$SKILL_DIR/meta-ads" [--profile <name>] <subcommand> [options]`

`$SKILL_DIR` ist das Base Directory dieses Skills (dort wo diese SKILL.md liegt).

## Modell: ein Systemnutzer pro Kundenportfolio

Jeder Kunde bekommt im **eigenen** Unternehmensportfolio eine Meta-App und einen
Systemnutzer, und damit einen eigenen Token. Die Assets (Dataset, Werbekonto,
Domain) sind aus Sicht dieses Systemnutzers eigene Assets, dafür reicht der
Standardzugriff der App: kein App-Review, keine Unternehmensverifizierung.

Ein zentraler Systemnutzer im eigenen Portfolio, dem die Kunden ihre Assets als
Partner freigeben, wäre bequemer, braucht für fremde Werbekonten aber Advanced
Access per App-Review samt Unternehmensverifizierung. Den Zugriff behält man nur
mit mindestens 500 Marketing-API-Aufrufen in 15 Tagen. Für wenige Kunden lohnt
sich das nicht.

## Konfiguration

`~/.claude/meta-ads.json` (außerhalb des Repos), Vorlage `meta-ads.json.example`:

```json
{
  "default_profile": "<kunde>",
  "profiles": {
    "<kunde>": {
      "token_env": "META_TOKEN_<KUNDE>",
      "business_id": "<portfolio-id>",
      "dataset_id": "<dataset-id>",
      "ad_account_id": "<werbekonto-id>"
    }
  }
}
```

Der Token steht unter dem Namen aus `token_env` in der Umgebung oder in `~/.env`.
Das Script gibt ihn nie aus, auch nicht in Fehlermeldungen. Felder, die ein
Kunde noch nicht hat (etwa `ad_account_id`), bleiben leer. Der Befehl, der sie
braucht, bricht dann mit einer Meldung ab.

Ohne `--profile` gilt `default_profile`, bei nur einem Profil dieses.

## Subcommands

```bash
python3 "$SKILL_DIR/meta-ads" version
python3 "$SKILL_DIR/meta-ads" profiles                 # Profile ohne Token
python3 "$SKILL_DIR/meta-ads" check                    # Identität, Berechtigungen, Portfolio
python3 "$SKILL_DIR/meta-ads" datasets                 # Datasets des Portfolios
python3 "$SKILL_DIR/meta-ads" dataset-info             # Details, last_fired_time
python3 "$SKILL_DIR/meta-ads" dataset-stats            # empfangene Events je Event-Typ
python3 "$SKILL_DIR/meta-ads" dataset-stats --aggregation url
python3 "$SKILL_DIR/meta-ads" adaccounts               # eigene und Kunden-Werbekonten
python3 "$SKILL_DIR/meta-ads" insights --preset last_30d
python3 "$SKILL_DIR/meta-ads" insights --since 2026-01-01 --until 2026-01-31 --level ad
```

**Schreibend, nur nach Freigabe des Users mit `--yes`:**

```bash
python3 "$SKILL_DIR/meta-ads" create-dataset --name example.org --yes
python3 "$SKILL_DIR/meta-ads" test-event --event Purchase --value 49 \
  --url https://example.org/kasse/ --test-code TEST12345 --yes
```

Ohne `--yes` bricht der Aufruf ab. `create-dataset` meldet ein gleichnamiges
Dataset als `exists` statt ein zweites anzulegen, das prüft es schon vor `--yes`.
`test-event` braucht den Testcode aus dem Events Manager (Dataset → Test-Events).
Damit erscheint das Event dort live und fließt nicht in die Statistik.

## Einrichtung in der Oberfläche (einmal pro Kunde)

Diese Schritte gehen nicht über die API. Die Rechtevergaben blockiert der
Auto-Modus von Claude Code als „Permission Grant". Für diese Schritte den
Auto-Modus abschalten (`Shift+Tab`) und jeden Klick einzeln freigeben.

1. **Zugang zum Portfolio:** Der Kunde lädt den eigenen Facebook-User als Admin
   ins Unternehmensportfolio ein (business.facebook.com → Einstellungen → Personen).
2. **App anlegen:** developers.facebook.com → App erstellen. Anwendungsfall
   „Werbeanzeigen mit Marketing API erstellen und verwalten", das Portfolio
   des Kunden verknüpfen. `ads_management`, `ads_read` und `business_management`
   sind damit schon gesetzt. Die App bleibt unveröffentlicht im Entwicklungsmodus,
   das reicht. Mit „App erstellen" stimmt man den Plattform-Nutzungsbedingungen zu.
3. **Systemnutzer:** Einstellungen → Systemnutzer → Hinzufügen, Rolle Admin. Beim
   ersten Systemnutzer verlangt Meta die Zustimmung zur Richtlinie gegen
   Diskriminierung. Dann Assets zuweisen → Apps → die App mit „App verwalten".
4. **Token:** Beim Systemnutzer „Token generieren", die App wählen, Ablauf
   festlegen, `ads_management`, `ads_read`, `business_management` anhaken. Meta
   zeigt den Token **nur einmal** an. Der User kopiert ihn selbst nach `~/.env`,
   Claude liest ihn nicht vom Bildschirm ab.
5. **Profil** in `~/.claude/meta-ads.json` eintragen, dann `check`.
6. **Dataset:** Das erste Dataset eines Portfolios muss in der Oberfläche
   angelegt werden (Einstellungen → Datensätze und Pixel → Hinzufügen). Erst
   damit stimmt das Portfolio den Nutzungsbedingungen für Meta-Business-Tools
   zu. Vorher scheitert `create-dataset` mit „Business has not accepted Pixel
   Terms of Service". Weitere Datasets gehen dann per API.
7. **Domain verifizieren:** Einstellungen → Domains → Hinzufügen → Domain
   erstellen. Meta zeigt den Wert für einen DNS-TXT-Record
   (`facebook-domain-verification=…`) oder ein Meta-Tag. Wo die Zone liegt
   und wie sie geändert wird, steht im Infra-Wiki (`/wiki query`). Nach dem
   Eintrag auf allen Nameservern „Domain verifizieren". Über die Graph-API gibt
   es dafür kein Edge, `owned_domains` liefert „nonexisting field".

## Fallstricke

- **API-Version:** Das Script setzt `v26.0` fest. Meldet Meta „deprecated version
  of the Ads API … upgrade to the latest version: vNN.0", die Konstante
  `GRAPH_VERSION` im Script hochziehen.
- **`/me` liefert eine andere ID** als der Business-Manager beim Systemnutzer
  anzeigt. Das ist die ID des Systemnutzers innerhalb der App, kein Fehler.
- **Haken „alle Datasets mit der Conversions API verknüpfen"** im Dialog „Neuen
  Datensatz erstellen" ist vorausgewählt und gilt für das ganze Portfolio. Läuft
  die Conversions API über ein Plugin (z.B. PixelYourSite), den Haken entfernen.
  Sonst sendet Meta zusätzlich selbst serverseitige Events.
- **Werbekonto außerhalb des Portfolios:** Laufen die Kampagnen über ein Konto der
  Agentur, liefert `adaccounts` nichts. Dann muss die Agentur das Werbekonto mit
  dem Portfolio teilen, oder das Dataset wird mit ihrem Konto geteilt.

## Offizieller Meta-MCP

Meta betreibt unter `https://mcp.facebook.com/ads` einen Ads-MCP-Server
(Reporting, Kampagnen anlegen und bearbeiten, Kataloge, Signalqualität). Er
meldet sich mit dem eigenen Meta-Login an, nicht mit dem Systemnutzer-Token.
Für die laufende Kampagnenauswertung ist er eine Alternative zu `insights`.
Dataset, Conversions API und Domain deckt er laut Doku nicht ab.
