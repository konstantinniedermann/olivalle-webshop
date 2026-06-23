# Produktkarte — Rabatt-Stil, Layout-Fix & 4er-Raster Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rabatt-bezogene Elemente der Produktkarte in den einheitlichen roten Stil bringen, den „In den Warenkorb"-Button am Wegdrücken hindern und das Desktop-Raster für 4 Produkte anpassen.

**Architecture:** Reine Frontend-/Template-Änderung in `templates/produkte.html` (einzige Stelle der Produktkartenmarkup, gerendert unter `/`). Ein neuer Integrationstest sichert den roten `−%`-Chip ab. Doku in `CLAUDE.md` nachgeführt.

**Tech Stack:** FastAPI + Jinja2-Template, Tailwind CSS (utility-Klassen), pytest + Starlette TestClient.

## Global Constraints

- UI-Texte Deutsch (CH) — Textinhalt der Karte bleibt unverändert.
- Tailwind-Konvention rote Box / weisse Schrift = `bg-red-600 text-white` (analog bestehendes `RABATT`-Badge).
- Akzentfarbe Gelb `bg-accent` bleibt dem Button vorbehalten, nicht mehr für Rabatt-Chips/Texte.
- Card-UI-Regeln aus `CLAUDE.md` einhalten (Responsive Grid, konsistente Abstände).
- Keine Änderung an Datenmodell, Aktions-Logik oder Preisberechnung.

---

### Task 1: Roter `−%`-Chip (test-getrieben)

**Files:**
- Modify: `templates/produkte.html:43`
- Test: `tests/test_api_produkte.py`

**Interfaces:**
- Consumes: bestehende Render-Route `GET /` (produkte.py → produkte.html); Aktions-Felder `produkt.ist_aktion`, `produkt.prozent`, `produkt.aktionstext` aus `EinzelProduktAnsicht`.
- Produces: `−%`-Chip-Markup mit Klassen `bg-red-600 text-white text-xs font-bold px-1.5 py-0.5 rounded`.

- [ ] **Step 1: Failing test schreiben**

Am Ende von `tests/test_api_produkte.py` anhängen:

```python
def test_startseite_aktion_chip_roter_stil(client):
    """Folge #135: Der −%-Chip nutzt den roten Stil (bg-red-600 text-white),
    nicht mehr die gelbe Akzent-Box (bg-accent). bg-accent bleibt dem
    'In den Warenkorb'-Button vorbehalten."""
    from app.database import get_db

    conn = get_db()
    # 750ml (id=2) kostet CHF 18.00 → Aktionspreis 12.00 ergibt klaren Prozentwert
    conn.execute(
        "UPDATE produkte SET aktionspreis_chf = 12.0, "
        "aktionstext = 'MHD 09/2026' WHERE id = 2"
    )
    conn.commit()
    conn.close()
    resp = client.get("/")
    assert resp.status_code == 200
    # Chip ist rot und direkt am −-Zeichen verankert (kein False-Positive vom Button)
    assert (
        'bg-red-600 text-white text-xs font-bold px-1.5 py-0.5 rounded">−'
        in resp.text
    )
    # Alter gelber Chip-Stil ist verschwunden
    assert (
        'bg-accent text-stone-900 text-xs font-bold px-1.5 py-0.5 rounded">−'
        not in resp.text
    )
```

- [ ] **Step 2: Test laufen lassen, Fehlschlag prüfen**

Run: `pytest tests/test_api_produkte.py::test_startseite_aktion_chip_roter_stil -v`
Expected: FAIL — der rote Chip-String fehlt (Chip ist noch `bg-accent text-stone-900`).

- [ ] **Step 3: Template anpassen**

In `templates/produkte.html` Zeile 43 ersetzen:

```jinja
{% if produkt.prozent > 0 %}<span class="bg-red-600 text-white text-xs font-bold px-1.5 py-0.5 rounded">−{{ produkt.prozent }}%</span>{% endif %}
```

- [ ] **Step 4: Test laufen lassen, Erfolg prüfen**

Run: `pytest tests/test_api_produkte.py::test_startseite_aktion_chip_roter_stil -v`
Expected: PASS.

- [ ] **Step 5: Volle Test-Suite + Lint**

Run: `make lint-all && pytest -q`
Expected: alle grün (bestehende Asserts RABATT/Aktionstext/`CHF 12.00`/`−0` unberührt).

- [ ] **Step 6: Commit**

```bash
git add templates/produkte.html tests/test_api_produkte.py
git commit -m "feat: −%-Chip der Produktkarte auf roten Stil umgestellt (#135)"
```

---

### Task 2: Aktionstext-Box, Beschreibung, Layout-Fix & 4er-Raster

**Files:**
- Modify: `templates/produkte.html:23,34,36,38-57`

**Interfaces:**
- Consumes: Render-Route `GET /`; Aktions-Felder wie Task 1.
- Produces: Aktionstext in roter Box; Beschreibung `text-sm`; Button volle Breite unter der Preiszeile; Raster `lg:grid-cols-4`.

- [ ] **Step 1: Raster auf 4 Spalten (Z. 23)**

