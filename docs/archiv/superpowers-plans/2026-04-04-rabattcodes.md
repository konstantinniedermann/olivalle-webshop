# Rabattcodes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rabattcodes im Olivalle Webshop — Admin erstellt Codes, Kunden geben sie im Checkout ein, Preis aktualisiert sich automatisch.

**Architecture:** Neuer Service `rabattcode_service.py` mit Validierungs- und Berechnungslogik. AJAX-Endpoint für Live-Validierung im Checkout. Admin-CRUD über eigene Routes/Templates. DB-Migration für zwei neue Tabellen + Erweiterung von `bestellungen`.

**Tech Stack:** Python/FastAPI, SQLite, Jinja2, Stripe API (Coupons), pytest

**Spec:** `docs/superpowers/specs/2026-04-04-rabattcodes-design.md`

---

## File Structure

| Aktion | Datei | Verantwortung |
|--------|-------|---------------|
| Create | `migrations/003_rabattcodes.sql` | Schema: rabattcodes, code_einloesungen, bestellungen-Erweiterung |
| Create | `app/services/rabattcode_service.py` | Validierung, Berechnung, Einlösung |
| Create | `app/repositories/rabattcode_repo.py` | DB-Queries für Rabattcodes |
| Create | `app/routers/rabattcodes.py` | API-Endpoint + Admin-Routes |
| Create | `templates/admin/rabattcodes.html` | Admin-Übersicht |
| Create | `templates/admin/rabattcode_form.html` | Admin-Formular (Erstellen/Bearbeiten) |
| Create | `tests/test_rabattcode_service.py` | Unit-Tests Service |
| Create | `tests/test_api_rabattcodes.py` | Integration-Tests API + Admin |
| Modify | `app/main.py:22-36` | Router einbinden |
| Modify | `app/repositories/bestell_repo.py:17-58` | bestellung_anlegen() erweitern |
| Modify | `app/routers/bestellungen.py:29-101` | Rabattcode im Bestellprozess |
| Modify | `app/services/stripe_service.py:8-41` | Stripe Coupon anwenden |
| Modify | `app/services/email_service.py:17-66,163-204` | Rabattinfo an Templates übergeben |
| Modify | `templates/checkout.html` | Rabattcode-Eingabefeld |
| Modify | `templates/emails/bestellbestaetigung.html:17-27` | Rabattzeile |
| Modify | `templates/emails/bestellung_stakeholder.html:34-44` | Rabattzeile |
| Modify | `templates/admin/base.html:29-31` | Nav-Link "Rabattcodes" |
| Modify | `templates/admin/bestellung_detail.html:122-131` | Rabattzeile in Positionen |

---

## Task 1: DB-Migration und Repository

**Files:**
- Create: `migrations/003_rabattcodes.sql`
- Create: `app/repositories/rabattcode_repo.py`
- Test: `tests/test_rabattcode_service.py` (DB-Teil)

- [ ] **Step 1: Write failing test for migration tables**

```python
# tests/test_rabattcode_service.py
from datetime import date


def test_rabattcodes_tabelle_existiert(db):
    """Migration 003 erstellt die Tabelle rabattcodes."""
    db.execute(
        "INSERT INTO rabattcodes (code, rabattart, rabattwert, gueltig_von, gueltig_bis) "
        "VALUES ('TEST10', 'prozent', 10.0, '2026-01-01', '2026-12-31')"
    )
    db.commit()
    row = db.execute("SELECT * FROM rabattcodes WHERE code = 'TEST10'").fetchone()
    assert row is not None
    assert row["rabattart"] == "prozent"
    assert row["aktuelle_einloesungen"] == 0
    assert row["aktiv"] == 1


def test_code_einloesungen_tabelle_existiert(db):
    """Migration 003 erstellt die Tabelle code_einloesungen."""
    # Zuerst Rabattcode + Kunde + Bestellung anlegen
    db.execute(
        "INSERT INTO rabattcodes (code, rabattart, rabattwert, gueltig_von, gueltig_bis) "
        "VALUES ('TEST5', 'fixbetrag', 5.0, '2026-01-01', '2026-12-31')"
    )
    db.execute(
        "INSERT INTO kunden (vorname, nachname, email, strasse, plz, ort) "
        "VALUES ('Test', 'User', 'test@example.com', 'Teststr. 1', '4600', 'Olten')"
    )
    db.execute(
        "INSERT INTO bestellungen (kunde_id, zahlungsart, versandart, versandkosten_chf, total_chf) "
        "VALUES (1, 'stripe', 'versand', 9.90, 25.90)"
    )
    db.commit()
    db.execute(
        "INSERT INTO code_einloesungen (rabattcode_id, email, bestellung_id) "
        "VALUES (1, 'test@example.com', 1)"
    )
    db.commit()
    row = db.execute("SELECT * FROM code_einloesungen WHERE email = 'test@example.com'").fetchone()
    assert row is not None


def test_bestellungen_hat_rabattfelder(db):
    """Migration 003 erweitert bestellungen um rabattcode_id und rabattbetrag_chf."""
    db.execute(
        "INSERT INTO kunden (vorname, nachname, email, strasse, plz, ort) "
        "VALUES ('Test', 'User', 'test@example.com', 'Teststr. 1', '4600', 'Olten')"
    )
    db.execute(
        "INSERT INTO bestellungen (kunde_id, zahlungsart, versandart, versandkosten_chf, "
        "total_chf, rabattcode_id, rabattbetrag_chf) "
        "VALUES (1, 'stripe', 'versand', 9.90, 20.90, NULL, 5.00)"
    )
    db.commit()
    row = db.execute("SELECT rabattbetrag_chf FROM bestellungen WHERE id = 1").fetchone()
    assert row["rabattbetrag_chf"] == 5.00
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_rabattcode_service.py -v`
Expected: FAIL — "no such table: rabattcodes"

- [ ] **Step 3: Write migration**

```sql
-- migrations/003_rabattcodes.sql

CREATE TABLE IF NOT EXISTS rabattcodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    rabattart TEXT NOT NULL CHECK (rabattart IN ('prozent', 'fixbetrag')),
    rabattwert REAL NOT NULL CHECK (rabattwert > 0),
    mindestbestellwert_chf REAL,
    max_einloesungen INTEGER,
    aktuelle_einloesungen INTEGER NOT NULL DEFAULT 0,
    gueltig_von TEXT NOT NULL,
    gueltig_bis TEXT NOT NULL,
    aktiv INTEGER NOT NULL DEFAULT 1,
    erstellt_am TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS code_einloesungen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rabattcode_id INTEGER NOT NULL REFERENCES rabattcodes(id),
    email TEXT NOT NULL,
    bestellung_id INTEGER NOT NULL REFERENCES bestellungen(id),
    eingeloest_am TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(rabattcode_id, email)
);

ALTER TABLE bestellungen ADD COLUMN rabattcode_id INTEGER REFERENCES rabattcodes(id);
ALTER TABLE bestellungen ADD COLUMN rabattbetrag_chf REAL NOT NULL DEFAULT 0;
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_rabattcode_service.py -v`
Expected: PASS

- [ ] **Step 5: Write failing test for repository functions**

Append to `tests/test_rabattcode_service.py`:

