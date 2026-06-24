[← Übersicht](index.md)

# Security-Notizen

Querschnittsdokumentation zu Security-relevanten Entscheidungen und Audits.

## Vorhandene Schutzmaßnahmen

Faktische Bestandsaufnahme der im Code umgesetzten Maßnahmen (kein Vollaudit):

- **CSRF-Schutz:** Token-basiert für alle Formulare, an pro-Nutzer Identity gebunden (`app/csrf.py`).
- **Rate-Limiting:** In-memory Sliding-Window auf `/bestellen` (10/Min) und Admin-Login (5/Min) (`app/services/rate_limit.py`).
- **Brute-Force-Schutz:** Lockout nach 5 Fehlversuchen auf `/admin/login`.
- **Security-Header:** gesetzt via Middleware (`app/middleware/security_headers.py`), inkl. CSP ohne `unsafe-eval`.
- **Admin-Auth:** bcrypt-gehashtes Passwort, kein Klartext im Code (`app/services/auth_service.py`).
- **Stripe-Webhooks:** Signaturprüfung, kein blindes Vertrauen in Webhook-Daten (`app/routers/webhooks.py`).
- **Secrets:** ausschließlich via Umgebungsvariablen / `fly secrets`; nichts im Repo (`.env` gitignored).
- **Transport:** HTTPS erzwungen durch fly.io.

## Template-XSS-Audit

**Stand:** 2026-04-07

`grep -rn "|safe\|Markup(" templates/ app/` findet keine Treffer. Es gibt
aktuell keine Stelle, an der Jinja2-Autoescape umgangen wird.

**Regel für die Zukunft:** Bei jeder neuen Verwendung von `|safe` oder
`Markup()` prüfen, ob Userinput in den markupten String fliessen kann.
Nur statische, vertrauenswürdige Strings markupen. Im Zweifel: stattdessen
escapen lassen.
