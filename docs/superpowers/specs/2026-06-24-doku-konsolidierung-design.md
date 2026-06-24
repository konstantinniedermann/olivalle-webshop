# Design: Doku-Konsolidierung Olivalle (CAS-Abgabe)

**Datum:** 2026-06-24
**Status:** In Review
**Kontext:** Olivalle ist Teil der CAS-AISE-Projektabgabe (Frist 2026-07-06). Es ist
**kein** formaler Projektbericht/SAD nötig — eine gute, für Dritte nachvollziehbare
Repo-Dokumentation reicht. Bewerter: wschaefer42 (Werner Schäfer). Das Repo ist
**öffentlich**, der Bewerter braucht daher keinen Sonderzugriff; er wird die Doku
laut eigener Aussage nur überfliegen.

## Ziel

Die Projektdokumentation auf einen einheitlichen, sauberen, für Dritte
nachvollziehbaren Stand bringen. Roter Faden: **Problem → Lösung → Architektur →
Validierung → Betrieb**. Ergebnis ist eine über GitHub Pages gehostete, klickbare
MkDocs-Site, auf die die README prominent verweist.

## Nicht-Ziele (Scope-Guard)

Bewusst **nicht** Teil dieser Arbeit (gegen Scope-Creep — die Ist-Aufnahme-Agenten
haben hier überzogen):

- Keine 10 neuen ADRs — nur **eine** konsolidierte Tech-Stack-ADR.
- Kein erzwungenes CHANGELOG.md.
- Kein groß angelegtes Security-Audit-Projekt (`security.md` wird nur geschärft).
- Keine Automatisierung des jährlichen Restore-Tests.
- Keine Code-Änderungen an der Applikation (reine Doku-/Config-Arbeit).

## Ist-Stand (verifiziert)

Gut vorhanden: README (solide), `arc42.md` (Rückgrat, 3 Diagramme), 3 ADRs
(Backup/Domain/E-Mail), 2 Runbooks, MkDocs **bereits eingerichtet** (Material +
mermaid2, `make docs` läuft, Deps im `docs`-Extra). Secrets sauber (`.env`,
`*.db`, `NOTES.local.md` gitignored, nichts Sensibles getrackt). Working Tree clean,
`main` in sync mit origin.

Verifizierte Mängel:

1. **Datenbankschema veraltet** — `datenbankschema.md` zeigt 4 Tabellen; real sind es
   7: zusätzlich `admin_log` (Migration 002), `rabattcodes` + `code_einloesungen`
   (003) sowie die Aktionspreis-Spalten auf `produkte` (per Python-Migration in
   `app/database.py: _add_column_if_not_exists()`).
2. **Drei konkurrierende Doku-Indizes** — `mkdocs.yml` nav ≠ `docs/index.md` ≠
   README-Tabelle. mkdocs vermisst Backup-ADR + beide Runbooks; nav-Link
   `produkttexte.md` ist tot (Datei liegt in `archiv/`).
3. **ADR-Lücke** — Kern-Tech-Entscheidungen (FastAPI/Python, SQLite, Stripe, fly.io,
   server-rendered Jinja statt SPA) sind nur in arc42 erzählt, nirgends als
   nachvollziehbare Entscheidung festgehalten.
4. **Diagramm-Dokus zu mager** — `bestellprozess.md`/`systemarchitektur.md` sind reine
   Diagramme ohne Zweck-Satz/Element-Erklärung; QR-Rechnung, Rabatt/Aktion und
   Fehler-/Webhook-Pfade fehlen.
5. **roadmap.md obsolet** — linearer Pre-Launch-Plan ohne Done-Markierungen.
6. **Kein roter Faden** — `index.md` ist eine flache Tabelle statt Narrativ-Einstieg.

## Ziel-Struktur

`docs/index.md` wird vom Link-Verzeichnis zur **erzählten Landing-Page** (zugleich
MkDocs-Startseite): Problem → Lösung → „so liest du diese Doku" → Lesereihenfolge.

Navigation (MkDocs nav = `docs/index.md`, eine einzige Wahrheit), nach rotem Faden:

| Gruppe | Inhalt |
|---|---|
| **Übersicht** | `index.md` (Narrativ-Einstieg) |
| **Architektur** | `arc42.md` · `systemarchitektur.md` · `datenbankschema.md` · `bestellprozess.md` |
| **Entscheidungen (ADRs)** | `adr-index.md` (neu) · `adr-tech-stack.md` (neu) · `adr-backup-strategie.md` · `adr-domain-registrar.md` · `adr-email-provider.md` |
| **Validierung** | `user-stories-testplan.md` · `security.md` |
| **Betrieb** | `runbook-restore.md` · `runbook-incident.md` · `datenschutz.md` (intern) |
| **Rechtliches** | `legal/agb.md` · `legal/datenschutz.md` · `legal/impressum.md` |
| **Projekt** | `projekt-status.md` (umgebaut aus `roadmap.md`) |
| **Archiv** | `archiv/…` |

