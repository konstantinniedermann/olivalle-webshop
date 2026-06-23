# Produktbezogene Aktionspreise — Design

> GitHub Issue: #134 (feat, phase-4)
> Datum: 2026-06-23

## Ziel

Der Stakeholder (SH) soll **einzelne Produkte temporär rabattiert** anbieten können —
z. B. Flaschen mit nahender Mindesthaltbarkeit. Der Aktionspreis ist direkt auf der
Produktkarte sichtbar (durchgestrichener Originalpreis, Aktionspreis, RABATT-Badge,
Prozent-Ersparnis, Begründungstext), **ohne dass der Kunde einen Code eingeben muss**.

Abgrenzung: Dies ist eine **andere Mechanik** als die bestehenden Rabattcodes
(`rabattcode_service.py`, Coupon auf Warenkorb-Ebene). Aktionspreise wirken auf den
**Einzelpreis** eines Produkts.

## Entscheidungen (aus Brainstorming)

| Frage | Entscheid |
|---|---|
| Pflege | **Admin-UI (Self-Service)** — SH setzt Aktion selbst, analog `rabattcode_form` |
| Datenmodell | **Spalten an `produkte`** (eine Aktion pro Produkt), kein separates Table |
| Gültigkeit | **von/bis optional, auto-ablaufend** — leer = unbegrenzt; nach `aktion_bis` automatisch Normalpreis |
| Rabattcode-Stacking | **Code gilt nur für Nicht-Aktions-Anteil** des Warenkorbs |
| Prozent-Badge | **berechnet** (`round((1 − aktion/original)·100)`), keine extra Spalte |
| Mails/Rechnung | Zeigen den korrekten reduzierten Betrag, **ohne** extra „du hast X gespart"-Zeile |

## Architektur-Kernprinzip

`berechne_total()` ist die **einzige autoritative Preisquelle** für Bestellung, Stripe,
DB-Positionen, Bestätigungs-/Rechnungs-Mails und QR-Rechnung. Fliesst der Aktionspreis dort
als `einzelpreis_chf` ein, zieht er sich automatisch korrekt durch die gesamte Bestellkette.
Der Warenkorb im Browser (localStorage) dient nur der Anzeige; der Server rechnet alles neu.

## 1. Datenmodell — Migration `004_aktionspreise.sql`

Vier NULL-bare Spalten an `produkte`:

