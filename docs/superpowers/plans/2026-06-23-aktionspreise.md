# Produktbezogene Aktionspreise — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Einzelne Produkte können einen temporären, auf der Produktkarte sichtbaren Aktionspreis (mit Begründungstext und optionalem Gültigkeitszeitraum) erhalten, den der SH selbst über die Admin-UI pflegt.

**Architecture:** Eine zentrale Funktion `effektiver_preis()` ist die einzige Stelle, die entscheidet, welcher Preis (Normal- oder Aktionspreis) zu einem Datum gilt. Sie speist die autoritative Serverberechnung `berechne_total()`, wodurch Stripe, DB-Positionen, Mails und QR-Rechnung automatisch korrekt rechnen. Rabattcodes greifen nur auf den Nicht-Aktions-Anteil des Warenkorbs.

**Tech Stack:** Python 3 / FastAPI, SQLite, Jinja2, Tailwind CSS, Vanilla JS (localStorage-Warenkorb), pytest, Stripe.

## Global Constraints

- **UI-Texte Deutsch (CH).** Keine englischen Strings im sichtbaren UI.
- **Preis-Autorität ist der Server.** `berechne_total()` ist die einzige verbindliche Preisquelle; der Browser-Warenkorb dient nur der Anzeige.
- **Neue Spalten an bestehenden Tabellen** werden idempotent via `_add_column_if_not_exists()` in `init_db()` ergänzt — **kein** `ALTER TABLE` in einer `.sql`-Datei (würde beim Re-Run scheitern). Dasselbe in der `db`-Fixture in `tests/conftest.py` spiegeln.
- **Ruff-konformer Stil** (Linter + Formatter). Vor jedem Commit lokal `make lint-all` bzw. `ruff check .` grün.
- **Geldbeträge** in CHF, 2 Nachkommastellen; bestehende 5-Rappen-Rundung der Rabattcodes nicht verändern.
- **CSRF**: Admin-POST-Routen mit Zustandsänderung schützen via `Depends(require_csrf)` (Muster aus `app/routers/admin.py`).
- **Commit-Konvention**: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`.

---

### Task 1: DB-Spalten für Aktionspreise

Vier NULL-bare Spalten an `produkte` ergänzen — idempotent in `init_db()` und in der Test-Fixture.

**Files:**
- Modify: `app/database.py` (Funktion `init_db`)
- Modify: `tests/conftest.py` (Fixture `db`)
- Test: `tests/test_aktions_columns.py` (neu)

**Interfaces:**
- Produces: Tabelle `produkte` hat die Spalten `aktionspreis_chf` (REAL NULL), `aktionstext` (TEXT NULL), `aktion_von` (TEXT NULL), `aktion_bis` (TEXT NULL).

- [ ] **Step 1: Failing test schreiben**

`tests/test_aktions_columns.py`:

```python
def test_produkte_hat_aktions_spalten(db):
    cols = {row[1] for row in db.execute("PRAGMA table_info(produkte)")}
    assert {"aktionspreis_chf", "aktionstext", "aktion_von", "aktion_bis"} <= cols
```

- [ ] **Step 2: Test laufen lassen — muss fehlschlagen**

Run: `uv run pytest tests/test_aktions_columns.py -v`
Expected: FAIL (Spalten fehlen).

- [ ] **Step 3: Spalten in `init_db()` ergänzen**

In `app/database.py`, in `init_db()` nach den bestehenden `_add_column_if_not_exists`-Aufrufen (vor `conn.commit()`):

```python
        _add_column_if_not_exists(conn, "produkte", "aktionspreis_chf", "REAL")
        _add_column_if_not_exists(conn, "produkte", "aktionstext", "TEXT")
        _add_column_if_not_exists(conn, "produkte", "aktion_von", "TEXT")
        _add_column_if_not_exists(conn, "produkte", "aktion_bis", "TEXT")
```

- [ ] **Step 4: Dieselben Spalten in der `db`-Fixture ergänzen**

In `tests/conftest.py`, in der `db`-Fixture nach den bestehenden `_add_column_if_not_exists`-Aufrufen (vor `conn.commit()`):

```python
    _add_column_if_not_exists(conn, "produkte", "aktionspreis_chf", "REAL")
    _add_column_if_not_exists(conn, "produkte", "aktionstext", "TEXT")
    _add_column_if_not_exists(conn, "produkte", "aktion_von", "TEXT")
    _add_column_if_not_exists(conn, "produkte", "aktion_bis", "TEXT")
```

- [ ] **Step 5: Test laufen lassen — muss bestehen**

Run: `uv run pytest tests/test_aktions_columns.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add app/database.py tests/conftest.py tests/test_aktions_columns.py
git commit -m "feat: Aktionspreis-Spalten an produkte (#134)"
```

---

### Task 2: Effektiv-Preis-Logik (`aktions_service`)

Die zentrale, rein funktionale Preisentscheidung. Keine DB, keine Seiteneffekte — vollständig unit-testbar.

**Files:**
- Create: `app/services/aktions_service.py`
- Test: `tests/test_aktions_service.py` (neu)

**Interfaces:**
- Produces:
  - `class EffektivPreis(NamedTuple)` mit Feldern `preis: float`, `ist_aktion: bool`, `original_preis: float`, `prozent: int`.
  - `effektiver_preis(preis_chf: float, aktionspreis_chf: float | None, aktion_von: str | None, aktion_bis: str | None, heute: date) -> EffektivPreis`. `aktion_von`/`aktion_bis` sind ISO-Strings (`YYYY-MM-DD`) oder `None`/`""`. Bei aktiver Aktion ist `preis` der Aktionspreis, sonst der Normalpreis. `prozent = round((1 - aktion/original) * 100)`, sonst `0`.

- [ ] **Step 1: Failing tests schreiben**

`tests/test_aktions_service.py`:

```python
from datetime import date

from app.services.aktions_service import effektiver_preis

HEUTE = date(2026, 6, 23)


def test_keine_aktion_wenn_aktionspreis_none():
    ep = effektiver_preis(18.0, None, None, None, HEUTE)
    assert ep.ist_aktion is False
    assert ep.preis == 18.0
    assert ep.original_preis == 18.0
    assert ep.prozent == 0


def test_aktion_ohne_datumsgrenzen_gilt():
    ep = effektiver_preis(18.0, 12.0, None, None, HEUTE)
    assert ep.ist_aktion is True
    assert ep.preis == 12.0
    assert ep.original_preis == 18.0
    assert ep.prozent == 33  # round((1-12/18)*100) = 33


def test_aktion_vor_beginn_inaktiv():
    ep = effektiver_preis(18.0, 12.0, "2026-07-01", None, HEUTE)
    assert ep.ist_aktion is False
    assert ep.preis == 18.0


def test_aktion_nach_ende_inaktiv():
    ep = effektiver_preis(18.0, 12.0, None, "2026-06-22", HEUTE)
    assert ep.ist_aktion is False
    assert ep.preis == 18.0


def test_aktion_innerhalb_zeitraum_aktiv():
    ep = effektiver_preis(18.0, 12.0, "2026-06-01", "2026-06-30", HEUTE)
    assert ep.ist_aktion is True
    assert ep.preis == 12.0


def test_aktion_grenze_von_inklusive():
    ep = effektiver_preis(18.0, 12.0, "2026-06-23", "2026-06-30", HEUTE)
    assert ep.ist_aktion is True


