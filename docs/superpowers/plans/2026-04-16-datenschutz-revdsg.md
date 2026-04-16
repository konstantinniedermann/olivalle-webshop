# Datenschutzerklärung revDSG-konform ergänzen — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Die Datenschutzerklärung um 7 revDSG-konforme Ergänzungen erweitern (Issue #69).

**Architecture:** Reine Template-Änderung in `templates/datenschutz.html`. Kein Backend-Code betroffen. Tests prüfen, dass die neuen Abschnitte im HTML gerendert werden.

**Tech Stack:** Jinja2-Template, pytest mit FastAPI TestClient

---

### Task 1: Failing Tests für neue Datenschutz-Inhalte schreiben

**Files:**
- Create: `tests/test_datenschutz.py`

- [ ] **Step 1: Test-Datei erstellen**

```python
def test_datenschutz_status(client):
    """Die Datenschutzseite ist erreichbar."""
    response = client.get("/datenschutz")
    assert response.status_code == 200


def test_datenschutz_verantwortlich(client):
    """Abschnitt 'Verantwortlich' mit Link zum Impressum."""
    response = client.get("/datenschutz")
    assert "Verantwortlich" in response.text
    assert "/impressum" in response.text


def test_datenschutz_rechtsgrundlage(client):
    """Zweck-Abschnitt nennt Kaufvertrag als Rechtsgrundlage."""
    response = client.get("/datenschutz")
    assert "Kaufvertrag" in response.text


def test_datenschutz_ausland(client):
    """Hinweis auf Datenbekanntgabe in die USA (Stripe)."""
    response = client.get("/datenschutz")
    assert "Bekanntgabe ins Ausland" in response.text
    assert "Standardvertragsklauseln" in response.text


def test_datenschutz_stripe_cookies(client):
    """Stripe Fraud-Detection-Cookies erwähnt."""
    response = client.get("/datenschutz")
    assert "Betrugserkennung" in response.text


def test_datenschutz_server_logs(client):
    """Abschnitt Server-Logs vorhanden."""
    response = client.get("/datenschutz")
    assert "Server-Logs" in response.text
    assert "IP-Adresse" in response.text


def test_datenschutz_datenherausgabe(client):
    """Recht auf Datenherausgabe (Art. 28 DSG) aufgeführt."""
    response = client.get("/datenschutz")
    assert "Datenherausgabe" in response.text
    assert "Art. 28 DSG" in response.text


def test_datenschutz_stand_datum(client):
    """Stand-Datum am Ende der Seite."""
    response = client.get("/datenschutz")
    assert "Stand: 16. April 2026" in response.text
```

- [ ] **Step 2: Tests ausführen — sicherstellen, dass sie fehlschlagen**

Run: `python -m pytest tests/test_datenschutz.py -v`
Expected: 1 PASS (`test_datenschutz_status`), 7 FAIL (alle inhaltlichen Tests)

- [ ] **Step 3: Commit**

```bash
git add tests/test_datenschutz.py
git commit -m "test: failing Tests für revDSG-Datenschutzergänzungen (#69)"
```

---

### Task 2: Template-Änderungen implementieren

**Files:**
- Modify: `templates/datenschutz.html`

- [ ] **Step 1: Abschnitt "Verantwortlich" nach Einleitung einfügen**

Nach dem Einleitung-`</p>` (Zeile 18) einfügen:

```html
            <h2 class="font-display text-3xl text-accent mb-3 mt-8">Verantwortlich</h2>
            <p class="text-stone-200 leading-relaxed">
                Angaben zur verantwortlichen Stelle finden Sie in unserem
                <a href="/impressum" class="text-accent hover:underline">Impressum</a>.
            </p>
```

- [ ] **Step 2: Rechtsgrundlage im Zweck-Abschnitt ergänzen**

Nach der bestehenden `</ul>` im Zweck-Abschnitt (Zeile 41) einfügen:

```html
            <p class="text-stone-200 leading-relaxed mt-3 text-justify">
                Die Datenbearbeitung erfolgt zur Erfüllung des Kaufvertrags sowie zur
                Wahrung unserer berechtigten Interessen (z.B. Betrugsprävention, Fehleranalyse).
            </p>
```

