# Admin-Bereich für Bestellübersicht — Design Spec

> GitHub Issue: #25
> Datum: 2026-03-30
> Status: Draft

## Ziel

Einfacher Admin-Bereich für den Shop-Betreiber (Einzelunternehmer, ~100 Bestellungen/Monat). Bestellungen einsehen, Status verwalten, Kommunikation dokumentieren. Erweiterbar Richtung Produkt-/Kundenverwaltung und Statistiken.

## Scope

**In Scope (jetzt):**
- Login mit Passwort (Label-basiert, mehrere Admins möglich)
- Dashboard mit Kennzahlen und Bestelltabelle
- Bestelldetail mit Statusänderung, Notizen, Email-Tracking
- Admin-Log für alle Aktionen
- Automatisches Logging ausgehender System-Mails

**Out of Scope (später):**
- Produktverwaltung (CRUD)
- Kundenübersicht
- Statistiken / Charts
- Resend Inbound-Webhook (automatischer Email-Eingang)
- E2E-Tests

## 1. Authentifizierung

### Env-Variable

```
ADMIN_CREDENTIALS=owner:$2b$12$...,dev:$2b$12$...
```

Format: `label:bcrypt_hash` kommagetrennt. Jeder Admin hat sein eigenes Passwort und ein Label für Audit-Zwecke.

### Login-Flow

1. `GET /admin/login` zeigt Passwort-Formular
2. `POST /admin/login` prüft Eingabe gegen alle bcrypt-Hashes
3. Bei Erfolg: signierter Session-Cookie (via `itsdangerous`), enthält `admin_label` und `login_zeitpunkt`
4. Alle `/admin/*`-Routen (ausser Login) prüfen Session via FastAPI-Dependency
5. Session-Timeout: 24 Stunden

### Brute-Force-Schutz

- Fehlgeschlagene Logins werden geloggt (IP, Zeitpunkt)
- Nach 5 Fehlversuchen innerhalb 15 Minuten: 5 Minuten Sperre
- In-memory Dictionary (reicht für Einzelserver auf fly.io)

### Neue Dependency

- `bcrypt` — Passwort-Hashing

### Config-Erweiterung (`app/config.py`)

```python
admin_credentials: str = ""  # "label:hash,label:hash"
admin_session_max_age: int = 86400  # 24h in Sekunden
```

## 2. Datenbank

### Neue Tabelle: `admin_log`

```sql
CREATE TABLE IF NOT EXISTS admin_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    zeitpunkt TEXT NOT NULL DEFAULT (datetime('now')),
    admin_label TEXT NOT NULL,
    aktion TEXT NOT NULL,
    details TEXT NOT NULL DEFAULT '',
    bestellung_id INTEGER REFERENCES bestellungen(id)
);
```

### Aktions-Kategorien

| Aktion | Beschreibung | `details`-Inhalt |
|---|---|---|
| `login` | Erfolgreicher Login | IP-Adresse |
| `login_fehlgeschlagen` | Falsches Passwort | IP-Adresse |
| `logout` | Admin hat sich abgemeldet | — |
| `status_geaendert` | Bestellstatus geändert | `{"von": "bezahlt", "nach": "versendet"}` |
| `notiz_hinzugefuegt` | Freitext-Notiz | Notiz-Text |
| `email_ausgang` | System hat Mail gesendet | Empfänger + Betreff |
| `email_eingang` | Email vom Kunden | Manueller Eintrag (später automatisch via Resend Inbound) |

### Bestellstatus-Werte

Kein Schema-Change nötig (`status` ist TEXT). Neue gültige Werte:

| Status | Bedeutung | Gesetzt von |
|---|---|---|
| `neu` | Bestellung eingegangen | System |
| `bezahlt` | Zahlung bestätigt | System (Stripe Webhook) |
| `in_bearbeitung` | Wird vorbereitet | Admin |
| `versendet` | Paket unterwegs | Admin |
| `abholbereit` | Zur Abholung bereit | Admin |
| `abgeschlossen` | Erledigt | Admin |
| `storniert` | Storniert | Admin |

### Migration

Neue Datei: `migrations/002_admin.sql`

## 3. Routen

**Router:** `app/routers/admin.py`, Prefix `/admin`

| Route | Methode | Beschreibung | Auth |
|---|---|---|---|
| `/admin/login` | GET | Login-Formular | Nein |
| `/admin/login` | POST | Login prüfen | Nein |
| `/admin/logout` | POST | Session löschen | Ja |
| `/admin/` | GET | Dashboard | Ja |
| `/admin/bestellungen/{id}` | GET | Bestelldetail | Ja |
| `/admin/bestellungen/{id}/status` | POST | Status ändern | Ja |
| `/admin/bestellungen/{id}/notiz` | POST | Notiz/Email hinzufügen | Ja |

### Dashboard (`GET /admin/`)

**Kennzahl-Cards:**
- Offene Bestellungen (Status `neu` + `bezahlt`)
- Umsatz aktueller Monat (CHF)
- Bestellungen heute

