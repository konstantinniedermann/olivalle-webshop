# Preis-Block zweizeilig (Rabatt-Eindeutigkeit) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Auf der Produktseite das `−%`-Rabatt-Chip eindeutig dem Alt-Preis zuordnen, indem Alt-Preis + Chip in eine obere Zeile wandern und der neue Preis als Resultat darunter steht.

**Architecture:** Reine Jinja2-Template-Umstellung in `templates/produkte.html`. Der bestehende Aktions-Fall (eine `flex-wrap`-Zeile) wird in zwei bewusste Blöcke aufgeteilt. Keine Backend-, Service- oder DB-Änderung — alle Daten (`original_preis`, `preis`, `prozent`, `ist_aktion`) werden bereits geliefert.

**Tech Stack:** FastAPI, Jinja2, Tailwind CSS, pytest (TestClient), uv.

## Global Constraints

- UI-Texte auf Deutsch (CH).
- `−`-Zeichen ist U+2212 (Minus), nicht ASCII-Hyphen — wie im Bestand.
- Roter Chip-Stil `bg-red-600 text-white text-xs font-bold px-1.5 py-0.5 rounded` bleibt; Gelb (`bg-accent`) bleibt dem „In den Warenkorb"-Button vorbehalten.
- Nicht-Aktions-Fall unverändert: nur ein fetter Preis `text-xl font-bold`.
- `RABATT`-Badge (oben rechts) und optionaler `aktionstext`-Badge bleiben unangetastet.
- Tests via `uv run pytest`; Lint via `make lint-all`.

---

### Task 1: Preis-Block zweizeilig umstrukturieren

**Files:**
- Modify: `templates/produkte.html:38-47`
- Test: `tests/test_api_produkte.py` (neuer Test, am Ende anfügen)
- Check: `docs/user-stories-testplan.md` (manuellen Prüfschritt zur Rabatt-Anzeige gegenchecken)

**Interfaces:**
- Consumes: Template-Variablen pro `produkt`: `ist_aktion` (bool), `original_preis` (float), `preis` (float), `prozent` (int). Geliefert von `app/services/aktions_service.py` via Route `/`.
- Produces: Gerendertes HTML, in dem im Aktions-Fall die Quelltext-Reihenfolge `Alt-Preis (line-through) → −%-Chip → neuer Preis (text-xl font-bold)` ist.

- [ ] **Step 1: Failing-Test schreiben**

Am Ende von `tests/test_api_produkte.py` anfügen. Der Test fixiert die Design-Absicht über die **Quelltext-Reihenfolge**: das `−%`-Chip muss VOR dem neuen Preis stehen (gehört zum Alt-Preis). Im alten Layout stand das Chip NACH dem neuen Preis → der Test schlägt dort fehl.

```python
def test_startseite_aktion_chip_steht_vor_neupreis(client):
    """#139: Der −%-Chip gehört zum Alt-Preis (obere Zeile), der neue Preis
    steht als Resultat darunter. Im gerenderten HTML erscheint der Chip daher
    VOR dem neuen Preis — so liest sich '−33%' als Abzug vom Alt-Preis (18.00),
    nicht als weiterer Rabatt auf den Endpreis (12.00).

    750ml (id=2) kostet CHF 18.00. Aktionspreis 12.00 → Rabatt round(33.3)=33%.
    Erwartete Reihenfolge im Quelltext: 'CHF 18.00' < '−33%' < 'CHF 12.00'.
    """
    from app.database import get_db

    conn = get_db()
    conn.execute("UPDATE produkte SET aktionspreis_chf = 12.0 WHERE id = 2")
    conn.commit()
    conn.close()
    resp = client.get("/")
    assert resp.status_code == 200
    html = resp.text
    pos_alt = html.index("CHF 18.00")  # durchgestrichener Alt-Preis
    pos_chip = html.index("−33%")  # U+2212 Minus + Prozent
    pos_neu = html.index("CHF 12.00")  # neuer Preis (Resultat)
    assert pos_alt < pos_chip < pos_neu
```

- [ ] **Step 2: Test laufen lassen, Fehlschlag verifizieren**

Run: `uv run pytest -v tests/test_api_produkte.py::test_startseite_aktion_chip_steht_vor_neupreis`
Expected: FAIL — im alten Layout ist `pos_neu < pos_chip` (Chip steht nach dem neuen Preis), die Assertion `pos_chip < pos_neu` schlägt fehl.

