[← Übersicht](index.md)

# Olivalle — Datenbankschema

**Zweck:** Dieses Entity-Relationship-Diagramm zeigt die 7 SQLite-Tabellen des Webshops und ihre Beziehungen — vom Produktkatalog über Bestellungen bis zu Rabattcodes und Admin-Audit-Log.

> Quelle: `migrations/001_initial.sql`, `002_admin.sql`, `003_rabattcodes.sql` sowie idempotente Spalten-Ergänzungen in `app/database.py` (`init_db()`).

```mermaid
erDiagram
    PRODUKTE {
        int id PK
        string name
        int menge_ml
        real preis_chf
        string beschreibung
        string bild_pfad
        int aktiv
        real aktionspreis_chf "nullable, Admin-editierbar"
        string aktionstext "nullable"
        string aktion_von "nullable, ISO-Datum"
        string aktion_bis "nullable, ISO-Datum"
    }

    KUNDEN {
        int id PK
        string vorname
        string nachname
        string email
        string telefon
        string strasse
        string hausnummer
        string plz
        string ort
    }

    BESTELLUNGEN {
        int id PK
        int kunde_id FK
        string status "neu, bezahlt, in_bearbeitung, versendet, abholbereit, abgeschlossen, storniert"
        string zahlungsart "stripe, rechnung, abholung_bar"
        string versandart "versand, abholung"
        real versandkosten_chf
        real total_chf
        string stripe_session_id "nullable"
        string kommentar
        string erstellt_am "ISO 8601"
        int rabattcode_id FK "nullable"
        real rabattbetrag_chf
    }

    BESTELLPOSITIONEN {
        int id PK
        int bestellung_id FK
        int produkt_id FK
        int menge
        real einzelpreis_chf
    }

    RABATTCODES {
        int id PK
        string code UK
        string rabattart "prozent, fixbetrag"
        real rabattwert
        real mindestbestellwert_chf "nullable"
        int max_einloesungen "nullable"
        int aktuelle_einloesungen
        string gueltig_von
        string gueltig_bis
        int aktiv
        string erstellt_am
    }

    CODE_EINLOESUNGEN {
        int id PK
        int rabattcode_id FK
        string email
        int bestellung_id FK
        string eingeloest_am
    }

    ADMIN_LOG {
        int id PK
        string zeitpunkt
        string admin_label
        string aktion
        string details
        int bestellung_id FK "nullable"
    }

    KUNDEN ||--o{ BESTELLUNGEN : "gibt auf"
    BESTELLUNGEN ||--|{ BESTELLPOSITIONEN : "enthält"
    PRODUKTE ||--o{ BESTELLPOSITIONEN : "enthalten in"
    RABATTCODES ||--o{ BESTELLUNGEN : "rabattiert"
    RABATTCODES ||--o{ CODE_EINLOESUNGEN : "eingelöst durch"
    BESTELLUNGEN ||--o{ CODE_EINLOESUNGEN : "protokolliert in"
    BESTELLUNGEN ||--o{ ADMIN_LOG : "verändert durch"
```

**Die Tabellen im Einzelnen:**

- **produkte** — Katalog. Die `aktion*`-Spalten werden im Admin gesetzt und überleben Container-Neustarts bewusst (Seed-UPSERT lässt sie unangetastet, vgl. Bug #137).
- **kunden** — Lieferadresse pro Bestellung. Pflicht: Vor-/Nachname, Strasse, PLZ, Ort, E-Mail; optional Telefon, Hausnummer.
- **bestellungen** — Kopf einer Bestellung mit Status-, Zahlungs- und Versandart sowie optional angewandtem Rabattcode.
- **bestellpositionen** — Warenkorb-Zeilen (Produkt × Menge zum Einzelpreis bei Bestellung).
- **rabattcodes** — Admin-verwaltete Codes (Prozent oder Fixbetrag), mit Gültigkeit und Einlöse-Limit.
- **code_einloesungen** — Einlöse-Protokoll; `UNIQUE(rabattcode_id, email)` verhindert Mehrfacheinlösung pro Person.
- **admin_log** — Audit-Trail aller Admin-Aktionen (DSG-relevant, siehe `datenschutz.md`).
