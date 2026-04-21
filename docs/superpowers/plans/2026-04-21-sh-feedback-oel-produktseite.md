# SH-Feedback Öl-/Produktseite — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** SH-Textfeedback (4 Öl-Seiten-Kacheln) und Hintergrundwechsel der Produktseite auf `olive-tree-hero.jpg` umsetzen, mit Regression-Tests für beide Seiten.

**Architecture:** Pure Template-Änderungen in zwei Jinja2-Files. Keine neuen Dateien, keine Logik, keine neuen Assets. Tests in bestehenden pytest-Modulen (`tests/test_api_seiten.py`, `tests/test_api_produkte.py`) erweitern bzw. anpassen.

**Tech Stack:** FastAPI · Jinja2 · Tailwind CSS (lokal gebaut, kein Rebuild nötig) · pytest

**Issue:** #102 — Spec: `docs/superpowers/specs/2026-04-21-sh-feedback-oel-produktseite-design.md`

---

## File Structure

| Datei | Aktion | Verantwortlichkeit |
|---|---|---|
| `templates/ueber-das-oel.html` | Modify (Zeilen 19-61) | 4 Text-Kacheln: Titel ohne Artikel, neue Haupttexte; Bio-Kontrollstelle-Zeile unverändert |
| `templates/produkte.html` | Modify (Zeile 6) | Inline-`style` `background-image`-URL auf `olive-tree-hero.jpg` |
| `tests/test_api_seiten.py` | Modify | `test_ueber_das_oel_inhalt` an neue Titel anpassen + 6 neue Assertions für Haupttext-Snippets und Typo-Regression |
| `tests/test_api_produkte.py` | Modify | Neue Testfunktion für Hintergrund-Regression |

Keine neuen Dateien.

---

## Task 1: Failing Tests für Öl-Seite

**Files:**
- Modify: `tests/test_api_seiten.py:7-14` (Funktion `test_ueber_das_oel_inhalt`)
- Modify: `tests/test_api_seiten.py` (neue Test-Funktionen am Ende anhängen)

- [ ] **Step 1: Bestehenden Test `test_ueber_das_oel_inhalt` anpassen**

Öffne `tests/test_api_seiten.py` und ersetze Zeilen 7-14 durch:

```python
def test_ueber_das_oel_inhalt(client):
    """Die Seite enthält die vier Abschnitte mit neuen Titeln (ohne bestimmten Artikel)."""
    response = client.get("/ueber-das-oel")
    assert "Unser Olivenöl" in response.text
    # Neue Titel ohne bestimmten Artikel (SH-Feedback 2026-04-21)
    assert ">Herkunft<" in response.text
    assert ">Kooperative OLIPE<" in response.text
    assert ">Qualität<" in response.text
    assert "Von Andalusien in die Schweiz" in response.text
    # Alte Titel mit "Die" sind entfernt
    assert ">Die Herkunft<" not in response.text
    assert ">Die Kooperative OLIPE<" not in response.text
    assert ">Die Qualität<" not in response.text
```

- [ ] **Step 2: Neue Test-Funktionen am Ende von `tests/test_api_seiten.py` anhängen**

Füge am Ende der Datei (nach Zeile 73, nach `test_ueber_das_oel_lagerhinweis`) hinzu:

```python


def test_ueber_das_oel_herkunft_text(client):
    """Der Herkunft-Text enthält die vom SH überarbeitete Formulierung."""
    response = client.get("/ueber-das-oel")
    assert "Nevadillo Blanco" in response.text
    assert "Berghainen" in response.text  # bewusst so gewählt (Hain am Berg)
    assert "Sierra Morena" in response.text
    assert "von Hand gearbeitet und geerntet" in response.text


def test_ueber_das_oel_kooperative_vollname(client):
    """Die Kooperative-Kachel nennt den ausformulierten Namen."""
    response = client.get("/ueber-das-oel")
    assert "Olivarera Los Pedroches" in response.text
    assert "800 Bauernfamilien" in response.text
    assert "Produzierenden" in response.text


def test_ueber_das_oel_typo_korrigiert(client):
    """Der Typo 'jahrzentelang' ist zu 'jahrzehntelang' korrigiert."""
    response = client.get("/ueber-das-oel")
    assert "jahrzehntelang" in response.text
    assert "jahrzentelang" not in response.text


def test_ueber_das_oel_qualitaet_text(client):
    """Der Qualität-Text beschreibt das Geschmacksprofil."""
    response = client.get("/ueber-das-oel")
    assert "12 bis 24 Stunden" in response.text
    assert "Polyphenolgehalt" in response.text
    assert "fruchtig, leicht bitter" in response.text
    assert "angenehmen Schärfe im Abgang" in response.text


def test_ueber_das_oel_andalusien_text(client):
    """Der Andalusien-Text endet mit dem neuen SH-Schlusssatz."""
    response = client.get("/ueber-das-oel")
    assert "Generalimporteur" in response.text
    assert "Ohne Zwischenhändler, ohne Umwege" in response.text
    assert "Leidenschaft für ein wunderbares Produkt" in response.text
```

