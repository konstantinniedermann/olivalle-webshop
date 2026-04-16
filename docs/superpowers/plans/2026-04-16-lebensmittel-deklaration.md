# Lebensmittel-Deklaration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Pflichtangaben gemäss Art. 39 LIV auf der Website ergänzen (Sachbezeichnung, Güteklasse, Nährwerte, Bio-Code, Lagerhinweis).

**Architecture:** Reine Template-Änderungen in Jinja2. Bio-Code wird in die bestehende OLIPE-Kachel integriert, alle anderen Pflichtangaben kommen in eine neue kombinierte Kachel „Produktinformation" auf `ueber-das-oel.html`. Der Link auf `produkte.html` wird angepasst, damit die Deklaration klar erreichbar ist.

**Tech Stack:** Jinja2, Tailwind CSS, pytest

---

### File Structure

| Datei | Aktion | Verantwortung |
|---|---|---|
| `tests/test_api_seiten.py` | Modify | Neue Tests für Deklarations-Inhalte |
| `tests/test_api_produkte.py` | Modify | Bestehenden Link-Test anpassen |
| `templates/ueber-das-oel.html` | Modify | OLIPE-Kachel + neue Produktinformation-Kachel |
| `templates/produkte.html` | Modify | Link-Text anpassen |

---

### Task 1: Tests schreiben

**Files:**
- Modify: `tests/test_api_seiten.py`
- Modify: `tests/test_api_produkte.py`

- [ ] **Step 1: Tests für Deklaration in test_api_seiten.py ergänzen**

Am Ende von `tests/test_api_seiten.py` folgende Tests hinzufügen:

```python
def test_ueber_das_oel_bio_code(client):
    """Die OLIPE-Kachel enthält den Bio-Kontrollstellen-Code."""
    response = client.get("/ueber-das-oel")
    assert "ES-ECO-001-AN" in response.text
    assert "C.A.A.E." in response.text


def test_ueber_das_oel_produktinformation(client):
    """Die Seite enthält die Kachel 'Produktinformation'."""
    response = client.get("/ueber-das-oel")
    assert "Produktinformation" in response.text


def test_ueber_das_oel_sachbezeichnung(client):
    """Sachbezeichnung ist auf der Seite deklariert."""
    response = client.get("/ueber-das-oel")
    assert "Natives Olivenöl extra" in response.text


def test_ueber_das_oel_gueteklasse(client):
    """Güteklasse-Pflichtsatz ist vorhanden."""
    response = client.get("/ueber-das-oel")
    assert "ausschliesslich mit mechanischen Verfahren" in response.text


def test_ueber_das_oel_naehrwerte(client):
    """Nährwerttabelle ist vorhanden mit allen Pflichtangaben."""
    response = client.get("/ueber-das-oel")
    assert "Nährwerte pro 100 g" in response.text
    assert "3700 kJ" in response.text
    assert "900 kcal" in response.text
    assert "Vitamin E" in response.text


def test_ueber_das_oel_lagerhinweis(client):
    """Lagerhinweis ist vorhanden."""
    response = client.get("/ueber-das-oel")
    assert "Kühl und dunkel lagern" in response.text
```

- [ ] **Step 2: Bestehenden Link-Test in test_api_produkte.py anpassen**

In `tests/test_api_produkte.py` den Test `test_startseite_teaser` (Zeile 82–88) anpassen — der prüft aktuell auf „Mehr erfahren", wir ändern den Link-Text:

```python
def test_startseite_teaser(client):
    """Startseite zeigt kurzen Teaser mit Link zu 'Über das Öl'."""
    response = client.get("/")
    assert "Biologisches Olivenöl extra virgen" in response.text
    assert 'href="/ueber-das-oel"' in response.text
    assert "Nährwerte" in response.text
```

- [ ] **Step 3: Tests ausführen — müssen fehlschlagen**

Run: `make test` oder `python -m pytest tests/test_api_seiten.py tests/test_api_produkte.py -v`

Expected: 7 FAIL (6 neue Tests + 1 angepasster Test), Rest PASS.

- [ ] **Step 4: Commit**

```bash
git add tests/test_api_seiten.py tests/test_api_produkte.py
git commit -m "test: failing tests für Lebensmittel-Deklaration (#100)"
```

---

### Task 2: OLIPE-Kachel anpassen + Produktinformation-Kachel hinzufügen

**Files:**
- Modify: `templates/ueber-das-oel.html:30-62`

- [ ] **Step 1: Bio-Code in OLIPE-Kachel ergänzen**

In `templates/ueber-das-oel.html`, in der OLIPE-Kachel (Zeile 30–39), den Absatztext erweitern. Nach „…gelebte Praxis seit Jahrzehnten." einen Zeilenumbruch und den Bio-Code ergänzen:

```html
            <div class="bg-stone-900/75 backdrop-blur-[4px] rounded-lg p-6 border border-stone-600/15">
                <h2 class="font-display text-3xl text-accent mb-3">Die Kooperative OLIPE</h2>
                <p class="text-stone-200 leading-relaxed text-justify">
                    Rund 800 Bauernfamilien der Kooperative OLIPE arbeiten seit 1957
                    gemeinsam. Die Kooperative garantiert faire Preise für die Produzenten
                    und kontrolliert die gesamte Kette von der Ernte bis zur Abfüllung.
                    Bio-Zertifizierung und Nachhaltigkeit sind dabei keine Marketing-Begriffe,
                    sondern gelebte Praxis seit Jahrzehnten.
                </p>
                <p class="text-stone-400 text-sm mt-3">Bio-Kontrollstelle: C.A.A.E. · ES-ECO-001-AN</p>
            </div>
```