def test_aktion_grenze_bis_inklusive():
    ep = effektiver_preis(18.0, 12.0, "2026-06-01", "2026-06-23", HEUTE)
    assert ep.ist_aktion is True


def test_leere_strings_wie_none_behandelt():
    ep = effektiver_preis(18.0, 12.0, "", "", HEUTE)
    assert ep.ist_aktion is True
```

- [ ] **Step 2: Tests laufen lassen — müssen fehlschlagen**

Run: `uv run pytest tests/test_aktions_service.py -v`
Expected: FAIL (Modul/Funktion fehlt).

- [ ] **Step 3: Implementierung schreiben**

`app/services/aktions_service.py`:

```python
"""Zentrale Logik für produktbezogene Aktionspreise (Issue #134).

Einzige Stelle, die entscheidet, ob und welcher Aktionspreis zu einem
gegebenen Datum gilt. Rein funktional, ohne DB-Zugriff.
"""

from __future__ import annotations

from datetime import date
from typing import NamedTuple


class EffektivPreis(NamedTuple):
    preis: float
    ist_aktion: bool
    original_preis: float
    prozent: int


def _aktion_aktiv(
    aktionspreis_chf: float | None,
    aktion_von: str | None,
    aktion_bis: str | None,
    heute: date,
) -> bool:
    if aktionspreis_chf is None:
        return False
    h = heute.isoformat()
    if aktion_von and h < aktion_von:
        return False
    if aktion_bis and h > aktion_bis:
        return False
    return True


def effektiver_preis(
    preis_chf: float,
    aktionspreis_chf: float | None,
    aktion_von: str | None,
    aktion_bis: str | None,
    heute: date,
) -> EffektivPreis:
    """Liefert den gültigen Preis samt Aktions-Metadaten für ein Datum."""
    if _aktion_aktiv(aktionspreis_chf, aktion_von, aktion_bis, heute):
        prozent = round((1 - aktionspreis_chf / preis_chf) * 100)
        return EffektivPreis(
            preis=aktionspreis_chf,
            ist_aktion=True,
            original_preis=preis_chf,
            prozent=prozent,
        )
    return EffektivPreis(
        preis=preis_chf,
        ist_aktion=False,
        original_preis=preis_chf,
        prozent=0,
    )
```

- [ ] **Step 4: Tests laufen lassen — müssen bestehen**

Run: `uv run pytest tests/test_aktions_service.py -v`
Expected: PASS (8 Tests).

- [ ] **Step 5: Commit**

```bash
git add app/services/aktions_service.py tests/test_aktions_service.py
git commit -m "feat: effektiver_preis-Logik für Aktionspreise (#134)"
```

---

### Task 3: Produkt-Model & Repo um Aktions-Felder erweitern

`Produkt` trägt die Aktions-Felder, `get_alle_produkte()` lädt sie mit.

**Files:**
- Modify: `app/models.py` (`class Produkt`)
- Modify: `app/repositories/produkt_repo.py` (`get_alle_produkte`)
- Test: `tests/test_produkt_repo.py` (ergänzen)

**Interfaces:**
- Consumes: DB-Spalten aus Task 1.
- Produces: `Produkt` hat zusätzlich `aktionspreis_chf: float | None = None`, `aktionstext: str | None = None`, `aktion_von: str | None = None`, `aktion_bis: str | None = None`. `get_alle_produkte()` füllt diese Felder.

- [ ] **Step 1: Failing test ergänzen**

In `tests/test_produkt_repo.py` ergänzen (eine aktive Aktion auf Produkt 2 setzen, dann laden):

```python
def test_get_alle_produkte_liefert_aktions_felder(db):
    from app.repositories.produkt_repo import get_alle_produkte

    db.execute(
        "UPDATE produkte SET aktionspreis_chf = 12.0, aktionstext = 'MHD 09/2026', "
        "aktion_von = '2026-06-01', aktion_bis = '2026-06-30' WHERE id = 2"
    )
    db.commit()
    produkte = get_alle_produkte(db)
    p2 = next(p for p in produkte if p.id == 2)
    assert p2.aktionspreis_chf == 12.0
    assert p2.aktionstext == "MHD 09/2026"
    assert p2.aktion_von == "2026-06-01"
    assert p2.aktion_bis == "2026-06-30"


def test_get_alle_produkte_ohne_aktion_felder_none(db):
    from app.repositories.produkt_repo import get_alle_produkte

    produkte = get_alle_produkte(db)
    p1 = next(p for p in produkte if p.id == 1)
    assert p1.aktionspreis_chf is None
```

- [ ] **Step 2: Tests laufen lassen — müssen fehlschlagen**

Run: `uv run pytest tests/test_produkt_repo.py -v`
Expected: FAIL (Felder fehlen / SELECT liefert sie nicht).

- [ ] **Step 3: Model erweitern**

In `app/models.py`, `class Produkt` um vier Felder nach `aktiv: bool = True` ergänzen:

```python
    aktionspreis_chf: float | None = None
    aktionstext: str | None = None
    aktion_von: str | None = None
    aktion_bis: str | None = None
```

- [ ] **Step 4: SELECT in `get_alle_produkte` erweitern**

In `app/repositories/produkt_repo.py` das SELECT ersetzen:

```python
def get_alle_produkte(conn: sqlite3.Connection) -> list[Produkt]:
    rows = conn.execute(
        "SELECT id, name, menge_ml, preis_chf, beschreibung, bild_pfad, aktiv, "
        "aktionspreis_chf, aktionstext, aktion_von, aktion_bis "
        "FROM produkte WHERE aktiv = 1 ORDER BY menge_ml"
    ).fetchall()
    return [Produkt(**dict(row)) for row in rows]
```

- [ ] **Step 5: Tests laufen lassen — müssen bestehen**

Run: `uv run pytest tests/test_produkt_repo.py tests/test_models.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add app/models.py app/repositories/produkt_repo.py tests/test_produkt_repo.py
git commit -m "feat: Produkt-Model und Repo um Aktions-Felder (#134)"
```

---

### Task 4: `berechne_total` rechnet mit Effektiv-Preis + rabattfähiger Subtotal

Die autoritative Serverberechnung nutzt den Aktionspreis und markiert Aktionspositionen.

**Files:**
- Modify: `app/services/bestell_service.py`
- Test: `tests/test_bestell_service.py` (ergänzen)

**Interfaces:**
- Consumes: `effektiver_preis(...)` (Task 2), Aktions-Spalten (Task 1).
- Produces:
  - `berechne_total(conn, items, heute: date | None = None) -> tuple[float, list[dict]]`. Jede Position-Dict hat jetzt zusätzlich `ist_aktion: bool` und `original_preis_chf: float`; `einzelpreis_chf` ist der Effektiv-Preis. `heute` default `date.today()`.
  - `rabattfaehiger_subtotal(positionen: list[dict]) -> float` — Summe `einzelpreis_chf * menge` über alle Positionen mit `ist_aktion is False`.

- [ ] **Step 1: Failing tests ergänzen**

In `tests/test_bestell_service.py` ergänzen:

```python
from datetime import date

from app.services.bestell_service import rabattfaehiger_subtotal


