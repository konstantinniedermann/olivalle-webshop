# Startseite als Produktseite + Warenkorb-Feedback — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Startseite zum Produkt-Showcase mit Variante-B-Text umbauen, visuelles Feedback beim Hinzufügen zum Warenkorb (Button-Animation + Flyout) einführen.

**Architecture:** Template `produkte.html` bekommt einen Hero-Bereich mit statischem Produkttext. `cart.js` wird um Animation- und Flyout-Logik erweitert. Flyout-HTML lebt in `base.html` neben dem Warenkorb-Link. Produktbeschreibungen in der DB werden aktualisiert.

**Tech Stack:** Jinja2, Tailwind CSS (CDN), Vanilla JS, SQLite

**Spec:** `docs/superpowers/specs/2026-03-29-startseite-warenkorb-feedback-design.md`

---

## File Map

| Datei | Aktion | Verantwortung |
|---|---|---|
| `migrations/001_initial.sql` | Modify (Zeilen 44-47) | Produktbeschreibungen aktualisieren |
| `templates/produkte.html` | Modify (komplett) | Hero-Bereich + Gebinde-Karten |
| `templates/base.html` | Modify (Zeilen 25-27) | Flyout-HTML + Warenkorb-Icon-Bereich |
| `static/js/cart.js` | Modify | `addToCart()` → Button-Animation + Flyout |
| `tests/test_api_produkte.py` | Modify | Tests an neues Layout anpassen |

---

### Task 1: Produktbeschreibungen in DB aktualisieren

**Files:**
- Modify: `migrations/001_initial.sql:44-47`
- Test: `tests/test_api_produkte.py`

- [ ] **Step 1: Write failing test — Startseite enthält Produktbeschreibungen**

In `tests/test_api_produkte.py` den bestehenden Test `test_startseite_enthaelt_produkte` erweitern:

