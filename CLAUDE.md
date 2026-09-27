# Olivalle Webshop — Claude Code Kontext

> Gemeinsame Arbeitsregeln (Workflow, Code-Qualität, Dokumentation) sind in `../CLAUDE.md` definiert.

> Für alle Aktionen → `make help` (zeigt alle verfügbaren Befehle)

## Über das Projekt
Webshop für "Olivalle" — Verkauf von biologischem Olivenöl (Import aus Andalusien, Spanien).
Wird für einen Freund (Auftraggeber/Inhaber) gebaut. Einzelunternehmer in der Schweiz.
Ersetzt den bisherigen manuellen Bestellprozess via Tally-Formular.

Private Infos (URLs, Zugangsdaten): siehe `NOTES.local.md` (nicht im Repo)

## Test-Strategie
**pytest** für Unit + Integration Tests. Mindestens abgedeckt: Bestelllogik, Stripe Webhook, API-Endpunkte.

## E-Mail-Dienst: Brevo (ehemals Sendinblue)
Für den Stakeholder: Bei ca. 100 Bestellungen/Mt bleibt man im Free Tier.
Entscheid dokumentiert in: `docs/adr-email-provider.md`

## Context-Scopes

Je nach Aufgabe nur den relevanten Scope laden — reduziert Token-Verbrauch und hält den Fokus:

| Scope | Pfade | Wann verwenden |
|---|---|---|
| App | `app/`, `templates/`, `static/`, `CLAUDE.md` | FastAPI, Jinja2, Stripe Webhook |
| Vollständig | alles | Architektur- und Querschnittsthemen |

## Architektur-Regeln
- Alles in FastAPI — kein separates Frontend-Framework
- UI-Texte auf Deutsch (CH)

## Status & Aufgaben
> **Maintenance-Modus seit 2026-07-11:** Olivalle wird nicht mehr aktiv weiterentwickelt. Das Projekt läuft produktiv und wird bei Bedarf gewartet (Security-Patches, Betriebsstörungen), aber es sind keine neuen Features geplant. Offene Issues sind optionale Phase-4-Themen. Aktives Hauptprojekt ist [Munica](../Munica/).

## Dokumentation
- Übersicht aller Dokumente: `docs/index.md`
- Architektur: `docs/arc42.md`
- Historische Artefakte: `docs/archiv/` (per `.claudeignore` aus Auto-Context ausgeschlossen, bei Bedarf explizit lesen)

## Git & GitHub
- Branch-Strategie: `main` (produktiv) — Feature-Branches via PR

## Wichtige Hinweise
- Schweizer Rechtslage: MWST, Datenschutz (DSG)
- Stripe unterstützt Twint nativ in der Schweiz
