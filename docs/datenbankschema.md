[← Übersicht](index.md)

# Olivalle — Datenbankschema

> Quelle: `migrations/001_initial.sql` (SQLite)

```mermaid
erDiagram
    PRODUKT {
        int id PK
        string name
        int menge_ml
        real preis_chf
        string beschreibung
        string bild_pfad
        int aktiv
    }

    KUNDE {
        int id PK
        string vorname
        string nachname
        string email
        string telefon
        string strasse
        string plz
        string ort
    }

    BESTELLUNG {
        int id PK
        int kunde_id FK
        string status
        string zahlungsart
        string versandart
        real versandkosten_chf
        real total_chf
        string stripe_session_id
        string kommentar
        string erstellt_am
    }

    BESTELLPOSITION {
        int id PK
        int bestellung_id FK
        int produkt_id FK
        int menge
        real einzelpreis_chf
    }

    KUNDE ||--o{ BESTELLUNG : "gibt auf"
    BESTELLUNG ||--|{ BESTELLPOSITION : "enthält"
    PRODUKT ||--o{ BESTELLPOSITION : "enthalten in"
```
