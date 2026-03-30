# Card-UI Cleanup Implementation Plan (Issue #53)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 4 Follow-up-Fixes aus dem Code Review von Issue #51 umsetzen — fragile Bildlogik ersetzen, toten Code entfernen, Accessibility verbessern, Ruff-Fehler beheben.

**Architecture:** Reine Cleanup-Aufgaben ohne neue Features. Tasks sind unabhängig voneinander.

**Tech Stack:** JavaScript (cart.js, Jinja2-Templates), Python (Ruff-Linter)

---

## File Map

| Datei | Aktion | Zweck |
|---|---|---|
| `static/js/cart.js` | Modify | `addToCart` Signatur erweitern, `updateMenge` entfernen |
| `templates/produkte.html` | Modify | Bild-URL an `addToCart` übergeben |
| `templates/warenkorb.html` | Modify | `getImageSlug` entfernen, `item.image` nutzen |
| `templates/bestaetigung.html` | Modify | `aria-hidden="true"` auf SVG |
| `app/main.py` | Modify | E402 Import-Position fixen |
| `app/routers/bestellungen.py` | Modify | E501 Zeilenlänge |
| `app/routers/warenkorb.py` | Modify | E501 Zeilenlänge |
| `tests/test_api_bestellungen.py` | Modify | E501 Zeilenlänge |
| `tests/test_api_webhooks.py` | Modify | I001 Import-Sortierung, E501 Zeilenlänge |
| `tests/test_bestell_repo.py` | Modify | I001 Import-Sortierung, E501 Zeilenlänge |
| `tests/test_csrf.py` | Modify | I001 Import-Sortierung, E702 Semicolon |
| `tests/test_email_service.py` | Modify | I001 Import-Sortierung, F401 unbenutzter Import |
| `tests/test_stripe_service.py` | Modify | E501 Zeilenlänge |

---

### Task 1: `bild_pfad` im Cart-Item speichern

**Files:**
- Modify: `static/js/cart.js:12-19`
- Modify: `templates/produkte.html:64`
- Modify: `templates/warenkorb.html:52,72-77`

- [ ] **Step 1: `addToCart` Signatur in `cart.js` erweitern**

In `static/js/cart.js`, Zeile 12 ändern — neuer Parameter `image` zwischen `price` und `buttonEl`:

```js
function addToCart(id, name, price, image, buttonEl) {
```

Zeile 18 ändern — `image` im Cart-Objekt speichern:

```js
cart.push({ produkt_id: id, name: name, preis: price, image: image, menge: 1 });
```

- [ ] **Step 2: Bild-URL in `produkte.html` mitgeben**

In `templates/produkte.html`, Zeile 64 ändern:

```html
<button onclick="addToCart({{ produkt.id }}, '{{ produkt.name }}', {{ produkt.preis_chf }}, '/static/images/{{ produkt.bild_pfad }}', this)"
```

- [ ] **Step 3: `warenkorb.html` — `item.image` nutzen, `getImageSlug` entfernen**

In `templates/warenkorb.html`, Zeile 52 ändern:

```js
img.src = item.image || "/static/images/products/olivalle-250ml.jpeg";
```

Zeilen 72-77 komplett entfernen (die `getImageSlug`-Funktion):

```js
// ENTFERNEN:
function getImageSlug(name) {
    if (name.includes("250")) return "250ml";
    if (name.includes("750")) return "750ml";
    if (name.includes("3")) return "3l";
    return "250ml";
}
```

- [ ] **Step 4: Manuell testen**

Server starten: `uv run uvicorn app.main:app --reload`

1. Produkt in Warenkorb legen
2. Warenkorb öffnen → Produktbild muss korrekt angezeigt werden
3. Browser-Console prüfen: keine JS-Fehler

- [ ] **Step 5: Commit**

```bash
git add static/js/cart.js templates/produkte.html templates/warenkorb.html
git commit -m "fix: bild_pfad im Cart-Item speichern statt getImageSlug (#53)"
```

---

### Task 2: `updateMenge` entfernen

**Files:**
- Modify: `static/js/cart.js:47-55`

- [ ] **Step 1: Funktion löschen**

In `static/js/cart.js`, Zeilen 47-55 entfernen:

```js
// ENTFERNEN:
function updateMenge(id, menge) {
    const cart = getCart();
    const item = cart.find((item) => item.produkt_id === id);
    if (item) {
        item.menge = Math.max(1, menge);
    }
    saveCart(cart);
    if (typeof renderCart === "function") renderCart();
}
```

- [ ] **Step 2: Verifizieren dass nirgends referenziert**

```bash
grep -r "updateMenge" templates/ static/js/ --include="*.html" --include="*.js"
```

Erwartetes Ergebnis: keine Treffer.

