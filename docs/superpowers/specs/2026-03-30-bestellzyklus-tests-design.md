# Bestellzyklus-Tests — Design-Spec

> Datum: 2026-03-30
> Scope: Automatisierte Tests (pytest) + manuelles Testprotokoll für den kompletten Bestellablauf

## Ziel

Den gesamten Bestellzyklus testbar machen — von der Bestellung über Zahlung, Admin-Freigabe bis zum Abschluss. Bestehende Testlücken schliessen und ein manuelles Testprotokoll für Browser-Tests vor dem Go-Live erstellen.

## Abgrenzung

- **In Scope:** E2E-Tests, Admin-API-Tests, Webhook-Fehlerszenarien, manuelles Testprotokoll
- **Out of Scope:** Versand-E-Mail (eigenes Issue), Stripe-Refund-Logik, E2E-Browser-Tests (Playwright)

## Teil A: Automatisierte Tests (pytest)

### A1. E2E-Bestellzyklus (`tests/test_e2e_bestellzyklus.py`)

Neue Datei mit 3 Tests, die den kompletten Zyklus durchlaufen. Echte DB (in-memory SQLite), externe Services gemockt (Stripe API, Resend).

**Test 1: Stripe-Flow**
1. `POST /bestellen` mit `zahlungsart=stripe` → Bestellung mit Status `neu` erstellt
2. Stripe-Webhook simulieren (`checkout.session.completed`) → Status wird `bezahlt`, Bestätigungs-E-Mail gesendet
3. Admin-Login → Bestellung in Dashboard sichtbar
4. Admin setzt Status auf `versendet`
5. Assertions: Korrekter Status-Verlauf im Admin-Log (`neu → bezahlt → versendet`), E-Mail genau 1x gesendet

**Test 2: Rechnungs-Flow**
1. `POST /bestellen` mit `zahlungsart=rechnung` → Status `neu`, Bestätigungs-E-Mail + QR-Rechnung gesendet
2. Admin-Login → Bestellung sichtbar mit Status `neu`
3. Admin setzt Status auf `bezahlt` (manueller Zahlungseingang)
4. Admin setzt Status auf `abholbereit` (Versandart: Abholung)
5. Assertions: Kompletter Log-Verlauf (`neu → bezahlt → abholbereit`), E-Mail mit QR-Anhang gesendet

**Test 3: Storno nach Zahlung**
1. `POST /bestellen` mit `zahlungsart=stripe` → Status `neu`
2. Stripe-Webhook → Status `bezahlt`
3. Admin setzt Status auf `storniert`
4. Assertions: Status korrekt, Log-Verlauf `neu → bezahlt → storniert`

### A2. Admin-API-Tests (erweitert `tests/test_api_admin.py`)

**Statusänderung (`POST /admin/bestellungen/{id}/status`):**
- Status erfolgreich ändern (`neu → bezahlt`) → Redirect, Status in DB aktualisiert
- Bestellung nicht gefunden → 404
- Log-Eintrag korrekt geschrieben (Aktion `status_geaendert`, Details mit `von`/`nach`)

**Notizen (`POST /admin/bestellungen/{id}/notiz`):**
- Notiz erfolgreich hinzufügen → Redirect, Notiz im Log sichtbar
- Bestellung nicht gefunden → 404
- Log-Eintrag mit Aktion `notiz_hinzugefuegt` und Notiz-Text

### A3. Webhook-Fehlerszenarien (erweitert `tests/test_api_webhooks.py`)

- **Ungültige Stripe-Signatur** → 400 Response
- **Bestellung nicht gefunden** (session_id passt zu keiner Bestellung) → kein Crash, Fehler geloggt
- **Doppelter Webhook** (gleiche session_id nochmal) → Status bleibt `bezahlt`, keine doppelte E-Mail

## Teil B: Manuelles Testprotokoll (`docs/testprotokoll.md`)

Checkliste für Browser-Tests mit Stripe Test-Keys. Jeder Schritt mit erwartetem Ergebnis und Checkbox.

### B1. Stripe-Flow
- [ ] Produkt in Warenkorb legen
- [ ] Checkout-Seite aufrufen, Kundendaten eingeben
- [ ] Zahlungsart "Stripe" wählen, Bestellung absenden
- [ ] Stripe-Testseite: mit Testkarte `4242 4242 4242 4242` bezahlen
- [ ] Bestätigungsseite wird angezeigt mit Bestellnummer
- [ ] Bestätigungs-E-Mail erhalten (Resend Dashboard prüfen)
- [ ] Admin-Dashboard: Bestellung mit Status `bezahlt` sichtbar
- [ ] Admin: Status auf `versendet` ändern
- [ ] Admin: Log-Verlauf zeigt alle Statusänderungen

### B2. Rechnungs-Flow
- [ ] Produkt in Warenkorb legen
- [ ] Checkout-Seite aufrufen, Kundendaten eingeben
- [ ] Zahlungsart "Rechnung" wählen, Bestellung absenden
- [ ] Bestätigungsseite wird angezeigt
- [ ] Bestätigungs-E-Mail mit QR-Rechnung im Anhang erhalten
- [ ] Admin-Dashboard: Bestellung mit Status `neu` sichtbar
- [ ] Admin: Status auf `bezahlt` ändern (manueller Zahlungseingang)
- [ ] Admin: Status auf `abholbereit` oder `versendet` ändern

### B3. Admin-Aktionen
- [ ] Admin-Login mit korrektem Passwort → Dashboard
- [ ] Bestellungen filtern nach Status
- [ ] Bestellungen suchen nach Kundenname
- [ ] Bestelldetail öffnen → Positionen, Kundendaten, Log sichtbar
- [ ] Notiz hinzufügen → erscheint im Log
- [ ] Logout → Login-Seite

### B4. Fehlerfälle
- [ ] Leeren Warenkorb bestellen → Fehlermeldung
- [ ] Admin-Login mit falschem Passwort → Fehlermeldung
- [ ] Nicht existierende Bestellungs-URL → 404
- [ ] Checkout ohne Pflichtfelder → Validierungsfehler

## Technische Details

### Test-Fixtures
- Bestehende `db` und `client` Fixtures aus `conftest.py` wiederverwenden
- Für E2E-Tests: Helper-Funktion `erstelle_testbestellung()` die eine komplette Bestellung mit Kunde und Positionen anlegt
- Admin-Session: bestehende `csrf_token`-Fixture + Admin-Login im Test-Setup

### Mocking-Strategie
| Service | Mock | Grund |
|---------|------|-------|
| Stripe API (`stripe.checkout.Session.create`) | `monkeypatch` | Kein echter Stripe-Call |
| Stripe Webhook (`stripe.Webhook.construct_event`) | `monkeypatch` | Event-Objekt simulieren |
| Resend (`resend.Emails.send`) | `monkeypatch` | Kein echter E-Mail-Versand |
| QR-Rechnung (`generiere_qr_rechnung`) | `monkeypatch` | Kein PDF generieren |

### Dateien die geändert/erstellt werden
| Datei | Aktion |
|-------|--------|
| `tests/test_e2e_bestellzyklus.py` | **Neu** — 3 E2E-Tests |
| `tests/test_api_admin.py` | **Erweitert** — Statusänderung + Notiz-Tests |
| `tests/test_api_webhooks.py` | **Erweitert** — Fehlerszenarien |
| `docs/testprotokoll.md` | **Neu** — Manuelles Testprotokoll |
