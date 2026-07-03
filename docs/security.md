[← Übersicht](index.md)

# Security-Notizen

Querschnittsdokumentation zu Security-relevanten Entscheidungen und Audits.

## Vorhandene Schutzmaßnahmen

Faktische Bestandsaufnahme der im Code umgesetzten Maßnahmen (kein Vollaudit):

- **CSRF-Schutz:** Token-basiert für alle Formulare, an pro-Nutzer Identity gebunden (`app/csrf.py`).
- **Rate-Limiting:** In-memory Sliding-Window aktiv auf `/bestellen` und Admin-Login (`app/services/rate_limit.py`).
- **Brute-Force-Schutz:** Lockout nach mehreren Fehlversuchen auf `/admin/login`.
- **Security-Header:** gesetzt via Middleware (`app/middleware/security_headers.py`), inkl. CSP ohne `unsafe-eval`.
- **Admin-Auth:** bcrypt-gehashtes Passwort, kein Klartext im Code (`app/services/auth_service.py`).
- **Stripe-Webhooks:** Signaturprüfung, kein blindes Vertrauen in Webhook-Daten (`app/routers/webhooks.py`).
- **Secrets:** ausschließlich via Umgebungsvariablen / `fly secrets`; nichts im Repo (`.env` gitignored).
- **Transport:** HTTPS erzwungen durch fly.io.

## Security-Header im Detail

Alle Antworten erhalten Security-Header über `SecurityHeadersMiddleware` (`app/middleware/security_headers.py`). Pro Request wird eine frische CSP-Nonce erzeugt und für Inline-Scripts verwendet (kein `unsafe-eval`, kein `unsafe-inline` bei `script-src`).

| Header | Wert | Zweck |
|---|---|---|
| `Content-Security-Policy` | `default-src 'self'`; `script-src 'self' 'nonce-…' https://js.stripe.com`; `style-src 'self' 'unsafe-inline' https://fonts.googleapis.com`; `img-src 'self' data:`; `font-src 'self' https://fonts.gstatic.com data:`; `connect-src 'self' https://api.stripe.com`; `frame-src https://js.stripe.com https://hooks.stripe.com`; `frame-ancestors 'none'`; `base-uri 'self'`; `form-action 'self' https://checkout.stripe.com` | XSS-/Injection-Schutz; nur eigene Quellen + Stripe erlaubt |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` (nur über HTTPS) | Erzwingt HTTPS im Browser für ein Jahr |
| `X-Frame-Options` | `DENY` | Clickjacking-Schutz (zusätzlich zu `frame-ancestors 'none'`) |
| `X-Content-Type-Options` | `nosniff` | Verhindert MIME-Type-Sniffing |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Begrenzt weitergegebene Referrer-Informationen |

**Hintergrund:** Tailwind wird zur Build-Zeit kompiliert (Issue #88), Inline-Scripts laufen über Nonces (Issue #89) — dadurch kommt die CSP ohne `unsafe-eval` aus. Stripe-Domains sind explizit erlaubt, weil Checkout und Webhook-Frames darüber laufen.

## Health-Check

Der Endpunkt `GET /health` (`app/main.py`) prüft aktiv die Datenbank-Erreichbarkeit (`SELECT 1`) und antwortet bei Fehler mit HTTP 503. Er dient dem fly.io-internen Self-Heal und dem externen Uptime-Monitoring (siehe [CI/CD & Versionierung](ci-cd-und-versionierung.md)).

## Template-XSS-Audit

**Stand:** 2026-04-07

`grep -rn "|safe\|Markup(" templates/ app/` findet keine Treffer. Es gibt
aktuell keine Stelle, an der Jinja2-Autoescape umgangen wird.

**Regel für die Zukunft:** Bei jeder neuen Verwendung von `|safe` oder
`Markup()` prüfen, ob Userinput in den markupten String fliessen kann.
Nur statische, vertrauenswürdige Strings markupen. Im Zweifel: stattdessen
escapen lassen.

**Client-seitig (JavaScript):** Nutzdaten (z.B. Produktnamen aus
`localStorage` oder `data`-Attributen) nie per String-Interpolation in
`innerHTML` rendern, sondern DOM-Knoten mit `createElement` +
`textContent` bauen (Issue #166). `innerHTML = ""` zum Leeren eines
Containers ist unbedenklich.