| Spalte | Typ | Bedeutung |
|---|---|---|
| `aktionspreis_chf` | REAL NULL | reduzierter Preis; NULL = keine Aktion |
| `aktionstext` | TEXT NULL | Begründung („Mindesthaltbarkeit 09/2026 …") |
| `aktion_von` | TEXT NULL | ISO-Datum (`YYYY-MM-DD`), leer = sofort gültig |
| `aktion_bis` | TEXT NULL | ISO-Datum, leer = unbegrenzt gültig |

**Aktion aktiv** ⇔ `aktionspreis_chf IS NOT NULL`
**und** (`aktion_von` leer **oder** heute ≥ `aktion_von`)
**und** (`aktion_bis` leer **oder** heute ≤ `aktion_bis`).

Nach `aktion_bis` greift automatisch wieder `preis_chf` — keine manuelle Deaktivierung nötig.

## 2. Effektiv-Preis als zentrale Logik

Neue Funktion in einem `app/services/aktions_service.py`:

```
effektiver_preis(produkt_row, heute) -> EffektivPreis
# liefert: preis, ist_aktion (bool), original_preis, prozent (int, gerundet)
```

Dies ist die **einzige** Stelle, die entscheidet, welcher Preis gilt. Alle Konsumenten rufen sie auf:

- **`berechne_total()`**: SELECT um die vier Aktions-Spalten erweitern; `einzelpreis_chf` =
  Effektiv-Preis. Jede zurückgegebene Position trägt zusätzlich `ist_aktion: bool`.
  → Stripe, DB-Positionen, Mails und QR-Rechnung rechnen automatisch mit dem Aktionspreis.
- **`get_alle_produkte()` / `Produkt`-Model**: Aktions-Felder mitliefern (optional, NULL-bar),
  damit die Produktkarte den Original- und Aktionspreis, Prozent und Text anzeigen kann.

Prozent-Ersparnis wird berechnet, nicht gespeichert.

## 3. Rabattcode-Zusammenspiel (nur Nicht-Aktions-Anteil)

`berechne_total()` markiert jede Position mit `ist_aktion`. Daraus ergibt sich der
**rabattfähige Subtotal** = Summe der Nicht-Aktions-Positionen.

- **Server (autoritativ, `bestellungen.py`)**: `pruefe_rabattcode(..., rabattfähiger_subtotal)`
  statt `total`. Stripe-Coupon `amount_off` bezieht sich damit nur auf Nicht-Aktionsware.
  Der Mindestbestellwert-Check im Rabattcode bezieht sich ebenfalls auf den rabattfähigen Subtotal.
- **Live-Vorschau (`checkout.html` + `/api/rabattcode/pruefen`)**: Warenkorb-Items bekommen ein
  `aktion`-Flag (gesetzt beim `addToCart` aus einem Data-Attribut). Der Client sendet den
  Nicht-Aktions-Subtotal an die Vorschau-API. Konsistent mit der bestehenden Vorschau-Architektur
  (Client liefert Subtotal, der Server bleibt bei Bestellabschluss die finale Autorität).
- **Reiner Aktions-Warenkorb** → rabattfähiger Subtotal = 0 → Code greift nicht, klare Meldung
  (z. B. „Auf Aktionsprodukte ist kein zusätzlicher Rabattcode möglich.").

## 4. Admin-UI (Self-Service)

Analog zum bestehenden Rabattcode-Bereich (`templates/admin/rabattcode_form.html`,
`app/routers/rabattcodes.py`):

- Liste „Produkte" im Admin-Bereich mit aktuellem (Aktions-)Status.
- Bearbeiten-Formular pro Produkt: Aktionspreis, Aktionstext, von/bis setzen oder entfernen.
- **Validierung**: Aktionspreis muss kleiner als `preis_chf` sein; sonst Fehlermeldung.
- Audit-Log-Eintrag (`log_eintrag_schreiben`) wie bei Rabattcodes.
- CSRF-Schutz analog bestehender Admin-Formulare.

## 5. Frontend-Anzeige (Produktkarte, `templates/produkte.html`)

Bei aktiver Aktion:
- **RABATT**-Badge
- durchgestrichener Originalpreis (`CHF 18.00`)
- grosser Aktionspreis (`CHF 12.00`)
- Prozent-Badge (`−33%`)
- Begründungstext (`aktionstext`)
- `data-product-price` trägt den **Aktionspreis** → Warenkorb, Flyout und Checkout-Vorschau
  zeigen automatisch den reduzierten Preis.

Ohne aktive Aktion: Darstellung unverändert (kein Badge, `preis_chf` wie bisher).
Tailwind-Klassen gemäss bestehender Card-UI-Konvention (siehe lokale `CLAUDE.md`).

## 6. Tests & Dokumentation

**Tests (pytest):**
- `effektiver_preis`: Grenzfälle — kein Aktionspreis, von/bis leer, vor `aktion_von`,
  nach `aktion_bis`, innerhalb Zeitraum, nur `von` gesetzt, nur `bis` gesetzt.
- `berechne_total`: mit/ohne Aktion; `einzelpreis_chf` und `ist_aktion` korrekt.
- Rabattcode-Ausschluss: gemischter Warenkorb (Code nur auf Nicht-Aktionsanteil),
  reiner Aktions-Warenkorb (Code greift nicht).

**Doku:**
- `docs/arc42.md` — Aktionspreis-Mechanik und Abgrenzung zu Rabattcodes.
- `docs/user-stories-testplan.md` — User Story + Testfälle ergänzen.

## Betroffene Dateien (Übersicht)

| Bereich | Datei(en) |
|---|---|
| Migration | `migrations/004_aktionspreise.sql` (neu) |
| Effektiv-Preis | `app/services/aktions_service.py` (neu) |
| Model | `app/models.py` (`Produkt` um Aktions-Felder) |
| Repo | `app/repositories/produkt_repo.py` |
| Bestelllogik | `app/services/bestell_service.py` (`berechne_total`) |
| Bestell-Route | `app/routers/bestellungen.py` (rabattfähiger Subtotal) |
| Rabattcode-Vorschau | `app/routers/rabattcodes.py`, `templates/checkout.html` |
| Warenkorb-JS | `static/js/cart.js` (`aktion`-Flag) |
| Admin-UI | `app/routers/` + `templates/admin/` (neu/erweitert) |
| Produktkarte | `templates/produkte.html` |
| Tests | `tests/` |
| Doku | `docs/arc42.md`, `docs/user-stories-testplan.md` |

## YAGNI / bewusst weggelassen

- Kein Aktions-Verlauf / mehrere geplante Aktionen pro Produkt (separate Tabelle) — eine
  aktive Aktion pro Produkt genügt für den Anlass.
- Keine manuelle Prozent-Eingabe — wird berechnet.
- Keine „du hast X gespart"-Zeile in Mails — der reduzierte Betrag genügt.