def test_berechne_total_mit_aktionspreis(db):
    db.execute(
        "UPDATE produkte SET aktionspreis_chf = 12.0, aktion_von = '2026-06-01', "
        "aktion_bis = '2026-06-30' WHERE id = 2"
    )
    db.commit()
    items = [WarenkorbItem(produkt_id=2, menge=1)]  # statt 18 jetzt 12
    total, positionen = berechne_total(db, items, heute=date(2026, 6, 23))
    assert total == 12.0
    assert positionen[0]["einzelpreis_chf"] == 12.0
    assert positionen[0]["ist_aktion"] is True
    assert positionen[0]["original_preis_chf"] == 18.0


def test_berechne_total_aktion_abgelaufen_normalpreis(db):
    db.execute(
        "UPDATE produkte SET aktionspreis_chf = 12.0, aktion_bis = '2026-06-22' "
        "WHERE id = 2"
    )
    db.commit()
    items = [WarenkorbItem(produkt_id=2, menge=1)]
    total, positionen = berechne_total(db, items, heute=date(2026, 6, 23))
    assert total == 18.0
    assert positionen[0]["ist_aktion"] is False


def test_rabattfaehiger_subtotal_nur_nicht_aktion():
    positionen = [
        {"einzelpreis_chf": 8.0, "menge": 2, "ist_aktion": False},  # 16
        {"einzelpreis_chf": 12.0, "menge": 1, "ist_aktion": True},  # ausgeschlossen
    ]
    assert rabattfaehiger_subtotal(positionen) == 16.0


def test_rabattfaehiger_subtotal_reine_aktion_null():
    positionen = [{"einzelpreis_chf": 12.0, "menge": 1, "ist_aktion": True}]
    assert rabattfaehiger_subtotal(positionen) == 0.0
```

- [ ] **Step 2: Tests laufen lassen — müssen fehlschlagen**

Run: `uv run pytest tests/test_bestell_service.py -v`
Expected: FAIL.

- [ ] **Step 3: `berechne_total` + Helper implementieren**

`app/services/bestell_service.py` — Imports oben ergänzen und Funktionen ersetzen/ergänzen:

```python
import sqlite3
from datetime import date

from app.models import WarenkorbItem
from app.services.aktions_service import effektiver_preis


def berechne_versandkosten(warenwert: float, versandart: str = "versand") -> float:
    if versandart == "abholung":
        return 0.0
    return 0.0 if warenwert >= 100 else 9.90


def berechne_total(
    conn: sqlite3.Connection,
    items: list[WarenkorbItem],
    heute: date | None = None,
) -> tuple[float, list[dict]]:
    """Validiert Items gegen DB und berechnet Total mit Effektiv-Preis.

    Returns: (total, positionen) wobei jede Position
    {"produkt_id", "menge", "einzelpreis_chf", "ist_aktion",
     "original_preis_chf"} enthält.
    """
    if heute is None:
        heute = date.today()
    positionen = []
    total = 0.0
    for item in items:
        row = conn.execute(
            "SELECT id, preis_chf, aktionspreis_chf, aktion_von, aktion_bis "
            "FROM produkte WHERE id = ? AND aktiv = 1",
            (item.produkt_id,),
        ).fetchone()
        if not row:
            raise ValueError(f"Produkt {item.produkt_id} nicht gefunden")
        ep = effektiver_preis(
            row["preis_chf"],
            row["aktionspreis_chf"],
            row["aktion_von"],
            row["aktion_bis"],
            heute,
        )
        positionen.append(
            {
                "produkt_id": item.produkt_id,
                "menge": item.menge,
                "einzelpreis_chf": ep.preis,
                "ist_aktion": ep.ist_aktion,
                "original_preis_chf": ep.original_preis,
            }
        )
        total += ep.preis * item.menge
    return total, positionen


def rabattfaehiger_subtotal(positionen: list[dict]) -> float:
    """Summe der Nicht-Aktions-Positionen — Basis für Rabattcodes."""
    return sum(
        p["einzelpreis_chf"] * p["menge"]
        for p in positionen
        if not p["ist_aktion"]
    )
```

- [ ] **Step 4: Tests laufen lassen — müssen bestehen**

Run: `uv run pytest tests/test_bestell_service.py -v`
Expected: PASS (inkl. der bestehenden `test_berechne_total`-Tests, da Verhalten ohne Aktion unverändert).

- [ ] **Step 5: Commit**

```bash
git add app/services/bestell_service.py tests/test_bestell_service.py
git commit -m "feat: berechne_total nutzt Aktionspreis + rabattfähiger Subtotal (#134)"
```

---

### Task 5: Bestell-Route — Rabattcode nur auf Nicht-Aktions-Anteil

Die Order-Route nutzt den rabattfähigen Subtotal und lehnt Codes bei reinem Aktions-Warenkorb ab.

**Files:**
- Modify: `app/routers/bestellungen.py` (Block ab `total, positionen = berechne_total(...)`)
- Test: `tests/test_aktionspreis_bestellung.py` (neu)

**Interfaces:**
- Consumes: `rabattfaehiger_subtotal()` (Task 4), `pruefe_rabattcode()`.
- Produces: Bei gemischtem Warenkorb bezieht sich der Rabatt nur auf Nicht-Aktionsware; reiner Aktions-Warenkorb mit Code → HTTP 400.

- [ ] **Step 1: Failing tests schreiben**

`tests/test_aktionspreis_bestellung.py`:

```python
import json


def _setze_aktion(produkt_id, aktionspreis):
    from app.database import get_db

    conn = get_db()
    conn.execute(
        "UPDATE produkte SET aktionspreis_chf = ? WHERE id = ?",
        (aktionspreis, produkt_id),
    )
    conn.commit()
    conn.close()


def _erstelle_rabattcode(code, art, wert):
    from app.database import get_db

    conn = get_db()
    conn.execute(
        "INSERT INTO rabattcodes (code, rabattart, rabattwert, gueltig_von, "
        "gueltig_bis) VALUES (?, ?, ?, '2026-01-01', '2026-12-31')",
        (code, art, wert),
    )
    conn.commit()
    conn.close()


def test_code_nur_auf_nicht_aktions_anteil(client, csrf_token):
    from app.database import get_db

    _setze_aktion(2, 12.0)  # Produkt 2 in Aktion
    _erstelle_rabattcode("ZEHN", "prozent", 10.0)
    # Warenkorb: 1x Produkt 1 (8.- normal) + 1x Produkt 2 (12.- Aktion)
    cart = json.dumps([{"produkt_id": 1, "menge": 1}, {"produkt_id": 2, "menge": 1}])
    resp = client.post(
        "/bestellen",
        data={
            "vorname": "T", "nachname": "U", "email": "t@example.com",
            "strasse": "Str. 1", "plz": "4600", "ort": "Olten",
            "versandart": "abholung", "zahlungsart": "abholung_bar",
            "cart_data": cart, "rabattcode": "ZEHN", "csrf_token": csrf_token,
        },
        follow_redirects=False,
    )
    assert resp.status_code in (200, 303)
    conn = get_db()
    row = conn.execute(
        "SELECT rabattbetrag_chf, total_chf FROM bestellungen WHERE id = 1"
    ).fetchone()
    conn.close()
    # 10% nur auf den 8.- Nicht-Aktionsanteil = 0.80 (5-Rappen-gerundet)
    assert row["rabattbetrag_chf"] == 0.80
    # Total: 8 + 12 - 0.80 + 0 Versand = 19.20
    assert row["total_chf"] == 19.20