```python
from app.repositories.rabattcode_repo import (
    rabattcode_anlegen,
    rabattcode_laden,
    rabattcode_laden_by_code,
    einloesung_zaehlen,
    einloesung_speichern,
    ist_bereits_eingeloest,
)


def test_rabattcode_anlegen_und_laden(db):
    code_id = rabattcode_anlegen(
        db,
        code="SOMMER20",
        rabattart="prozent",
        rabattwert=20.0,
        gueltig_von="2026-06-01",
        gueltig_bis="2026-08-31",
    )
    assert code_id > 0
    loaded = rabattcode_laden(db, code_id)
    assert loaded["code"] == "SOMMER20"
    assert loaded["rabattwert"] == 20.0


def test_rabattcode_laden_by_code(db):
    rabattcode_anlegen(
        db, code="HERBST5", rabattart="fixbetrag", rabattwert=5.0,
        gueltig_von="2026-09-01", gueltig_bis="2026-11-30",
    )
    loaded = rabattcode_laden_by_code(db, "herbst5")  # case-insensitive
    assert loaded is not None
    assert loaded["code"] == "HERBST5"


def test_einloesung_speichern_und_pruefen(db):
    code_id = rabattcode_anlegen(
        db, code="EINMAL", rabattart="fixbetrag", rabattwert=5.0,
        gueltig_von="2026-01-01", gueltig_bis="2026-12-31",
    )
    db.execute(
        "INSERT INTO kunden (vorname, nachname, email, strasse, plz, ort) "
        "VALUES ('A', 'B', 'a@b.ch', 'Str. 1', '4600', 'Olten')"
    )
    db.execute(
        "INSERT INTO bestellungen (kunde_id, zahlungsart, versandart, versandkosten_chf, total_chf) "
        "VALUES (1, 'stripe', 'versand', 0, 50)"
    )
    db.commit()

    assert ist_bereits_eingeloest(db, code_id, "a@b.ch") is False
    einloesung_speichern(db, rabattcode_id=code_id, email="a@b.ch", bestellung_id=1)
    assert ist_bereits_eingeloest(db, code_id, "a@b.ch") is True

    loaded = rabattcode_laden(db, code_id)
    assert loaded["aktuelle_einloesungen"] == 1
```

- [ ] **Step 6: Run tests to verify they fail**

Run: `python -m pytest tests/test_rabattcode_service.py::test_rabattcode_anlegen_und_laden -v`
Expected: FAIL — ModuleNotFoundError

- [ ] **Step 7: Implement repository**

```python
# app/repositories/rabattcode_repo.py
import sqlite3


def rabattcode_anlegen(
    conn: sqlite3.Connection,
    *,
    code: str,
    rabattart: str,
    rabattwert: float,
    gueltig_von: str,
    gueltig_bis: str,
    mindestbestellwert_chf: float | None = None,
    max_einloesungen: int | None = None,
) -> int:
    cursor = conn.execute(
        "INSERT INTO rabattcodes "
        "(code, rabattart, rabattwert, mindestbestellwert_chf, "
        "max_einloesungen, gueltig_von, gueltig_bis) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            code.upper().strip(),
            rabattart,
            rabattwert,
            mindestbestellwert_chf,
            max_einloesungen,
            gueltig_von,
            gueltig_bis,
        ),
    )
    conn.commit()
    return cursor.lastrowid


def rabattcode_laden(conn: sqlite3.Connection, code_id: int) -> dict | None:
    row = conn.execute(
        "SELECT * FROM rabattcodes WHERE id = ?", (code_id,)
    ).fetchone()
    return dict(row) if row else None


def rabattcode_laden_by_code(conn: sqlite3.Connection, code: str) -> dict | None:
    row = conn.execute(
        "SELECT * FROM rabattcodes WHERE code = ?", (code.upper().strip(),)
    ).fetchone()
    return dict(row) if row else None


def alle_rabattcodes(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM rabattcodes ORDER BY erstellt_am DESC"
    ).fetchall()
    return [dict(r) for r in rows]


def rabattcode_aktualisieren(
    conn: sqlite3.Connection,
    code_id: int,
    **felder,
) -> None:
    if not felder:
        return
    set_clause = ", ".join(f"{k} = ?" for k in felder)
    values = list(felder.values()) + [code_id]
    conn.execute(f"UPDATE rabattcodes SET {set_clause} WHERE id = ?", values)
    conn.commit()


def einloesung_speichern(
    conn: sqlite3.Connection,
    *,
    rabattcode_id: int,
    email: str,
    bestellung_id: int,
) -> None:
    conn.execute(
        "INSERT INTO code_einloesungen (rabattcode_id, email, bestellung_id) "
        "VALUES (?, ?, ?)",
        (rabattcode_id, email.lower().strip(), bestellung_id),
    )
    conn.execute(
        "UPDATE rabattcodes SET aktuelle_einloesungen = aktuelle_einloesungen + 1 "
        "WHERE id = ?",
        (rabattcode_id,),
    )
    conn.commit()


def ist_bereits_eingeloest(
    conn: sqlite3.Connection, rabattcode_id: int, email: str
) -> bool:
    row = conn.execute(
        "SELECT 1 FROM code_einloesungen WHERE rabattcode_id = ? AND email = ?",
        (rabattcode_id, email.lower().strip()),
    ).fetchone()
    return row is not None
```

- [ ] **Step 8: Run tests to verify they pass**

Run: `python -m pytest tests/test_rabattcode_service.py -v`
Expected: ALL PASS

- [ ] **Step 9: Commit**

```bash
git add migrations/003_rabattcodes.sql app/repositories/rabattcode_repo.py tests/test_rabattcode_service.py
git commit -m "feat: DB-Migration und Repository fuer Rabattcodes (#62)"
```

---

## Task 2: Rabattcode-Service (Validierung + Berechnung)

**Files:**
- Create: `app/services/rabattcode_service.py`
- Test: `tests/test_rabattcode_service.py` (erweitern)

- [ ] **Step 1: Write failing tests for berechne_rabatt**

Append to `tests/test_rabattcode_service.py`:

```python
from app.services.rabattcode_service import berechne_rabatt


def test_berechne_rabatt_prozent():
    assert berechne_rabatt("prozent", 10.0, 26.00) == 2.60


def test_berechne_rabatt_prozent_5rappen_rundung():
    # 7% von 18.00 = 1.26 → gerundet auf 1.25
    assert berechne_rabatt("prozent", 7.0, 18.00) == 1.25


def test_berechne_rabatt_fixbetrag():
    assert berechne_rabatt("fixbetrag", 5.0, 26.00) == 5.00


def test_berechne_rabatt_fixbetrag_nicht_mehr_als_subtotal():
    assert berechne_rabatt("fixbetrag", 50.0, 26.00) == 26.00


def test_berechne_rabatt_prozent_5rappen_rundung_weitere():
    # 15% von 8.00 = 1.20 → bleibt 1.20
    assert berechne_rabatt("prozent", 15.0, 8.00) == 1.20
    # 10% von 9.90 = 0.99 → gerundet auf 1.00
    assert berechne_rabatt("prozent", 10.0, 9.90) == 1.00
    # 3% von 7.00 = 0.21 → gerundet auf 0.20
    assert berechne_rabatt("prozent", 3.0, 7.00) == 0.20
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_rabattcode_service.py::test_berechne_rabatt_prozent -v`
Expected: FAIL — ImportError

- [ ] **Step 3: Implement berechne_rabatt**

```python
# app/services/rabattcode_service.py
import sqlite3
from datetime import date

from app.repositories.rabattcode_repo import (
    ist_bereits_eingeloest,
    rabattcode_laden_by_code,
)


def berechne_rabatt(rabattart: str, rabattwert: float, subtotal: float) -> float:
    """Berechnet den Rabattbetrag mit Schweizer 5-Rappen-Rundung."""
    if rabattart == "prozent":
        betrag = subtotal * rabattwert / 100
    else:
        betrag = min(rabattwert, subtotal)
    # 5-Rappen-Rundung
    return round(betrag * 20) / 20
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_rabattcode_service.py -k "berechne_rabatt" -v`
Expected: ALL PASS

- [ ] **Step 5: Write failing tests for pruefe_rabattcode**

Append to `tests/test_rabattcode_service.py`:

