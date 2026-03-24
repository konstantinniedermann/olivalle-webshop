[← Übersicht](index.md)

# Olivalle — Roadmap

```mermaid
graph TD
    START(["Projektstart"]) --> P1

    subgraph P1["Phase 1 — Fundament"]
        direction TB
        p1a["FastAPI + Jinja2 aufsetzen (Tailwind CSS)"]
        p1b["SQLite verbinden (DB anlegen, Migrations)"]
        p1c["Datenbankschema erstellen (Produkte, Kunden, Bestellungen)"]
        p1d["Produkte in DB erfassen (250ml, 750ml, 3l mit Preisen)"]
        p1e["Produktseite rendern (Produkte aus DB laden & anzeigen)"]
        M1{{"Meilenstein: Shop ist sichtbar"}}

        p1a --> p1b --> p1c --> p1d --> p1e --> M1
    end

    subgraph P2["Phase 2 — Shop"]
        direction TB
        p2a["Warenkorb (Vanilla JS + localStorage)"]
        p2b["Checkout-Formular (Adresse, Versandart wählen)"]
        p2c["Bestellung in DB speichern (POST /bestellung via FastAPI)"]
        p2d["Stripe Checkout Integration (Kreditkarte + Twint)"]
        p2e["Stripe Webhook (Bestellstatus auf bezahlt setzen)"]
        p2f["Bestellbestätigung per E-Mail (Resend)"]
        M2{{"Meilenstein: Erste echte Bestellung möglich"}}

        p2a --> p2b --> p2c --> p2d --> p2e --> p2f --> M2
    end

    subgraph P3["Phase 3 — Automatisierung"]
        direction TB
        p3a["QR-Rechnung generieren (swiss-qr-bill, PDF-Download)"]
        p3b["Automatisierte Rechnungsstellung (nach Bestellung)"]
        p3c["Admin-Bereich (Bestellübersicht, Status verwalten)"]
        p3d["SSL erneuern & Domain konfigurieren (olivalle.ch, vor Launch)"]
        M3{{"Meilenstein: Produktivbetrieb"}}

        p3a --> p3b --> p3c --> p3d --> M3
    end

    M1 --> P2
    M2 --> P3
```
