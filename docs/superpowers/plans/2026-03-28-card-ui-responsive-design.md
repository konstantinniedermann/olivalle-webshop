# Card-UI & Responsive Design Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Alle 4 Kundenseiten (Produkte, Warenkorb, Checkout, Bestätigung) auf Card-UI & Responsive Design umstellen (Issue #51).

**Architecture:** Reine Frontend-Änderungen in Jinja2-Templates und einer JS-Datei. Kein Backend-Code betroffen. Tailwind CSS via CDN, keine Build-Pipeline.

**Tech Stack:** Jinja2 Templates, Tailwind CSS (CDN), Vanilla JavaScript

---

## File Structure

| Datei | Aktion | Verantwortung |
|---|---|---|
| `templates/produkte.html` | Modify | Produktkarten: Schatten, Hover, Breakpoints |
| `templates/warenkorb.html` | Modify | Tabelle → Cards mit +/− Steuerung |
| `static/js/cart.js` | Modify | Neue Funktionen `increaseMenge` / `decreaseMenge` |
| `templates/checkout.html` | Modify | Sektionen als Cards, autocomplete, Optional-Hinweise |
| `templates/bestaetigung.html` | Modify | Zentrierte Card mit Häkchen-Icon |
| `tests/test_api_produkte.py` | Modify | Tests für neue CSS-Klassen und HTML-Struktur |

---

### Task 1: Produktkarten — Schatten, Hover, Responsive Breakpoints

**Files:**
- Modify: `templates/produkte.html:5-23`
- Test: `tests/test_api_produkte.py`

- [ ] **Step 1: Test schreiben — Responsive Grid-Klassen prüfen**

```python
# tests/test_api_produkte.py — am Ende anfügen

def test_produkte_responsive_grid(client):
    """Produktgrid nutzt stufenweise Breakpoints: 1 → 2 → 3 Spalten."""
    response = client.get("/")
    assert "sm:grid-cols-2" in response.text
    assert "lg:grid-cols-3" in response.text


def test_produkte_karten_hover(client):
    """Produktkarten haben Schatten und Hover-Effekte."""
    response = client.get("/")
    assert "shadow-md" in response.text
    assert "hover:shadow-lg" in response.text
    assert "hover:-translate-y-1" in response.text
```

- [ ] **Step 2: Tests ausführen — müssen fehlschlagen**

Run: `python -m pytest tests/test_api_produkte.py::test_produkte_responsive_grid tests/test_api_produkte.py::test_produkte_karten_hover -v`
Expected: FAIL — `sm:grid-cols-2` und `shadow-md` noch nicht im HTML

- [ ] **Step 3: Template anpassen**

`templates/produkte.html` — Grid und Karten-Klassen ändern:

```html
{% extends "base.html" %}
{% block title %}Produkte{% endblock %}
{% block content %}
<h1 class="font-display text-5xl font-bold text-accent mb-8">Unser Olivenöl</h1>
<div class="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
    {% for produkt in produkte %}
    <div class="bg-stone-700 rounded-lg p-6 flex flex-col shadow-md hover:shadow-lg hover:-translate-y-1 transition-all duration-200">
        {% if produkt.bild_pfad %}
        <img src="/static/images/{{ produkt.bild_pfad }}" alt="{{ produkt.name }}"
             class="w-full h-48 object-contain mb-4">
        {% endif %}
        <h2 class="font-display text-2xl font-bold text-accent">{{ produkt.name }}</h2>
        <p class="text-stone-300 mt-2 flex-1">{{ produkt.beschreibung }}</p>
        <div class="mt-4 flex items-center justify-between">
            <span class="text-xl font-bold">CHF {{ "%.2f"|format(produkt.preis_chf) }}</span>
            <button onclick="addToCart({{ produkt.id }}, '{{ produkt.name }}', {{ produkt.preis_chf }})"
                    class="bg-accent text-stone-900 px-4 py-2 rounded font-bold hover:bg-yellow-400 transition-colors">
                In den Warenkorb
            </button>
        </div>
    </div>
    {% endfor %}
</div>
{% endblock %}
```