```python
from app.services.rabattcode_service import pruefe_rabattcode
from app.repositories.rabattcode_repo import rabattcode_anlegen, einloesung_speichern


def _erstelle_testcode(db, **overrides):
    """Hilfsfunktion: Rabattcode mit sinnvollen Defaults erstellen."""
    defaults = {
        "code": "TEST10",
        "rabattart": "prozent",
        "rabattwert": 10.0,
        "gueltig_von": "2026-01-01",
        "gueltig_bis": "2026-12-31",
    }
    defaults.update(overrides)
    return rabattcode_anlegen(db, **defaults)


def _erstelle_testbestellung(db):
    """Hilfsfunktion: Kunde + Bestellung fuer Einloesungs-Tests."""
    db.execute(
        "INSERT INTO kunden (vorname, nachname, email, strasse, plz, ort) "
        "VALUES ('A', 'B', 'a@b.ch', 'Str. 1', '4600', 'Olten')"
    )
    db.execute(
        "INSERT INTO bestellungen (kunde_id, zahlungsart, versandart, versandkosten_chf, total_chf) "
        "VALUES (1, 'stripe', 'versand', 0, 50)"
    )
    db.commit()


def test_pruefe_rabattcode_gueltig(db):
    _erstelle_testcode(db)
    result = pruefe_rabattcode(db, "TEST10", "kunde@test.ch", 26.00)
    assert result["gueltig"] is True
    assert result["rabattbetrag"] == 2.60


def test_pruefe_rabattcode_unbekannt(db):
    result = pruefe_rabattcode(db, "GIBTSNICHT", "kunde@test.ch", 26.00)
    assert result["gueltig"] is False
    assert "nicht gefunden" in result["fehler"].lower() or "ungültig" in result["fehler"].lower()


def test_pruefe_rabattcode_deaktiviert(db):
    code_id = _erstelle_testcode(db)
    db.execute("UPDATE rabattcodes SET aktiv = 0 WHERE id = ?", (code_id,))
    db.commit()
    result = pruefe_rabattcode(db, "TEST10", "kunde@test.ch", 26.00)
    assert result["gueltig"] is False


def test_pruefe_rabattcode_abgelaufen(db):
    _erstelle_testcode(db, gueltig_von="2025-01-01", gueltig_bis="2025-12-31")
    result = pruefe_rabattcode(db, "TEST10", "kunde@test.ch", 26.00)
    assert result["gueltig"] is False
    assert "abgelaufen" in result["fehler"].lower()


def test_pruefe_rabattcode_noch_nicht_gueltig(db):
    _erstelle_testcode(db, gueltig_von="2027-01-01", gueltig_bis="2027-12-31")
    result = pruefe_rabattcode(db, "TEST10", "kunde@test.ch", 26.00)
    assert result["gueltig"] is False


def test_pruefe_rabattcode_max_einloesungen_erreicht(db):
    _erstelle_testcode(db, max_einloesungen=1)
    db.execute(
        "UPDATE rabattcodes SET aktuelle_einloesungen = 1 WHERE code = 'TEST10'"
    )
    db.commit()
    result = pruefe_rabattcode(db, "TEST10", "kunde@test.ch", 26.00)
    assert result["gueltig"] is False
    assert "aufgebraucht" in result["fehler"].lower()


def test_pruefe_rabattcode_bereits_eingeloest(db):
    code_id = _erstelle_testcode(db)
    _erstelle_testbestellung(db)
    einloesung_speichern(db, rabattcode_id=code_id, email="a@b.ch", bestellung_id=1)
    result = pruefe_rabattcode(db, "TEST10", "a@b.ch", 26.00)
    assert result["gueltig"] is False
    assert "bereits" in result["fehler"].lower()


def test_pruefe_rabattcode_mindestbestellwert_nicht_erreicht(db):
    _erstelle_testcode(db, mindestbestellwert_chf=50.0)
    result = pruefe_rabattcode(db, "TEST10", "kunde@test.ch", 26.00)
    assert result["gueltig"] is False
    assert "mindestbestellwert" in result["fehler"].lower()


def test_pruefe_rabattcode_mindestbestellwert_erreicht(db):
    _erstelle_testcode(db, mindestbestellwert_chf=25.0)
    result = pruefe_rabattcode(db, "TEST10", "kunde@test.ch", 26.00)
    assert result["gueltig"] is True
```

- [ ] **Step 6: Run tests to verify they fail**

Run: `python -m pytest tests/test_rabattcode_service.py::test_pruefe_rabattcode_gueltig -v`
Expected: FAIL — ImportError

- [ ] **Step 7: Implement pruefe_rabattcode**

Add to `app/services/rabattcode_service.py`:

```python
def pruefe_rabattcode(
    conn: sqlite3.Connection,
    code: str,
    email: str,
    subtotal: float,
) -> dict:
    """Validiert einen Rabattcode und gibt das Ergebnis zurück."""
    rc = rabattcode_laden_by_code(conn, code)

    if not rc or not rc["aktiv"]:
        return {"gueltig": False, "fehler": "Rabattcode ungültig oder nicht gefunden."}

    heute = date.today().isoformat()
    if heute < rc["gueltig_von"]:
        return {"gueltig": False, "fehler": "Rabattcode ist noch nicht gültig."}
    if heute > rc["gueltig_bis"]:
        return {"gueltig": False, "fehler": "Rabattcode ist abgelaufen."}

    if rc["max_einloesungen"] is not None and rc["aktuelle_einloesungen"] >= rc["max_einloesungen"]:
        return {"gueltig": False, "fehler": "Rabattcode ist aufgebraucht."}

    if ist_bereits_eingeloest(conn, rc["id"], email):
        return {"gueltig": False, "fehler": "Du hast diesen Code bereits eingelöst."}

    if rc["mindestbestellwert_chf"] is not None and subtotal < rc["mindestbestellwert_chf"]:
        return {
            "gueltig": False,
            "fehler": f"Mindestbestellwert CHF {rc['mindestbestellwert_chf']:.2f} nicht erreicht.",
        }

    rabattbetrag = berechne_rabatt(rc["rabattart"], rc["rabattwert"], subtotal)

    return {
        "gueltig": True,
        "rabattbetrag": rabattbetrag,
        "rabattart": rc["rabattart"],
        "rabattwert": rc["rabattwert"],
        "rabattcode_id": rc["id"],
        "code": rc["code"],
    }
```

- [ ] **Step 8: Run tests to verify they pass**

Run: `python -m pytest tests/test_rabattcode_service.py -v`
Expected: ALL PASS

- [ ] **Step 9: Commit**

```bash
git add app/services/rabattcode_service.py tests/test_rabattcode_service.py
git commit -m "feat: Rabattcode-Service mit Validierung und 5-Rappen-Rundung (#62)"
```

---

## Task 3: API-Endpoint zur Code-Prüfung

**Files:**
- Create: `app/routers/rabattcodes.py`
- Modify: `app/main.py:22-36`
- Test: `tests/test_api_rabattcodes.py`

- [ ] **Step 1: Write failing test for API endpoint**

```python
# tests/test_api_rabattcodes.py
import json


def test_rabattcode_pruefen_gueltig(client):
    """POST /api/rabattcode/pruefen gibt Rabatt zurueck bei gueltigem Code."""
    # Testcode direkt in DB anlegen
    from app.database import get_db
    conn = get_db()
    conn.execute(
        "INSERT INTO rabattcodes (code, rabattart, rabattwert, gueltig_von, gueltig_bis) "
        "VALUES ('AKTION10', 'prozent', 10.0, '2026-01-01', '2026-12-31')"
    )
    conn.commit()
    conn.close()

    response = client.post(
        "/api/rabattcode/pruefen",
        json={"code": "AKTION10", "email": "test@example.com", "subtotal": 26.00},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["gueltig"] is True
    assert data["rabattbetrag"] == 2.60


def test_rabattcode_pruefen_ungueltig(client):
    """POST /api/rabattcode/pruefen gibt Fehler bei unbekanntem Code."""
    response = client.post(
        "/api/rabattcode/pruefen",
        json={"code": "GIBTSNICHT", "email": "test@example.com", "subtotal": 26.00},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["gueltig"] is False
    assert "fehler" in data
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_api_rabattcodes.py -v`
Expected: FAIL — 404 (route not found)

