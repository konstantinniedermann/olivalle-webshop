# CSP-Härtung — Design

**Datum:** 2026-04-08
**Kontext:** Aufteilung von #79 in zwei unabhängige Nachfolge-Issues (#88, #89)
**Status:** Brainstorming abgeschlossen, Implementierung steht aus

## Problem

Die aktuelle Content-Security-Policy des Olivalle-Webshops erlaubt in `script-src` sowohl `'unsafe-inline'` als auch `'unsafe-eval'`. Damit ist die CSP als zweite Verteidigungslinie gegen XSS praktisch wirkungslos: eingeschleuster Code würde vom Browser trotzdem ausgeführt.

Zwei technische Ursachen erzwingen diese Flags aktuell:

1. **Tailwind via CDN (`cdn.tailwindcss.com`)** kompiliert im Browser zur Laufzeit → braucht `'unsafe-eval'`. Zusätzlich: externer Request bei jedem Seitenaufruf ist DSG-relevant.
2. **Inline-`<script>`-Blöcke** in mehreren Templates (checkout.html, warenkorb.html, bestaetigung.html, admin/*, base.html) → brauchen `'unsafe-inline'`.

## Risiko-Bewertung

- **Eintrittswahrscheinlichkeit:** niedrig. Jinja2-Autoescape ist aktiv, kein User-generated Content reflektiert, kein öffentliches Login mit Session-Hijacking-Risiko.
- **Schadenshöhe im XSS-Fall:** hoch. Kreditkartenbetrug via gefälschtem Stripe-Redirect auf eigener Domain, Session-Übernahme, DSG-Meldepflicht, Stripe-Account-Sperre.
- **Entscheidung:** Härtung **vor Go-Live**, weil ab Live-Betrieb echte Kundendaten und Zahlungen durchlaufen und Nacharbeiten teurer werden.

## Lösungsansatz

Statt des ursprünglich einen grossen Issues (#79) wird in zwei unabhängige Teile aufgeteilt. Begründung: technisch disjunkt (CSS-Pipeline + Docker vs. Jinja-Templates + Middleware), jeder Teil bringt eigenen messbaren CSP-Gewinn, kleinere PRs sind reviewfreundlicher.

### Teil 1 — #88: Tailwind lokal builden

**Ziel:** `'unsafe-eval'` aus `script-src` entfernen, externen CDN-Request eliminieren.

**Umfang:**
- Tailwind CLI als Build-Step (lokal via `make`, in Docker via Multi-Stage-Build mit Node-Stage)
- Finales Docker-Image bleibt Python-only (kein Node zur Laufzeit)
- `cdn.tailwindcss.com` aus `base.html` entfernen, gebautes `static/css/app.css` einbinden
- CSP: `'unsafe-eval'` aus `script-src` raus, `cdn.tailwindcss.com` aus allen Directives raus
- Tests: CSP-Header-Test anpassen

**Nutzen:** CSP-Härtung (eval) + DSG (kein externer Request) + Performance (gecachtes CSS statt Runtime-JIT).

### Teil 2 — #89: Inline-Scripts per CSP-Nonce

**Ziel:** `'unsafe-inline'` aus `script-src` entfernen, ohne alle Inline-Scripts in externe Dateien auslagern zu müssen.

**Umfang:**
- CSP-Middleware erweitert: pro Request kryptografisch zufälligen Nonce generieren (`secrets.token_urlsafe`), in `request.state.csp_nonce` hinterlegen, im CSP-Header als `'nonce-<value>'` in `script-src` einfügen
- Jinja2-Context-Processor: Nonce als `csp_nonce` in allen Templates verfügbar machen
- Alle Inline-`<script>`-Blöcke erhalten `nonce="{{ csp_nonce }}"`
- Betroffene Templates: `base.html`, `checkout.html`, `warenkorb.html`, `bestaetigung.html`, `admin/*`
- CSP: `'unsafe-inline'` aus `script-src` raus
- Tests: Nonce-Präsenz in Header + Template, CSP-Header-Test anpassen, Nonce pro Request unterschiedlich

**Nutzen:** CSP-Härtung (inline) → echte zweite Verteidigungslinie gegen XSS.

## Abhängigkeiten

- #88 und #89 sind **technisch unabhängig** und können in beliebiger Reihenfolge umgesetzt werden.
- Keine `Blocked by`-Beziehung zwischen den beiden.
- **Reihenfolge in der Umsetzung:** #89 zuerst (kleiner Scope, reine Python/Jinja-Arbeit, sofortiger Security-Gewinn), danach #88 (grösserer Umbau mit Docker/Node-Stage).
- Jedes Issue erhält einen eigenen Impl-Plan in einer frischen Session.

## Nicht im Scope

- Auslagern aller Inline-Scripts in externe `.js`-Dateien (Alternative zu Nonces verworfen — zu viel Umbau für den Nutzen)
- Subresource Integrity (SRI) für externe Scripts
- CSP Reporting-Endpoint
- Weitere CSP-Directives härten (`style-src`, `img-src`, `connect-src`) — separater Task, falls nötig

## Offene Punkte für die Impl-Pläne

- **#88:** Welche Tailwind-Version pinnen? Wie Hot-Reload lokal (Tailwind-Watch-Mode via `make dev`)? CI-Integration (GitHub Actions Node-Step)?
- **#89:** Middleware-Reihenfolge prüfen (Nonce muss vor Template-Rendering gesetzt sein). Edge-Cases bei Error-Pages (haben die eigenen Middleware-Pfad?).

Diese Punkte werden in den jeweiligen Impl-Plänen der Folge-Sessions geklärt.