def test_reiner_aktionswarenkorb_lehnt_code_ab(client, csrf_token):
    _setze_aktion(2, 12.0)
    _erstelle_rabattcode("ZEHN", "prozent", 10.0)
    cart = json.dumps([{"produkt_id": 2, "menge": 1}])  # nur Aktionsware
    resp = client.post(
        "/bestellen",
        data={
            "vorname": "T", "nachname": "U", "email": "t@example.com",
            "strasse": "Str. 1", "plz": "4600", "ort": "Olten",
            "versandart": "abholung", "zahlungsart": "abholung_bar",
            "cart_data": cart, "rabattcode": "ZEHN", "csrf_token": csrf_token,
        },
        follow_redirects=False,
    )
    assert resp.status_code == 400
```

> Hinweis: Ohne explizite `aktion_von/aktion_bis` gilt die Aktion sofort und unbegrenzt — `date.today()` liegt im Gültigkeitsbereich.

- [ ] **Step 2: Tests laufen lassen — müssen fehlschlagen**

Run: `uv run pytest tests/test_aktionspreis_bestellung.py -v`
Expected: FAIL (Rabatt aktuell auf vollem Total).

- [ ] **Step 3: Rabattcode-Block in `bestellungen.py` anpassen**

In `app/routers/bestellungen.py`: Import-Zeile erweitern:

```python
from app.services.bestell_service import (
    berechne_total,
    berechne_versandkosten,
    rabattfaehiger_subtotal,
)
```

Den Rabattcode-Block (aktuell ab `if rabattcode:` mit `pruefe_rabattcode(conn, rabattcode, email, total)`) ersetzen durch:

```python
        # Rabattcode pruefen — gilt nur auf Nicht-Aktions-Anteil
        rabattcode_id = None
        rabattbetrag = 0.0
        if rabattcode:
            from app.services.rabattcode_service import pruefe_rabattcode

            rabattbasis = rabattfaehiger_subtotal(positionen)
            if rabattbasis <= 0:
                raise ValueError(
                    "Auf Aktionsprodukte ist kein zusätzlicher Rabattcode möglich."
                )
            rc_result = pruefe_rabattcode(conn, rabattcode, email, rabattbasis)
            if rc_result["gueltig"]:
                rabattcode_id = rc_result["rabattcode_id"]
                rabattbetrag = rc_result["rabattbetrag"]
            else:
                raise ValueError(f"Rabattcode ungültig: {rc_result['fehler']}")
```

> Die bestehende `versandkosten = berechne_versandkosten(total, versandart)`-Zeile und `gesamt = total - rabattbetrag + versandkosten` bleiben unverändert (Versand auf vollem Warenwert, Total korrekt).

- [ ] **Step 4: Tests laufen lassen — müssen bestehen**

Run: `uv run pytest tests/test_aktionspreis_bestellung.py tests/test_api_rabattcodes.py -v`
Expected: PASS (auch bestehende Rabattcode-Tests grün, da ohne Aktion `rabattbasis == total`).

- [ ] **Step 5: Commit**

```bash
git add app/routers/bestellungen.py tests/test_aktionspreis_bestellung.py
git commit -m "feat: Rabattcode greift nur auf Nicht-Aktions-Anteil (#134)"
```

---

### Task 6: Produktkarte zeigt Aktionspreis

Die Startseite rendert Badge, durchgestrichenen Originalpreis, Aktionspreis, Prozent-Badge und Begründungstext; `data-product-price` trägt den Aktionspreis.

**Files:**
- Modify: `app/routers/produkte.py` (`startseite`)
- Modify: `templates/produkte.html`
- Test: `tests/test_api_produkte.py` (ergänzen)

**Interfaces:**
- Consumes: `effektiver_preis()` (Task 2), `get_alle_produkte()` (Task 3).
- Produces: Template-Context `produkte` ist eine Liste von Dicts mit `id, name, beschreibung, bild_pfad, preis, ist_aktion, original_preis, prozent, aktionstext`.

- [ ] **Step 1: Failing test ergänzen**

In `tests/test_api_produkte.py` ergänzen:

```python
def test_startseite_zeigt_aktionspreis(client):
    from app.database import get_db

    conn = get_db()
    conn.execute(
        "UPDATE produkte SET aktionspreis_chf = 12.0, "
        "aktionstext = 'MHD 09/2026' WHERE id = 2"
    )
    conn.commit()
    conn.close()
    resp = client.get("/")
    assert resp.status_code == 200
    assert "RABATT" in resp.text
    assert "MHD 09/2026" in resp.text
    assert "CHF 12.00" in resp.text