```python
def test_startseite_enthaelt_produkte(client):
    response = client.get("/")
    assert "Olivenöl 250ml" in response.text
    assert "CHF 8" in response.text
    assert "ideal zum Kennenlernen" in response.text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `make test` oder `pytest tests/test_api_produkte.py::test_startseite_enthaelt_produkte -v`
Expected: FAIL — "ideal zum Kennenlernen" not found (aktuell steht "kleine Flasche")

- [ ] **Step 3: Update migration seed data**

In `migrations/001_initial.sql` die Zeilen 44-47 ersetzen:

```sql
-- Seed: Olivalle-Produkte
INSERT OR REPLACE INTO produkte (id, name, menge_ml, preis_chf, beschreibung, bild_pfad) VALUES
    (1, 'Olivenöl 250ml', 250, 8.00, 'Die kleine Flasche ist ideal zum Kennenlernen, als Geschenk oder für Feinkostläden, die Olivalle ins Sortiment aufnehmen möchten.', 'products/olivalle-250ml.jpeg'),
    (2, 'Olivenöl 750ml', 750, 18.00, 'Der Klassiker für den täglichen Gebrauch in der Küche. Ob zum Verfeinern von Salaten, zum Braten oder einfach mit frischem Brot — diese Flasche gehört auf jeden Tisch.', 'products/olivalle-750ml.jpeg'),
    (3, 'Olivenöl 3l Kanister', 3000, 50.00, 'Für Liebhaber, die nicht genug bekommen, und für Gastronomiebetriebe, die auf Qualität setzen: Der Kanister bietet das beste Preis-Leistungs-Verhältnis.', 'products/olivalle-3l.jpeg');
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_api_produkte.py::test_startseite_enthaelt_produkte -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add migrations/001_initial.sql tests/test_api_produkte.py
git commit -m "feat: Produktbeschreibungen aus produkttexte.md in Seed-Daten übernehmen"
```

---

### Task 2: Startseite mit Hero-Bereich und Variante-B-Text

**Files:**
- Modify: `templates/produkte.html` (komplett umbauen)
- Modify: `tests/test_api_produkte.py`

- [ ] **Step 1: Write failing test — Startseite enthält Variante-B-Text**

Neuen Test in `tests/test_api_produkte.py` hinzufügen:

```python
def test_startseite_hero_variante_b(client):
    """Startseite zeigt den Variante-B Produkttext im Hero-Bereich."""
    response = client.get("/")
    assert "Kooperative OLIPE" in response.text
    assert "Nevadillo Blanco" in response.text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_api_produkte.py::test_startseite_hero_variante_b -v`
Expected: FAIL — "Kooperative OLIPE" not in response

- [ ] **Step 3: Rebuild `produkte.html` with Hero section**

Kompletter Inhalt von `templates/produkte.html`:

```html
{% extends "base.html" %}
{% block title %}Olivalle — Biologisches Olivenöl{% endblock %}
{% block content %}
{# Hero-Bereich: Variante-B Produkttext #}
<section class="mb-12">
    <h1 class="font-display text-5xl font-bold text-accent mb-6">Unser Olivenöl</h1>
    <div class="bg-stone-700 rounded-lg p-6 shadow-md">
        <p class="text-stone-200 leading-relaxed text-lg">
            Olivalle steht für biologisches Olivenöl extra virgen aus dem Herzen
            Andalusiens. Die Oliven der Sorte Nevadillo Blanco wachsen in den
            Berghainen der Sierra Morena bei Córdoba — gepflegt von rund 800
            Bauernfamilien der Kooperative OLIPE, die seit 1957 gemeinsam arbeiten.
            Innerhalb von 12 bis 24 Stunden nach der Ernte werden die Oliven schonend
            gepresst, was einen besonders hohen Polyphenolgehalt und ein intensives
            Aroma bewahrt. Das Ergebnis ist ein Öl mit Charakter: fruchtig, leicht
            bitter und mit einer angenehmen Schärfe im Abgang. Seit rund 20 Jahren
            bringen wir dieses Olivenöl als Generalimporteur direkt von Andalusien
            in die Schweiz. Jede Flasche erzählt die Geschichte einer Landschaft,
            einer Gemeinschaft und einer Leidenschaft für ehrliches Handwerk.
        </p>
    </div>
</section>

{# Gebinde-Auswahl #}
<section>
    <h2 class="font-display text-3xl font-bold text-accent mb-6">Unsere Gebinde</h2>
    <div class="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {% for produkt in produkte %}
        <div class="bg-stone-700 rounded-lg p-6 flex flex-col shadow-md hover:shadow-lg hover:-translate-y-1 transition-all duration-200">
            {% if produkt.bild_pfad %}
            <img src="/static/images/{{ produkt.bild_pfad }}" alt="{{ produkt.name }}"
                 class="w-full h-48 object-contain mb-4">
            {% endif %}
            <h3 class="font-display text-2xl font-bold text-accent">{{ produkt.name }}</h3>
            <p class="text-stone-300 mt-2 flex-1">{{ produkt.beschreibung }}</p>
            <div class="mt-4 flex items-center justify-between">
                <span class="text-xl font-bold">CHF {{ "%.2f"|format(produkt.preis_chf) }}</span>
                <button onclick="addToCart({{ produkt.id }}, '{{ produkt.name }}', {{ produkt.preis_chf }}, this)"
                        class="add-to-cart-btn bg-accent text-stone-900 px-4 py-2 rounded font-bold hover:bg-yellow-400 transition-colors">
                    In den Warenkorb
                </button>
            </div>
        </div>
        {% endfor %}
    </div>
</section>
{% endblock %}
```

Wichtig: Der `onclick` bekommt `this` als 4. Parameter — das brauchen wir für die Button-Animation in Task 3.

- [ ] **Step 4: Fix existing tests that check for old layout**

Der Test `test_produkte_responsive_grid` prüft `sm:grid-cols-2` und `lg:grid-cols-3` — die bleiben im neuen Template, also kein Update nötig.

Der Test `test_produkte_karten_hover` prüft `shadow-md`, `hover:shadow-lg`, `hover:-translate-y-1` — bleiben ebenfalls.

Run: `pytest tests/test_api_produkte.py -v`
Expected: Alle Tests PASS

- [ ] **Step 5: Commit**

```bash
git add templates/produkte.html tests/test_api_produkte.py
git commit -m "feat: Startseite mit Hero-Bereich und Variante-B Produkttext"
```

---

### Task 3: Button-Animation beim Hinzufügen

**Files:**
- Modify: `static/js/cart.js` (Funktion `addToCart` erweitern)

- [ ] **Step 1: Erweitere `addToCart()` um Button-Animation**

In `static/js/cart.js` die bestehende `addToCart`-Funktion ersetzen:

```javascript
function addToCart(id, name, price, buttonEl) {
    const cart = getCart();
    const existing = cart.find((item) => item.produkt_id === id);
    if (existing) {
        existing.menge += 1;
    } else {
        cart.push({ produkt_id: id, name: name, preis: price, menge: 1 });
    }
    saveCart(cart);

    // Button-Animation
    if (buttonEl) {
        const originalText = buttonEl.textContent;
        buttonEl.textContent = "Hinzugefügt \u2713";
        buttonEl.classList.remove("bg-accent", "hover:bg-yellow-400");
        buttonEl.classList.add("bg-green-600", "text-white");
        setTimeout(() => {
            buttonEl.textContent = originalText;
            buttonEl.classList.remove("bg-green-600", "text-white");
            buttonEl.classList.add("bg-accent", "hover:bg-yellow-400");
        }, 1000);
    }

    // Flyout anzeigen (wird in Task 4 implementiert)
    if (typeof showCartFlyout === "function") {
        setTimeout(() => showCartFlyout(), 300);
    }
}
```

- [ ] **Step 2: Manuell testen im Browser**

Run: `make run` (oder `uvicorn app.main:app --reload`)
1. Startseite öffnen
2. "In den Warenkorb" klicken
3. Button wird grün + "Hinzugefügt ✓" für 1 Sekunde
4. Danach zurück zu gelb + "In den Warenkorb"

- [ ] **Step 3: Commit**

```bash
git add static/js/cart.js
git commit -m "feat: Button-Animation beim Hinzufügen zum Warenkorb"
```

---

### Task 4: Mini-Warenkorb-Flyout

**Files:**
- Modify: `templates/base.html:22-28` (Flyout-HTML einfügen)
- Modify: `static/js/cart.js` (Flyout-Logik)

- [ ] **Step 1: Flyout-HTML in `base.html` einfügen**

Den Warenkorb-Link-Bereich (Zeilen 25-27) in `templates/base.html` ersetzen durch:

```html
            <div class="relative">
                <a href="/warenkorb" class="text-stone-300 hover:text-accent">
                    Warenkorb (<span id="cart-count">0</span>)
                </a>
                <div id="cart-flyout" class="hidden absolute right-0 top-full mt-2 w-72 bg-stone-700 rounded-lg shadow-lg border border-stone-600 z-50 p-4">
                    <div id="cart-flyout-items" class="text-sm space-y-2 mb-3"></div>
                    <div class="border-t border-stone-600 pt-2 flex justify-between font-bold text-sm">
                        <span>Total</span>
                        <span id="cart-flyout-total"></span>
                    </div>
                    <div class="mt-3 flex gap-2 text-sm">
                        <a href="/warenkorb" class="flex-1 text-center py-2 border border-stone-500 rounded hover:bg-stone-600 transition-colors">Warenkorb</a>
                        <a href="/checkout" class="flex-1 text-center py-2 bg-accent text-stone-900 rounded font-bold hover:bg-yellow-400 transition-colors">Zur Kasse</a>
                    </div>
                </div>
            </div>
```

- [ ] **Step 2: Flyout-Logik in `cart.js` hinzufügen**

Am Ende von `static/js/cart.js` (vor der `DOMContentLoaded`-Zeile) einfügen:

```javascript
let flyoutTimer = null;

function showCartFlyout() {
    const flyout = document.getElementById("cart-flyout");
    const itemsContainer = document.getElementById("cart-flyout-items");
    const totalEl = document.getElementById("cart-flyout-total");
    if (!flyout || !itemsContainer || !totalEl) return;

    const cart = getCart();
    if (cart.length === 0) return;

    // Inhalt rendern
    itemsContainer.innerHTML = cart
        .map(
            (item) =>
                `<div class="flex justify-between text-stone-200">
                    <span>${item.menge}× ${item.name}</span>
                    <span>CHF ${(item.preis * item.menge).toFixed(2)}</span>
                </div>`
        )
        .join("");
    totalEl.textContent = "CHF " + getCartTotal().toFixed(2);

    // Anzeigen
    flyout.classList.remove("hidden");

    // Timer: nach 2s automatisch schliessen
    if (flyoutTimer) clearTimeout(flyoutTimer);
    flyoutTimer = setTimeout(() => hideCartFlyout(), 2000);
}

function hideCartFlyout() {
    const flyout = document.getElementById("cart-flyout");
    if (flyout) flyout.classList.add("hidden");
    if (flyoutTimer) {
        clearTimeout(flyoutTimer);
        flyoutTimer = null;
    }
}

// Klick ausserhalb schliesst Flyout
document.addEventListener("click", (e) => {
    const flyout = document.getElementById("cart-flyout");
    if (flyout && !flyout.closest(".relative").contains(e.target)) {
        hideCartFlyout();
    }
});
```

- [ ] **Step 3: Write test — Flyout-HTML ist vorhanden**

Neuen Test in `tests/test_api_produkte.py`:

```python
def test_startseite_warenkorb_flyout(client):
    """Startseite enthält das Mini-Warenkorb-Flyout."""
    response = client.get("/")
    assert 'id="cart-flyout"' in response.text
    assert "Zur Kasse" in response.text
```

- [ ] **Step 4: Run all tests**

Run: `pytest tests/test_api_produkte.py -v`
Expected: Alle Tests PASS

- [ ] **Step 5: Manuell testen im Browser**

1. Startseite öffnen
2. "In den Warenkorb" klicken
3. Button wird grün (1s), dann erscheint Flyout (nach 300ms)
4. Flyout zeigt Produkt, Menge, Total, Links "Warenkorb" und "Zur Kasse"
5. Flyout schliesst sich nach 2 Sekunden automatisch
6. Alternativ: Klick ausserhalb schliesst Flyout sofort

- [ ] **Step 6: Commit**

```bash
git add templates/base.html static/js/cart.js tests/test_api_produkte.py
git commit -m "feat: Mini-Warenkorb-Flyout nach Hinzufügen mit 2s Auto-Close"
```

---

### Task 5: Gesamttest und Aufräumen

- [ ] **Step 1: Alle Tests laufen lassen**

Run: `make test` oder `pytest -v`
Expected: Alle Tests PASS

- [ ] **Step 2: Linter laufen lassen**

Run: `make lint` oder `ruff check app/ tests/`
Expected: Keine Fehler

- [ ] **Step 3: Manuell im Browser prüfen**

Checkliste:
- [ ] Startseite zeigt Hero mit Variante-B-Text
- [ ] Drei Gebinde-Karten mit neuen Beschreibungen
- [ ] Button-Animation funktioniert (grün → zurück)
- [ ] Flyout erscheint nach Hinzufügen
- [ ] Flyout schliesst nach 2s
- [ ] Flyout-Links "Warenkorb" und "Zur Kasse" funktionieren
- [ ] Mobile: Layout stapelt sich korrekt
- [ ] Warenkorb-Seite funktioniert weiterhin (+/- Buttons)
- [ ] Checkout-Flow unverändert

- [ ] **Step 4: Finaler Commit (falls Fixes nötig waren)**

```bash
git add -A
git commit -m "fix: Korrekturen nach manuellem Test"
```
