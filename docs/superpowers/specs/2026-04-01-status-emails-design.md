# Design: Automatisierte Status-E-Mails (Issue #24)

## Kontext

Der Rechnungs-Flow ist bereits implementiert: Kunde bestellt per QR-Rechnung, erhält Bestätigungsmail mit QR-Anhang. Admin kann Status im Admin-Interface ändern. Was fehlt: automatische E-Mail-Benachrichtigung an den Kunden bei bestimmten Statusänderungen.

## Anforderungen

### E-Mails bei folgenden Statusänderungen

| Status | Bedingung | E-Mail |
|---|---|---|
| `bezahlt` | nur wenn `zahlungsart == "rechnung"` | Zahlungseingangsbestätigung |
| `versendet` | nur wenn `versandart == "versand"` | Versandbestätigung |
| `abholbereit` | nur wenn `versandart == "abholung"` | Abholbenachrichtigung |

Alle anderen Statusänderungen (`neu`, `in_bearbeitung`, `abgeschlossen`, `storniert`) lösen keine E-Mail aus.

### Begründung der Einschränkungen

- **bezahlt + Stripe:** Stripe schickt bereits eigene Zahlungsbestätigungen, eine zweite wäre redundant.
- **versendet + Abholung / abholbereit + Versand:** Logisch inkonsistent, wird durch die Dispatch-Logik verhindert.

### E-Mail-Inhalt

Kurz und knapp — keine Bestellübersicht (hat der Kunde bereits in der Bestätigungsmail):
- Begrüssung mit Vorname
- Statusmeldung mit Bestellnummer
- Ggf. relevanter Hinweis (Abholadresse bei "abholbereit")
- "Liebe Grüsse, Olivalle"

## Architektur

### Ansatz: Zentrale Dispatch-Funktion im Email-Service

Die gesamte Logik (ob und welche E-Mail gesendet wird) ist in einer einzigen Funktion im `email_service.py` gekapselt. Der Admin-Router ruft nach der Statusänderung nur diese Funktion auf.

### Neue Funktion

**`app/services/email_service.py`:**

```python
def sende_status_email(
    bestellung_id: int,
    neuer_status: str,
    conn: sqlite3.Connection,
) -> None
```

**Ablauf:**
1. Bestelldetails laden via `get_bestellung_detail(conn, bestellung_id)`
2. Prüfen ob für Status + Zahlungsart/Versandart eine E-Mail nötig ist
3. Template und Betreff via Dict-Mapping wählen
4. Template rendern (Jinja2) mit Kunde-Vorname und Bestellnummer
5. Via Brevo senden (gleicher Pattern wie `sende_bestellbestaetigung`)
6. In `admin_log` loggen mit `aktion="email_ausgang"`

**Fehlerbehandlung:** Bei Versandfehler wird geloggt, die Statusänderung bleibt bestehen. Der Admin sieht den Fehler im Log.

### Neue E-Mail-Templates

Alle in `templates/emails/`, gleiches Pattern wie `bestellbestaetigung.html` (inline Styles, `#f1d600` Akzentfarbe):

| Template | Betreff |
|---|---|
| `zahlungseingang.html` | Zahlungseingang bestätigt — Bestellung #{{bestell_id}} |
| `versandbestaetigung.html` | Deine Bestellung #{{bestell_id}} ist unterwegs |
| `abholbereit.html` | Deine Bestellung #{{bestell_id}} ist abholbereit |

### Integration im Admin-Router

**`app/routers/admin.py`** — nach `update_bestellung_status()` und `log_eintrag_schreiben()`:

```python
sende_status_email(bestellung_id, neuer_status, conn)
```

Ein einziger Aufruf. Keine weitere Logik im Router.

## Betroffene Dateien

| Datei | Änderung |
|---|---|
| `app/services/email_service.py` | Neue Funktion `sende_status_email` |
| `app/routers/admin.py` | Aufruf von `sende_status_email` nach Statusänderung |
| `templates/emails/zahlungseingang.html` | Neues Template |
| `templates/emails/versandbestaetigung.html` | Neues Template |
| `templates/emails/abholbereit.html` | Neues Template |
| `tests/test_email_service.py` | Unit-Tests für `sende_status_email` |
| `tests/test_e2e_bestellzyklus.py` | E2E-Test erweitern |

## Tests

### Unit-Tests (`tests/test_email_service.py`)

| Testfall | Erwartung |
|---|---|
| bezahlt + zahlungsart rechnung | E-Mail gesendet |
| bezahlt + zahlungsart stripe | Keine E-Mail |
| versendet + versandart versand | E-Mail gesendet |
| versendet + versandart abholung | Keine E-Mail |
| abholbereit + versandart abholung | E-Mail gesendet |
| abholbereit + versandart versand | Keine E-Mail |
| storniert | Keine E-Mail |

Brevo wird gemockt (`@patch("app.services.email_service.brevo_client")`).

### E2E-Test (`tests/test_e2e_bestellzyklus.py`)

Bestehenden Rechnungs-Flow erweitern: nach Admin-Statusänderung auf "bezahlt" prüfen ob `sende_status_email` aufgerufen wird.