- [ ] **Step 3: Create router with API endpoint**

```python
# app/routers/rabattcodes.py
from pydantic import BaseModel

from fastapi import APIRouter

from app.database import get_db
from app.services.rabattcode_service import pruefe_rabattcode

router = APIRouter()


class RabattcodeRequest(BaseModel):
    code: str
    email: str
    subtotal: float


@router.post("/api/rabattcode/pruefen")
def rabattcode_pruefen(req: RabattcodeRequest):
    conn = get_db()
    try:
        result = pruefe_rabattcode(conn, req.code, req.email, req.subtotal)
        if result["gueltig"]:
            if result["rabattart"] == "prozent":
                beschreibung = f"{result['rabattwert']:.0f}% Rabatt"
            else:
                beschreibung = f"CHF {result['rabattbetrag']:.2f} Rabatt"
            return {
                "gueltig": True,
                "rabattbetrag": result["rabattbetrag"],
                "rabattart": result["rabattart"],
                "beschreibung": beschreibung,
                "code": result["code"],
            }
        return {"gueltig": False, "fehler": result["fehler"]}
    finally:
        conn.close()
```

- [ ] **Step 4: Register router in main.py**

In `app/main.py`, add import and include:

```python
# Add to imports (after existing router imports):
from app.routers import (
    admin, bestellungen, produkte, rabattcodes, seiten, warenkorb, webhooks
)

# Add after existing include_router calls:
app.include_router(rabattcodes.router)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/test_api_rabattcodes.py -v`
Expected: ALL PASS

- [ ] **Step 6: Commit**

```bash
git add app/routers/rabattcodes.py app/main.py tests/test_api_rabattcodes.py
git commit -m "feat: API-Endpoint POST /api/rabattcode/pruefen (#62)"
```

---

## Task 4: Bestellprozess mit Rabattcode

**Files:**
- Modify: `app/repositories/bestell_repo.py:17-58`
- Modify: `app/routers/bestellungen.py:29-101`
- Test: `tests/test_api_rabattcodes.py` (erweitern)

- [ ] **Step 1: Write failing test for order with discount**

Append to `tests/test_api_rabattcodes.py`:

```python
def test_bestellung_mit_rabattcode(client, csrf_token):
    """POST /bestellen mit gueltigem Rabattcode speichert Rabatt."""
    from app.database import get_db
    conn = get_db()
    conn.execute(
        "INSERT INTO rabattcodes (code, rabattart, rabattwert, gueltig_von, gueltig_bis) "
        "VALUES ('WILLKOMMEN', 'fixbetrag', 5.0, '2026-01-01', '2026-12-31')"
    )
    conn.commit()
    conn.close()

    cart_data = json.dumps([{"produkt_id": 1, "menge": 2}])  # 2x CHF 8 = 16
    response = client.post(
        "/bestellen",
        data={
            "vorname": "Test",
            "nachname": "User",
            "email": "test@example.com",
            "strasse": "Teststr. 1",
            "plz": "4600",
            "ort": "Olten",
            "versandart": "abholung",
            "zahlungsart": "abholung_bar",
            "cart_data": cart_data,
            "rabattcode": "WILLKOMMEN",
            "csrf_token": csrf_token,
        },
        follow_redirects=False,
    )
    # Bestellung erfolgreich (Redirect oder 200)
    assert response.status_code in (200, 303)

    conn = get_db()
    row = conn.execute("SELECT rabattbetrag_chf, total_chf FROM bestellungen WHERE id = 1").fetchone()
    conn.close()
    assert row["rabattbetrag_chf"] == 5.00
    assert row["total_chf"] == 11.00  # 16 - 5 + 0 Versand


def test_bestellung_ohne_rabattcode(client, csrf_token):
    """POST /bestellen ohne Rabattcode funktioniert weiterhin."""
    cart_data = json.dumps([{"produkt_id": 1, "menge": 1}])
    response = client.post(
        "/bestellen",
        data={
            "vorname": "Test",
            "nachname": "User",
            "email": "test@example.com",
            "strasse": "Teststr. 1",
            "plz": "4600",
            "ort": "Olten",
            "versandart": "abholung",
            "zahlungsart": "abholung_bar",
            "cart_data": cart_data,
            "csrf_token": csrf_token,
        },
        follow_redirects=False,
    )
    assert response.status_code in (200, 303)

    conn = get_db()
    row = conn.execute("SELECT rabattbetrag_chf, total_chf FROM bestellungen WHERE id = 1").fetchone()
    conn.close()
    assert row["rabattbetrag_chf"] == 0
    assert row["total_chf"] == 8.00  # CHF 8 + 0 Versand
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_api_rabattcodes.py::test_bestellung_mit_rabattcode -v`
Expected: FAIL

- [ ] **Step 3: Extend bestell_repo.bestellung_anlegen()**

In `app/repositories/bestell_repo.py`, modify `bestellung_anlegen()`:

```python
def bestellung_anlegen(
    conn: sqlite3.Connection,
    *,
    kunde_id: int,
    positionen: list[dict],
    zahlungsart: str,
    versandart: str,
    versandkosten: float,
    total: float,
    kommentar: str = "",
    stripe_session_id: str | None = None,
    rabattcode_id: int | None = None,
    rabattbetrag_chf: float = 0,
) -> int:
    cursor = conn.execute(
        "INSERT INTO bestellungen "
        "(kunde_id, zahlungsart, versandart, versandkosten_chf, "
        "total_chf, kommentar, stripe_session_id, rabattcode_id, rabattbetrag_chf) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            kunde_id,
            zahlungsart,
            versandart,
            versandkosten,
            total,
            kommentar,
            stripe_session_id,
            rabattcode_id,
            rabattbetrag_chf,
        ),
    )
    bestell_id = cursor.lastrowid
    for pos in positionen:
        conn.execute(
            "INSERT INTO bestellpositionen "
            "(bestellung_id, produkt_id, menge, einzelpreis_chf) "
            "VALUES (?, ?, ?, ?)",
            (
                bestell_id,
                pos["produkt_id"],
                pos["menge"],
                pos["einzelpreis_chf"],
            ),
        )
    conn.commit()
    return bestell_id
```

- [ ] **Step 4: Modify bestellungen.py to accept and apply discount**

In `app/routers/bestellungen.py`:

1. Add `rabattcode: str = Form("")` to `bestellen()` parameters (after `kommentar`)
2. Add import for `pruefe_rabattcode` and `einloesung_speichern`
3. After `total, positionen = berechne_total(conn, items)` (line 70), add discount logic:

```python
# After line 70: total, positionen = berechne_total(conn, items)
# Rabattcode prüfen und anwenden
rabattcode_id = None
rabattbetrag = 0.0
if rabattcode:
    from app.services.rabattcode_service import pruefe_rabattcode
    rc_result = pruefe_rabattcode(conn, rabattcode, email, total)
    if rc_result["gueltig"]:
        rabattcode_id = rc_result["rabattcode_id"]
        rabattbetrag = rc_result["rabattbetrag"]

versandkosten = berechne_versandkosten(total, versandart)
gesamt = total - rabattbetrag + versandkosten
```

4. Pass `rabattcode_id` and `rabattbetrag_chf` to `bestellung_anlegen()`:

```python
bestell_id = bestellung_anlegen(
    conn, kunde_id=kunde_id, positionen=positionen,
    zahlungsart=zahlungsart, versandart=versandart,
    versandkosten=versandkosten, total=gesamt,
    kommentar=kommentar,
    rabattcode_id=rabattcode_id,
    rabattbetrag_chf=rabattbetrag,
)
```

5. After successful order creation, if `rabattcode_id`, record redemption:

```python
if rabattcode_id:
    from app.repositories.rabattcode_repo import einloesung_speichern
    einloesung_speichern(
        conn, rabattcode_id=rabattcode_id,
        email=email, bestellung_id=bestell_id,
    )
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/test_api_rabattcodes.py -v`
Expected: ALL PASS