```jinja
<div class="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
```

- [ ] **Step 2: Beschreibung kleiner (Z. 34)**

```jinja
<p class="text-stone-200 text-sm mt-2 flex-1">{{ produkt.beschreibung }}</p>
```

- [ ] **Step 3: Aktionstext in rote Box (Z. 36)**

```jinja
{% if produkt.ist_aktion and produkt.aktionstext %}
<p class="bg-red-600 text-white text-xs font-bold px-2 py-1 rounded inline-block mt-2">{{ produkt.aktionstext }}</p>
{% endif %}
```

- [ ] **Step 4: Preiszeile + Button umbauen (Z. 38-57)**

Den `<div class="mt-4 flex items-center justify-between">`-Block ersetzen durch:

```jinja
<div class="mt-4">
    <div class="flex items-baseline flex-wrap gap-2 mb-3">
        {% if produkt.ist_aktion %}
        <span class="text-stone-400 line-through text-sm">CHF {{ "%.2f"|format(produkt.original_preis) }}</span>
        <span class="text-xl font-bold">CHF {{ "%.2f"|format(produkt.preis) }}</span>
        {% if produkt.prozent > 0 %}<span class="bg-red-600 text-white text-xs font-bold px-1.5 py-0.5 rounded">−{{ produkt.prozent }}%</span>{% endif %}
        {% else %}
        <span class="text-xl font-bold">CHF {{ "%.2f"|format(produkt.preis) }}</span>
        {% endif %}
    </div>
    <button type="button"
            class="add-to-cart-btn bg-accent text-stone-900 px-4 py-2 rounded font-bold hover:bg-yellow-400 transition-colors w-full"
            data-product-id="{{ produkt.id }}"
            data-product-name="{{ produkt.name }}"
            data-product-price="{{ produkt.preis }}"
            data-product-aktion="{{ '1' if produkt.ist_aktion else '0' }}"
            data-product-image="/static/images/{{ produkt.bild_pfad }}">
        In den Warenkorb
    </button>
</div>
```

(Der `−%`-Chip behält den roten Stil aus Task 1.)

- [ ] **Step 5: Test-Suite + Lint**

Run: `make lint-all && pytest -q`
Expected: alle grün.

- [ ] **Step 6: Visuell verifizieren (Mobile + Desktop)**

App lokal starten (`make help` für den kanonischen Befehl) und `/` öffnen:
- Desktop (≥1024px): 4 Karten nebeneinander, Button volle Breite, kein Wegdrücken.
- Mobile (<640px): Karten gestapelt, Button volle Breite, Rabatt-Elemente rot.
- Bei aktiver Aktion: Aktionstext + `−%` rot, alter Preis grau durchgestrichen, nichts überdeckt sich.

- [ ] **Step 7: Commit**

```bash
git add templates/produkte.html
git commit -m "feat: Produktkarte 4er-Raster, Button volle Breite, Aktionstext rot (#135)"
```

---

### Task 3: Doku nachführen

**Files:**
- Modify: `CLAUDE.md` (olivalle, Tabelle „Tailwind Card-UI Klassen")

**Interfaces:**
- Consumes: nichts.
- Produces: konsistente Doku der Grid-Klasse.

- [ ] **Step 1: Grid-Klasse in CLAUDE.md aktualisieren**

In der Tabelle „Tailwind Card-UI Klassen (Issue #51)" die Zeile „Responsive Grid":

```
| Responsive Grid | `grid gap-6 sm:grid-cols-2 lg:grid-cols-4` |
```

- [ ] **Step 2: Redundanz-/Konsistenzcheck**

Run: `grep -rn "lg:grid-cols-3" CLAUDE.md ../CLAUDE.md docs/arc42.md docs/user-stories-testplan.md`
Expected: keine verbliebene Referenz auf das alte 3er-Raster im Kontext der Produktkarte; falls doch, dort ebenfalls anpassen.

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: Card-UI Grid-Konvention auf lg:grid-cols-4 aktualisiert (#135)"
```

---

## Self-Review

**Spec coverage:**
- Raster `lg:grid-cols-4` → Task 2 Step 1, Task 3. ✓
- Aktionstext roter Stil → Task 2 Step 3. ✓
- `−%`-Chip roter Stil → Task 1. ✓
- Alter Preis unverändert → Task 2 Step 4 (behält `text-stone-400 line-through`). ✓
- Beschreibung `text-sm` → Task 2 Step 2. ✓
- Layout Button volle Breite + `flex-wrap` → Task 2 Step 4. ✓
- Regressions-Test → Task 1. ✓
- Doku CLAUDE.md → Task 3. ✓
- Separates Issue für ausklappbaren Text → ausserhalb dieses Plans (Pause-Cleanup).

**Placeholder scan:** keine TBD/TODO; alle Code-Blöcke vollständig.

**Type consistency:** Klassen-Strings für den `−%`-Chip in Task 1 (Step 3) und Task 2 (Step 4) identisch (`bg-red-600 text-white text-xs font-bold px-1.5 py-0.5 rounded`). ✓
