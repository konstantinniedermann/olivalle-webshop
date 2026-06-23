# Design-Spec: Produkt „Olivenöl 500ml" (Geschenkflasche)

**Issue:** #135 · **Datum:** 2026-06-23 · **Phase:** 4 (Erweiterung im Betrieb)

## Kontext

Der Stakeholder (SH) hat ein neues Gebinde ins Sortiment aufgenommen: eine 500-ml-Geschenkflasche
der Design-Kollektion „3 Ríos" zu CHF 25.00. Diese soll im Webshop ergänzt werden.

Der Shop ist vollständig datengetrieben: Warenkorb (`cart.js`), Stripe-Checkout, QR-Rechnung,
Bestätigungs-Mails und Admin lesen alle aus der Tabelle `produkte`. Ein neues Produkt erscheint
damit automatisch überall, sobald es in der DB ist. Die Produktliste ist nach `menge_ml` sortiert
(`produkt_repo.py: ORDER BY menge_ml`), das 500-ml-Gebinde erscheint also zwischen 250 ml und 750 ml.

**Preis-Auffälligkeit (gewollt):** CHF 25 für 500 ml ist teurer als CHF 18 für 750 ml. Es handelt
sich um eine Premium-/Geschenk-Design-Edition. Der Produkttext kennzeichnet dies klar
(„Geschenkflasche", „exklusive Design Kollektion"), ein zusätzliches Badge ist nicht nötig (YAGNI).

## Entscheidungen

### 1. Seed: `001_initial.sql` erweitern (keine neue Migration)

Eine vierte Zeile wird in den bestehenden `INSERT … ON CONFLICT(id) DO UPDATE`-Block in
`migrations/001_initial.sql` eingefügt. Begründung:

- Der gesamte Produktkatalog bleibt an **einer** Stelle (DRY, leicht auffindbar).
- Das Seed läuft idempotent bei jedem Container-Start (`init_db()`) — `001` ist faktisch bereits
  die Live-Seed-Quelle, nicht nur ein historischer Snapshot.
- Eine separate Migration würde den Katalog ohne Mehrwert auf zwei Dateien aufteilen.
- Die UPSERT-Regel bleibt unberührt: admin-editierbare Aktions-Spalten
  (`aktionspreis_chf`, `aktionstext`, `aktion_von`, `aktion_bis`) werden im `DO UPDATE` weiterhin
  **nicht** aufgeführt (Bug #137).

Neue Zeile:

```sql
(4, 'Olivenöl 500ml', 500, 25.00, '<Produkttext>', 'products/olivalle-500ml.jpeg')
```

### 2. Produkttext

Das Feld `name` = „Olivenöl 500ml" dient als Kartenüberschrift. Der vom SH gelieferte Text wird
verbatim in `beschreibung` übernommen; der Titel-Vorspann „Olivar de los 3 Ríos" fließt in den
Beschreibungstext ein, damit die Markenbezeichnung nicht verloren geht:

> Olivar de los 3 Ríos – die perfekte Geschenkflasche. Die exklusive Design Kollektion ist inspiriert
> von den Flusslandschaften des Guadalbarbo, Cuzna und Gato – wo Natur und Olivenkultur seit
> Generationen im Einklang leben.

### 3. Produktbild

Das gelieferte Original `static/images/products/Tres-Rios-Olivalle.jpg` ist **6.7 MB / 6336×8938 px**
(Hochformat) — zu gross für eine Webseite. Die bestehenden Produktbilder sind ~50 KB / 1080×1080.

- Verkleinern auf max. **1080 px** lange Kante (Seitenverhältnis bleibt erhalten), JPEG-Qualität ~80.
- Ablage als `static/images/products/olivalle-500ml.jpeg` (konsistentes Namensschema
  `olivalle-<menge>.jpeg`).
- Das 6.7-MB-Original wird **nicht** ins Repo aufgenommen (nur das optimierte Bild).
- Das Template (`templates/produkte.html`) nutzt `object-contain` → Hochformat wird sauber
  eingepasst, kein Crop nötig.

### 4. AGB robust machen (Drift beseitigen)

`templates/agb.html` enthält eine hartcodierte Sortiments-Preistabelle (Überschrift „Sortiment" +
Tabelle), die manuell gepflegt werden müsste und bereits veraltet war. Statt eine vierte Zeile
einzutragen, wird Tabelle **und** Überschrift durch einen kurzen Verweis auf den Shop ersetzt:

> Die aktuellen Produkte und Preise finden Sie in unserem Shop.

Rechtlich unbedenklich: Preise werden am Point of Sale (Shop) verbindlich angezeigt; die AGB müssen
keine Preisliste enthalten. Damit ist die Seite gegen künftige Sortimentsänderungen robust.

## Betroffene Dateien

| Datei | Änderung |
|---|---|
| `migrations/001_initial.sql` | Vierte Produktzeile im Seed |
| `static/images/products/olivalle-500ml.jpeg` | Neues, optimiertes Bild (aus `Tres-Rios-Olivalle.jpg`) |
| `static/images/products/Tres-Rios-Olivalle.jpg` | Original entfernen (nicht committen) |
| `templates/agb.html` | Sortimentstabelle → Shop-Verweis |
| `tests/test_produkt_repo.py` | Produktanzahl 3→4 / 2→3; neuer Test für 500-ml-Produkt |
| `CLAUDE.md` | Preistabelle um 500-ml-Zeile ergänzen |
| `docs/superpowers/specs/2026-03-24-produkttexte-design.md` | 500-ml-Produkttext ergänzen |
| `docs/user-stories-testplan.md` | Gegencheck, ggf. ergänzen |

## Akzeptanzkriterien (aus Issue #135)

- [ ] Produkt „Olivenöl 500ml" (500 ml, CHF 25) in DB/Seed angelegt
- [ ] Produktbild als statisches Asset hinterlegt, optimiert und korrekt verlinkt
- [ ] Produkttext wie vom SH vorgegeben angezeigt
- [ ] Produkt im Shop bestell- und bezahlbar (Warenkorb, Stripe, Mails, QR-Rechnung) — automatisch
      über die datengetriebene Anzeige
- [ ] AGB gegen Sortiments-Drift robust gemacht
- [ ] Doku/Produkttexte aktualisiert
- [ ] CLAUDE.md Produkttabelle ergänzt

## Tests

- `test_produkt_repo.py`: bestehende Annahmen über die Produktanzahl anpassen
  (`get_alle_produkte` 3→4, `nur_aktive` 2→3, `alle_produkte_admin` 3→4).
- Neuer Test: 500-ml-Produkt existiert mit `menge_ml == 500` und `preis_chf == 25.0`, korrekt
  einsortiert zwischen 250 ml und 750 ml.
- Bestehende e2e-/API-Tests bleiben grün (datengetrieben, keine harte „3 Produkte"-Annahme dort).

## Nicht im Scope (YAGNI)

- Kein Premium-/Geschenk-Badge auf der Produktkarte (Text genügt).
- Keine Admin-UI zum Anlegen neuer Produkte (separates Thema, nicht Teil von #135).
- AGB nicht datengetrieben machen (Verweis genügt, vermeidet Kopplung der statischen Seite an die DB).
