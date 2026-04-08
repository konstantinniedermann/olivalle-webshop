# Doc- & Projektstruktur-Cleanup nach v1.0

**Datum:** 2026-04-08
**Status:** Approved
**Kontext:** Olivalle ist seit v1.0 (2026-04-08) live. Viele Dokumente in `docs/` und im Repo-Root sind historische Artefakte aus Phase 0–3 und werden bei jeder Session unnötig in den Context gezogen. Ziel: Aufräumen ohne Informationsverlust.

## Ziele

- Aktive Referenz-Doku (Architektur, ADRs, Domain, Recht) bleibt unverändert in `docs/` erreichbar
- Historische Artefakte (einmalige Setup-Anleitungen, abgeschlossene Test-/Smoke-Protokolle, Evaluationen) wandern nach `docs/archiv/`
- `docs/archiv/` bleibt im Repo (Git-History + MkDocs-Build möglich), wird aber per `.claudeignore` aus dem Auto-Context ausgeschlossen
- Repo-Root entrümpeln (PDF-Idee, obsoletes Helper-Skript)

## Out of Scope

- MEMORY-Index Cleanup → separate Session danach
- CLAUDE.md Redundanz-Check zwischen parent/projekt → separat
- Impressum gegen Live-Stand abgleichen → separat

## Sicherheits-Vorabprüfung (durchgeführt 2026-04-08)

✅ Keine echten Secrets (Stripe-, Brevo-Keys, Passwörter) in getrackten Dateien
✅ `.env`, `*.db`, `NOTES.local.md`, `.DS_Store`, `*.code-workspace` sauber gitignored
✅ `testprotokoll.md` ist generische Checkliste — keine echten Kundendaten
⚠️ `docs/legal/impressum.md` enthält gesetzlich erforderliche SH-Daten (Name, Adresse) — bewusst öffentlich, kein Leak
⚠️ `olivalle.olten@outlook.com` in ~20 Dateien — offizielle Geschäfts-E-Mail aus Impressum, unkritisch

## Klassifikation

### Bleibt aktiv in `docs/`
- `arc42.md`, `systemarchitektur.md`, `datenbankschema.md` — Architektur-Referenz
- `bestellprozess.md` — Domain-Logik
- `adr-domain-registrar.md`, `adr-email-provider.md` — ADRs (Konvention: ADRs bleiben)
- `produkttexte.md` — laufender Content
- `roadmap.md`, `index.md` — Übersicht
- `security.md` — laufende Referenz
- `user-stories-testplan.md` — laufend gepflegt (Memory-Regel)
- `datenschutz.md`, `legal/` — rechtlich, dauerhaft relevant
- `superpowers/` — laufender Workflow-Output

### Wird nach `docs/archiv/` verschoben
- `anleitung-stripe-setup.md` (+ `.pdf`) — einmaliges Setup, erledigt
- `email-provider-evaluation.md` (+ `.pdf`) — Entscheidung in ADR konserviert
- `go-live-smoke-tests.md` (+ `.pdf`) — Go-Live durch
- `sh-testanleitung.md` (+ `.pdf`) — SH-Testphase abgeschlossen
- `testprotokoll.md` — manuelle Pre-Go-Live Checkliste, Artefakt
- `CAS_Projektidee_Olivalle.pdf` (aus Repo-Root) — initiale Projektidee

### Root-Aufräumen
- `docs-serve.command` → löschen. `make docs` erledigt dasselbe (`uv run mkdocs serve`); der einzige Unterschied (`--open`) ist verzichtbar

## Konfig-Anpassungen

- **`.claudeignore`** ergänzen: `docs/archiv/` (PDFs sind dort ohnehin schon gematcht, aber explizit doppelt sicher)
- **`mkdocs.yml`** prüfen: Die zu archivierenden Dateien stehen aktuell **nicht** in der `nav`. Keine Änderung nötig. (MkDocs `material` zeigt nur explizit gelistete Dateien — archivierte werden also auch im Build nicht prominent.)
- **`docs/index.md`** prüfen und ggf. Verweise auf archivierte Dateien aktualisieren oder entfernen

## Ablauf

1. `mkdir docs/archiv`
2. `git mv` für die 6 Doc-Dateien (jeweils `.md` + ggf. `.pdf`) nach `docs/archiv/`
3. `git mv CAS_Projektidee_Olivalle.pdf docs/archiv/`
4. `git rm docs-serve.command`
5. `.claudeignore` ergänzen
6. `docs/index.md` auf tote Links prüfen, anpassen
7. Smoke-Check: `make docs` startet ohne Fehler, `pytest` grün
8. Commit: `docs: historische Artefakte nach docs/archiv/ verschieben`
9. PR oder direkt auf main (Entscheidung im Implementierungsschritt)

## Akzeptanzkriterien

- [ ] `docs/archiv/` existiert mit den gelisteten 6 Dateien (+ PDFs)
- [ ] `CAS_Projektidee_Olivalle.pdf` nicht mehr im Root
- [ ] `docs-serve.command` gelöscht
- [ ] `.claudeignore` enthält `docs/archiv/`
- [ ] `docs/index.md` enthält keine toten Links
- [ ] `make docs` läuft fehlerfrei
- [ ] `pytest` grün
- [ ] Sauberer Commit mit `docs:`-Präfix