Änderungen gegenüber aktuell:
- Grid: `md:grid-cols-3` → `sm:grid-cols-2 lg:grid-cols-3`
- Karten: `shadow-md hover:shadow-lg hover:-translate-y-1 transition-all duration-200` hinzugefügt
- Button: `transition-colors` hinzugefügt

- [ ] **Step 4: Tests ausführen — müssen bestehen**

Run: `python -m pytest tests/test_api_produkte.py -v`
Expected: alle PASS

- [ ] **Step 5: Commit**

```bash
git add templates/produkte.html tests/test_api_produkte.py
git commit -m "feat: Produktkarten mit Schatten, Hover und stufenweisen Breakpoints (#51)"
```

---

### Task 2: Warenkorb — Tabelle zu Cards mit +/− Steuerung

**Files:**
- Modify: `static/js/cart.js:29-37`
- Modify: `templates/warenkorb.html:1-65`
- Test: `tests/test_api_produkte.py`

- [ ] **Step 1: Test schreiben — Warenkorb-Seite nutzt Card-Struktur**

```python
# tests/test_api_produkte.py — am Ende anfügen

def test_warenkorb_card_struktur(client):
    """Warenkorb nutzt Card-basiertes Layout statt Tabelle."""
    response = client.get("/warenkorb")
    # Keine Tabelle mehr
    assert "<table" not in response.text
    assert "<thead" not in response.text
    # Card-Klassen vorhanden
    assert "cart-card" in response.text
```

- [ ] **Step 2: Tests ausführen — müssen fehlschlagen**

Run: `python -m pytest tests/test_api_produkte.py::test_warenkorb_card_struktur -v`
Expected: FAIL — `<table` ist noch im HTML

- [ ] **Step 3: cart.js erweitern — increaseMenge / decreaseMenge**

Zwei Hilfsfunktionen in `static/js/cart.js` hinzufügen, direkt nach der bestehenden `updateMenge`-Funktion (nach Zeile 37):

```javascript
function increaseMenge(id) {
    const cart = getCart();
    const item = cart.find((item) => item.produkt_id === id);
    if (item) {
        item.menge += 1;
        saveCart(cart);
        if (typeof renderCart === "function") renderCart();
    }
}

function decreaseMenge(id) {
    const cart = getCart();
    const item = cart.find((item) => item.produkt_id === id);
    if (item) {
        if (item.menge <= 1) {
            removeFromCart(id);
        } else {
            item.menge -= 1;
            saveCart(cart);
            if (typeof renderCart === "function") renderCart();
        }
    }
}
```

- [ ] **Step 4: warenkorb.html komplett ersetzen**