- [ ] **Step 3: Bekanntgabe ins Ausland im Drittanbieter-Abschnitt ergänzen**

Nach dem bestehenden Absatz "Diese Anbieter verarbeiten Daten..." (Zeile 79) einfügen:

```html
            <p class="text-stone-200 leading-relaxed mt-3 text-justify">
                <strong>Bekanntgabe ins Ausland:</strong> Stripe verarbeitet Zahlungsdaten
                teilweise in den USA. Der Datenschutz wird durch Standardvertragsklauseln
                (Standard Contractual Clauses) sichergestellt.
            </p>
```

- [ ] **Step 4: Stripe-Cookies im Cookie-Abschnitt ergänzen**

Nach dem bestehenden Cookie-Absatz (Zeile 86) einfügen:

```html
            <p class="text-stone-200 leading-relaxed mt-3 text-justify">
                Stripe setzt zudem eigene Cookies zur Betrugserkennung (Fraud Detection).
                Diese Cookies sind technisch notwendig für die sichere Zahlungsabwicklung.
            </p>
```

- [ ] **Step 5: Neuen Abschnitt "Server-Logs" nach Cookies einfügen**

Nach dem erweiterten Cookie-Abschnitt einfügen:

```html
            <h2 class="font-display text-3xl text-accent mb-3 mt-8">Server-Logs</h2>
            <p class="text-stone-200 leading-relaxed text-justify">
                Beim Besuch unserer Website werden automatisch folgende Daten in
                Server-Logs gespeichert: IP-Adresse, Zeitpunkt des Zugriffs, aufgerufene
                Seite und verwendeter Browser. Diese Daten dienen der Sicherstellung des
                Betriebs und der Fehleranalyse. Sie werden nicht mit anderen Daten
                zusammengeführt.
            </p>
```

- [ ] **Step 6: Recht auf Datenherausgabe in "Ihre Rechte" ergänzen**

Nach dem bestehenden Löschungs-`</li>` (Zeile 103) einfügen:

```html
                <li><strong>Datenherausgabe</strong> — Ihre Daten in einem gängigen elektronischen Format (z.B. PDF) zu erhalten (Art. 28 DSG)</li>
```

- [ ] **Step 7: Stand-Datum am Ende einfügen**

Nach dem Änderungen-Absatz (Zeile 116), vor dem schliessenden `</div>`, einfügen:

```html
            <p class="text-stone-400 text-sm mt-8">
                Stand: 16. April 2026
            </p>
```

- [ ] **Step 8: Tests ausführen — alle müssen grün sein**

Run: `python -m pytest tests/test_datenschutz.py -v`
Expected: 8 PASS

- [ ] **Step 9: Commit**

```bash
git add templates/datenschutz.html
git commit -m "feat: Datenschutzerklärung revDSG-konform ergänzt (#69)"
```

---

### Task 3: Visuelle Überprüfung und Abschluss

- [ ] **Step 1: Dev-Server starten und Seite prüfen**

Run: `make dev` (oder `uvicorn app.main:app --reload`)

Prüfen unter `http://localhost:8000/datenschutz`:
- [ ] Abschnitt "Verantwortlich" sichtbar nach Einleitung, Link zu /impressum funktioniert
- [ ] Rechtsgrundlage "Kaufvertrag" im Zweck-Abschnitt
- [ ] "Bekanntgabe ins Ausland" im Drittanbieter-Abschnitt
- [ ] Stripe-Cookies erwähnt
- [ ] Server-Logs-Abschnitt vorhanden
- [ ] Datenherausgabe in der Rechte-Liste
- [ ] Stand-Datum am Ende der Seite
- [ ] Layout und Abstände konsistent mit den anderen Abschnitten

- [ ] **Step 2: Gesamte Test-Suite ausführen**

Run: `python -m pytest -v`
Expected: Alle bestehenden Tests weiterhin grün, keine Regressionen.

- [ ] **Step 3: GitHub Issue #69 schliessen**

```bash
gh issue close 69 --comment "Datenschutzerklärung revDSG-konform ergänzt. Alle 8 SH-Punkte umgesetzt."
```