**Bestelltabelle:**
- Spalten: Nr, Datum, Kunde (Name), Status, Zahlungsart, Versandart, Total
- Filter: Status (Dropdown), Zeitraum (von/bis Datum)
- Suche: Freitext (Kunden-Name, Email, Bestell-Nr)
- Sortierung: Datum absteigend (neueste zuerst)
- Pagination: Noch nicht nötig bei ~100 Bestellungen/Monat. Einfach ergänzbar via Limit/Offset wenn nötig.
- Klick auf Zeile → Detailansicht

### Bestelldetail (`GET /admin/bestellungen/{id}`)

**Kundendaten:** Name, Adresse, Email, Telefon
**Positionen:** Produkt, Menge, Einzelpreis, Zeilensumme
**Zusammenfassung:** Versandkosten, Total, Zahlungsart, Versandart
**Status-Änderung:** Dropdown mit erlaubten Status + "Ändern"-Button
**Log:** Chronologische Liste aller Einträge (Statusänderungen, Notizen, Emails)
**Notiz-Formular:** Textfeld + Typ-Auswahl (Notiz / Email-Eingang) + "Speichern"-Button

## 4. Code-Architektur

### Neue Dateien

```
app/
├── routers/admin.py          # Admin-Routen
├── repositories/admin_repo.py # DB-Queries für Dashboard, Log
├── services/auth_service.py   # Login, Session, Brute-Force
templates/admin/
├── base.html                  # Admin-Base (erbt von base.html)
├── login.html                 # Login-Formular
├── dashboard.html             # Dashboard mit Cards + Tabelle
├── bestellung_detail.html     # Bestelldetail + Log
migrations/
└── 002_admin.sql              # admin_log Tabelle
```

### Bestehende Dateien (Änderungen)

- `app/config.py` — Neue Settings: `admin_credentials`, `admin_session_max_age`
- `app/main.py` — Admin-Router einbinden
- `app/services/email_service.py` — Nach Mailversand `email_ausgang` in admin_log schreiben
- `app/routers/webhooks.py` — Nach Statusänderung auf `bezahlt` in admin_log schreiben
- `.env.example` — Neue Variablen dokumentieren

## 5. Styling

### Admin-Base-Template

- Erbt von `base.html` (Fonts, Tailwind-Config, Grundfarben)
- Eigener Header: "Admin" links, eingeloggtes Label + Logout-Button rechts
- Kein Warenkorb-Icon, keine Shop-Navigation

### Tailwind-Klassen (konsistent mit CLAUDE.md Card-UI)

| Element | Klassen |
|---|---|
| Kennzahl-Card | `bg-stone-700 rounded-lg p-6 shadow-md` |
| Tabelle | `bg-stone-700 rounded-lg overflow-hidden` |
| Tabellenzeile Hover | `hover:bg-stone-600 cursor-pointer transition-colors` |
| Status-Badge grün | `bg-green-600/20 text-green-400 px-2 py-1 rounded text-sm` |
| Status-Badge gelb | `bg-yellow-600/20 text-yellow-400 px-2 py-1 rounded text-sm` |
| Status-Badge rot | `bg-red-600/20 text-red-400 px-2 py-1 rounded text-sm` |
| Log-Eintrag | `border-l-2 border-stone-600 pl-4 py-2` |
| Responsive Tabelle | `overflow-x-auto` auf Mobile |

### Status-Farben

| Status | Farbe |
|---|---|
| `neu` | Gelb |
| `bezahlt` | Grün |
| `in_bearbeitung` | Blau |
| `versendet` | Blau |
| `abholbereit` | Blau |
| `abgeschlossen` | Grau |
| `storniert` | Rot |

## 6. Sicherheit

- **Session-Cookie:** `httponly=True`, `secure=True` (Production), `samesite=strict`
- **CSRF:** Gleicher Mechanismus wie Checkout (`itsdangerous`), auf alle POST-Routen
- **Brute-Force:** 5 Fehlversuche / 15 Min → 5 Min Sperre (in-memory)
- **Logging:** Alle Admin-Aktionen in `admin_log` (Audit-Trail)
- **Kein öffentlicher Link:** `/admin` nicht im Shop-Frontend verlinkt
- **Passwörter:** Nur bcrypt-Hashes in Env-Variable, nie Klartext

## 7. Erweiterbarkeit (Richtung C)

Das Design ist so angelegt, dass folgendes ohne Umbau ergänzt werden kann:

| Feature | Was nötig ist |
|---|---|
| Produktverwaltung | Neue Routen `/admin/produkte`, CRUD-Templates, Erweiterung `produkt_repo.py` |
| Kundenübersicht | Neue Route `/admin/kunden`, Query auf `kunden`-Tabelle |
| Statistiken | Neue Route `/admin/statistiken`, Auswertung auf `admin_log` + `bestellungen` |
| Mehr Admins | Weiteren `label:hash` an `ADMIN_CREDENTIALS` anhängen |
| Email-Inbound | Resend-Webhook-Route, schreibt `email_eingang` in `admin_log` |

## 8. Nicht-funktionale Anforderungen

- **Performance:** Alle Queries mit Limit/Offset für Pagination (bei Wachstum). Für ~100 Bestellungen/Monat reichen einfache Queries.
- **Kompatibilität:** Kein JavaScript nötig für Kernfunktionalität (Links, Formulare). Progressive Enhancement möglich.
- **Responsive:** Mobile-first, Tabelle horizontal scrollbar auf kleinen Screens.