```html
{% extends "base.html" %}
{% block title %}Warenkorb{% endblock %}
{% block content %}
<h1 class="font-display text-5xl font-bold text-accent mb-8">Warenkorb</h1>
<div id="cart-content">
    <p class="text-stone-400">Dein Warenkorb ist leer.</p>
</div>
<template id="cart-template">
    <div class="flex flex-col gap-3" id="cart-items"></div>
    <div class="bg-stone-700 rounded-lg p-5 mt-4 text-right shadow-md">
        <p class="text-stone-400">Versandkosten: CHF <span id="versand">9.90</span></p>
        <p class="text-stone-400 text-sm">(Ab CHF 100 gratis Versand)</p>
        <p class="text-xl font-bold mt-2">Total: CHF <span id="cart-total">0.00</span></p>
        <a href="/checkout" class="inline-block mt-4 bg-accent text-stone-900 px-6 py-3 rounded font-bold hover:bg-yellow-400 transition-colors">
            Zur Kasse
        </a>
    </div>
</template>
<template id="cart-item-template">
    <div class="cart-card bg-stone-700 rounded-lg p-4 shadow-md flex items-center gap-4">
        <img class="cart-card-img w-16 h-16 object-contain bg-stone-800 rounded p-1 flex-shrink-0" src="" alt="">
        <div class="flex-1 min-w-0">
            <div class="cart-card-name font-semibold"></div>
            <div class="cart-card-unit text-stone-400 text-sm mt-1"></div>
        </div>
        <div class="flex items-center gap-4">
            <div class="flex items-center border border-stone-600 rounded overflow-hidden">
                <button class="qty-decrease bg-stone-800 hover:bg-stone-600 text-white w-8 h-8 flex items-center justify-center transition-colors">−</button>
                <span class="qty-value bg-stone-700 text-white w-9 h-8 flex items-center justify-center text-sm font-semibold border-x border-stone-600"></span>
                <button class="qty-increase bg-stone-800 hover:bg-stone-600 text-white w-8 h-8 flex items-center justify-center transition-colors">+</button>
            </div>
            <span class="cart-card-price font-bold min-w-[90px] text-right"></span>
            <button class="cart-card-remove text-red-400 hover:text-red-300 transition-colors">✕</button>
        </div>
    </div>
</template>
<script>
function renderCart() {
    const cart = getCart();
    const container = document.getElementById("cart-content");
    if (cart.length === 0) {
        container.innerHTML = '<p class="text-stone-400">Dein Warenkorb ist leer.</p>';
        return;
    }
    const tmpl = document.getElementById("cart-template").content.cloneNode(true);
    const itemsContainer = tmpl.querySelector("#cart-items");
    const itemTmpl = document.getElementById("cart-item-template");

    cart.forEach(item => {
        const card = itemTmpl.content.cloneNode(true);
        const img = card.querySelector(".cart-card-img");
        img.src = "/static/images/products/olivalle-" + getImageSlug(item.name) + ".jpeg";
        img.alt = item.name;
        card.querySelector(".cart-card-name").textContent = item.name;
        card.querySelector(".cart-card-unit").textContent = "CHF " + item.preis.toFixed(2) + " pro Stück";
        card.querySelector(".qty-value").textContent = item.menge;
        card.querySelector(".cart-card-price").textContent = "CHF " + (item.preis * item.menge).toFixed(2);
        card.querySelector(".qty-decrease").addEventListener("click", () => decreaseMenge(item.produkt_id));
        card.querySelector(".qty-increase").addEventListener("click", () => increaseMenge(item.produkt_id));
        card.querySelector(".cart-card-remove").addEventListener("click", () => removeFromCart(item.produkt_id));
        itemsContainer.appendChild(card);
    });

    const subtotal = getCartTotal();
    const versand = getVersandkosten(subtotal);
    tmpl.querySelector("#versand").textContent = versand.toFixed(2);
    tmpl.querySelector("#cart-total").textContent = (subtotal + versand).toFixed(2);
    container.innerHTML = "";
    container.appendChild(tmpl);
}

function getImageSlug(name) {
    if (name.includes("250")) return "250ml";
    if (name.includes("750")) return "750ml";
    if (name.includes("3")) return "3l";
    return "250ml";
}

document.addEventListener("DOMContentLoaded", renderCart);
</script>
{% endblock %}
```

Änderungen:
- Tabelle → Card-basiert mit `<template>` für einzelne Items
- +/− Buttons statt Number-Input (via `increaseMenge`/`decreaseMenge`)
- Produktbild links (über `getImageSlug` Mapping)
- Einzelpreis sichtbar ("CHF X.XX pro Stück")
- Summary als eigene Card unten
- Inline-Events durch `addEventListener` ersetzt (sicherer)

- [ ] **Step 5: Tests ausführen — müssen bestehen**

Run: `python -m pytest tests/test_api_produkte.py -v`
Expected: alle PASS

- [ ] **Step 6: Commit**

```bash
git add templates/warenkorb.html static/js/cart.js tests/test_api_produkte.py
git commit -m "feat: Warenkorb als Cards mit +/- Mengensteuerung und Produktbild (#51)"
```

