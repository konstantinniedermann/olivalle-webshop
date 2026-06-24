# Olivalle — Projektdokumentation

Webshop für biologisches Olivenöl aus Andalusien, live auf [olivalle.ch](https://olivalle.ch). Diese Dokumentation führt von der Problemstellung über die Lösung und Architektur bis zu Validierung und Betrieb.

## Das Projekt in einem Satz

Olivalle ersetzt einen manuellen Bestellprozess (Tally-Formular + manuelle Rechnungen) durch einen vollständigen Webshop mit Kartenzahlung/TWINT, automatischer Bestellbestätigung und Schweizer QR-Rechnung — gebaut für einen Einzelunternehmer im Rahmen des CAS AI-Supported Software Engineering (FFHS).

## So liest du diese Doku (roter Faden)

1. **Problem & Ziele** → [arc42 §1](arc42.md) — was sollte gelöst werden, für wen.
2. **Lösung & Architektur** → [arc42](arc42.md) (Gesamtbild), [Systemarchitektur](systemarchitektur.md) (Komponenten), [Datenbankschema](datenbankschema.md) (Daten), [Bestellprozess](bestellprozess.md) (Ablauf).
3. **Entscheidungen** → [ADR-Index](adr-index.md) — warum dieser Tech-Stack, dieses Backup, diese Anbieter.
4. **Validierung** → [User Stories & Testplan](user-stories-testplan.md), [Security-Referenz](security.md).
5. **Betrieb** → [CI/CD & Versionierung](ci-cd-und-versionierung.md), [Restore-Runbook](runbook-restore.md), [Incident-Runbook](runbook-incident.md), [Datenschutz (intern)](datenschutz.md).
6. **Prozess** → [Design-Entscheidungen & Specs](design-entscheidungen.md) — wie diese Lösung im agentischen Workflow entstanden ist (Specs + Pläne).

## Alle Dokumente

| Bereich | Dokument |
|---|---|
| **Architektur** | [arc42](arc42.md) · [Systemarchitektur](systemarchitektur.md) · [Datenbankschema](datenbankschema.md) · [Bestellprozess](bestellprozess.md) |
| **Entscheidungen** | [ADR-Index](adr-index.md) · [Tech-Stack](adr-tech-stack.md) · [Backup-Strategie](adr-backup-strategie.md) · [Domain-Registrar](adr-domain-registrar.md) · [E-Mail-Provider](adr-email-provider.md) |
| **Validierung** | [User Stories & Testplan](user-stories-testplan.md) · [Security](security.md) |
| **Betrieb** | [CI/CD & Versionierung](ci-cd-und-versionierung.md) · [Restore-Runbook](runbook-restore.md) · [Incident-Runbook](runbook-incident.md) · [Datenschutz (intern)](datenschutz.md) |
| **Rechtliches** | [AGB](legal/agb.md) · [Datenschutzerklärung](legal/datenschutz.md) · [Lebensmittel-Deklaration](legal/lebensmittel-deklaration.md) · [Impressum](legal/impressum.md) |
| **Projekt** | [Status & Historie](projekt-status.md) |
| **Prozess** | [Design-Entscheidungen & Specs](design-entscheidungen.md) |

> Historische Artefakte (Setup-Anleitungen, Go-Live-Protokolle, Implementierungspläne) liegen unter `docs/archiv/`.
