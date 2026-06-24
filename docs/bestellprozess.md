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
