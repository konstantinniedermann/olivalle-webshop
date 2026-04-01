[← Übersicht](index.md)

# Olivalle — Systemarchitektur

```mermaid
graph TD
    subgraph flyio["fly.io (1 Docker-Container)"]
        API["FastAPI"]
        Templates["Jinja2-Templates + Tailwind CSS"]
        DB["SQLite"]
        QR["swiss-qr-bill"]
    end

    Browser["Browser"] -->|HTTP| API
    API --> Templates
    API --> DB
    API -->|Checkout Session| Stripe
    Stripe -->|Webhook| API
    API -->|Bestellbestätigung| Brevo["Brevo (E-Mail)"]
    API -->|PDF generieren| QR

    Brevo -->|bestellung@olivalle.ch| Kunde["Kunde (E-Mail)"]
```