---

### Task 3: Checkout — Cards, Autocomplete, Optional-Hinweise

**Files:**
- Modify: `templates/checkout.html:1-88`
- Test: `tests/test_api_produkte.py`

- [ ] **Step 1: Test schreiben — Checkout hat autocomplete und Card-Struktur**

```python
# tests/test_api_produkte.py — am Ende anfügen

def test_checkout_autocomplete(client):
    """Checkout-Formular hat autocomplete-Attribute für Browser-Autofill."""
    response = client.get("/checkout")
    assert 'autocomplete="given-name"' in response.text
    assert 'autocomplete="family-name"' in response.text
    assert 'autocomplete="email"' in response.text
    assert 'autocomplete="street-address"' in response.text
    assert 'autocomplete="postal-code"' in response.text
    assert 'autocomplete="address-level2"' in response.text


def test_checkout_optional_hinweise(client):
    """Optionale Felder sind als solche gekennzeichnet."""
    response = client.get("/checkout")
    assert "(optional)" in response.text


def test_checkout_card_sektionen(client):
    """Checkout-Sektionen sind als Cards gestaltet."""
    response = client.get("/checkout")
    assert response.text.count("bg-stone-700 rounded-lg") >= 3
```

- [ ] **Step 2: Tests ausführen — müssen fehlschlagen**

Run: `python -m pytest tests/test_api_produkte.py::test_checkout_autocomplete tests/test_api_produkte.py::test_checkout_optional_hinweise tests/test_api_produkte.py::test_checkout_card_sektionen -v`
Expected: FAIL

- [ ] **Step 3: checkout.html komplett ersetzen**

```html
{% extends "base.html" %}
{% block title %}Kasse{% endblock %}
{% block content %}
<h1 class="font-display text-5xl font-bold text-accent mb-8">Kasse</h1>
<form method="POST" action="/bestellen" id="checkout-form" class="max-w-lg space-y-6">
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
    <input type="hidden" name="cart_data" id="cart-data">

    <div class="bg-stone-700 rounded-lg p-6 shadow-md">
        <h2 class="text-xl font-bold mb-4">Lieferadresse</h2>
        <div class="grid grid-cols-2 gap-4">
            <div>
                <label class="block text-stone-400 text-sm mb-1">Vorname *</label>
                <input type="text" name="vorname" required autocomplete="given-name"
                       class="w-full bg-stone-800 border border-stone-600 rounded px-3 py-2">
            </div>
            <div>
                <label class="block text-stone-400 text-sm mb-1">Nachname *</label>
                <input type="text" name="nachname" required autocomplete="family-name"
                       class="w-full bg-stone-800 border border-stone-600 rounded px-3 py-2">
            </div>
            <div class="col-span-2">
                <label class="block text-stone-400 text-sm mb-1">E-Mail *</label>
                <input type="email" name="email" required autocomplete="email"
                       class="w-full bg-stone-800 border border-stone-600 rounded px-3 py-2">
            </div>
            <div class="col-span-2">
                <label class="block text-stone-400 text-sm mb-1">Strasse *</label>
                <input type="text" name="strasse" required autocomplete="street-address"
                       class="w-full bg-stone-800 border border-stone-600 rounded px-3 py-2">
            </div>
            <div>
                <label class="block text-stone-400 text-sm mb-1">PLZ *</label>
                <input type="text" name="plz" required pattern="[0-9]{4}" autocomplete="postal-code"
                       class="w-full bg-stone-800 border border-stone-600 rounded px-3 py-2">
            </div>
            <div>
                <label class="block text-stone-400 text-sm mb-1">Ort *</label>
                <input type="text" name="ort" required autocomplete="address-level2"
                       class="w-full bg-stone-800 border border-stone-600 rounded px-3 py-2">
            </div>
            <div class="col-span-2">
                <label class="block text-stone-400 text-sm mb-1">Telefon <span class="text-stone-500">(optional)</span></label>
                <input type="tel" name="telefon" autocomplete="tel"
                       class="w-full bg-stone-800 border border-stone-600 rounded px-3 py-2">
            </div>
        </div>
    </div>

    <div class="bg-stone-700 rounded-lg p-6 shadow-md">
        <h2 class="text-xl font-bold mb-4">Versand</h2>
        <div class="space-y-2">
            <label class="flex items-center gap-2">
                <input type="radio" name="versandart" value="versand" checked
                       class="text-accent"> Postversand (CHF 9.90, ab CHF 100 gratis)
            </label>
            <label class="flex items-center gap-2">
                <input type="radio" name="versandart" value="abholung"
                       class="text-accent"> Abholung vor Ort (Details per E-Mail)
            </label>
        </div>
    </div>

    <div class="bg-stone-700 rounded-lg p-6 shadow-md">
        <h2 class="text-xl font-bold mb-4">Zahlung</h2>
        <div class="space-y-2">
            <label class="flex items-center gap-2">
                <input type="radio" name="zahlungsart" value="stripe" checked
                       class="text-accent"> Twint / Kreditkarte (via Stripe)
            </label>
            <label class="flex items-center gap-2">
                <input type="radio" name="zahlungsart" value="rechnung"
                       class="text-accent"> Auf Rechnung (QR-Rechnung per E-Mail)
            </label>
        </div>
    </div>

    <div class="bg-stone-700 rounded-lg p-6 shadow-md">
        <h2 class="text-xl font-bold mb-4">Kommentar <span class="text-stone-500 text-base font-normal">(optional)</span></h2>
        <textarea name="kommentar" rows="3"
                  class="w-full bg-stone-800 border border-stone-600 rounded px-3 py-2"></textarea>
    </div>

    <button type="submit"
            class="w-full bg-accent text-stone-900 py-3 rounded font-bold text-lg hover:bg-yellow-400 transition-colors">
        Kostenpflichtig bestellen
    </button>
</form>
<script>
document.getElementById("checkout-form").addEventListener("submit", function() {
    document.getElementById("cart-data").value = JSON.stringify(getCart());
});
</script>
{% endblock %}
```

