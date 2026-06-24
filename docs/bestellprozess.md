[← Übersicht](index.md)

# Olivalle — Bestellprozess

**Zweck:** Dieses Sequenzdiagramm zeigt den Ablauf einer Bestellung vom Warenkorb bis zur Bestätigung — mit beiden Zahlwegen (Stripe und QR-Rechnung), Rabattcode-Anwendung und dem Verhalten bei fehlgeschlagener Zahlung.

```mermaid
sequenceDiagram
    actor Kunde
    participant Shop as Olivalle Shop (FastAPI + Jinja2)
    participant Stripe
    participant DB as SQLite
    participant Brevo

    Kunde->>Shop: Produkte in Warenkorb legen
    Kunde->>Shop: Checkout starten
    Shop->>Kunde: Formular (Adresse, Versand, Zahlungsart)
    opt Rabattcode eingegeben
        Kunde->>Shop: Code absenden
        Shop->>DB: Code prüfen (gültig, Limit, Mindestwert)
        Shop->>Kunde: Rabatt angewandt oder Fehlermeldung
    end
    Kunde->>Shop: Formular absenden
    Shop->>DB: Bestellung speichern (Status: neu)

    alt Zahlungsart Stripe (Twint / Karte)
        Shop->>Stripe: Checkout Session erstellen
        Stripe-->>Kunde: Redirect zu Stripe Checkout
        Kunde->>Stripe: Zahlung durchführen
        alt Zahlung erfolgreich
            Stripe->>Shop: Webhook checkout.session.completed
            Shop->>DB: Status auf bezahlt setzen
            Shop->>Brevo: Bestätigungs-E-Mail auslösen
            Brevo-->>Kunde: Bestellbestätigung
        else Zahlung fehlgeschlagen / abgebrochen
            Stripe-->>Kunde: Fehlerhinweis, Bestellung bleibt "neu"
        end
    else Zahlungsart QR-Rechnung
        Shop->>Shop: QR-Rechnungs-PDF erzeugen (swiss-qr-bill)
        Shop->>Brevo: E-Mail mit QR-Rechnung im Anhang
        Brevo-->>Kunde: Bestellbestätigung + QR-Rechnung
    end
```

**Die Schritte im Einzelnen:**

- **Warenkorb & Checkout** — der Kunde wählt Produkte, gibt Adresse, Versand- und Zahlungsart an.
- **Rabattcode (optional)** — wird gegen Gültigkeit, Einlöse-Limit und Mindestbestellwert geprüft, bevor er den Total reduziert.
- **Stripe-Pfad** — bei Erfolg meldet ein Webhook die Zahlung; erst dann wird die Bestellung auf „bezahlt" gesetzt und die Bestätigung versendet. Bei Abbruch bleibt sie „neu" (Stripe wiederholt Webhooks bei Zustellfehlern automatisch).
- **QR-Rechnungs-Pfad** — für Rechnungskäufer erzeugt der Shop ein Schweizer QR-Rechnungs-PDF und versendet es als E-Mail-Anhang.

---

## Betreibersicht — eingehende Bestellung verarbeiten

**Zweck:** Spiegelbild zum Kunden-Sequenzdiagramm — der Ablauf aus Sicht des Betreibers (Stakeholder/Admin), der eine eingegangene Bestellung im Admin-Bereich bearbeitet und damit eine Status-E-Mail an den Kunden auslöst.

```mermaid
sequenceDiagram
    actor SH as Betreiber (Admin)
    participant Shop as Olivalle Shop (FastAPI + Jinja2)
    participant DB as SQLite
    participant Brevo
    actor Kunde

    SH->>Shop: POST /admin/login (Passwort)
    Shop->>SH: signiertes Session-Cookie
    SH->>Shop: GET /admin/ (Dashboard)
    Shop->>DB: offene Bestellungen + KPIs laden
    Shop->>SH: KPI-Kacheln + Bestellliste
    SH->>Shop: GET /admin/bestellungen/{id}
    Shop->>DB: Bestelldetail + Verlauf laden
    Shop->>SH: Kundendaten, Positionen, Status
    SH->>Shop: POST /admin/bestellungen/{id}/status
    Shop->>DB: Status aktualisieren + admin_log schreiben
    alt Status loest Mail aus (bezahlt / versendet / abholbereit)
        Shop->>Brevo: Status-E-Mail anstossen
        Brevo-->>Kunde: Status-Benachrichtigung
    end
    Shop->>SH: aktualisierte Bestelldetail-Seite
```

**Die Schritte im Einzelnen:**

- **Login** — der Betreiber meldet sich mit einem Passwort an (`POST /admin/login`); bei Erfolg gibt der Shop ein signiertes Session-Cookie aus.
- **Dashboard** — `GET /admin/` zeigt KPI-Kacheln (offene Bestellungen, Monatsumsatz, Bestellungen heute) und die filterbare Bestellliste.
- **Bestelldetail** — `GET /admin/bestellungen/{id}` öffnet Kundendaten, Positionen und den bisherigen Verlauf.
- **Statuswechsel** — `POST /admin/bestellungen/{id}/status` ändert den Status, schreibt einen Eintrag ins `admin_log` und löst — sofern der Zielstatus eine Mail vorsieht (`bezahlt`, `versendet`, `abholbereit`) — automatisch die passende Kunden-E-Mail über Brevo aus.