- [ ] **Step 3: Tests ausführen — MÜSSEN FAILEN**

```bash
cd /Users/KN/Dropbox/Privat/CAS/projekte/olivalle
uv run pytest tests/test_api_seiten.py -v
```

Erwartung: exakt diese 5 Tests schlagen fehl (rot):
- `test_ueber_das_oel_inhalt` — alte `>Die Herkunft<` etc. noch im HTML, neue `>Herkunft<` fehlt
- `test_ueber_das_oel_herkunft_text` — alter Text endet mit "wie seit Generationen", neue Assertion "von Hand gearbeitet und geerntet" fehlt
- `test_ueber_das_oel_kooperative_vollname` — "Olivarera Los Pedroches" fehlt noch
- `test_ueber_das_oel_typo_korrigiert` — alter Text enthält weder "jahrzehntelang" noch "jahrzentelang" (alt: "gelebte Praxis seit Jahrzehnten"), die Positiv-Assertion schlägt fehl
- `test_ueber_das_oel_andalusien_text` — alter Text endet mit "ehrliches Handwerk", neue Assertion "wunderbares Produkt" fehlt

Diese Tests sind bereits grün (kein Handlungsbedarf, schützen nach Impl. vor Regression):
- `test_ueber_das_oel_qualitaet_text` — alter und neuer Text sind inhaltlich identisch, alle Snippets bereits enthalten

- [ ] **Step 4: Commit der failing Tests**

```bash
git -C /Users/KN/Dropbox/Privat/CAS/projekte/olivalle add tests/test_api_seiten.py
git -C /Users/KN/Dropbox/Privat/CAS/projekte/olivalle commit -m "$(cat <<'EOF'
test: failing Tests für SH-Textfeedback Öl-Seite (#102)

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Öl-Seiten-Texte aktualisieren

**Files:**
- Modify: `templates/ueber-das-oel.html:19-61` (4 Kachel-Inhalte)

- [ ] **Step 1: Kachel 1 (Herkunft) ersetzen**

In `templates/ueber-das-oel.html`, ersetze Zeilen 19-27:

```html
                <h2 class="font-display text-3xl text-accent mb-3">Die Herkunft</h2>
                <p class="text-stone-200 leading-relaxed text-justify">
                    Die Oliven der Sorte Nevadillo Blanco wachsen in den Berghainen der
                    Sierra Morena bei Córdoba. Die Region ist geprägt von heissen Sommern,
                    milden Wintern und kargen Böden — ideale Bedingungen für aromatische
                    Oliven mit hohem Ölgehalt. Die Bäume stehen oft an steilen Hängen,
                    wo maschinelle Ernte unmöglich ist. Hier wird von Hand gearbeitet,
                    wie seit Generationen.
                </p>
```

durch:

```html
                <h2 class="font-display text-3xl text-accent mb-3">Herkunft</h2>
                <p class="text-stone-200 leading-relaxed text-justify">
                    Die Oliven der Sorte Nevadillo Blanco wachsen in den Berghainen der
                    Sierra Morena bei Córdoba. Die Region ist geprägt von heissen Sommern,
                    milden Wintern und kargen Böden — ideale Bedingungen für aromatische
                    Oliven mit hohem Ölgehalt. Die Bäume stehen oft an steilen Hängen,
                    wo maschinelle Ernte unmöglich ist. Hier wird seit Generationen von
                    Hand gearbeitet und geerntet.
                </p>
