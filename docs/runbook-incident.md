# Runbook: Incident-Triage für Olivalle

**Ziel-Leser:** Entwickler. Szenarien A–C erfordern fly-CLI-Zugang.

**Siehe auch:** [`runbook-restore.md`](runbook-restore.md), [`adr-backup-strategie.md`](adr-backup-strategie.md)

## Zugänge, die nötig sind

| Was | Wo | Wer hat Zugriff |
|---|---|---|
| fly-Account (olivalle-App) | https://fly.io | Entwickler |
| Healthchecks.io | https://healthchecks.io | Entwickler |
| Domain-Registrar (DNS) | siehe `adr-domain-registrar.md` | Entwickler |
| GitHub-Repo | https://github.com/konstantinniedermann/olivalle-webshop | Entwickler |

---

## Alarm kam rein — was jetzt?

1. **Browser-Test:** `https://olivalle.ch/health` aufrufen.
   - 200 `{"status": "ok"}` → False-Positive oder bereits selbst-resolved → Schritt 5.
   - 503 → Szenario A.
   - Timeout/Connection refused → Szenario B.
   - TLS-Fehler im Browser → Szenario C.
2. **fly-Status:** `fly status -a olivalle` und `fly logs -a olivalle`.
3. **Szenario auswählen** (unten).
4. **Nach Fix:** Browser-Test wiederholen, Healthchecks.io-Dashboard kontrollieren.
5. **False-Positive?** Kein Handlungsbedarf — Healthchecks.io selbst-resolved beim nächsten erfolgreichen Ping.

---

## Szenario A — 503 vom Health-Check (DB-Problem)

**Symptom:** `/health` antwortet 503, App-Prozess läuft aber.

**Ursache meist:** SQLite-DB fehlt oder ist korrupt (Volume-Detach,
Permission, File-System-Fehler).

```bash
fly logs -a olivalle              # Hinweise: OperationalError, "unable to open database file"?
fly ssh console -a olivalle       # In die Machine einloggen
ls -la /data/                     # Ist olivalle.db vorhanden und > 0 Byte?
```

Wenn DB fehlt oder offensichtlich defekt:
**→ [`runbook-restore.md`](runbook-restore.md), Szenario A oder B.**

---

## Szenario B — Timeout / Connection refused (Machine tot)

**Symptom:** Keine HTTP-Antwort, Browser zeigt Timeout oder "Connection refused".

```bash
fly status -a olivalle            # Running? Failed?
fly machine list -a olivalle
fly logs -a olivalle --since 1h
```

Häufige Ursachen + Reaktion:

| Beobachtung | Aktion |
|---|---|
| Machine "stopped" | `fly machine start <id>` |
| Machine "crashed" in Loop | `fly deploy` — Image-Problem, Neubau |
| `out of memory` im Log | RAM upsizen in `fly.toml` oder Memory-Leak-Debug |
| fly-Region-Ausfall | https://status.flyio.net prüfen, warten |

---

## Szenario C — TLS-Alarm (`olivalle-tls-expiry`)

**Symptom:** Alarm-Mail von Healthchecks.io mit Check-Name `olivalle-tls-expiry`.
Restlaufzeit des TLS-Zertifikats ist unter 30 Tage gefallen.

**Diagnose:**

```bash
echo | openssl s_client -connect olivalle.ch:443 -servername olivalle.ch 2>/dev/null | openssl x509 -noout -dates
fly certs list -a olivalle
fly certs check olivalle.ch -a olivalle
```

**Aktion:**

- fly renewed Let's Encrypt automatisch. Wenn das nicht passiert:
  - DNS-Records auf Registrar-Seite prüfen (A/AAAA → fly-IP; CAA-Record erlaubt Let's Encrypt?).
  - `fly certs check olivalle.ch` zeigt fehlschlagende Challenges.
- Notfalls: `fly certs remove olivalle.ch && fly certs add olivalle.ch` (Vorsicht: DNS muss passen, sonst bleibt die Seite vorübergehend ohne Cert).
- Bei Registrar-Problemen → `adr-domain-registrar.md` konsultieren.

---

## Szenario D — Healthchecks.io meldet Silence, aber Shop erreichbar

**Symptom:** Alarm für `olivalle-http-uptime` oder `olivalle-tls-expiry`, aber
Browser kann olivalle.ch normal aufrufen.

**Ursache meist:** GitHub-Actions-Runner-Queue verzögert, oder Workflow
deaktiviert/kaputt.

```bash
gh run list --workflow monitor-uptime.yml --limit 5
gh run list --workflow monitor-tls.yml --limit 5
```

- Wenn Runs ausfallen/fehlen: GitHub-Status https://www.githubstatus.com prüfen.
- Wenn Runs rot sind: Log öffnen, Ursache fixen.
- Healthchecks.io resolved automatisch beim nächsten erfolgreichen Ping — keine manuelle Aktion nötig ausser Ursachen-Fix.

---

## Verifikation der Monitoring-Kette (regelmässig, z.B. 1×/Quartal)

1. `fly checks list -a olivalle` → `/health`-Check passing.
2. GitHub Actions-Tab → grüne Runs für beide Monitor-Workflows.
3. Healthchecks.io-Dashboard → drei Checks (`litestream-heartbeat`, `http-uptime`, `tls-expiry`) zeigen "up".
4. Test-Alarm auslösen:
   - In Healthchecks.io einen Check manuell auf "pause" stellen.
   - Nach Grace-Period E-Mail-Eingang prüfen.
   - Check wieder "resume".

---

## Eskalation

| Wann | An wen |
|---|---|
| fly-Machine nicht wiederherstellbar | fly-Community-Support: https://community.fly.io |
| Domain-Problem | Registrar (siehe `adr-domain-registrar.md`) |
| DB korrupt + Backup ebenfalls defekt | SH informieren, letzter manueller Export? |