- [ ] **Step 6: Run ALL existing tests to verify no regressions**

Run: `python -m pytest tests/ -v`
Expected: ALL PASS

- [ ] **Step 7: Commit**

```bash
git add app/repositories/bestell_repo.py app/routers/bestellungen.py tests/test_api_rabattcodes.py
git commit -m "feat: Rabattcode im Bestellprozess anwenden und speichern (#62)"
```

---

## Task 5: Stripe-Integration (Coupon)

**Files:**
- Modify: `app/services/stripe_service.py:8-41`
- Modify: `app/routers/bestellungen.py` (Stripe-Pfad)

- [ ] **Step 1: Modify stripe_service.py to accept discount**

Add `rabattbetrag` parameter to `erstelle_checkout_session()`:

```python
def erstelle_checkout_session(
    positionen: list[dict],
    versandkosten: float,
    bestell_id: int,
    rabattbetrag: float = 0,
) -> stripe.checkout.Session:
    line_items = []
    for pos in positionen:
        line_items.append({
            "price_data": {
                "currency": "chf",
                "product_data": {"name": pos["name"]},
                "unit_amount": int(pos["einzelpreis_chf"] * 100),
            },
            "quantity": pos["menge"],
        })

    if versandkosten > 0:
        line_items.append({
            "price_data": {
                "currency": "chf",
                "product_data": {"name": "Versandkosten"},
                "unit_amount": int(versandkosten * 100),
            },
            "quantity": 1,
        })

    # Discount als Stripe Coupon
    discounts = []
    if rabattbetrag > 0:
        coupon = stripe.Coupon.create(
            amount_off=int(rabattbetrag * 100),
            currency="chf",
            duration="once",
            name=f"Rabatt Bestellung #{bestell_id}",
        )
        discounts = [{"coupon": coupon.id}]

    return stripe.checkout.Session.create(
        payment_method_types=["card", "twint"],
        line_items=line_items,
        mode="payment",
        discounts=discounts if discounts else stripe.UNDEFINED,
        success_url=f"{settings.base_url}/bestaetigung?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{settings.base_url}/checkout",
        metadata={"bestell_id": str(bestell_id)},
    )
```

- [ ] **Step 2: Pass rabattbetrag in bestellungen.py Stripe path**

In `app/routers/bestellungen.py`, modify the Stripe call (around line 91):

```python
session = erstelle_checkout_session(
    positionen=positionen,
    versandkosten=versandkosten,
    bestell_id=bestell_id,
    rabattbetrag=rabattbetrag,
)
```

- [ ] **Step 3: Run all tests**

Run: `python -m pytest tests/ -v`
Expected: ALL PASS

- [ ] **Step 4: Commit**

```bash
git add app/services/stripe_service.py app/routers/bestellungen.py
git commit -m "feat: Stripe Coupon fuer Rabattcodes erstellen (#62)"
```

---

## Task 6: Checkout-Frontend (Rabattcode-Eingabe)

**Files:**
- Modify: `templates/checkout.html`

- [ ] **Step 1: Add discount code input field to checkout form**

In `templates/checkout.html`, insert a new card between the Kommentar-Card (line 82-86) and the submit button (line 88). Also add a hidden field for the validated code:

After the closing `</div>` of the Kommentar-Card (after line 86), add:

```html
    <div class="bg-stone-700 rounded-lg p-6 shadow-md">
        <h2 class="text-xl font-bold mb-4">Rabattcode <span class="text-stone-500 text-base font-normal">(optional)</span></h2>
        <div class="flex gap-2">
            <input type="text" id="rabattcode-input" placeholder="Code eingeben"
                   class="flex-1 bg-stone-800 border border-stone-600 rounded px-3 py-2 uppercase">
            <button type="button" id="rabattcode-btn"
                    class="bg-accent text-stone-900 px-4 py-2 rounded font-bold hover:bg-yellow-400 transition-colors">
                Einlösen
            </button>
        </div>
        <div id="rabattcode-feedback" class="mt-2 text-sm hidden"></div>
        <input type="hidden" name="rabattcode" id="rabattcode-hidden" value="">
    </div>

    <div id="preis-zusammenfassung" class="bg-stone-700 rounded-lg p-6 shadow-md hidden">
        <h2 class="text-xl font-bold mb-4">Zusammenfassung</h2>
        <div class="space-y-2 text-sm">
            <div class="flex justify-between">
                <span>Warenkorb</span>
                <span id="preis-subtotal" class="font-mono"></span>
            </div>
            <div id="preis-rabatt-zeile" class="flex justify-between text-green-400 hidden">
                <span id="preis-rabatt-label">Rabatt</span>
                <span id="preis-rabatt-betrag" class="font-mono"></span>
            </div>
            <div class="flex justify-between">
                <span>Versandkosten</span>
                <span id="preis-versand" class="font-mono"></span>
            </div>
            <div class="border-t border-stone-600 pt-2 flex justify-between font-bold">
                <span>Total</span>
                <span id="preis-total" class="font-mono"></span>
            </div>
        </div>
    </div>
```

- [ ] **Step 2: Add JavaScript for AJAX validation**

Replace the `<script>` block (lines 93-114) with:

```html
<script>
document.getElementById("checkout-form").addEventListener("submit", function() {
    document.getElementById("cart-data").value = JSON.stringify(getCart());
});

// Versandart-Toggle
document.querySelectorAll('input[name="versandart"]').forEach(function(radio) {
    radio.addEventListener("change", function() {
        var abholungOption = document.getElementById("abholung-bar-option");
        var abholungRadio = abholungOption.querySelector("input");
        if (this.value === "abholung") {
            abholungOption.classList.remove("hidden");
            abholungRadio.checked = true;
        } else {
            abholungOption.classList.add("hidden");
            if (abholungRadio.checked) {
                document.querySelector('input[name="zahlungsart"][value="stripe"]').checked = true;
            }
        }
        aktualisierePreiszusammenfassung();
    });
});

// Rabattcode-Logik
var aktuellerRabatt = null;

document.getElementById("rabattcode-btn").addEventListener("click", function() {
    var codeInput = document.getElementById("rabattcode-input");
    var code = codeInput.value.trim();
    if (!code) return;

    var emailField = document.querySelector('input[name="email"]');
    var email = emailField ? emailField.value.trim() : "";
    if (!email) {
        zeigeFeedback("Bitte zuerst E-Mail-Adresse eingeben.", false);
        return;
    }

    var subtotal = getCartTotal();
    var btn = this;
    btn.disabled = true;
    btn.textContent = "Prüfe...";

    fetch("/api/rabattcode/pruefen", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({code: code, email: email, subtotal: subtotal})
    })
    .then(function(r) { return r.json(); })
    .then(function(data) {
        if (data.gueltig) {
            aktuellerRabatt = data;
            document.getElementById("rabattcode-hidden").value = data.code;
            zeigeFeedback(data.code + " — " + data.beschreibung, true);
            btn.textContent = "Entfernen";
            btn.onclick = entferneRabattcode;
            codeInput.disabled = true;
        } else {
            zeigeFeedback(data.fehler, false);
            btn.textContent = "Einlösen";
        }
        btn.disabled = false;
        aktualisierePreiszusammenfassung();
    })
    .catch(function() {
        zeigeFeedback("Fehler bei der Prüfung. Bitte erneut versuchen.", false);
        btn.textContent = "Einlösen";
        btn.disabled = false;
    });
});

function entferneRabattcode() {
    aktuellerRabatt = null;
    document.getElementById("rabattcode-hidden").value = "";
    document.getElementById("rabattcode-input").value = "";
    document.getElementById("rabattcode-input").disabled = false;
    document.getElementById("rabattcode-feedback").classList.add("hidden");
    var btn = document.getElementById("rabattcode-btn");
    btn.textContent = "Einlösen";
    btn.onclick = null;
    // Re-attach original click handler
    btn.addEventListener("click", arguments.callee.caller);
    aktualisierePreiszusammenfassung();
    // Reload page section to reset handler cleanly
    location.reload();
}

function zeigeFeedback(text, erfolg) {
    var el = document.getElementById("rabattcode-feedback");
    el.textContent = text;
    el.className = "mt-2 text-sm " + (erfolg ? "text-green-400" : "text-red-400");
    el.classList.remove("hidden");
}

function aktualisierePreiszusammenfassung() {
    var subtotal = getCartTotal();
    if (subtotal <= 0) return;

    var versandart = document.querySelector('input[name="versandart"]:checked');
    var versandkosten = (versandart && versandart.value === "abholung") ? 0 : getVersandkosten(subtotal);
    var rabatt = aktuellerRabatt ? aktuellerRabatt.rabattbetrag : 0;
    var total = subtotal - rabatt + versandkosten;

    document.getElementById("preis-subtotal").textContent = "CHF " + subtotal.toFixed(2);
    document.getElementById("preis-versand").textContent = versandkosten > 0 ? "CHF " + versandkosten.toFixed(2) : "gratis";
    document.getElementById("preis-total").textContent = "CHF " + total.toFixed(2);

    var rabattZeile = document.getElementById("preis-rabatt-zeile");
    if (rabatt > 0) {
        document.getElementById("preis-rabatt-label").textContent = "Rabatt (" + aktuellerRabatt.code + ")";
        document.getElementById("preis-rabatt-betrag").textContent = "- CHF " + rabatt.toFixed(2);
        rabattZeile.classList.remove("hidden");
    } else {
        rabattZeile.classList.add("hidden");
    }

    document.getElementById("preis-zusammenfassung").classList.remove("hidden");
}

// Initial
if (getCartTotal() > 0) aktualisierePreiszusammenfassung();
</script>
```

