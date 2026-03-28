# Design Spec: Card-UI & Responsive Design Guidelines (ALL-CARD)

**Datum:** 2026-03-28
**Quelle:** PV2, Folie 41 (Werner Schaefer, FFHS)
**Scope:** Alle Projekte (übergeordnete CLAUDE.md)

## Kontext

Die Vorlesung PV2 hat Card-UI-Prinzipien und Mobile-first als Best Practice für UI-Entwicklung vorgestellt. Diese sollen als laufende Design-Richtlinie in die gemeinsame `CLAUDE.md` aufgenommen werden, damit sie bei jeder UI-Arbeit in allen Projekten beachtet werden.

## Entscheidungen

### Was wird gemacht

1. **Neue Sektion `## Design-Prinzipien`** in `/Users/KN/Dropbox/Privat/CAS/projekte/CLAUDE.md`
2. Platzierung: nach der Architektur-Checkliste, vor Dokumentation
3. Format: Fliesstext-Richtlinie mit Bullet Points (kein Checklisten-Format)
4. Technologieunabhängig — keine framework-spezifischen Klassen

### Was wird NICHT gemacht

- Kein Umbau des bestehenden Olivalle-Frontends (eigenes GitHub Issue)
- Keine Tailwind-spezifischen Empfehlungen in der gemeinsamen CLAUDE.md
- Keine projektspezifische CLAUDE.md-Anpassung (folgt im Issue)

### Inhalt der Sektion

```markdown
## Design-Prinzipien (bei UI-Arbeit beachten)

Card-UI & Responsive Design (Quelle: PV2, Folie 41):
- Eine Sache pro Karte — nicht überladen
- Rastersystem verwenden (CSS Grid)
- Abstände und Ausrichtung konsistent halten
- Karten anklickbar und interaktiv gestalten (Hover-Feedback)
- Schatten für visuelle Tiefe
- Mobile-first: Mobile → Tablet → Desktop
```

## Folgaktion

GitHub Issue erstellen fuer die konkrete Umsetzung der Guidelines im Olivalle-Projekt (Produktkarten aufwerten, Warenkorb/Checkout pruefen).