def test_startseite_ohne_aktion_kein_badge(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "RABATT" not in resp.text
```

- [ ] **Step 2: Tests laufen lassen — müssen fehlschlagen**

Run: `uv run pytest tests/test_api_produkte.py -v`
Expected: FAIL.

- [ ] **Step 3: Produkte-Route Context aufbauen**

`app/routers/produkte.py` ersetzen:

```python
from datetime import date

from fastapi import APIRouter, Request

from app.database import get_db
from app.repositories.produkt_repo import get_alle_produkte
from app.services.aktions_service import effektiver_preis
from app.templating import templates

router = APIRouter()


@router.get("/")
def startseite(request: Request):
    conn = get_db()
    try:
        produkte = get_alle_produkte(conn)
    finally:
        conn.close()
    heute = date.today()
    ansichten = []
    for p in produkte:
        ep = effektiver_preis(
            p.preis_chf, p.aktionspreis_chf, p.aktion_von, p.aktion_bis, heute
        )
        ansichten.append(
            {
                "id": p.id,
                "name": p.name,
                "beschreibung": p.beschreibung,
                "bild_pfad": p.bild_pfad,
                "preis": ep.preis,
                "ist_aktion": ep.ist_aktion,
                "original_preis": ep.original_preis,
                "prozent": ep.prozent,
                "aktionstext": p.aktionstext,
            }
        )
    return templates.TemplateResponse(
        request, "produkte.html", {"produkte": ansichten, "active_page": "produkte"}
    )
```

- [ ] **Step 4: Produktkarte im Template anpassen**

In `templates/produkte.html` den Karten-Block (`{% for produkt in produkte %}` … `{% endfor %}`) ersetzen. Karte als `relative` für das Badge; Preisbereich zeigt bei Aktion durchgestrichenen Originalpreis + Aktionspreis + Prozent-Badge + Begründungstext:

```html
                {% for produkt in produkte %}
                <div class="relative bg-stone-900/75 backdrop-blur-[4px] rounded-lg p-6 flex flex-col shadow-md border border-stone-600/15 hover:shadow-lg hover:-translate-y-1 transition-all duration-200">
                    {% if produkt.ist_aktion %}
                    <span class="absolute top-3 right-3 bg-red-600 text-white text-xs font-bold px-2 py-1 rounded">RABATT</span>
                    {% endif %}
                    {% if produkt.bild_pfad %}
                    <img src="/static/images/{{ produkt.bild_pfad }}" alt="{{ produkt.name }}"
                         class="w-full h-48 object-contain mb-4">
                    {% endif %}
                    <h3 class="font-display text-2xl font-bold text-accent">{{ produkt.name }}</h3>
                    <p class="text-stone-200 mt-2 flex-1">{{ produkt.beschreibung }}</p>
                    {% if produkt.ist_aktion and produkt.aktionstext %}
                    <p class="text-accent text-sm mt-2">{{ produkt.aktionstext }}</p>
                    {% endif %}
                    <div class="mt-4 flex items-center justify-between">
                        <div class="flex items-baseline gap-2">
                            {% if produkt.ist_aktion %}
                            <span class="text-stone-400 line-through text-sm">CHF {{ "%.2f"|format(produkt.original_preis) }}</span>
                            <span class="text-xl font-bold">CHF {{ "%.2f"|format(produkt.preis) }}</span>
                            <span class="bg-accent text-stone-900 text-xs font-bold px-1.5 py-0.5 rounded">−{{ produkt.prozent }}%</span>
                            {% else %}
                            <span class="text-xl font-bold">CHF {{ "%.2f"|format(produkt.preis) }}</span>
                            {% endif %}
                        </div>
                        <button type="button"
                                class="add-to-cart-btn bg-accent text-stone-900 px-4 py-2 rounded font-bold hover:bg-yellow-400 transition-colors"
                                data-product-id="{{ produkt.id }}"
                                data-product-name="{{ produkt.name }}"
                                data-product-price="{{ produkt.preis }}"
                                data-product-aktion="{{ '1' if produkt.ist_aktion else '0' }}"
                                data-product-image="/static/images/{{ produkt.bild_pfad }}">
                            In den Warenkorb
                        </button>
                    </div>
                </div>
                {% endfor %}
```

- [ ] **Step 5: Tests laufen lassen — müssen bestehen**

Run: `uv run pytest tests/test_api_produkte.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add app/routers/produkte.py templates/produkte.html tests/test_api_produkte.py
git commit -m "feat: Produktkarte zeigt Aktionspreis, Badge und Ersparnis (#134)"
```

---

### Task 7: Warenkorb & Checkout-Vorschau berücksichtigen Aktionsware

Warenkorb-Items tragen ein `aktion`-Flag; die Rabattcode-Live-Vorschau im Checkout bezieht sich auf den Nicht-Aktions-Subtotal.

**Files:**
- Modify: `static/js/cart.js` (`addToCart`, neue `getRabattSubtotal`, Klick-Handler)
- Modify: `templates/checkout.html` (Vorschau-Script: `getRabattSubtotal()` statt `getCartTotal()` als `subtotal`)
- Verifikation: manuell (kein JS-Test-Harness im Projekt)

**Interfaces:**
- Consumes: `data-product-aktion`-Attribut aus Task 6.
- Produces: Warenkorb-Items haben Feld `aktion: bool`. `getRabattSubtotal()` summiert nur Nicht-Aktions-Items. Server bleibt autoritativ (Task 5).

- [ ] **Step 1: `addToCart` und Klick-Handler um Aktions-Flag erweitern**

In `static/js/cart.js`:

`addToCart`-Signatur und Push erweitern:

```javascript
function addToCart(id, name, price, image, buttonEl, aktion) {
    const cart = getCart();
    const existing = cart.find((item) => item.produkt_id === id);
    if (existing) {
        existing.menge += 1;
    } else {
        cart.push({ produkt_id: id, name: name, preis: price, image: image, menge: 1, aktion: !!aktion });
    }
    saveCart(cart);
```

(Rest der Funktion unverändert.)

Den delegierten Klick-Handler am Dateiende erweitern:

```javascript
document.addEventListener("click", (e) => {
    const btn = e.target.closest(".add-to-cart-btn[data-product-id]");
    if (!btn) return;
    addToCart(
        parseInt(btn.dataset.productId, 10),
        btn.dataset.productName,
        parseFloat(btn.dataset.productPrice),
        btn.dataset.productImage,
        btn,
        btn.dataset.productAktion === "1"
    );
});
```

Und eine Helper-Funktion nach `getCartTotal()` ergänzen:

```javascript
function getRabattSubtotal() {
    return getCart().reduce((sum, item) => sum + (item.aktion ? 0 : item.preis * item.menge), 0);
}
```

- [ ] **Step 2: Checkout-Vorschau auf rabattfähigen Subtotal umstellen**

In `templates/checkout.html`, Funktion `rabattcodeEinloesen()`: die Zeile

```javascript
    var subtotal = getCartTotal();
```

ersetzen durch:

```javascript
    var subtotal = getRabattSubtotal();
    if (subtotal <= 0) {
        zeigeFeedback("Auf Aktionsprodukte ist kein zusätzlicher Rabattcode möglich.", false);
        return;
    }
```

> Die Preis-Zusammenfassung (`aktualisierePreiszusammenfassung`) nutzt weiterhin `getCartTotal()` für Warenkorb/Versand/Total — korrekt, da der Warenkorb bereits Aktionspreise enthält. Nur die an die Vorschau-API gesendete Rabattbasis ändert sich. Der Server (Task 5) bleibt die finale Autorität.

- [ ] **Step 3: Bestehende Tests laufen lassen (Regression)**

Run: `uv run pytest tests/test_api_rabattcodes.py -v`
Expected: PASS (Server-API unverändert; JS nicht von pytest abgedeckt).

- [ ] **Step 4: Manuelle Verifikation (dokumentieren, nicht blockierend)**

Lokal `make run` (oder Projektäquivalent), dann im Browser:
1. Produkt mit Aktion + Normalprodukt in den Warenkorb legen.
2. Checkout: Rabattcode einlösen → Rabatt nur auf Normalprodukt-Anteil.
3. Nur Aktionsprodukt im Korb → Code-Einlösung zeigt Hinweis, kein Rabatt.

- [ ] **Step 5: Commit**

```bash
git add static/js/cart.js templates/checkout.html
git commit -m "feat: Warenkorb-Aktionsflag und Rabattcode-Vorschau ohne Aktionsware (#134)"
```

---

### Task 8: Admin-Repo — Produkte laden & Aktion setzen/entfernen

Repo-Funktionen für die Admin-UI: alle Produkte (inkl. inaktive), einzelnes Produkt, Aktion setzen, Aktion entfernen.

**Files:**
- Modify: `app/repositories/produkt_repo.py`
- Test: `tests/test_produkt_repo.py` (ergänzen)

**Interfaces:**
- Produces:
  - `alle_produkte_admin(conn) -> list[dict]` — alle Produkte mit Aktions-Spalten, sortiert nach `menge_ml`.
  - `produkt_laden(conn, produkt_id: int) -> dict | None`.
  - `aktion_setzen(conn, produkt_id, *, aktionspreis_chf: float, aktionstext: str, aktion_von: str | None, aktion_bis: str | None) -> None`.
  - `aktion_entfernen(conn, produkt_id: int) -> None` — setzt alle vier Aktions-Spalten auf NULL.

- [ ] **Step 1: Failing tests ergänzen**

In `tests/test_produkt_repo.py` ergänzen:

```python
def test_aktion_setzen_und_laden(db):
    from app.repositories.produkt_repo import aktion_setzen, produkt_laden

    aktion_setzen(
        db, 2, aktionspreis_chf=12.0, aktionstext="MHD 09/2026",
        aktion_von="2026-06-01", aktion_bis="2026-06-30",
    )
    p = produkt_laden(db, 2)
    assert p["aktionspreis_chf"] == 12.0
    assert p["aktionstext"] == "MHD 09/2026"
    assert p["aktion_von"] == "2026-06-01"
    assert p["aktion_bis"] == "2026-06-30"


def test_aktion_entfernen_setzt_null(db):
    from app.repositories.produkt_repo import aktion_entfernen, aktion_setzen, produkt_laden

    aktion_setzen(db, 2, aktionspreis_chf=12.0, aktionstext="x",
                  aktion_von=None, aktion_bis=None)
    aktion_entfernen(db, 2)
    p = produkt_laden(db, 2)
    assert p["aktionspreis_chf"] is None
    assert p["aktionstext"] is None
    assert p["aktion_von"] is None
    assert p["aktion_bis"] is None


def test_alle_produkte_admin_enthaelt_alle(db):
    from app.repositories.produkt_repo import alle_produkte_admin

    produkte = alle_produkte_admin(db)
    assert len(produkte) == 3
    assert produkte[0]["menge_ml"] <= produkte[-1]["menge_ml"]
```

- [ ] **Step 2: Tests laufen lassen — müssen fehlschlagen**

Run: `uv run pytest tests/test_produkt_repo.py -v`
Expected: FAIL.

- [ ] **Step 3: Repo-Funktionen ergänzen**

In `app/repositories/produkt_repo.py` ans Dateiende anhängen:

```python
def alle_produkte_admin(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        "SELECT id, name, menge_ml, preis_chf, beschreibung, bild_pfad, aktiv, "
        "aktionspreis_chf, aktionstext, aktion_von, aktion_bis "
        "FROM produkte ORDER BY menge_ml"
    ).fetchall()
    return [dict(row) for row in rows]


def produkt_laden(conn: sqlite3.Connection, produkt_id: int) -> dict | None:
    row = conn.execute(
        "SELECT id, name, menge_ml, preis_chf, beschreibung, bild_pfad, aktiv, "
        "aktionspreis_chf, aktionstext, aktion_von, aktion_bis "
        "FROM produkte WHERE id = ?",
        (produkt_id,),
    ).fetchone()
    return dict(row) if row else None


def aktion_setzen(
    conn: sqlite3.Connection,
    produkt_id: int,
    *,
    aktionspreis_chf: float,
    aktionstext: str,
    aktion_von: str | None,
    aktion_bis: str | None,
) -> None:
    conn.execute(
        "UPDATE produkte SET aktionspreis_chf = ?, aktionstext = ?, "
        "aktion_von = ?, aktion_bis = ? WHERE id = ?",
        (aktionspreis_chf, aktionstext, aktion_von or None, aktion_bis or None, produkt_id),
    )
    conn.commit()


def aktion_entfernen(conn: sqlite3.Connection, produkt_id: int) -> None:
    conn.execute(
        "UPDATE produkte SET aktionspreis_chf = NULL, aktionstext = NULL, "
        "aktion_von = NULL, aktion_bis = NULL WHERE id = ?",
        (produkt_id,),
    )
    conn.commit()
```

- [ ] **Step 4: Tests laufen lassen — müssen bestehen**

Run: `uv run pytest tests/test_produkt_repo.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/repositories/produkt_repo.py tests/test_produkt_repo.py
git commit -m "feat: Admin-Repo für Produkt-Aktionen (#134)"
```

---

### Task 9: Admin-UI für Aktionen (Router, Templates, Navigation)

Liste der Produkte mit Aktions-Status, Formular zum Setzen/Entfernen, mit Validierung (`aktionspreis < preis_chf`), CSRF-Schutz und Audit-Log.

**Files:**
- Create: `app/routers/produkt_admin.py`
- Create: `templates/admin/produkte.html`
- Create: `templates/admin/produkt_aktion_form.html`
- Modify: `app/main.py` (Router registrieren)
- Modify: `templates/admin/base.html` (Nav-Link)
- Test: `tests/test_api_produkt_admin.py` (neu)

**Interfaces:**
- Consumes: `alle_produkte_admin`, `produkt_laden`, `aktion_setzen`, `aktion_entfernen` (Task 8); `log_eintrag_schreiben`; `require_csrf`, `admin_identity`, `generiere_csrf_token`; `validate_session`.
- Produces: Routen `GET /admin/produkte`, `GET /admin/produkte/{id}/aktion`, `POST /admin/produkte/{id}/aktion`.

- [ ] **Step 1: Failing tests schreiben**

`tests/test_api_produkt_admin.py`:

```python
def _make_admin_client(tmp_path, monkeypatch):
    import bcrypt
    from fastapi.testclient import TestClient

    pw_hash = bcrypt.hashpw(b"testpass", bcrypt.gensalt()).decode()
    monkeypatch.setattr(
        "app.config.settings.database_path", str(tmp_path / "admin_test.db")
    )
    monkeypatch.setattr("app.config.settings.admin_credentials", f"dev:{pw_hash}")
    monkeypatch.setattr("app.config.settings.cookie_secure", False)
    from app.database import init_db

    init_db()
    from app.main import app

    return TestClient(app)


def _admin_login(admin_client):
    from app.config import settings
    from app.csrf import generiere_csrf_token

    get_resp = admin_client.get("/admin/login")
    csrf_id = get_resp.cookies.get("csrf_id", "")
    csrf = generiere_csrf_token(settings.secret_key, identity=f"anon:{csrf_id}")
    resp = admin_client.post(
        "/admin/login",
        data={"password": "testpass", "csrf_token": csrf},
        follow_redirects=False,
    )
    return resp.cookies


def _csrf_fuer_session(cookies):
    from app.config import settings
    from app.csrf import admin_identity, generiere_csrf_token

    return generiere_csrf_token(
        settings.secret_key, identity=admin_identity(cookies.get("admin_session"))
    )


def test_admin_produkte_liste(tmp_path, monkeypatch):
    admin_client = _make_admin_client(tmp_path, monkeypatch)
    admin_client.cookies = _admin_login(admin_client)
    resp = admin_client.get("/admin/produkte")
    assert resp.status_code == 200
    assert "Olivenöl 750ml" in resp.text


def test_admin_aktion_setzen(tmp_path, monkeypatch):
    admin_client = _make_admin_client(tmp_path, monkeypatch)
    cookies = _admin_login(admin_client)
    admin_client.cookies = cookies
    csrf = _csrf_fuer_session(cookies)
    resp = admin_client.post(
        "/admin/produkte/2/aktion",
        data={
            "aktionspreis_chf": "12.00", "aktionstext": "MHD 09/2026",
            "aktion_von": "", "aktion_bis": "", "csrf_token": csrf,
        },
        follow_redirects=False,
    )
    assert resp.status_code == 303
    from app.database import get_db

    conn = get_db()
    row = conn.execute(
        "SELECT aktionspreis_chf, aktionstext FROM produkte WHERE id = 2"
    ).fetchone()
    conn.close()
    assert row["aktionspreis_chf"] == 12.0
    assert row["aktionstext"] == "MHD 09/2026"


def test_admin_aktion_groesser_als_preis_abgelehnt(tmp_path, monkeypatch):
    admin_client = _make_admin_client(tmp_path, monkeypatch)
    cookies = _admin_login(admin_client)
    admin_client.cookies = cookies
    csrf = _csrf_fuer_session(cookies)
    resp = admin_client.post(
        "/admin/produkte/2/aktion",
        data={
            "aktionspreis_chf": "20.00", "aktionstext": "zu teuer",
            "aktion_von": "", "aktion_bis": "", "csrf_token": csrf,
        },
        follow_redirects=False,
    )
    assert resp.status_code == 400
    from app.database import get_db

    conn = get_db()
    row = conn.execute("SELECT aktionspreis_chf FROM produkte WHERE id = 2").fetchone()
    conn.close()
    assert row["aktionspreis_chf"] is None


def test_admin_aktion_entfernen(tmp_path, monkeypatch):
    admin_client = _make_admin_client(tmp_path, monkeypatch)
    cookies = _admin_login(admin_client)
    admin_client.cookies = cookies
    csrf = _csrf_fuer_session(cookies)
    # erst setzen
    admin_client.post(
        "/admin/produkte/2/aktion",
        data={"aktionspreis_chf": "12.00", "aktionstext": "x",
              "aktion_von": "", "aktion_bis": "", "csrf_token": csrf},
        follow_redirects=False,
    )
    # dann leerer Aktionspreis = entfernen
    resp = admin_client.post(
        "/admin/produkte/2/aktion",
        data={"aktionspreis_chf": "", "aktionstext": "",
              "aktion_von": "", "aktion_bis": "", "csrf_token": csrf},
        follow_redirects=False,
    )
    assert resp.status_code == 303
    from app.database import get_db

    conn = get_db()
    row = conn.execute("SELECT aktionspreis_chf FROM produkte WHERE id = 2").fetchone()
    conn.close()
    assert row["aktionspreis_chf"] is None


def test_admin_produkte_ohne_login_redirect(tmp_path, monkeypatch):
    admin_client = _make_admin_client(tmp_path, monkeypatch)
    resp = admin_client.get("/admin/produkte", follow_redirects=False)
    assert resp.status_code == 303
```

- [ ] **Step 2: Tests laufen lassen — müssen fehlschlagen**

Run: `uv run pytest tests/test_api_produkt_admin.py -v`
Expected: FAIL (Routen fehlen).

- [ ] **Step 3: Router implementieren**

`app/routers/produkt_admin.py`:

```python
from fastapi import APIRouter, Cookie, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse

from app.config import settings
from app.csrf import admin_identity, generiere_csrf_token, require_csrf
from app.database import get_db
from app.repositories.admin_repo import log_eintrag_schreiben
from app.repositories.produkt_repo import (
    aktion_entfernen,
    aktion_setzen,
    alle_produkte_admin,
    produkt_laden,
)
from app.services.auth_service import validate_session
from app.templating import templates

router = APIRouter()


def _get_admin_label(admin_session: str | None) -> str | None:
    if not admin_session:
        return None
    return validate_session(
        admin_session,
        secret=settings.secret_key,
        max_age=settings.admin_session_max_age,
    )


@router.get("/admin/produkte")
def admin_produkte_liste(request: Request, admin_session: str | None = Cookie(None)):
    label = _get_admin_label(admin_session)
    if not label:
        return RedirectResponse("/admin/login", status_code=303)
    conn = get_db()
    try:
        produkte = alle_produkte_admin(conn)
    finally:
        conn.close()
    csrf = generiere_csrf_token(
        settings.secret_key, identity=admin_identity(admin_session or "")
    )
    return templates.TemplateResponse(
        request,
        "admin/produkte.html",
        {"admin_label": label, "csrf_token": csrf, "produkte": produkte},
    )


@router.get("/admin/produkte/{produkt_id}/aktion")
def admin_aktion_formular(
    request: Request, produkt_id: int, admin_session: str | None = Cookie(None)
):
    label = _get_admin_label(admin_session)
    if not label:
        return RedirectResponse("/admin/login", status_code=303)
    conn = get_db()
    try:
        produkt = produkt_laden(conn, produkt_id)
    finally:
        conn.close()
    if not produkt:
        return RedirectResponse("/admin/produkte", status_code=303)
    csrf = generiere_csrf_token(
        settings.secret_key, identity=admin_identity(admin_session or "")
    )
    return templates.TemplateResponse(
        request,
        "admin/produkt_aktion_form.html",
        {"admin_label": label, "csrf_token": csrf, "produkt": produkt},
    )


@router.post("/admin/produkte/{produkt_id}/aktion", dependencies=[Depends(require_csrf)])
def admin_aktion_speichern(
    request: Request,
    produkt_id: int,
    aktionspreis_chf: str = Form(""),
    aktionstext: str = Form(""),
    aktion_von: str = Form(""),
    aktion_bis: str = Form(""),
    csrf_token: str = Form(""),
    admin_session: str | None = Cookie(None),
):
    label = _get_admin_label(admin_session)
    if not label:
        return RedirectResponse("/admin/login", status_code=303)
    conn = get_db()
    try:
        produkt = produkt_laden(conn, produkt_id)
        if not produkt:
            raise HTTPException(404, "Produkt nicht gefunden")
        if not aktionspreis_chf.strip():
            aktion_entfernen(conn, produkt_id)
            log_eintrag_schreiben(
                conn, admin_label=label, aktion="aktion_entfernt",
                details=produkt["name"],
            )
        else:
            preis = float(aktionspreis_chf)
            if preis <= 0 or preis >= produkt["preis_chf"]:
                raise HTTPException(
                    400, "Aktionspreis muss grösser als 0 und kleiner als der "
                    "Normalpreis sein.",
                )
            aktion_setzen(
                conn, produkt_id,
                aktionspreis_chf=preis,
                aktionstext=aktionstext.strip(),
                aktion_von=aktion_von.strip() or None,
                aktion_bis=aktion_bis.strip() or None,
            )
            log_eintrag_schreiben(
                conn, admin_label=label, aktion="aktion_gesetzt",
                details=f"{produkt['name']}: CHF {preis:.2f}",
            )
    finally:
        conn.close()
    return RedirectResponse("/admin/produkte", status_code=303)
```

- [ ] **Step 4: Router registrieren**

In `app/main.py`: in den `from app.routers import (...)`-Block `produkt_admin` ergänzen und nach `app.include_router(rabattcodes.router)` einfügen:

```python
app.include_router(produkt_admin.router)
```

- [ ] **Step 5: Listen-Template anlegen**

`templates/admin/produkte.html`:

```html
{% extends "admin/base.html" %}
{% block title %}Aktionspreise{% endblock %}
{% block content %}
<h1 class="font-display text-5xl font-bold text-accent mb-8">Aktionspreise</h1>
<div class="flex flex-col gap-3">
    {% for p in produkte %}
    <div class="bg-stone-700 rounded-lg p-4 shadow-md flex items-center justify-between gap-4">
        <div>
            <div class="font-semibold">{{ p.name }}</div>
            <div class="text-stone-400 text-sm">
                Normalpreis: CHF {{ "%.2f"|format(p.preis_chf) }}
                {% if p.aktionspreis_chf %}
                — <span class="text-accent">Aktion: CHF {{ "%.2f"|format(p.aktionspreis_chf) }}</span>
                {% if p.aktion_von or p.aktion_bis %}
                ({{ p.aktion_von or "…" }} – {{ p.aktion_bis or "…" }})
                {% endif %}
                {% endif %}
            </div>
        </div>
        <a href="/admin/produkte/{{ p.id }}/aktion"
           class="bg-accent text-stone-900 px-4 py-2 rounded font-bold hover:bg-yellow-400 transition-colors whitespace-nowrap">
            {{ "Aktion bearbeiten" if p.aktionspreis_chf else "Aktion setzen" }}
        </a>
    </div>
    {% endfor %}
</div>
{% endblock %}
```

- [ ] **Step 6: Formular-Template anlegen**

`templates/admin/produkt_aktion_form.html`:

```html
{% extends "admin/base.html" %}
{% block title %}Aktion: {{ produkt.name }}{% endblock %}
{% block content %}
<a href="/admin/produkte" class="text-stone-400 hover:text-accent text-sm transition-colors">&larr; Zurück</a>
<h1 class="font-display text-5xl font-bold text-accent mt-4 mb-2">Aktion: {{ produkt.name }}</h1>
<p class="text-stone-400 mb-8">Normalpreis: CHF {{ "%.2f"|format(produkt.preis_chf) }}</p>
<form method="post" class="max-w-lg space-y-6">
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
    <div class="bg-stone-700 rounded-lg p-6 shadow-md space-y-4">
        <div>
            <label class="block text-stone-400 text-sm mb-1">Aktionspreis CHF <span class="text-stone-500">(leer = Aktion entfernen)</span></label>
            <input type="number" name="aktionspreis_chf" step="0.01" min="0"
                   value="{{ produkt.aktionspreis_chf if produkt.aktionspreis_chf else '' }}"
                   class="w-full bg-stone-800 border border-stone-600 rounded px-3 py-2">
        </div>
        <div>
            <label class="block text-stone-400 text-sm mb-1">Begründungstext</label>
            <input type="text" name="aktionstext" maxlength="200"
                   value="{{ produkt.aktionstext or '' }}"
                   placeholder="z.B. Mindesthaltbarkeit 09/2026"
                   class="w-full bg-stone-800 border border-stone-600 rounded px-3 py-2">
        </div>
        <div class="grid grid-cols-2 gap-4">
            <div>
                <label class="block text-stone-400 text-sm mb-1">Gültig von <span class="text-stone-500">(optional)</span></label>
                <input type="date" name="aktion_von" value="{{ produkt.aktion_von or '' }}"
                       class="w-full bg-stone-800 border border-stone-600 rounded px-3 py-2">
            </div>
            <div>
                <label class="block text-stone-400 text-sm mb-1">Gültig bis <span class="text-stone-500">(optional)</span></label>
                <input type="date" name="aktion_bis" value="{{ produkt.aktion_bis or '' }}"
                       class="w-full bg-stone-800 border border-stone-600 rounded px-3 py-2">
            </div>
        </div>
    </div>
    <button type="submit"
            class="w-full bg-accent text-stone-900 py-3 rounded font-bold text-lg hover:bg-yellow-400 transition-colors">
        Speichern
    </button>
</form>
{% endblock %}
```

- [ ] **Step 7: Nav-Link ergänzen**

In `templates/admin/base.html` nach dem Rabattcodes-Link (Zeile mit `href="/admin/rabattcodes"`) einfügen:

```html
                <a href="/admin/produkte" class="text-stone-400 hover:text-accent text-sm transition-colors ml-4">Aktionspreise</a>
```

- [ ] **Step 8: Tests laufen lassen — müssen bestehen**

Run: `uv run pytest tests/test_api_produkt_admin.py -v`
Expected: PASS (6 Tests).

- [ ] **Step 9: Commit**

```bash
git add app/routers/produkt_admin.py app/main.py templates/admin/produkte.html templates/admin/produkt_aktion_form.html templates/admin/base.html tests/test_api_produkt_admin.py
git commit -m "feat: Admin-UI für produktbezogene Aktionspreise (#134)"
```

---

### Task 10: Dokumentation

arc42 und user-stories-testplan aktualisieren.

**Files:**
- Modify: `docs/arc42.md`
- Modify: `docs/user-stories-testplan.md`

**Interfaces:** keine (Doku).

- [ ] **Step 1: arc42 ergänzen**

In `docs/arc42.md` einen kurzen Abschnitt zur Aktionspreis-Mechanik ergänzen: zentrale Funktion `effektiver_preis()` als einzige Preisautorität; Spalten an `produkte`; Abgrenzung zu Rabattcodes (Einzelpreis- vs. Warenkorb-Ebene); Regel „Rabattcode nur auf Nicht-Aktions-Anteil". An die bestehende Struktur/Überschriftenebene des Dokuments anpassen.

- [ ] **Step 2: user-stories-testplan ergänzen**

In `docs/user-stories-testplan.md` eine User Story + Testfälle ergänzen:
- Als SH kann ich einem Produkt einen befristeten Aktionspreis mit Begründungstext geben.
- Testfälle: Aktion sichtbar auf Produktkarte (Badge, durchgestrichen, −%, Text); Bestellung rechnet mit Aktionspreis; Rabattcode nur auf Nicht-Aktionsanteil; reiner Aktions-Warenkorb lehnt Code ab; Aktion läuft nach `aktion_bis` automatisch aus.
An Format und Nummerierung der bestehenden Einträge anpassen.

- [ ] **Step 3: Vollständige Test-Suite + Lint**

Run: `uv run pytest -q && ruff check .`
Expected: alle Tests grün, keine Lint-Fehler.

- [ ] **Step 4: Commit**

```bash
git add docs/arc42.md docs/user-stories-testplan.md
git commit -m "docs: Aktionspreise in arc42 und user-stories-testplan (#134)"
```

---

## Self-Review

**Spec-Abdeckung:**
- AK „Aktionspreis + Begründungstext, optional, mit Zeitraum" → Tasks 1, 2, 8, 9. ✔
- AK „Produktkarte zeigt durchgestrichen/Aktion/Badge/%/Text" → Task 6. ✔
- AK „Warenkorb, Total, Stripe, Mails rechnen mit Aktionspreis" → Task 4 (zentral via `berechne_total`, daher Stripe/DB/Mails/QR automatisch). ✔
- AK „Verhalten ohne Aktion unverändert" → Task 4/6 (bestehende Tests bleiben grün), explizit getestet. ✔
- AK „Tests: mit/ohne Aktionspreis, Gültigkeits-Grenzfälle" → Tasks 2, 4, 5. ✔
- AK „Doku aktualisiert" → Task 10. ✔
- Entscheid „Rabattcode nur auf Nicht-Aktions-Anteil" → Tasks 4, 5, 7. ✔
- Entscheid „Admin Self-Service" → Tasks 8, 9. ✔
- Entscheid „Prozent berechnet" → Task 2. ✔

**Platzhalter-Scan:** Keine TBD/TODO; alle Code-Schritte enthalten vollständigen Code. Task 10 beschreibt Doku-Inhalte prosaisch (kein Code nötig), referenziert konkrete Inhalte. ✔

**Typ-Konsistenz:** `effektiver_preis(preis_chf, aktionspreis_chf, aktion_von, aktion_bis, heute)` identisch in Tasks 2, 4, 6 verwendet. `EffektivPreis`-Felder (`preis, ist_aktion, original_preis, prozent`) konsistent. Positions-Dict-Keys (`einzelpreis_chf, ist_aktion, original_preis_chf`) konsistent zwischen Tasks 4 und 5. Repo-Funktionsnamen (`aktion_setzen, aktion_entfernen, produkt_laden, alle_produkte_admin`) konsistent zwischen Tasks 8 und 9. ✔
