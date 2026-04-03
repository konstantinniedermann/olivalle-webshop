# Stripe-Abbruch/Fehler: Bestellung automatisch stornieren

**Datum:** 2026-04-03
**Status:** Genehmigt
**User Story 11:** Wenn jemand den Stripe-Checkout abbricht oder ungueltige Kreditkartendaten eingibt, soll keine aktive Bestellung entstehen. Stattdessen wird die Bestellung automatisch als storniert markiert mit Begruendung.

## Kontext

Bestellungen werden aktuell VOR dem Stripe-Checkout in der DB angelegt (Status `neu`). Bei erfolgreicher Zahlung setzt der Webhook den Status auf `bezahlt`. Bei Abbruch oder Fehlschlag bleibt die Bestellung jedoch mit Status `neu` stehen und erscheint im Admin-Dashboard als offene Bestellung.

## Entscheidungen

- **Bestellung weiterhin vor Stripe anlegen** — der bestehende Flow bleibt erhalten
- **Bei Stripe-Fehler/Abbruch: Status auf `storniert` setzen** mit Log-Eintrag
- **Nur Webhook-basiert** (kein Cronjob) — KISS-Prinzip, Stripe ist zuverlaessig genug
- **Keine E-Mail an Kunden** bei Stornierung — Kunde weiss, dass er abgebrochen hat
- **QR-Rechnungs-Flow bleibt unberuehrt** — dort ist Status `neu` korrekt

## Aenderungen

### 1. Webhook erweitern (`app/routers/webhooks.py`)

Zwei neue Stripe-Events behandeln:

| Stripe Event | Ausloeser | Log-Details |
|---|---|---|
| `checkout.session.expired` | Kunde bricht ab oder Session laeuft ab (24h) | `"Stripe Checkout abgebrochen oder abgelaufen"` |
| `checkout.session.async_payment_failed` | Zahlung fehlgeschlagen (z.B. ungueltige KK) | `"Zahlung fehlgeschlagen"` |

Logik pro Event:
1. Bestellung anhand `stripe_session_id` finden
2. Idempotenz-Check: nur verarbeiten wenn Status noch `neu`
3. Status auf `storniert` setzen
4. Log-Eintrag ins `admin_log` mit `admin_label="system"` und Begruendung

### 2. Keine weiteren Aenderungen noetig

- **Dashboard-Stats:** `storniert` ist bereits von "offene Bestellungen" ausgeschlossen
- **Admin-UI:** Stornierte Bestellungen sind bereits darstellbar und filterbar
- **Bestellprozess:** Keine Aenderung
- **E-Mail-Service:** Keine Aenderung

## Nicht im Scope

- Cronjob als Fallback (kann spaeter nachgeruestet werden)
- E-Mail-Benachrichtigung bei Stornierung
- Aenderungen am QR-Rechnungs-Flow