Änderungen:
- 4 Sektionen als Cards (`bg-stone-700 rounded-lg p-6 shadow-md`)
- `autocomplete`-Attribute auf allen Feldern
- "(optional)" bei Telefon und Kommentar
- `space-y-6` für konsistente Abstände zwischen Cards
- `transition-colors` auf Submit-Button

- [ ] **Step 4: Tests ausführen — müssen bestehen**

Run: `python -m pytest tests/test_api_produkte.py -v`
Expected: alle PASS

- [ ] **Step 5: Commit**

```bash
git add templates/checkout.html tests/test_api_produkte.py
git commit -m "feat: Checkout-Sektionen als Cards mit autocomplete und Optional-Hinweisen (#51)"
```

---

### Task 4: Bestätigungsseite — Zentrierte Card mit Häkchen

**Files:**
- Modify: `templates/bestaetigung.html:1-16`
- Test: `tests/test_api_produkte.py`

- [ ] **Step 1: Test schreiben — Bestätigung nutzt Card**

```python
# tests/test_api_produkte.py — am Ende anfügen

def test_bestaetigung_card(client, db):
    """Bestätigungsseite zeigt Inhalt in einer Card."""
    # Testbestellung anlegen
    db.execute(
        "INSERT INTO kunden (vorname, nachname, email, strasse, plz, ort) VALUES (?, ?, ?, ?, ?, ?)",
        ("Test", "User", "test@example.com", "Teststr. 1", "8000", "Zürich"),
    )
    kunde_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    db.execute(
        "INSERT INTO bestellungen (kunde_id, status, zahlungsart, versandart, versandkosten_chf, total_chf) VALUES (?, ?, ?, ?, ?, ?)",
        (kunde_id, "bezahlt", "rechnung", "versand", 9.90, 27.90),
    )
    db.commit()
    response = client.get("/bestaetigung?bestell_id=1&zahlungsart=rechnung")
    assert "bg-stone-700 rounded-lg" in response.text
    assert "shadow-md" in response.text
```

