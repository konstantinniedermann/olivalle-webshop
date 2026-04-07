# Security-Header Middleware — Design

**Issue:** #74
**Datum:** 2026-04-07
**Status:** Approved

## Ziel
Standard-HTTP-Security-Header für alle Responses setzen, um vor Go-Live grundlegenden Browser-seitigen Schutz (Clickjacking, MIME-Sniffing, Mixed Content, Referrer-Leaks, Script-Injection) zu aktivieren.

## Scope
- Eine neue Middleware, die fünf Header auf jede Response setzt.
- **Nicht im Scope:** Inline-`<script>`-Blöcke entfernen, Tailwind als Build-Step, CSP mit Nonces. Dafür wird ein Folge-Issue angelegt (nach Go-Live).

## Architektur
- Neue Datei: `app/middleware/security_headers.py`
- Klasse `SecurityHeadersMiddleware(BaseHTTPMiddleware)`
- Registrierung in `app/main.py` via `app.add_middleware(SecurityHeadersMiddleware)`, direkt nach der bestehenden `redirect_www`-Middleware.
- Keine externe Library — fünf Header reichen, eine Abhängigkeit weniger.

## Headers

| Header | Wert | Bedingung |
|---|---|---|
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` | Nur wenn `x-forwarded-proto: https` (nicht in lokaler Dev-Umgebung) |
| `X-Content-Type-Options` | `nosniff` | immer |
| `X-Frame-Options` | `DENY` | immer |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | immer |
| `Content-Security-Policy` | siehe unten | immer |

### Content-Security-Policy
```
default-src 'self';
script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.tailwindcss.com https://js.stripe.com;
style-src 'self' 'unsafe-inline' https://fonts.googleapis.com;
img-src 'self' data:;
font-src 'self' https://fonts.gstatic.com data:;
connect-src 'self' https://api.stripe.com;
frame-src https://js.stripe.com https://hooks.stripe.com;
frame-ancestors 'none';
base-uri 'self';
form-action 'self' https://checkout.stripe.com
```

**Begründung der Lockerungen:**
- `'unsafe-inline'` + `'unsafe-eval'` für Scripts: Tailwind CDN (`cdn.tailwindcss.com`) evaluiert Klassen zur Laufzeit; ausserdem nutzen mehrere Templates Inline-`<script>`-Blöcke (checkout, warenkorb, bestaetigung, admin/*). Strenge CSP folgt im Folge-Issue.
- `'unsafe-inline'` für Styles: Tailwind generiert Inline-Styles.
- Stripe-Domains explizit gewhitelistet (`js.stripe.com`, `api.stripe.com`, `hooks.stripe.com`, `checkout.stripe.com`).
- Google Fonts (`fonts.googleapis.com`, `fonts.gstatic.com`) explizit erlaubt.
- `frame-ancestors 'none'` schützt zusätzlich zu `X-Frame-Options: DENY` (moderne Browser bevorzugen CSP).

## Tests
Neue Datei: `tests/test_security_headers.py`

1. **`test_security_headers_present_on_homepage`** — GET `/`, prüft alle 5 Header gesetzt, CSP enthält `js.stripe.com`.
2. **`test_hsts_only_on_https`** — GET `/health` ohne `x-forwarded-proto: https` → kein HSTS-Header. Mit Header → HSTS gesetzt.
3. **`test_admin_login_frame_ancestors`** — GET `/admin/login`, prüft `frame-ancestors 'none'` in CSP und `X-Frame-Options: DENY`.

## Folge-Issue (nach Go-Live)
Neues Issue anlegen: „Security: Inline-Scripts entfernen, Tailwind als Build-Step, CSP mit Nonces härten". Verlinkt #74.

## Risiken
- **Stripe-Checkout-Redirect:** Olivalle nutzt Stripe Hosted Checkout (Redirect, kein Embed). `form-action https://checkout.stripe.com` deckt das ab. Falls später Stripe Elements eingebettet werden, muss `frame-src` ggf. erweitert werden.
- **Google Fonts ausfallen:** Bei Netzwerkfehlern lädt nur der Fallback-Font. Kein CSP-bedingter Bruch.