## Umsetzungsplan pro Artefakt

### Neu erstellen
- **`docs/adr-tech-stack.md`** — konsolidierte ADR über alle Kern-Entscheidungen
  (Sprache/Framework: Python+FastAPI; DB: SQLite; Payments: Stripe; QR: swiss-qr-bill;
  Hosting: fly.io; UI: server-rendered Jinja statt SPA). Klassisches ADR-Format mit
  Kontext, Optionen, Entscheidung, verworfenen Alternativen, Konsequenzen.
- **`docs/adr-index.md`** — Tabellarischer ADR-Überblick (ID, Titel, Status, Datum).
- **GitHub Action `.github/workflows/docs.yml`** — baut MkDocs bei Push auf `main`
  und deployed nach GitHub Pages. SHA-gepinnte Actions (Projektregel).

### Überarbeiten
- **`docs/index.md`** — Narrativ-Einstieg (roter Faden), Lesereihenfolge,
  einzige kanonische Doku-Übersicht.
- **`docs/datenbankschema.md`** — ER-Diagramm auf 7 Tabellen + Aktionspreis-Spalten
  korrigieren; Enum-Werte (status, zahlungsart, versandart) als Prosa ergänzen;
  Zweck-Satz + Element-Erklärung.
- **`docs/systemarchitektur.md`** — Zweck-Satz + Element-Erklärung zum Diagramm;
  Litestream/Tigris-Backup-Pfad sichtbar machen.
- **`docs/bestellprozess.md`** — Diagramm um QR-Rechnung, Rabatt/Aktion und
  Stripe-Fehler-/Webhook-Retry-Pfad ergänzen; Zweck-Satz + Element-Erklärung.
- **`docs/arc42.md`** — Produkttabelle/Stand prüfen; Verweis auf neue Tech-Stack-ADR
  statt Inline-Erzählung; GitHub-Issue-Referenzen entschärfen wo sinnvoll.
- **`roadmap.md` → `docs/projekt-status.md`** — Phasen als abgeschlossen markieren (✓)
  + kurzer Ausblick auf offene Issues. (Datei umbenennen, Links nachziehen.)
- **`README.md`** — Doku-Tabelle (Zeilen ~104–114) auf einen prominenten Verweis zur
  Doku-Site + `docs/index.md` reduzieren. Tech-Stack/Schnellstart/Deployment bleiben.
- **`mkdocs.yml`** — nav mit `docs/index.md` synchronisieren; toten `produkttexte`-Link
  entfernen; Backup-ADR + Runbooks + ADR-Index aufnehmen.
- **`security.md`** — knapp schärfen: bestehende Schutzmaßnahmen (CSRF, Rate-Limiting,
  Security-Header, bcrypt-Login) faktisch auflisten statt nur XSS-Audit-Notiz. Kein
  Vollaudit.

### Diagramm-Regel
Jedes Mermaid-Diagramm erhält: (1) einen **Zweck-Satz** davor („Dieses Diagramm
zeigt …") und (2) eine **Element-Erklärung** danach (kurze Liste/Absatz, was die
Knoten/Beziehungen bedeuten). Keine `\n` in Mermaid-Node-Labels (Projektregel).

## Validierung

- `make docs` baut die Site lokal fehlerfrei (alle nav-Einträge existieren, keine
  Build-Warnungen zu fehlenden Seiten).
- Alle internen Doku-Links auflösbar (grep nach `](*.md)` → Ziel existiert).
- GitHub Action baut + deployed grün; Doku-URL erreichbar.
- `make lint-all` + `make test` bleiben grün (keine Code-Regression).
- Konsistenz-Check: README ↔ index.md ↔ mkdocs.yml nennen dieselbe Doku-Menge.

## CAS-Abgabe-Teil (Punkt 4 der Aufgabe)

- **Collaborator-Invite entfällt** — Repo ist öffentlich, Bewerter braucht keinen
  Zugriff. (Korrigiert das ursprüngliche Briefing „Repo bleibt privat".)
- Sicherstellen: `main` aktuell gepusht, Working Tree clean.
- Secrets-Check final bestätigen (bereits verifiziert: nichts Sensibles getrackt).
- README verweist klar auf die gehostete Doku-Site (Einstieg für den Bewerter).

## Abschluss

GitHub-Issues/Doku/Repo konsistent, Working Tree clean, Stand zusammenfassen, neue
Session vorschlagen.
