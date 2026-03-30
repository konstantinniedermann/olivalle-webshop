# Design Spec: Card-UI Cleanup (Issue #53)

> Follow-up-Punkte aus dem Code Review von Issue #51 (Card-UI & Responsive Design).

## 1. `bild_pfad` im Cart-Item speichern

**Problem:** `getImageSlug()` in `warenkorb.html:72-76` leitet den Bildpfad aus dem Produktnamen ab mit `name.includes("3")` — matcht zu breit (z.B. "3er-Pack"). Funktion gehört nicht ins Template.

**Lösung:** Bild-URL direkt im Cart-Item speichern statt im Frontend ableiten.

### Änderungen

**`static/js/cart.js` — `addToCart` Signatur erweitern:**
```js
// Vorher:
function addToCart(id, name, price, buttonEl)

// Nachher:
function addToCart(id, name, price, image, buttonEl)
```

Im Cart-Objekt `image` mitspeichern:
```js
cart.push({ produkt_id: id, name: name, preis: price, image: image, menge: 1 });
```

**`templates/produkte.html:64` — Bild-URL mitgeben:**
```html
<!-- Vorher: -->
<button onclick="addToCart({{ produkt.id }}, '{{ produkt.name }}', {{ produkt.preis_chf }}, this)">

<!-- Nachher: -->
<button onclick="addToCart({{ produkt.id }}, '{{ produkt.name }}', {{ produkt.preis_chf }}, '/static/images/{{ produkt.bild_pfad }}', this)">
```

**`templates/warenkorb.html` — `getImageSlug` ersetzen:**
```js
// Vorher:
img.src = "/static/images/products/olivalle-" + getImageSlug(item.name) + ".jpeg";

// Nachher:
img.src = item.image || "/static/images/products/olivalle-250ml.jpeg";
```

Fallback für bestehende Cart-Items im localStorage, die noch kein `image`-Feld haben.

`getImageSlug`-Funktion (Zeilen 72-77) komplett entfernen.

## 2. `updateMenge` entfernen

**Problem:** `static/js/cart.js:47-55` — durch `increaseMenge`/`decreaseMenge` ersetzt, wird nirgends aufgerufen.

**Lösung:** Funktion löschen (`cart.js:47-55`).

## 3. SVG `aria-hidden` setzen

**Problem:** `templates/bestaetigung.html:7` — dekoratives SVG-Häkchen ohne `aria-hidden="true"`, Screen Reader liest leeres Element.

**Lösung:**
```html
<!-- Vorher: -->
<svg class="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">

<!-- Nachher: -->
<svg class="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
```

## 4. Ruff-Fehler fixen

**Problem:** 14 pre-existing Ruff-Fehler in verschiedenen Dateien.

**Lösung:**
1. `ruff check --fix .` — auto-fixbare Fehler (I001 Import-Sortierung, F401 unbenutzter Import)
2. Manuelle Fixes für:
   - E501 (Zeilenlängen >88): Zeilen umbrechen
   - E402 (Import nicht am Anfang): Import-Reihenfolge in `app/main.py` anpassen
   - E702 (Mehrfach-Statement): Semicolon-Zeile aufteilen

### Betroffene Dateien
- `app/main.py` (E402)
- `app/routers/bestellungen.py` (E501)
- `app/routers/warenkorb.py` (E501)
- `tests/test_api_bestellungen.py` (E501)
- Weitere Dateien mit I001/F401

## Testbarkeit

- Manuelle Prüfung: Warenkorb öffnen, Bilder werden korrekt angezeigt
- `uv run ruff check .` zeigt 0 Fehler
- Bestehende Tests laufen weiter grün (`uv run pytest`)