- [ ] **Step 3: Manual test in browser**

1. Go to `/checkout`
2. Fill in email address
3. Enter "TESTCODE" → should show error
4. Verify form still submits correctly without code

- [ ] **Step 4: Commit**

```bash
git add templates/checkout.html
git commit -m "feat: Rabattcode-Eingabe und Live-Preisanzeige im Checkout (#62)"
```

---

## Task 7: E-Mail-Templates mit Rabattzeile

**Files:**
- Modify: `app/services/email_service.py:17-66,163-204`
- Modify: `templates/emails/bestellbestaetigung.html:17-27`
- Modify: `templates/emails/bestellung_stakeholder.html:34-44`
- Modify: `app/routers/bestellungen.py` (rabattinfo an E-Mail übergeben)

- [ ] **Step 1: Add rabattbetrag and rabattcode parameters to email functions**

In `app/services/email_service.py`, modify `sende_bestellbestaetigung()` signature and render call:

```python
def sende_bestellbestaetigung(
    empfaenger: str,
    bestell_id: int,
    kunde: dict,
    positionen: list[dict],
    versandkosten: float,
    total: float,
    anhang: bytes | None = None,
    conn: sqlite3.Connection | None = None,
    template_name: str = "bestellbestaetigung.html",
    rabattbetrag: float = 0,
    rabattcode: str = "",
) -> object:
    template = env.get_template(template_name)
    html = template.render(
        kunde=kunde,
        bestell_id=bestell_id,
        positionen=positionen,
        versandkosten=versandkosten,
        total=total,
        rabattbetrag=rabattbetrag,
        rabattcode=rabattcode,
    )
    # ... rest unchanged
```

Modify `sende_stakeholder_benachrichtigung()` similarly:

```python
def sende_stakeholder_benachrichtigung(
    bestell_id: int,
    kunde: dict,
    positionen: list[dict],
    versandkosten: float,
    total: float,
    zahlungsart: str,
    versandart: str,
    conn: sqlite3.Connection | None = None,
    rabattbetrag: float = 0,
    rabattcode: str = "",
) -> object:
    template = env.get_template("bestellung_stakeholder.html")
    html = template.render(
        bestell_id=bestell_id,
        kunde=kunde,
        positionen=positionen,
        versandkosten=versandkosten,
        total=total,
        zahlungsart=zahlungsart,
        zahlungsart_label=_ZAHLUNGSART_LABELS.get(zahlungsart, zahlungsart),
        versandart_label=_VERSANDART_LABELS.get(versandart, versandart),
        rabattbetrag=rabattbetrag,
        rabattcode=rabattcode,
    )
    # ... rest unchanged
```

- [ ] **Step 2: Update bestellbestaetigung.html template**

In `templates/emails/bestellbestaetigung.html`, insert before the Versandkosten row (before line 18):

```html
        {% if rabattbetrag > 0 %}
        <tr style="border-bottom: 1px solid #ddd; color: #22c55e;">
            <td style="padding: 8px;" colspan="2">Rabatt ({{ rabattcode }})</td>
            <td style="padding: 8px; text-align: right;">- CHF {{ "%.2f"|format(rabattbetrag) }}</td>
        </tr>
        {% endif %}
```

- [ ] **Step 3: Update bestellung_stakeholder.html template**

In `templates/emails/bestellung_stakeholder.html`, insert before the Versandkosten row (before line 35):

```html
        {% if rabattbetrag > 0 %}
        <tr style="border-bottom: 1px solid #ddd; color: #22c55e;">
            <td style="padding: 8px;" colspan="2">Rabatt ({{ rabattcode }})</td>
            <td style="padding: 8px; text-align: right;">- CHF {{ "%.2f"|format(rabattbetrag) }}</td>
        </tr>
        {% endif %}
```

- [ ] **Step 4: Pass rabattinfo in bestellungen.py email calls**

In `app/routers/bestellungen.py`, in all three payment paths, add `rabattbetrag` and `rabattcode` to every `sende_bestellbestaetigung()` and `sende_stakeholder_benachrichtigung()` call. Need a variable for the code name:

After the rabattcode validation block, add:

```python
rabattcode_name = ""
if rabattcode_id and rabattcode:
    rabattcode_name = rabattcode.upper().strip()
```

Then in each email call, add:

```python
rabattbetrag=rabattbetrag,
rabattcode=rabattcode_name,
```

- [ ] **Step 5: Run all tests**

Run: `python -m pytest tests/ -v`
Expected: ALL PASS

- [ ] **Step 6: Commit**

```bash
git add app/services/email_service.py templates/emails/bestellbestaetigung.html templates/emails/bestellung_stakeholder.html app/routers/bestellungen.py
git commit -m "feat: Rabattzeile in E-Mail-Templates (#62)"
```

---

## Task 8: Admin-Portal — Rabattcodes verwalten

**Files:**
- Create: `templates/admin/rabattcodes.html`
- Create: `templates/admin/rabattcode_form.html`
- Modify: `app/routers/rabattcodes.py` (Admin-Routes hinzufügen)
- Modify: `templates/admin/base.html:29-31` (Nav-Link)
- Modify: `templates/admin/bestellung_detail.html:122-131` (Rabattzeile)
- Test: `tests/test_api_rabattcodes.py` (erweitern)

- [ ] **Step 1: Write failing test for admin discount overview**

Append to `tests/test_api_rabattcodes.py`:

```python
def _admin_login(client):
    """Hilfsfunktion: Admin einloggen und Session-Cookie erhalten."""
    from app.config import settings
    from app.csrf import generiere_csrf_token
    csrf = generiere_csrf_token(settings.secret_key)
    response = client.post(
        "/admin/login",
        data={"password": "admin", "csrf_token": csrf},
        follow_redirects=False,
    )
    return response.cookies


def test_admin_rabattcodes_uebersicht(client):
    """GET /admin/rabattcodes zeigt Übersicht."""
    cookies = _admin_login(client)
    response = client.get("/admin/rabattcodes", cookies=cookies)
    assert response.status_code == 200
    assert "Rabattcodes" in response.text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_api_rabattcodes.py::test_admin_rabattcodes_uebersicht -v`
