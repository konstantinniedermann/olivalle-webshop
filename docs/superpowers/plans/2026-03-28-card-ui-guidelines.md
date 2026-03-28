# Card-UI & Responsive Design Guidelines — Implementierungsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Card-UI & Responsive Design Prinzipien als laufende Richtlinie in die gemeinsame CLAUDE.md aufnehmen und ein GitHub Issue fuer die projektspezifische Umsetzung erstellen.

**Architecture:** Reine Dokumentationsaenderung — keine Code-Aenderungen. Neue Sektion in der uebergeordneten CLAUDE.md, plus ein GitHub Issue fuer die Olivalle-Umsetzung.

**Tech Stack:** Markdown, GitHub CLI

---

### Task 1: Design-Prinzipien in CLAUDE.md einfuegen

**Files:**
- Modify: `/Users/KN/Dropbox/Privat/CAS/projekte/CLAUDE.md` (nach Zeile 86, vor `## Dokumentation`)

- [ ] **Step 1: Sektion einfuegen**

Zwischen der Architektur-Checkliste und der Dokumentation-Sektion einfuegen:

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

- [ ] **Step 2: Pruefen**

Datei oeffnen und sicherstellen dass die Sektion korrekt platziert ist (nach Architektur-Checkliste, vor Dokumentation).

- [ ] **Step 3: Commit**

```bash
git add /Users/KN/Dropbox/Privat/CAS/projekte/CLAUDE.md
git commit -m "docs: Design-Prinzipien (Card-UI, Mobile-first) in gemeinsame CLAUDE.md"
```

---

### Task 2: GitHub Issue fuer Olivalle-Umsetzung erstellen

- [ ] **Step 1: Issue erstellen**

```bash
gh issue create \
  --title "Card-UI & Responsive Design auf bestehendes Frontend anwenden" \
  --body "$(cat <<'EOF'
## Kontext
Design-Prinzipien (Card-UI, Mobile-first) wurden in die gemeinsame CLAUDE.md aufgenommen (ALL-CARD).
Dieses Issue deckt die konkrete Umsetzung im Olivalle-Frontend ab.

## Aufgaben
- [ ] Produktkarten aufwerten: Schatten, Hover-Effekte, konsistente Abstände
- [ ] Responsive Breakpoints prüfen: Mobile → Tablet → Desktop
- [ ] Warenkorb und Checkout prüfen: profitieren diese Seiten von Card-UI?
- [ ] Tailwind-spezifische Utility-Klassen in projektspezifische CLAUDE.md dokumentieren

## Referenz
- Design-Prinzipien: `../CLAUDE.md` → Sektion "Design-Prinzipien"
- Spec: `docs/superpowers/specs/2026-03-28-card-ui-guidelines-design.md`
EOF
)" \
  --label "phase-1"
```

- [ ] **Step 2: Issue-Nummer notieren und Abhaengigkeiten prüfen**

Pruefen ob das neue Issue andere Issues blockt oder von anderen geblockt wird.

- [ ] **Step 3: Commit der Spec und Plan**

```bash
git add docs/superpowers/specs/2026-03-28-card-ui-guidelines-design.md
git add docs/superpowers/plans/2026-03-28-card-ui-guidelines.md
git commit -m "docs: Design Spec und Plan fuer Card-UI Guidelines (ALL-CARD)"
```

---

### Task 3: ALL-CARD in TODO.md als erledigt markieren

- [ ] **Step 1: TODO.md aktualisieren**

`ALL-CARD` aus der "Allgemein"-Tabelle in die "Erledigt"-Tabelle verschieben mit Datum 2026-03-28.

- [ ] **Step 2: Commit**

```bash
git add /Users/KN/Dropbox/Privat/CAS/projekte/TODO.md
git commit -m "docs: ALL-CARD als erledigt markieren"
```