```

- [ ] **Step 2: Kachel 2 (Kooperative OLIPE) ersetzen**

Ersetze Zeilen 31-38 (h2 + p) durch:

```html
                <h2 class="font-display text-3xl text-accent mb-3">Kooperative OLIPE</h2>
                <p class="text-stone-200 leading-relaxed text-justify">
                    Seit 1957 arbeiten rund 800 Bauernfamilien gemeinsam im Namen der
                    Kooperative Olivarera Los Pedroches (OLIPE). Die Kooperative garantiert
                    faire Preise für die Produzierenden und kontrolliert die gesamte Kette
                    von der Ernte bis zur Abfüllung des Öls. Bio-Zertifizierung und
                    Nachhaltigkeit sind dabei keine Marketing-Begriffe, sondern
                    jahrzehntelang gelebte Praxis.
                </p>
```

Die Zeile `<p class="text-stone-400 text-sm mt-3">Bio-Kontrollstelle: C.A.A.E. · ES-ECO-001-AN</p>` (Zeile 39 alt) **bleibt unverändert** direkt darunter.

- [ ] **Step 3: Kachel 3 (Qualität) ersetzen**

Ersetze Zeilen 43-51 (h2 + p) durch:

```html
                <h2 class="font-display text-3xl text-accent mb-3">Qualität</h2>
                <p class="text-stone-200 leading-relaxed text-justify">
                    Innerhalb von 12 bis 24 Stunden nach der Ernte werden die Oliven
                    schonend kalt gepresst. Diese schnelle Verarbeitung bewahrt einen
                    besonders hohen Polyphenolgehalt — natürliche Antioxidantien, die
                    das Öl nicht nur gesund, sondern auch geschmacklich einzigartig machen.
                    Das Ergebnis: fruchtig, leicht bitter und mit einer angenehmen Schärfe
                    im Abgang.
                </p>
```

(Inhaltlich identisch zum aktuellen Text — nur der Titel wurde geändert. Der SH hat den Text nochmal geschickt, unverändert. Wir lassen ihn so.)

- [ ] **Step 4: Kachel 4 (Von Andalusien in die Schweiz) ersetzen**

Ersetze Zeilen 55-61 (nur p, h2 bleibt) durch:

```html
                <h2 class="font-display text-3xl text-accent mb-3">Von Andalusien in die Schweiz</h2>
                <p class="text-stone-200 leading-relaxed text-justify">
                    Seit rund 20 Jahren bringen wir dieses Olivenöl als Generalimporteur
                    direkt von Andalusien in die Schweiz. Ohne Zwischenhändler, ohne Umwege.
                    Jede Flasche erzählt die Geschichte einer Landschaft, einer Gemeinschaft
                    und einer Leidenschaft für ein wunderbares Produkt.
                </p>
