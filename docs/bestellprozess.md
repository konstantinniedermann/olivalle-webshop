[← Übersicht](index.md)

# Olivalle — Bestellprozess

```mermaid
sequenceDiagram
    actor Kunde
    participant Shop as Olivalle Shop (FastAPI + Jinja2)
    participant Stripe
    participant DB as SQLite

    Kunde->>Shop: Produkt in Warenkorb legen
    Kunde->>Shop: Checkout starten
    Shop->>Kunde: Formular (Adresse, Versand)
    Kunde->>Shop: Formular absenden
    Shop->>DB: Bestellung speichern (Status: neu)
    Shop->>Stripe: Checkout Session erstellen
    Stripe-->>Kunde: Redirect zu Stripe Checkout
    Kunde->>Stripe: Zahlung durchführen (Twint / Karte)
    Stripe->>Shop: Webhook: checkout.session.completed
    Shop->>DB: Status auf bezahlt setzen
    Shop->>Kunde: Bestellbestätigung per E-Mail
```
