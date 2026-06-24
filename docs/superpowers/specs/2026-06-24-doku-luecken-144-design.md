# Design: Restliche Doku-Lücken aus Gesamt-Audit (#144)

> Status: genehmigt · Datum: 2026-06-24 · Branch: `docs/issue-144-restliche-doku-luecken`

## Kontext

Sammel-Issue #144 fasst die verbleibenden, grösseren Erkenntnisse des Doku-Vollständigkeits-Audits zusammen. In dieser Session werden **drei** der fünf Punkte umgesetzt:

- **Punkt 1** — Lebensmittel-Deklaration (LIV Art. 39) dokumentieren
- **Punkt 4** — Betreiber-/Admin-Sicht in den Diagrammen ergänzen (alle drei Vorschläge)
- **Punkt 5** — Tigris in der Datenschutzerklärung ergänzen (DSG)

**Vertagt (bleiben offen im Issue):**
- Punkt 2 (`/health` ohne `version`-Feld) — Code-Entscheidung, später.
- Punkt 3 (Sichtbarkeit der Specs/Plans in der MkDocs-Site) — Diskussion, später.

**Verworfen:** Eigenes Rabattcode-Ablaufdiagramm (YAGNI) — bleibt Routentabelle + Fliesstext in §5.2/§8.

## Rahmenbedingungen

- Ein Feature-Branch, ein PR. Commit-Präfix `docs:`.
- Verifikationsgate vor jedem Commit: `uv run --extra docs mkdocs build --strict` **und** separate Mermaid-Validierung jedes neuen/geänderten Diagramms (strict-build prüft keine Mermaid-Syntax).
- **Mermaid-Regeln:** kein `\n` in Node-Labels; kein `@` in Kanten-Labels (Mermaid v11 `LINK_ID`-Parse-Error, vgl. commit `00a1ab6`).
- Legal-relevante Texte (Punkt 1 + 5) im PR/Issue als **„mit SH gegenlesen"** markieren.

---

## A — Punkt 5: Tigris / DSG

Litestream repliziert die SQLite-DB (inkl. Kundendaten: Name, Adresse, E-Mail, Bestelldaten) kontinuierlich nach Tigris → eintragspflichtiger Auftragsverarbeiter. Standort lt. `adr-backup-strategie.md`: Location `eur` (Amsterdam + Frankfurt, EU).

**A1 — `docs/legal/datenschutz.md`** (öffentlich): Tigris-Zeile ergänzen:

| Anbieter | Zweck | Standort |
|---|---|---|
| Tigris | Verschlüsseltes Datenbank-Backup (Bestelldaten, via Litestream) | EU (Amsterdam, Frankfurt) |

**A2 — `templates/datenschutz.html`** (Live, rechtlich bindend): gleiche Zeile in die HTML-Tabelle. Aktuell stehen dort nur Stripe/Brevo/fly.io.

**A3 — SQLite-Drift beheben (entschieden: „Entfernen + Satz"):** SQLite ist eine lokale Library auf der fly.io-Infrastruktur, **kein externer Auftragsverarbeiter**. SQLite-Zeile aus beiden Drittanbieter-Tabellen entfernen (in der Doku-Tabelle ist sie aktuell vorhanden, im Live-Template nicht) und durch einen erklärenden Satz ersetzen (Daten liegen lokal auf fly.io, abgedeckt durch die fly.io-Zeile).

**Ergebnis (Doku & Live konsistent):** Stripe · Brevo · fly.io · **Tigris**.

**A4 — `docs/datenschutz.md`** (intern): behandelt nur Admin-Log/`client_ip` — **keine Änderung nötig** (Backup ist über `adr-backup-strategie.md` belegt).

## B — Punkt 1: Lebensmittel-Deklaration (LIV Art. 39)

Neue Seite **`docs/legal/lebensmittel-deklaration.md`** als Compliance-Nachweis, in `mkdocs.yml` nav unter „Rechtliches" eintragen.

Inhalt:
- **Umgesetzte Pflichtangaben:** Sachbezeichnung „Natives Olivenöl extra (biologisch)", Güteklassen-Beschreibung, Nährwerte pro 100 g (Energie, Fett / davon gesättigte, Kohlenhydrate, Eiweiss, Salz).
- **Wo live:** `templates/ueber-das-oel.html` (Abschnitt „Sachbezeichnung" + „Nährwerte pro 100 g").
- **Rechtsgrundlage:** LIV (Lebensmittelinformationsverordnung) Art. 39.
- Markiert als **„mit SH gegenlesen"**.

## C — Punkt 4: Betreiber-Diagramme

Quelle der Wahrheit für die Status-Logik: `templates/admin/bestellung_detail.html` (`normalTransitions`) + `app/services/email_service.py` (`_STATUS_EMAIL_CONFIG`).

**C1 — Zustandsdiagramm Bestellstatus** (`stateDiagram-v2`) in `docs/arc42.md §5.2 Administrationsbereich`. Kanonischer Lebenszyklus + pro Übergang ausgelöste Status-Mail + `storniert` als Quereinstieg. Status-Mail-Trigger:
- `neu → bezahlt`: Zahlungseingang-Mail (nur bei Zahlungsart Rechnung/Bar; bei Stripe via Webhook bereits bestätigt)
- `… → versendet`: Versandbestätigungs-Mail (nur Versandart Versand)
- `… → abholbereit`: Abholbereit-Mail (nur Versandart Abholung)

Dynamische Reihenfolge bezahlt↔versendet bei Rechnung/Bar → als Fliesstext-Notiz unter dem Diagramm (nicht im Diagramm, Lesbarkeit).

**C2 — Admin-Sequenzdiagramm** (`sequenceDiagram`) in `docs/bestellprozess.md`, neuer Abschnitt „Betreibersicht". Akteure: SH/Admin, FastAPI, SQLite, Brevo. Ablauf: Login → Dashboard → Bestelldetail öffnen → Statuswechsel (POST `/admin/bestellungen/{id}/status`) → DB-Update + Audit-Log → Kunden-Status-Mail via Brevo.

**C3 — Verteilungssicht** (`docs/arc42.md §7`) erweitern (entschieden: SH/Admin **und** Tigris):
- SH/Admin als zweiten Akteur mit `/admin/*`-Zugriff.
- Tigris-Backup-Knoten (Litestream-Replikation von SQLite → Tigris), konsistent mit A.

## Verifikation & Abschluss

1. `uv run --extra docs mkdocs build --strict` grün (tote Links / fehlende nav-Ziele).
2. Jedes neue/geänderte Mermaid-Diagramm separat validieren (Syntax, keine `@`/`\n`-Fallen).
3. `docs/user-stories-testplan.md` gegenchecken (Erwartung: unberührt — reine Doku-/Legal-Texte, keine App-Logik).
4. `docs/index.md` prüfen, ob die neue Legal-Seite im roten Faden erwähnt werden sollte.
5. PR mit Hinweis „Legal-Texte (A, B) mit SH gegenlesen". Issue #144: Punkte 1/4/5 abhaken, 2/3 offen lassen.