```

- [ ] **Step 5: Tests ausführen — MÜSSEN GRÜN SEIN**

```bash
cd /Users/KN/Dropbox/Privat/CAS/projekte/olivalle
uv run pytest tests/test_api_seiten.py -v
```

Erwartung: alle 16 Tests in der Datei sind grün (11 bestehende + 5 neue).

Falls ein Test rot: Fehlermeldung lesen, Template-Änderung prüfen (Tippfehler, Whitespace), erst weiter wenn alles grün.

- [ ] **Step 6: Commit Implementierung**

```bash
git -C /Users/KN/Dropbox/Privat/CAS/projekte/olivalle add templates/ueber-das-oel.html
git -C /Users/KN/Dropbox/Privat/CAS/projekte/olivalle commit -m "$(cat <<'EOF'
feat: Öl-Seiten-Texte gemäss SH-Feedback aktualisiert (#102)

- Kachel-Titel ohne bestimmten Artikel ("Die Herkunft" → "Herkunft" etc.)
- Herkunft, Kooperative OLIPE, Qualität, Andalusien mit SH-Text ersetzt
- Kooperative nennt ausformulierten Namen "Olivarera Los Pedroches"
- Typo "jahrzentelang" → "jahrzehntelang" korrigiert
- Bio-Kontrollstelle-Zeile (rechtlich) unverändert

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Failing Test für Produktseiten-Hintergrund

**Files:**
- Modify: `tests/test_api_produkte.py` (neue Testfunktion am Ende)

- [ ] **Step 1: Test am Ende von `tests/test_api_produkte.py` anhängen**

Öffne die Datei und hänge am Ende an:

```python


def test_startseite_hintergrund_olivenbaum(client):
    """Die Produktseite nutzt den Olivenbaum-Hintergrund (SH-Feedback 2026-04-21)."""
    response = client.get("/")
    assert "backgrounds/olive-tree-hero.jpg" in response.text
    # Vorheriger Terracotta-Hintergrund ist ersetzt
    assert "backgrounds/terracotta-texture.webp" not in response.text
```

- [ ] **Step 2: Test ausführen — MUSS FAILEN**

```bash
cd /Users/KN/Dropbox/Privat/CAS/projekte/olivalle
uv run pytest tests/test_api_produkte.py::test_startseite_hintergrund_olivenbaum -v
```

Erwartung: FAIL — der Test findet noch `terracotta-texture.webp` im HTML.

- [ ] **Step 3: Commit des failing Tests**

```bash
git -C /Users/KN/Dropbox/Privat/CAS/projekte/olivalle add tests/test_api_produkte.py
git -C /Users/KN/Dropbox/Privat/CAS/projekte/olivalle commit -m "$(cat <<'EOF'
test: failing Test für Produktseiten-Hintergrund (#102)

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: Produktseiten-Hintergrund wechseln

**Files:**
- Modify: `templates/produkte.html:6`

- [ ] **Step 1: Inline-Style-URL in `templates/produkte.html` austauschen**

Ersetze in Zeile 6:

```html
     style="background-image: url('/static/images/backgrounds/terracotta-texture.webp');">
```

durch:

```html
     style="background-image: url('/static/images/backgrounds/olive-tree-hero.jpg');">
```

- [ ] **Step 2: Test ausführen — MUSS GRÜN SEIN**

```bash
cd /Users/KN/Dropbox/Privat/CAS/projekte/olivalle
uv run pytest tests/test_api_produkte.py::test_startseite_hintergrund_olivenbaum -v
```

Erwartung: PASS.

- [ ] **Step 3: Alle Tests laufen lassen — Regression-Check**

```bash
cd /Users/KN/Dropbox/Privat/CAS/projekte/olivalle
uv run pytest -q
```

Erwartung: alle bestehenden Tests weiterhin grün (keine Regression in Checkout, Admin, Bestellzyklus etc.).

- [ ] **Step 4: Commit Implementierung**

```bash
git -C /Users/KN/Dropbox/Privat/CAS/projekte/olivalle add templates/produkte.html
git -C /Users/KN/Dropbox/Privat/CAS/projekte/olivalle commit -m "$(cat <<'EOF'
feat: Produktseiten-Hintergrund auf Olivenbaum-Motiv (#102)

Stil der Produktseite harmonisiert mit "Über das Öl"-Seite
gemäss SH-Feedback. olive-tree-hero.jpg statt terracotta-texture.webp.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: Manueller Smoke-Test (Browser)

**Files:** keine Änderungen — reiner Verifikationsschritt.

- [ ] **Step 1: Dev-Server starten**

```bash
cd /Users/KN/Dropbox/Privat/CAS/projekte/olivalle
make dev
```

Erwartung: Server läuft auf `http://localhost:8000` (oder wie in `make help` dokumentiert).

- [ ] **Step 2: Produktseite (`/`) visuell prüfen**

Im Browser öffnen: `http://localhost:8000/`

Prüfen:
- [ ] Olivenbaum-Hintergrund sichtbar (kein Terracotta mehr)
- [ ] Produktkarten lesbar auf neuem Hintergrund (Kontrast durch Overlay OK)
- [ ] Hover-Effekt auf Karten funktioniert
- [ ] Mobile-Ansicht (DevTools → Mobile Preview): weiterhin lesbar

- [ ] **Step 3: Öl-Seite (`/ueber-das-oel`) visuell prüfen**

Im Browser öffnen: `http://localhost:8000/ueber-das-oel`

Prüfen:
- [ ] Titel ohne "Die": "Herkunft", "Kooperative OLIPE", "Qualität"
- [ ] Haupttexte komplett ausgetauscht (Stichprobe: "Olivarera Los Pedroches", "fruchtig, leicht bitter", "wunderbares Produkt")
- [ ] Kein "jahrzentelang" mehr, aber "jahrzehntelang" vorhanden
- [ ] Bio-Kontrollstellen-Zeile (C.A.A.E. · ES-ECO-001-AN) weiterhin da
- [ ] Produktinformation-Kachel + Nährwerte unverändert
- [ ] CTA "Zu unseren Produkten →" funktioniert

- [ ] **Step 4: Dev-Server beenden**

Strg+C im Terminal, wo `make dev` läuft.

- [ ] **Step 5: Falls visuelle Korrekturen nötig waren: nacharbeiten**

Falls die Smoke-Tests Probleme aufdecken (z.B. Kontrast, Zeilenumbrüche):
- Fix im Template nachziehen
- Tests erneut laufen lassen (`uv run pytest -q`)
- Commit mit `fix:`-Präfix und `(#102)`-Suffix

Falls alles passt: keine weitere Aktion nötig.

---

## Task 6: Issue schliessen & Abschluss

**Files:** keine — GitHub-Issue-Management.

- [ ] **Step 1: Push to main**

```bash
git -C /Users/KN/Dropbox/Privat/CAS/projekte/olivalle push origin main
```

Erwartung: 4 neue Commits auf `origin/main` (Task 1 Test-Commit, Task 2 Feat-Commit, Task 3 Test-Commit, Task 4 Feat-Commit, evtl. Fix-Commits aus Task 5).

- [ ] **Step 2: Issue-Checklisten abhaken**

Im Browser: https://github.com/konstantinniedermann/olivalle-webshop/issues/102

Alle Checkboxen im Issue-Body abhaken. Kommentar nach folgendem Template posten (per Web-UI oder `gh issue comment 102`):

```
Umgesetzt:
- Texte Öl-Seite (4 Kacheln, Titel ohne Artikel, Typo gefixt)
- Hintergrund Produktseite auf olive-tree-hero.jpg
- 16 Tests grün (5 neue für SH-Feedback)
- Smoke-Test lokal bestanden

Commits:
- feat: Öl-Seiten-Texte gemäss SH-Feedback aktualisiert
- feat: Produktseiten-Hintergrund auf Olivenbaum-Motiv
```

- [ ] **Step 3: Issue schliessen**

```bash
gh issue close 102 --repo konstantinniedermann/olivalle-webshop --comment "Umgesetzt und live. Spec: docs/superpowers/specs/2026-04-21-sh-feedback-oel-produktseite-design.md, Plan: docs/superpowers/plans/2026-04-21-sh-feedback-oel-produktseite.md"
```

- [ ] **Step 4: Deployment verifizieren (fly.io)**

Fly-CI deployt automatisch bei Push auf main (siehe `.github/workflows/*`). Nach ~2-3 Minuten verifizieren:

```bash
curl -s https://olivalle.ch/ueber-das-oel | grep -c "Olivarera Los Pedroches"
# Erwartung: 1

curl -s https://olivalle.ch/ | grep -c "olive-tree-hero.jpg"
# Erwartung: mindestens 1
```

Falls beide Checks > 0 zurückgeben: Live-Deployment erfolgreich.

---

## Zusammenfassung Commits

Am Ende des Plans stehen diese Commits auf main:

1. `test: failing Tests für SH-Textfeedback Öl-Seite (#102)`
2. `feat: Öl-Seiten-Texte gemäss SH-Feedback aktualisiert (#102)`
3. `test: failing Test für Produktseiten-Hintergrund (#102)`
4. `feat: Produktseiten-Hintergrund auf Olivenbaum-Motiv (#102)`
5. (Optional) `fix: …` falls Smoke-Test Nachbesserungen erfordert

Plus der bereits gemachte Spec-Commit: `docs: Design-Spec für SH-Feedback Öl-/Produktseite (#102)`.

---

## Was NICHT Teil dieses Plans ist

- Tailwind CSS Rebuild (nicht nötig, Inline-Style)
- Neue Assets (olive-tree-hero.jpg existiert bereits)
- Löschen von `terracotta-texture.webp` (bleibt im Repo für Rollback)
- Änderungen an Produktinformation-Kachel, CTA, Navigation, Admin-Bereich, E-Mail-Templates
- Neuer Feature-Branch (konsistent zu letzten Commits auf main: #100 wurde ebenfalls direkt auf main umgesetzt)