- [ ] **Step 3: Template umstrukturieren**

In `templates/produkte.html` den Block Zeilen 38–47 ersetzen.

Vorher:
```html
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
```

Nachher:
```html
                    <div class="mt-4">
                        {% if produkt.ist_aktion %}
                        <div class="flex items-baseline gap-2 mb-1">
                            <span class="text-stone-400 line-through text-sm">CHF {{ "%.2f"|format(produkt.original_preis) }}</span>
                            {% if produkt.prozent > 0 %}<span class="bg-red-600 text-white text-xs font-bold px-1.5 py-0.5 rounded">−{{ produkt.prozent }}%</span>{% endif %}
                        </div>
                        <div class="text-xl font-bold mb-3">CHF {{ "%.2f"|format(produkt.preis) }}</div>
                        {% else %}
                        <div class="text-xl font-bold mb-3">CHF {{ "%.2f"|format(produkt.preis) }}</div>
                        {% endif %}
```

Änderungen im Detail:
- Aktions-Fall: obere Zeile `flex items-baseline gap-2 mb-1` enthält nur noch Alt-Preis + `−%`-Chip (kein `flex-wrap` mehr nötig — Zeile ist kurz).
- Neuer Preis als eigener `<div class="text-xl font-bold mb-3">` darunter (das Resultat).
- Nicht-Aktions-Fall: unverändert ein `<div class="text-xl font-bold mb-3">`.

- [ ] **Step 4: Neuen Test laufen lassen, Erfolg verifizieren**

Run: `uv run pytest -v tests/test_api_produkte.py::test_startseite_aktion_chip_steht_vor_neupreis`
Expected: PASS

- [ ] **Step 5: Bestehende Produkt-Tests laufen lassen (keine Regression)**

Run: `uv run pytest -v tests/test_api_produkte.py`
Expected: Alle PASS — insbesondere `test_startseite_zeigt_aktionspreis`, `test_startseite_aktion_null_prozent_badge_versteckt`, `test_startseite_aktion_chip_roter_stil` (Chip-Substring und Roter-Stil bleiben unverändert gültig).

- [ ] **Step 6: Testplan-Doku gegenchecken**

`docs/user-stories-testplan.md` öffnen und nach dem manuellen Prüfschritt zur Rabatt-/Aktionspreis-Anzeige suchen. Falls ein Schritt die alte einzeilige Darstellung beschreibt, auf die neue zweizeilige Darstellung anpassen (Alt-Preis + `−%` oben, neuer Preis darunter). Falls kein solcher Schritt existiert oder er die Anordnung nicht festschreibt: keine Änderung nötig (kurz im Commit-Body vermerken).

- [ ] **Step 7: Voller Test-Lauf + Lint**

Run: `uv run pytest`
Expected: Alle PASS

Run: `make lint-all`
Expected: sauber (keine neuen Findings)

- [ ] **Step 8: Commit**

```bash
git add templates/produkte.html tests/test_api_produkte.py
# docs/user-stories-testplan.md nur falls in Step 6 geändert
git commit -m "feat: Preis-Block zweizeilig — −%-Chip beim Alt-Preis, neuer Preis als Resultat (#139)"
```

---

## Self-Review

**Spec coverage:**
- „Alt-Preis + Chip oben, neuer Preis als Resultat darunter" → Task 1, Step 3 (Template) + Step 1 (Test fixiert Reihenfolge). ✓
- „Kein Backend-Touch" → nur `templates/produkte.html` modifiziert. ✓
- „Nicht-Aktions-Fall unverändert" → Step 3 behält den einen fetten Preis. ✓
- „RABATT-/aktionstext-Badge unangetastet" → Block Z. 26–37 nicht berührt. ✓
- „tests/ ggf. anpassen" → neuer Test (Step 1), Regressions-Check (Step 5). ✓
- „user-stories-testplan.md gegenchecken (#140)" → Step 6. ✓
- „Verifikation am schmalen Layout" → manuell nach Merge; automatisiert über Reihenfolge-Test abgedeckt. ✓

**Placeholder scan:** Keine TBD/TODO; alle Schritte enthalten konkreten Code/Befehle. ✓

**Type consistency:** Variablennamen `original_preis`, `preis`, `prozent`, `ist_aktion` stimmen mit Template-Bestand und Service überein. Prozent-Berechnung round((1−12/18)·100)=33 → Chip „−33%" konsistent mit Test-Assertion. ✓