Hinweis: Dieser Test setzt voraus, dass der `/bestaetigung`-Endpunkt `bestell_id` und `zahlungsart` als Query-Parameter akzeptiert. Falls der Endpunkt anders funktioniert (z.B. nur via Stripe-Redirect), den Test an den tatsächlichen Endpunkt anpassen.

- [ ] **Step 2: Tests ausführen — müssen fehlschlagen**

Run: `python -m pytest tests/test_api_produkte.py::test_bestaetigung_card -v`
Expected: FAIL — kein `bg-stone-700 rounded-lg` im HTML

- [ ] **Step 3: bestaetigung.html ersetzen**

```html
{% extends "base.html" %}
{% block title %}Bestellbestätigung{% endblock %}
{% block content %}
<div class="max-w-lg mx-auto mt-8">
    <div class="bg-stone-700 rounded-lg p-8 shadow-md text-center">
        <div class="text-green-400 mb-4">
            <svg class="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
            </svg>
        </div>
        <h1 class="font-display text-5xl font-bold text-accent mb-4">Vielen Dank!</h1>
        <p class="text-lg text-stone-300 mb-2">Deine Bestellung #{{ bestell_id }} wurde erfolgreich aufgenommen.</p>
        {% if zahlungsart == "rechnung" %}
        <p class="text-stone-400">Du erhältst in Kürze eine E-Mail mit der QR-Rechnung.</p>
        {% else %}
        <p class="text-stone-400">Du erhältst in Kürze eine Bestellbestätigung per E-Mail.</p>
        {% endif %}
        <a href="/" class="inline-block mt-8 text-accent hover:underline">Zurück zum Shop</a>
    </div>
</div>
<script>localStorage.removeItem("olivalle-cart");</script>
{% endblock %}
```

Änderungen:
- Card-Container (`bg-stone-700 rounded-lg p-8 shadow-md`)
- Häkchen-Icon als SVG (grün, 64px)
- `mt-8` für Abstand nach oben

- [ ] **Step 4: Tests ausführen — müssen bestehen**

Run: `python -m pytest tests/test_api_produkte.py -v`
Expected: alle PASS (oder Test anpassen falls Endpunkt anders funktioniert)

- [ ] **Step 5: Commit**

```bash
git add templates/bestaetigung.html tests/test_api_produkte.py
git commit -m "feat: Bestätigungsseite als Card mit Häkchen-Icon (#51)"
```

---

### Task 5: Tailwind-Klassen dokumentieren und Issue schliessen

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Tailwind Card-UI Klassen in CLAUDE.md dokumentieren**

In `CLAUDE.md` nach der Sektion "## Design" eine neue Untersektion einfügen:

```markdown
### Tailwind Card-UI Klassen (Issue #51)
| Element | Klassen |
|---|---|
| Card | `bg-stone-700 rounded-lg p-6 shadow-md` |
| Card Hover (Produktkarten) | `hover:shadow-lg hover:-translate-y-1 transition-all duration-200` |
| Responsive Grid | `grid gap-6 sm:grid-cols-2 lg:grid-cols-3` |
| Button Transition | `transition-colors` |
```

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: Tailwind Card-UI Klassen in CLAUDE.md dokumentieren (#51)"
```

- [ ] **Step 3: O-UI in TODO.md als erledigt markieren**

`../TODO.md` — O-UI von Phase 1 nach Erledigt verschieben mit Datum.

- [ ] **Step 4: Issue #51 schliessen**

```bash
gh issue close 51 --comment "Card-UI & Responsive Design umgesetzt: Produktkarten, Warenkorb, Checkout, Bestätigung."
```

- [ ] **Step 5: Commit**

```bash
git add ../TODO.md
git commit -m "docs: O-UI als erledigt markieren, Issue #51 geschlossen"
```