- [ ] **Step 3: Commit**

```bash
git add static/js/cart.js
git commit -m "refactor: unbenutzte updateMenge aus cart.js entfernen (#53)"
```

---

### Task 3: SVG `aria-hidden` setzen

**Files:**
- Modify: `templates/bestaetigung.html:7`

- [ ] **Step 1: `aria-hidden="true"` hinzufügen**

In `templates/bestaetigung.html`, Zeile 7 ändern:

```html
<svg class="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
```

- [ ] **Step 2: Commit**

```bash
git add templates/bestaetigung.html
git commit -m "fix: aria-hidden auf dekorativem SVG in Bestellbestätigung (#53)"
```

---

### Task 4: Ruff-Fehler fixen

**Files:**
- Modify: `app/main.py`, `app/routers/bestellungen.py`, `app/routers/warenkorb.py`
- Modify: `tests/test_api_bestellungen.py`, `tests/test_api_webhooks.py`, `tests/test_bestell_repo.py`, `tests/test_csrf.py`, `tests/test_email_service.py`, `tests/test_stripe_service.py`

- [ ] **Step 1: Auto-fixbare Fehler beheben**

```bash
uv run ruff check --fix .
```

Das fixt automatisch: I001 (Import-Sortierung, 4 Dateien), F401 (unbenutzter MagicMock-Import).

- [ ] **Step 2: E402 in `app/main.py` fixen**

Der Router-Import auf Zeile 22 steht nach `init_db()` und `app.mount()` — das ist hier beabsichtigt (zirkuläre Imports vermeiden). Lösung: `# noqa: E402` anhängen.

In `app/main.py`, Zeile 22 ändern:

```python
from app.routers import admin, bestellungen, produkte, seiten, warenkorb, webhooks  # noqa: E402
```

- [ ] **Step 3: E501 in `app/routers/bestellungen.py:132` fixen**

```python
        return templates.TemplateResponse(
            request,
            "bestaetigung.html",
            {
                "bestell_id": bestell_id,
                "zahlungsart": zahlungsart,
                "active_page": "bestaetigung",
            },
        )
```

- [ ] **Step 4: E501 in `app/routers/warenkorb.py:10` fixen**

```python
@router.get("/warenkorb")
def warenkorb(request: Request):
    return templates.TemplateResponse(
        request, "warenkorb.html", {"active_page": "warenkorb"}
    )
```

- [ ] **Step 5: E501 in `tests/test_api_bestellungen.py:25` fixen**

```python
def test_bestellen_rechnung_erfolgreich(
    mock_qrbill, mock_email, client, monkeypatch, csrf_token
):
```

- [ ] **Step 6: E501 in `tests/test_api_webhooks.py:13,17` fixen**

Zeile 13 — SQL-String umbrechen:

```python
    db.execute(
        "INSERT INTO bestellungen"
        " (kunde_id, zahlungsart, versandart, total_chf,"
        " stripe_session_id, status) "
        "VALUES (1, 'stripe', 'versand', 25.90, 'cs_test_123', 'neu')"
    )
```

Zeile 17 — SQL-String umbrechen:

```python
    db.execute(
        "INSERT INTO bestellpositionen"
        " (bestellung_id, produkt_id, menge, einzelpreis_chf) "
        "VALUES (1, 1, 2, 8.0)"
    )
```

- [ ] **Step 7: E501 in `tests/test_bestell_repo.py:29` fixen**

```python
    row = db.execute(
        "SELECT * FROM bestellungen WHERE id = ?", (bestell_id,)
    ).fetchone()
```

- [ ] **Step 8: E702/I001 in `tests/test_csrf.py:16` fixen**

Semicolon-Zeile aufteilen und `import time` an den Dateianfang verschieben:

```python
    token = generiere_csrf_token("test-secret", max_age=-1)
    time.sleep(0.1)
```

Prüfe wo `import time` im Datei-Header eingefügt werden muss (nach den bestehenden Imports).

- [ ] **Step 9: E501 in `tests/test_stripe_service.py:13` fixen**

```python
            {
                "produkt_id": 1,
                "menge": 2,
                "einzelpreis_chf": 8.0,
                "name": "Olivenöl 250ml",
            },
```

- [ ] **Step 10: Ruff verifizieren**

```bash
uv run ruff check .
```

Erwartetes Ergebnis: `All checks passed!` (0 Fehler).

- [ ] **Step 11: Tests laufen lassen**

```bash
uv run pytest -v
```

Erwartetes Ergebnis: alle Tests grün.

- [ ] **Step 12: Commit**

```bash
git add -A
git commit -m "fix: alle Ruff-Fehler behoben (E501, E402, E702, I001, F401) (#53)"
```
