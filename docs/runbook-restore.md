# Runbook: Backup-Restore für Olivalle

**Ziel-Leser:** Entwickler oder Inhaber. Szenario A kann der Inhaber
eigenständig durchführen, falls fly-CLI-Zugang vorhanden.

**Siehe auch:** [`adr-backup-strategie.md`](adr-backup-strategie.md)

## Zugänge, die nötig sind

| Was | Wo | Wer hat Zugriff |
|---|---|---|
| fly-Account (olivalle-App) | https://fly.io | Entwickler |
| Tigris-Bucket `olivalle-backup` | `fly storage` | automatisch via fly-Secrets |
| Healthchecks.io-Check | https://healthchecks.io | Entwickler |
| Domain-Registrar (DNS) | siehe `adr-domain-registrar.md` | Entwickler |

fly-Support im Ernstfall: https://community.fly.io oder
https://fly.io/docs/about/support/.

---

## Szenario A — Komplettverlust des fly-Volumes

**Symptom:** fly meldet Volume-Ausfall, die Machine startet nicht oder startet
mit leerer DB.

```bash
fly logs -a olivalle                    # Ursache prüfen
fly deploy                              # entrypoint.sh triggert Auto-Restore
```

`entrypoint.sh` erkennt beim Start, dass `/data/olivalle.db` fehlt, und zieht
den letzten Stand aus Tigris. Erwartete Downtime ~5 Min, Datenverlust im
Sekundenbereich.

**Verifikation:**
1. Shop-Startseite aufrufen → 200
2. Im Admin-Bereich die letzten 5 Bestellungen gegen das Stripe-Dashboard
   abgleichen

---

## Szenario B — DB ist da, aber korrupt

**Symptom:** Admin-Bereich zeigt Unsinn, Fehler in `fly logs`, oder
`PRAGMA integrity_check` schlägt fehl.

```bash
fly ssh console -a olivalle
```

Im Container:

```sh
# Alte DB wegsichern (nicht löschen — forensische Reserve)
mv /data/olivalle.db /data/olivalle.db.broken

# Restore aus Tigris (optional Point-in-Time)
litestream restore -config /etc/litestream.yml /data/olivalle.db
# Point-in-Time-Variante:
# litestream restore -timestamp 2026-04-22T14:00:00Z \
#   -config /etc/litestream.yml /data/olivalle.db

exit
```

Danach:

```bash
fly machine restart -a olivalle
```

**Verifikation** wie Szenario A.

---

## Szenario C — Jährlicher Restore-Test

**Kalendereintrag:** "Olivalle Backup-Test" — 1x/Jahr (empfohlen im April,
zum Jahrestag der Einführung).

### Schritte

1. Tigris-Credentials lokal als ENV-Vars setzen (aus fly-Secrets):

   ```bash
   export LITESTREAM_ACCESS_KEY_ID="$(fly secrets list --app olivalle | grep LITESTREAM_ACCESS_KEY_ID)"  # Wert ist nicht sichtbar → temporär via 'fly ssh console' und echo holen ODER aus eigenem Passwort-Manager
   export LITESTREAM_SECRET_ACCESS_KEY="…"
   ```

   > **Hinweis:** `fly secrets list` zeigt Secrets nicht im Klartext. Praktikabler
   > Weg: `fly ssh console -a olivalle -C 'printenv LITESTREAM_ACCESS_KEY_ID'`
   > (einmalig für den Test, danach lokal wieder löschen).

2. Restore in ein tmp-File:

   ```bash
   litestream restore \
     -config litestream.yml \
     -o /tmp/olivalle-restore-test.db
   ```

3. Integritätscheck:

   ```bash
   sqlite3 /tmp/olivalle-restore-test.db "PRAGMA integrity_check;"
   ```

   Erwartet: `ok`.

4. Plausibilitätsabfrage:

   ```bash
   sqlite3 /tmp/olivalle-restore-test.db \
     "SELECT COUNT(*) AS bestellungen,
             MIN(erstellt_am) AS erste,
             MAX(erstellt_am) AS letzte
      FROM bestellungen;"
   ```

   Die Anzahl muss plausibel zum Shop-Umsatz der letzten Monate passen.

5. Ergebnis im Anhang unten festhalten und tmp-File löschen:

   ```bash
   rm /tmp/olivalle-restore-test.db
   ```

---

## Heartbeat-Alert erhalten — was tun?

Healthchecks.io mailt, wenn > 15 Min kein Ping kam. **Seit 2026-04-22
(Issue #116) läuft die Machine via `min_machines_running = 1` durchgängig
— ein Alert ist daher ernst zu nehmen, kein Toleranzband mehr durch
Machine-Stop.**

1. `fly status -a olivalle` — Machine muss `started` sein. Falls `stopped`
   oder `failed`: fly-Problem, `fly machine restart` versuchen, bei
   Wiederholung fly-Support.
2. `fly logs -a olivalle --no-tail` — letzte Replikations-Zeilen prüfen.
   Nach `litestream:` filtern — Replikationsfehler sichtbar?
3. `fly ssh console -a olivalle` → `ls -la /data/olivalle.db-litestream`
   → Modifikationszeiten prüfen (sollten < 1 Min alt sein).
4. Häufigster Fall: Tigris-Credentials rotiert/abgelaufen → neue Keys
   erzeugen (`fly storage create` hat eine `regen`-Variante oder Bucket
   neu anlegen) und via `fly secrets set` injizieren.

---

## Anhang: Protokoll der Restore-Tests

| Datum | Ergebnis `integrity_check` | Bestellungen | Bemerkung |
|---|---|---|---|
| YYYY-MM-DD | ok / FAIL | N | — |