- [ ] **Step 2: Neue Kachel „Produktinformation" einfügen**

In `templates/ueber-das-oel.html`, nach der letzten Inhaltskachel („Von Andalusien in die Schweiz", Zeile 53–61) und vor dem CTA-Block (Zeile 63), folgende Kachel einfügen:

```html
            <div class="bg-stone-900/75 backdrop-blur-[4px] rounded-lg p-6 border border-stone-600/15">
                <h2 class="font-display text-3xl text-accent mb-3">Produktinformation</h2>
                <div class="text-stone-200 leading-relaxed space-y-2">
                    <p>
                        <span class="font-semibold text-stone-100">Sachbezeichnung:</span>
                        Natives Olivenöl extra (biologisch)
                    </p>
                    <blockquote class="border-l-2 border-accent pl-3 italic text-stone-400">
                        «Olivenöl höchster Qualität, direkt aus Oliven ausschliesslich
                        mit mechanischen Verfahren gewonnen.»
                    </blockquote>
                    <p>
                        <span class="font-semibold text-stone-100">Lagerung:</span>
                        Kühl und dunkel lagern, vor Licht schützen.
                    </p>
                </div>

                <hr class="border-stone-600/30 my-4">

                <h3 class="font-display text-2xl text-accent mb-3">Nährwerte pro 100 g</h3>
                <table class="w-full max-w-sm text-stone-200 text-sm">
                    <tbody>
                        <tr class="border-b border-stone-600/20">
                            <td class="py-2 font-semibold text-stone-100">Energie</td>
                            <td class="py-2 text-right">3700 kJ / 900 kcal</td>
                        </tr>
                        <tr class="border-b border-stone-600/20">
                            <td class="py-2 font-semibold text-stone-100">Fett</td>
                            <td class="py-2 text-right">100 g</td>
                        </tr>
                        <tr class="border-b border-stone-600/20">
                            <td class="py-2 pl-4 text-stone-400">davon gesättigte Fettsäuren</td>
                            <td class="py-2 text-right text-stone-400">16 g</td>
                        </tr>
                        <tr class="border-b border-stone-600/20">
                            <td class="py-2 font-semibold text-stone-100">Kohlenhydrate</td>
                            <td class="py-2 text-right">0,0 g</td>
                        </tr>
                        <tr class="border-b border-stone-600/20">
                            <td class="py-2 pl-4 text-stone-400">davon Zucker</td>
                            <td class="py-2 text-right text-stone-400">0,0 g</td>
                        </tr>
                        <tr class="border-b border-stone-600/20">
                            <td class="py-2 font-semibold text-stone-100">Eiweiss</td>
                            <td class="py-2 text-right">0,0 g</td>
                        </tr>
                        <tr class="border-b border-stone-600/20">
                            <td class="py-2 font-semibold text-stone-100">Salz</td>
                            <td class="py-2 text-right">0,0 g</td>
                        </tr>
                        <tr>
                            <td class="py-2 font-semibold text-stone-100">Vitamin E</td>
                            <td class="py-2 text-right">20 mg (167% NRV*)</td>
                        </tr>
                    </tbody>
                </table>
                <p class="text-stone-500 text-xs mt-2">* NRV = Nährstoffreferenzwert</p>
            </div>
```

- [ ] **Step 3: Tests ausführen**

Run: `python -m pytest tests/test_api_seiten.py -v`

Expected: Alle Tests PASS (inkl. 6 neue).

- [ ] **Step 4: Commit**

```bash
git add templates/ueber-das-oel.html
git commit -m "feat: Lebensmittel-Deklaration auf Über-das-Öl-Seite (#100)"
```

---

### Task 3: Link auf Produktseite anpassen

**Files:**
- Modify: `templates/produkte.html:16`

- [ ] **Step 1: Link-Text anpassen**

In `templates/produkte.html`, Zeile 16, den bestehenden Link-Text ändern von:

```html
                <a href="/ueber-das-oel" class="text-accent hover:underline">Mehr erfahren →</a>
```

zu:

```html
                <a href="/ueber-das-oel" class="text-accent hover:underline">Mehr über das Öl erfahren — inkl. Nährwerte &amp; Deklaration →</a>
```

- [ ] **Step 2: Tests ausführen**

Run: `python -m pytest tests/test_api_produkte.py tests/test_api_seiten.py -v`

Expected: Alle Tests PASS.

- [ ] **Step 3: Gesamte Testsuite laufen lassen**

Run: `make test`

Expected: Alle Tests PASS, keine Regressionen.

- [ ] **Step 4: Commit**

```bash
git add templates/produkte.html
git commit -m "feat: Produktseite verlinkt auf Deklaration (#100)"
```

---

### Task 4: Visuell prüfen & abschliessen

- [ ] **Step 1: Dev-Server starten**

Run: `make run` (oder entsprechendes Kommando)

- [ ] **Step 2: Seiten im Browser prüfen**

1. `http://localhost:8000/ueber-das-oel` — OLIPE-Kachel hat Bio-Code, Produktinformation-Kachel sieht sauber aus (Tabelle, Zitat, Abstände)
2. `http://localhost:8000/` — Link-Text zeigt „inkl. Nährwerte & Deklaration", Link führt korrekt zu /ueber-das-oel
3. Mobile Ansicht prüfen (Browser DevTools, 375px) — Tabelle bricht nicht um, Kacheln stacken sauber

- [ ] **Step 3: Abschluss-Commit (falls visuelle Korrekturen nötig)**

Falls Tailwind-Klassen angepasst werden mussten:

```bash
git add templates/ueber-das-oel.html templates/produkte.html
git commit -m "fix: visuelle Korrekturen Deklaration (#100)"
```