Expected: FAIL — 404 or redirect

- [ ] **Step 3: Add admin routes to rabattcodes.py**

Extend `app/routers/rabattcodes.py` with admin routes:

```python
# Add imports at top
from fastapi import Cookie, Form, Request
from fastapi.responses import RedirectResponse

from app.config import settings
from app.csrf import generiere_csrf_token
from app.repositories.rabattcode_repo import (
    alle_rabattcodes,
    rabattcode_aktualisieren,
    rabattcode_anlegen,
    rabattcode_laden,
)
from app.services.auth_service import validate_session
from app.templating import templates


def _get_admin_label(admin_session: str | None) -> str | None:
    if not admin_session:
        return None
    return validate_session(
        admin_session,
        secret=settings.secret_key,
        max_age=settings.admin_session_max_age,
    )


@router.get("/admin/rabattcodes")
def admin_rabattcodes_liste(
    request: Request,
    admin_session: str | None = Cookie(None),
):
    label = _get_admin_label(admin_session)
    if not label:
        return RedirectResponse("/admin/login", status_code=303)

    conn = get_db()
    try:
        codes = alle_rabattcodes(conn)
    finally:
        conn.close()

    csrf = generiere_csrf_token(settings.secret_key)
    return templates.TemplateResponse(
        request,
        "admin/rabattcodes.html",
        {"admin_label": label, "csrf_token": csrf, "codes": codes},
    )


@router.get("/admin/rabattcodes/neu")
def admin_rabattcode_neu(
    request: Request,
    admin_session: str | None = Cookie(None),
):
    label = _get_admin_label(admin_session)
    if not label:
        return RedirectResponse("/admin/login", status_code=303)

    csrf = generiere_csrf_token(settings.secret_key)
    return templates.TemplateResponse(
        request,
        "admin/rabattcode_form.html",
        {"admin_label": label, "csrf_token": csrf, "code": None},
    )


@router.post("/admin/rabattcodes/neu")
def admin_rabattcode_erstellen(
    request: Request,
    code: str = Form(),
    rabattart: str = Form(),
    rabattwert: float = Form(),
    gueltig_von: str = Form(),
    gueltig_bis: str = Form(),
    mindestbestellwert_chf: str = Form(""),
    max_einloesungen: str = Form(""),
    aktiv: str = Form("0"),
    csrf_token: str = Form(""),
    admin_session: str | None = Cookie(None),
):
    label = _get_admin_label(admin_session)
    if not label:
        return RedirectResponse("/admin/login", status_code=303)

    conn = get_db()
    try:
        from app.repositories.admin_repo import log_eintrag_schreiben

        rabattcode_anlegen(
            conn,
            code=code,
            rabattart=rabattart,
            rabattwert=rabattwert,
            gueltig_von=gueltig_von,
            gueltig_bis=gueltig_bis,
            mindestbestellwert_chf=float(mindestbestellwert_chf) if mindestbestellwert_chf else None,
            max_einloesungen=int(max_einloesungen) if max_einloesungen else None,
        )
        log_eintrag_schreiben(
            conn, admin_label=label, aktion="rabattcode_erstellt",
            details=code.upper().strip(),
        )
    finally:
        conn.close()

    return RedirectResponse("/admin/rabattcodes", status_code=303)


@router.get("/admin/rabattcodes/{code_id}/bearbeiten")
def admin_rabattcode_bearbeiten(
    request: Request,
    code_id: int,
    admin_session: str | None = Cookie(None),
):
    label = _get_admin_label(admin_session)
    if not label:
        return RedirectResponse("/admin/login", status_code=303)

    conn = get_db()
    try:
        rc = rabattcode_laden(conn, code_id)
    finally:
        conn.close()

    if not rc:
        return RedirectResponse("/admin/rabattcodes", status_code=303)

    csrf = generiere_csrf_token(settings.secret_key)
    return templates.TemplateResponse(
        request,
        "admin/rabattcode_form.html",
        {"admin_label": label, "csrf_token": csrf, "code": rc},
    )


@router.post("/admin/rabattcodes/{code_id}/bearbeiten")
def admin_rabattcode_speichern(
    request: Request,
    code_id: int,
    code: str = Form(),
    rabattart: str = Form(),
    rabattwert: float = Form(),
    gueltig_von: str = Form(),
    gueltig_bis: str = Form(),
    mindestbestellwert_chf: str = Form(""),
    max_einloesungen: str = Form(""),
    aktiv: str = Form("0"),
    csrf_token: str = Form(""),
    admin_session: str | None = Cookie(None),
):
    label = _get_admin_label(admin_session)
    if not label:
        return RedirectResponse("/admin/login", status_code=303)

    conn = get_db()
    try:
        rabattcode_aktualisieren(
            conn, code_id,
            code=code.upper().strip(),
            rabattart=rabattart,
            rabattwert=rabattwert,
            gueltig_von=gueltig_von,
            gueltig_bis=gueltig_bis,
            mindestbestellwert_chf=float(mindestbestellwert_chf) if mindestbestellwert_chf else None,
            max_einloesungen=int(max_einloesungen) if max_einloesungen else None,
            aktiv=1 if aktiv == "1" else 0,
        )
    finally:
        conn.close()

    return RedirectResponse("/admin/rabattcodes", status_code=303)
```

- [ ] **Step 4: Create admin overview template**

```html
{# templates/admin/rabattcodes.html #}
{% extends "admin/base.html" %}

{% block title %}Rabattcodes{% endblock %}

{% block content %}
<div class="flex items-center justify-between mb-8">
    <h1 class="font-display text-5xl font-bold text-accent">Rabattcodes</h1>
    <a href="/admin/rabattcodes/neu"
       class="bg-accent text-stone-900 font-bold px-4 py-2 rounded hover:bg-yellow-400 transition-colors text-sm">
        + Neuer Code
    </a>
</div>

<div class="bg-stone-700 rounded-lg shadow-md overflow-x-auto">
    <table class="w-full text-sm">
        <thead>
            <tr class="border-b border-stone-600 text-left text-stone-400">
                <th class="px-4 py-3">Code</th>
                <th class="px-4 py-3">Art</th>
                <th class="px-4 py-3 text-right">Wert</th>
                <th class="px-4 py-3">Gültig bis</th>
                <th class="px-4 py-3 text-right">Einlösungen</th>
                <th class="px-4 py-3">Status</th>
                <th class="px-4 py-3">Aktionen</th>
            </tr>
        </thead>
        <tbody>
            {% for c in codes %}
            {% set heute = now().strftime('%Y-%m-%d') if now is defined else '' %}
            {% set ist_abgelaufen = c.gueltig_bis < heute if heute else false %}
            {% set ist_aufgebraucht = c.max_einloesungen is not none and c.aktuelle_einloesungen >= c.max_einloesungen %}
            <tr class="border-b border-stone-600/50 hover:bg-stone-600 transition-colors">
                <td class="px-4 py-3 font-mono font-bold">{{ c.code }}</td>
                <td class="px-4 py-3">{{ "Prozent" if c.rabattart == "prozent" else "Fixbetrag" }}</td>
                <td class="px-4 py-3 text-right font-mono">
                    {% if c.rabattart == "prozent" %}{{ c.rabattwert|int }}%{% else %}CHF {{ "%.2f"|format(c.rabattwert) }}{% endif %}
                </td>
                <td class="px-4 py-3">{{ c.gueltig_bis }}</td>
                <td class="px-4 py-3 text-right font-mono">
                    {{ c.aktuelle_einloesungen }}{% if c.max_einloesungen %}/{{ c.max_einloesungen }}{% else %}/&infin;{% endif %}
                </td>
                <td class="px-4 py-3">
                    {% if not c.aktiv %}
                    <span class="bg-stone-600/20 text-stone-400 px-2 py-1 rounded text-xs">deaktiviert</span>
                    {% elif ist_aufgebraucht %}
                    <span class="bg-red-600/20 text-red-400 px-2 py-1 rounded text-xs">aufgebraucht</span>
                    {% elif ist_abgelaufen %}
                    <span class="bg-yellow-600/20 text-yellow-400 px-2 py-1 rounded text-xs">abgelaufen</span>
                    {% else %}
                    <span class="bg-green-600/20 text-green-400 px-2 py-1 rounded text-xs">aktiv</span>
                    {% endif %}
                </td>
                <td class="px-4 py-3">
                    <a href="/admin/rabattcodes/{{ c.id }}/bearbeiten"
                       class="text-accent hover:underline text-xs">Bearbeiten</a>
                </td>
            </tr>
            {% else %}
            <tr><td colspan="7" class="px-4 py-8 text-center text-stone-400">Keine Rabattcodes vorhanden.</td></tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}
```

- [ ] **Step 5: Create admin form template**

```html
{# templates/admin/rabattcode_form.html #}
{% extends "admin/base.html" %}

{% block title %}{{ "Bearbeiten: " + code.code if code else "Neuer Rabattcode" }}{% endblock %}

{% block content %}
<a href="/admin/rabattcodes" class="text-stone-400 hover:text-accent text-sm transition-colors">&larr; Zurück</a>

<h1 class="font-display text-5xl font-bold text-accent mt-4 mb-8">
    {{ "Rabattcode bearbeiten" if code else "Neuer Rabattcode" }}
</h1>

<form method="post" class="max-w-lg space-y-6">
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">

    <div class="bg-stone-700 rounded-lg p-6 shadow-md space-y-4">
        <div>
            <label class="block text-stone-400 text-sm mb-1">Code *</label>
            <input type="text" name="code" required value="{{ code.code if code else '' }}"
                   class="w-full bg-stone-800 border border-stone-600 rounded px-3 py-2 uppercase"
                   placeholder="z.B. FRUEHLING10">
        </div>
        <div class="grid grid-cols-2 gap-4">
            <div>
                <label class="block text-stone-400 text-sm mb-1">Rabattart *</label>
                <select name="rabattart" class="w-full bg-stone-800 border border-stone-600 rounded px-3 py-2">
                    <option value="prozent" {{ 'selected' if code and code.rabattart == 'prozent' }}>Prozent (%)</option>
                    <option value="fixbetrag" {{ 'selected' if code and code.rabattart == 'fixbetrag' }}>Fixbetrag (CHF)</option>
                </select>
            </div>
            <div>
                <label class="block text-stone-400 text-sm mb-1">Wert *</label>
                <input type="number" name="rabattwert" required step="0.01" min="0.01"
                       value="{{ code.rabattwert if code else '' }}"
                       class="w-full bg-stone-800 border border-stone-600 rounded px-3 py-2">
            </div>
        </div>
        <div class="grid grid-cols-2 gap-4">
            <div>
                <label class="block text-stone-400 text-sm mb-1">Gültig von *</label>
                <input type="date" name="gueltig_von" required
                       value="{{ code.gueltig_von if code else '' }}"
                       class="w-full bg-stone-800 border border-stone-600 rounded px-3 py-2">
            </div>
            <div>
                <label class="block text-stone-400 text-sm mb-1">Gültig bis *</label>
                <input type="date" name="gueltig_bis" required
                       value="{{ code.gueltig_bis if code else '' }}"
                       class="w-full bg-stone-800 border border-stone-600 rounded px-3 py-2">
            </div>
        </div>
        <div class="grid grid-cols-2 gap-4">
            <div>
                <label class="block text-stone-400 text-sm mb-1">Max. Einlösungen <span class="text-stone-500">(leer = unbegrenzt)</span></label>
                <input type="number" name="max_einloesungen" min="1"
                       value="{{ code.max_einloesungen if code and code.max_einloesungen else '' }}"
                       class="w-full bg-stone-800 border border-stone-600 rounded px-3 py-2">
            </div>
            <div>
                <label class="block text-stone-400 text-sm mb-1">Mindestbestellwert CHF <span class="text-stone-500">(optional)</span></label>
                <input type="number" name="mindestbestellwert_chf" step="0.01" min="0"
                       value="{{ code.mindestbestellwert_chf if code and code.mindestbestellwert_chf else '' }}"
                       class="w-full bg-stone-800 border border-stone-600 rounded px-3 py-2">
            </div>
        </div>
        {% if code %}
        <div>
            <label class="flex items-center gap-2">
                <input type="checkbox" name="aktiv" value="1" {{ 'checked' if code.aktiv }}
                       class="text-accent">
                Aktiv
            </label>
        </div>
        {% else %}
        <input type="hidden" name="aktiv" value="1">
        {% endif %}
    </div>

    <button type="submit"
            class="w-full bg-accent text-stone-900 py-3 rounded font-bold text-lg hover:bg-yellow-400 transition-colors">
        {{ "Speichern" if code else "Erstellen" }}
    </button>
</form>
{% endblock %}
```

- [ ] **Step 6: Add nav link in admin base template**

In `templates/admin/base.html`, modify the header nav area (after line 31):

```html
            <div class="flex items-center gap-3">
                <a href="/admin/" class="font-display text-4xl font-bold text-accent">Olivalle</a>
                <span class="text-stone-400 text-sm border border-stone-600 rounded px-2 py-0.5">Admin</span>
                <a href="/admin/rabattcodes" class="text-stone-400 hover:text-accent text-sm transition-colors ml-4">Rabattcodes</a>
            </div>
```

- [ ] **Step 7: Add discount info to bestellung_detail.html**

In `templates/admin/bestellung_detail.html`, insert a row in the tfoot before the Versand row (before line 123):

```html
                <tfoot>
                    {% if bestellung.rabattbetrag_chf and bestellung.rabattbetrag_chf > 0 %}
                    <tr class="border-b border-stone-600/50 text-green-400">
                        <td colspan="3" class="py-2">Rabatt{% if bestellung.rabattcode_id %} (Code){% endif %}</td>
                        <td class="py-2 text-right font-mono">- CHF {{ "%.2f"|format(bestellung.rabattbetrag_chf) }}</td>
                    </tr>
                    {% endif %}
                    <tr class="border-b border-stone-600/50 text-stone-400">
```

- [ ] **Step 8: Run tests**

Run: `python -m pytest tests/ -v`
Expected: ALL PASS

- [ ] **Step 9: Commit**

```bash
git add app/routers/rabattcodes.py templates/admin/rabattcodes.html templates/admin/rabattcode_form.html templates/admin/base.html templates/admin/bestellung_detail.html tests/test_api_rabattcodes.py
git commit -m "feat: Admin-Portal fuer Rabattcode-Verwaltung (#62)"
```

---

## Task 9: Abschluss — Gesamttest und Issue schliessen

**Files:** keine neuen

- [ ] **Step 1: Run complete test suite**

Run: `python -m pytest tests/ -v`
Expected: ALL PASS

- [ ] **Step 2: Manual smoke test**

1. `make run` (Server starten)
2. Admin: `/admin/rabattcodes/neu` → Code "TEST10" (10%, bis 2026-12-31) erstellen
3. Shop: Produkt in Warenkorb → Checkout → Code "TEST10" eingeben → Preis prüfen
4. Bestellung abschliessen (Abholung/Bar) → E-Mail-Inhalt prüfen
5. Admin: Bestellung öffnen → Rabattzeile sichtbar
6. Gleichen Code nochmal mit gleicher E-Mail → Fehler erwartet

- [ ] **Step 3: Commit any fixes from smoke test**

- [ ] **Step 4: Update user-stories-testplan.md**

Check `docs/user-stories-testplan.md` and add test cases for discount code functionality.

- [ ] **Step 5: Close issue #62**

```bash
gh issue close 62 --comment "Rabattcodes implementiert: Admin-CRUD, Checkout-Integration, Stripe Coupon, E-Mail-Templates, 5-Rappen-Rundung."
```
