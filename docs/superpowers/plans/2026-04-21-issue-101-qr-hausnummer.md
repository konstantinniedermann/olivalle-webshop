# QR-Rechnung Hausnummer-Feld — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Separates optionales Hausnummer-Feld im Checkout erfassen, in `kunden`-Tabelle persistieren und an `qrbill` als `house_num` übergeben, damit Banking-Apps eine saubere S-Typ-Adresse parsen.

**Architecture:** Bottom-up-TDD durch die Schichten: QR-Service → Model → DB/Repo → Router → Template → Admin → E2E → Docs. Jede Task ist ein eigener rot→grün→commit-Zyklus. Backward-Compat über Default `""` auf allen Ebenen.

**Tech Stack:** Python 3.14 · FastAPI · Jinja2 · Pydantic · SQLite · `qrbill` · pytest · `uv`

**Issue:** #101 — Spec: `docs/superpowers/specs/2026-04-21-issue-101-qr-hausnummer-design.md`

---

## File Structure

| Datei | Aktion | Verantwortlichkeit |
|---|---|---|
| `app/services/qr_service.py` | Modify | Neuer Parameter `kunde_hausnummer`, als `house_num` an `QRBill(debtor=...)` |
| `app/models.py` | Modify | `KundeInput.hausnummer: str = Field(default="", max_length=16)` |
| `app/database.py` | Modify | Zusätzlicher `_add_column_if_not_exists("kunden", "hausnummer", ...)` in `init_db` |
| `app/repositories/bestell_repo.py` | Modify | `kunde_anlegen` INSERT um Spalte `hausnummer` erweitert |
| `app/repositories/admin_repo.py` | Modify | `get_bestellung_detail`-SELECT um `k.hausnummer` erweitert |
| `app/routers/bestellungen.py` | Modify | Neuer Form-Parameter `hausnummer`, Weitergabe an `KundeInput` + `generiere_qr_rechnung` |
| `templates/checkout.html` | Modify | Strasse-Zeile wird zu 3:1-Grid mit zusätzlichem Nr.-Feld |
| `templates/admin/bestellung_detail.html` | Modify | Strasse-Zeile zeigt `{{ strasse }} {{ hausnummer }}` |
| `tests/conftest.py` | Modify | `db`-Fixture spiegelt den neuen Migration-Helper-Aufruf |
| `tests/test_qr_service.py` | Modify | Neue Tests für `house_num`-Verhalten auf QR-Nutzlast-Ebene |
| `tests/test_models.py` | Modify | Neue Tests für `KundeInput.hausnummer` |
| `tests/test_bestell_repo.py` | Modify | `kunde_anlegen` mit/ohne Hausnummer; DB-Spalte verifizieren |
| `tests/test_api_bestellungen.py` | Modify | POST `/bestellen` mit/ohne Hausnummer |
| `tests/test_admin_repo.py` | Modify | `get_bestellung_detail` liefert `hausnummer` |
| `tests/test_e2e_bestellzyklus.py` | Modify | Mindestens ein E2E-Pfad mit gesetzter Hausnummer |
| `docs/user-stories-testplan.md` | Modify | Schritte „Kundendaten eingeben" um Hausnummer erweitern |

Keine neuen Dateien.

---

## Task 1: QR-Service akzeptiert `house_num`

**Files:**
- Modify: `tests/test_qr_service.py` (bestehenden Test belassen, zwei neue Tests anhängen)
- Modify: `app/services/qr_service.py:9-43` (Signatur + `QRBill(debtor=...)`)

- [ ] **Step 1: Failing Tests für QR-Nutzlast schreiben**

Öffne `tests/test_qr_service.py` und hänge am Ende an:

```python


def test_qr_rechnung_mit_hausnummer_in_nutzlast(monkeypatch):
    """Wenn kunde_hausnummer gesetzt ist, landet sie in QR-Zeile 24 (Index 23)."""
    from qrbill import QRBill

    monkeypatch.setattr("app.config.settings.qr_iban", "CH5604835012345678009")
    monkeypatch.setattr("app.config.settings.qr_name", "Test GmbH")
    monkeypatch.setattr("app.config.settings.qr_address", "Teststr. 1")
    monkeypatch.setattr("app.config.settings.qr_zip", "3000")
    monkeypatch.setattr("app.config.settings.qr_city", "Bern")

    bill = QRBill(
        account="CH5604835012345678009",
        creditor={
            "name": "Test GmbH", "street": "Teststr.", "house_num": "1",
            "pcode": "3000", "city": "Bern", "country": "CH",
        },
        debtor={
            "name": "Klara Tester", "street": "Musterstrasse", "house_num": "42",
            "pcode": "8001", "city": "Zürich", "country": "CH",
        },
        amount="25.90", currency="CHF",
    )
    zeilen = bill.qr_data().split("\r\n")
    # Zeile 23 = Strasse (Index 22), Zeile 24 = Hausnummer (Index 23)
    assert zeilen[22] == "Musterstrasse"
    assert zeilen[23] == "42"


def test_generiere_qr_rechnung_mit_hausnummer(monkeypatch):
    """generiere_qr_rechnung akzeptiert kunde_hausnummer und gibt gültiges PDF zurück."""
    monkeypatch.setattr("app.config.settings.qr_iban", "CH5604835012345678009")
    monkeypatch.setattr("app.config.settings.qr_name", "Test GmbH")
    monkeypatch.setattr("app.config.settings.qr_address", "Teststr. 1")
    monkeypatch.setattr("app.config.settings.qr_zip", "3000")
    monkeypatch.setattr("app.config.settings.qr_city", "Bern")

    pdf_bytes = generiere_qr_rechnung(
        betrag=25.90, bestell_id=1,
        kunde_name="Klara Tester",
        kunde_adresse="Musterstrasse",
        kunde_hausnummer="42",
        kunde_plz="8001", kunde_ort="Zürich",
    )
    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes[:5] == b"%PDF-"
```

- [ ] **Step 2: Tests ausführen — MÜSSEN FAILEN**

Run:
```bash
cd /Users/KN/Dropbox/Privat/CAS/projekte/olivalle
uv run pytest tests/test_qr_service.py -v
```

Erwartung:
- `test_qr_rechnung_mit_hausnummer_in_nutzlast` → PASS (testet nur `qrbill`, braucht keinen Code-Change)
- `test_generiere_qr_rechnung_mit_hausnummer` → FAIL mit `TypeError: generiere_qr_rechnung() got an unexpected keyword argument 'kunde_hausnummer'`

Wenn der erste Test schon fehlschlägt: `qrbill`-Version prüfen (`uv run python -c "import qrbill; print(qrbill.__version__)"`).

- [ ] **Step 3: `qr_service.py` anpassen**

Ersetze `app/services/qr_service.py` komplett durch:

```python
from io import BytesIO, StringIO

from fpdf import FPDF
from qrbill import QRBill

from app.config import settings


def generiere_qr_rechnung(
    betrag: float,
    bestell_id: int,
    kunde_name: str,
    kunde_adresse: str,
    kunde_plz: str,
    kunde_ort: str,
    kunde_hausnummer: str = "",
) -> bytes:
    bill = QRBill(
        account=settings.qr_iban,
        creditor={
            "name": settings.qr_name,
            "street": settings.qr_address,
            "pcode": settings.qr_zip,
            "city": settings.qr_city,
            "country": "CH",
        },
        debtor={
            "name": kunde_name,
            "street": kunde_adresse,
            "house_num": kunde_hausnummer,
            "pcode": kunde_plz,
            "city": kunde_ort,
            "country": "CH",
        },
        amount=f"{betrag:.2f}",
        currency="CHF",
        additional_information=f"Bestellung #{bestell_id}",
    )
    svg_buffer = StringIO()
    bill.as_svg(svg_buffer, full_page=True)

    pdf = FPDF()
    pdf.add_page()
    pdf.image(BytesIO(svg_buffer.getvalue().encode("utf-8")), x=0, y=0, w=210)
    return bytes(pdf.output())
```

- [ ] **Step 4: Tests ausführen — MÜSSEN PASSEN**

Run:
```bash
uv run pytest tests/test_qr_service.py -v
```

Erwartung: alle 3 Tests PASS (der alte `test_generiere_qr_rechnung`, die 2 neuen).

- [ ] **Step 5: Commit**

```bash
git add app/services/qr_service.py tests/test_qr_service.py
git commit -m "$(cat <<'EOF'
feat: qr_service akzeptiert kunde_hausnummer für house_num (#101)

Neuer optionaler Parameter kunde_hausnummer wird als house_num an
QRBill(debtor=...) übergeben. Backward-compat: Default "" hält
bestehende Aufrufer kompatibel.
EOF
)"
```

---

## Task 2: `KundeInput.hausnummer`-Feld

**Files:**
- Modify: `tests/test_models.py` (neue Testfunktionen am Ende)
- Modify: `app/models.py:14-21` (KundeInput)

- [ ] **Step 1: Failing Tests für `KundeInput.hausnummer` schreiben**

Öffne `tests/test_models.py` und hänge am Ende an:

```python


def test_kunde_input_mit_hausnummer():
    """KundeInput akzeptiert optionales Feld hausnummer."""
    from app.models import KundeInput

    kunde = KundeInput(
        vorname="Max", nachname="Muster", email="max@test.ch",
        strasse="Musterstrasse", hausnummer="42",
        plz="4600", ort="Olten",
    )
    assert kunde.hausnummer == "42"


def test_kunde_input_hausnummer_default_leer():
    """Ohne hausnummer ist der Default ein leerer String."""
    from app.models import KundeInput

    kunde = KundeInput(
        vorname="Max", nachname="Muster", email="max@test.ch",
        strasse="Musterstr. 1", plz="4600", ort="Olten",
    )
    assert kunde.hausnummer == ""


def test_kunde_input_hausnummer_max_length():
    """Hausnummer über 16 Zeichen wirft ValidationError (qrbill-Limit)."""
    from pydantic import ValidationError

    from app.models import KundeInput

    try:
        KundeInput(
            vorname="Max", nachname="Muster", email="max@test.ch",
            strasse="Musterstr.", hausnummer="x" * 17,
            plz="4600", ort="Olten",
        )
        raise AssertionError("ValidationError erwartet")
    except ValidationError:
        pass
```

- [ ] **Step 2: Tests ausführen — MÜSSEN FAILEN**

Run:
```bash
uv run pytest tests/test_models.py -v -k hausnummer
```

Erwartung: drei Tests FAIL mit "extra_forbidden" / fehlender Attributzugriff auf `.hausnummer`.

- [ ] **Step 3: `KundeInput` erweitern**

In `app/models.py` die Klasse `KundeInput` (Zeilen 14-21) ersetzen durch:

```python
class KundeInput(BaseModel):
    vorname: str = Field(max_length=100)
    nachname: str = Field(max_length=100)
    email: str = Field(max_length=254)
    telefon: str = Field(default="", max_length=30)
    strasse: str = Field(max_length=200)
    hausnummer: str = Field(default="", max_length=16)
    plz: str = Field(max_length=10)
    ort: str = Field(max_length=100)
```

- [ ] **Step 4: Tests ausführen — MÜSSEN PASSEN**

Run:
```bash
uv run pytest tests/test_models.py -v
```

Erwartung: alle Tests in der Datei PASS (die drei neuen plus bestehende).

- [ ] **Step 5: Commit**

```bash
git add app/models.py tests/test_models.py
git commit -m "$(cat <<'EOF'
feat: KundeInput.hausnummer optional, max 16 Zeichen (#101)

Neues Pydantic-Feld mit Default "". max_length=16 harmonisiert mit
dem qrbill house_num-Limit, damit keine ValueError bei QR-Generierung
auftritt.
EOF
)"
```

---

## Task 3: DB-Migration + Repository

**Files:**
- Modify: `tests/test_bestell_repo.py` (neue Tests am Ende)
- Modify: `tests/conftest.py:38-47` (`_add_column_if_not_exists`-Aufruf für Spiegel-Fixture)
- Modify: `app/database.py:26-42` (`init_db`)
- Modify: `app/repositories/bestell_repo.py:15-23` (`kunde_anlegen` INSERT)

- [ ] **Step 1: Failing Tests schreiben**

Öffne `tests/test_bestell_repo.py` und hänge am Ende an:

```python


def test_kunde_anlegen_mit_hausnummer(db):
    """kunde_anlegen schreibt hausnummer-Spalte korrekt in die DB."""
    kunde = KundeInput(
        vorname="Klara", nachname="Tester", email="klara@test.ch",
        strasse="Musterstrasse", hausnummer="42",
        plz="8001", ort="Zürich",
    )
    kunde_id = kunde_anlegen(db, kunde)
    row = db.execute(
        "SELECT strasse, hausnummer FROM kunden WHERE id = ?", (kunde_id,)
    ).fetchone()
    assert row["strasse"] == "Musterstrasse"
    assert row["hausnummer"] == "42"


def test_kunde_anlegen_ohne_hausnummer_default(db):
    """Ohne hausnummer bleibt die DB-Spalte leer (DEFAULT '')."""
    kunde = KundeInput(
        vorname="Max", nachname="Muster", email="max@test.ch",
        strasse="Musterstr. 1", plz="4600", ort="Olten",
    )
    kunde_id = kunde_anlegen(db, kunde)
    row = db.execute(
        "SELECT hausnummer FROM kunden WHERE id = ?", (kunde_id,)
    ).fetchone()
    assert row["hausnummer"] == ""
```

- [ ] **Step 2: Tests ausführen — MÜSSEN FAILEN**

Run:
```bash
uv run pytest tests/test_bestell_repo.py -v -k hausnummer
```

Erwartung: beide FAIL mit `sqlite3.OperationalError: no such column: hausnummer` (Migration fehlt) bzw. `table kunden has no column named hausnummer` (INSERT-Mismatch).

- [ ] **Step 3: Migration in `init_db` ergänzen**

In `app/database.py` die Funktion `init_db` (Zeilen 26-42) erweitern um einen zusätzlichen `_add_column_if_not_exists`-Aufruf. Finde den Block:

```python
        _add_column_if_not_exists(
            conn, "bestellungen", "rabattbetrag_chf",
            "REAL NOT NULL DEFAULT 0",
        )
        conn.commit()
```

Und ersetze ihn durch:

```python
        _add_column_if_not_exists(
            conn, "bestellungen", "rabattbetrag_chf",
            "REAL NOT NULL DEFAULT 0",
        )
        _add_column_if_not_exists(
            conn, "kunden", "hausnummer",
            "TEXT NOT NULL DEFAULT ''",
        )
        conn.commit()
```

- [ ] **Step 4: Spiegel-Fixture in `conftest.py` ergänzen**

In `tests/conftest.py` die `db`-Fixture (Zeilen 30-49) spiegelt die Migration manuell. Finde den Block:

```python
    _add_column_if_not_exists(
        conn, "bestellungen", "rabattbetrag_chf",
        "REAL NOT NULL DEFAULT 0",
    )
    conn.commit()
```

Und ersetze ihn durch:

```python
    _add_column_if_not_exists(
        conn, "bestellungen", "rabattbetrag_chf",
        "REAL NOT NULL DEFAULT 0",
    )
    _add_column_if_not_exists(
        conn, "kunden", "hausnummer",
        "TEXT NOT NULL DEFAULT ''",
    )
    conn.commit()
```

- [ ] **Step 5: Repository-INSERT erweitern**

In `app/repositories/bestell_repo.py` die Funktion `kunde_anlegen` (Zeilen 15-23) ersetzen durch:

```python
def kunde_anlegen(conn: sqlite3.Connection, kunde: KundeInput) -> int:
    cursor = conn.execute(
        "INSERT INTO kunden (vorname, nachname, email, telefon, "
        "strasse, hausnummer, plz, ort) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (kunde.vorname, kunde.nachname, kunde.email, kunde.telefon,
         kunde.strasse, kunde.hausnummer, kunde.plz, kunde.ort),
    )
    conn.commit()
    return cursor.lastrowid
```

- [ ] **Step 6: Tests ausführen — MÜSSEN PASSEN**

Run:
```bash
uv run pytest tests/test_bestell_repo.py -v
```

Erwartung: alle Tests in der Datei PASS (bestehende + zwei neue).

- [ ] **Step 7: Gesamter Test-Suite grün?**

Run:
```bash
uv run pytest -x
```

Erwartung: kein Test schlägt fehl. Wenn ein Test bricht, weil er ein `dict(row)` auf einer Kunden-Zeile macht und neue Spalte ein neues Key bringt → anschauen, anpassen.

- [ ] **Step 8: Commit**

```bash
git add app/database.py app/repositories/bestell_repo.py tests/conftest.py tests/test_bestell_repo.py
git commit -m "$(cat <<'EOF'
feat: kunden.hausnummer-Spalte + INSERT erweitert (#101)

Idempotente Migration via _add_column_if_not_exists, Default ''
für Bestandskunden. kunde_anlegen schreibt jetzt auch hausnummer.
conftest db-Fixture spiegelt den Migration-Aufruf.
EOF
)"
```

---

## Task 4: Router-Form-Parameter

**Files:**
- Modify: `tests/test_api_bestellungen.py` (neue Testfunktion am Ende)
- Modify: `app/routers/bestellungen.py:112-155` (POST `/bestellen`)

- [ ] **Step 1: Failing Test schreiben**

Öffne `tests/test_api_bestellungen.py` und hänge am Ende an:

```python


@patch("app.services.email_service.brevo_client")
@patch("app.services.qr_service.generiere_qr_rechnung", return_value=b"%PDF-fake")
def test_bestellen_mit_hausnummer_persistiert(
    mock_qr, mock_email, client, csrf_token
):
    """POST /bestellen mit hausnummer → Wert landet in kunden.hausnummer."""
    import sqlite3

    from app.config import settings

    cart = json.dumps([{"produkt_id": 1, "menge": 2}])
    response = client.post("/bestellen", data={
        "vorname": "Klara", "nachname": "Tester",
        "email": "klara@test.ch", "strasse": "Musterstrasse",
        "hausnummer": "42",
        "plz": "8001", "ort": "Zürich",
        "versandart": "versand", "zahlungsart": "rechnung",
        "cart_data": cart, "kommentar": "",
        "csrf_token": csrf_token,
    }, follow_redirects=False)
    assert response.status_code in (200, 303)

    conn = sqlite3.connect(settings.database_path)
    try:
        row = conn.execute(
            "SELECT hausnummer FROM kunden WHERE email = ?", ("klara@test.ch",),
        ).fetchone()
        assert row is not None
        assert row[0] == "42"
    finally:
        conn.close()

    # QR-Service wurde mit kunde_hausnummer aufgerufen
    call_kwargs = mock_qr.call_args.kwargs
    assert call_kwargs.get("kunde_hausnummer") == "42"


def test_bestellen_ohne_hausnummer_kein_fehler(client, csrf_token):
    """POST /bestellen ohne hausnummer-Feld ist weiterhin gültig (Feld optional)."""
    cart = json.dumps([{"produkt_id": 1, "menge": 1}])
    response = client.post("/bestellen", data={
        "vorname": "Max", "nachname": "Muster",
        "email": "max@test.ch", "strasse": "Str. 1",
        "plz": "4600", "ort": "Olten",
        "versandart": "versand", "zahlungsart": "rechnung",
        "cart_data": cart, "kommentar": "",
        "csrf_token": csrf_token,
    }, follow_redirects=False)
    # Kein 422 (Form-Validierung), nicht unbedingt 200 (könnte Mail-Mock-abhängig sein)
    assert response.status_code != 422
```

- [ ] **Step 2: Tests ausführen — MÜSSEN FAILEN**

Run:
```bash
uv run pytest tests/test_api_bestellungen.py -v -k hausnummer
```

Erwartung: `test_bestellen_mit_hausnummer_persistiert` FAIL — der Router ignoriert das `hausnummer`-Feld (Form-Parameter nicht deklariert), DB enthält `hausnummer=""` statt `"42"`; und `mock_qr.call_args.kwargs.get("kunde_hausnummer")` ist `None`.

`test_bestellen_ohne_hausnummer_kein_fehler` könnte bereits PASS sein (da Router ohne Hausnummer funktioniert).

- [ ] **Step 3: Router-Signatur erweitern**

In `app/routers/bestellungen.py` die Funktion `bestellen` (Zeile 112 ff.) anpassen.

**3a)** Form-Parameter direkt nach `ort: str = Form()` einfügen (Zeile 120). Finde:

```python
    ort: str = Form(),
    telefon: str = Form(""),
```

Und ersetze durch:

```python
    ort: str = Form(),
    hausnummer: str = Form(""),
    telefon: str = Form(""),
```

**3b)** `KundeInput`-Construct (Zeilen 152-155) erweitern. Finde:

```python
    kunde_input = KundeInput(
        vorname=vorname, nachname=nachname, email=email,
        telefon=telefon, strasse=strasse, plz=plz, ort=ort,
    )
```

Und ersetze durch:

```python
    kunde_input = KundeInput(
        vorname=vorname, nachname=nachname, email=email,
        telefon=telefon, strasse=strasse, hausnummer=hausnummer,
        plz=plz, ort=ort,
    )
```

**3c)** QR-Service-Call (Zeilen 214-221) erweitern. Finde:

```python
            qr_pdf = generiere_qr_rechnung(
                betrag=gesamt,
                bestell_id=bestell_id,
                kunde_name=f"{kunde_input.vorname} {kunde_input.nachname}",
                kunde_adresse=kunde_input.strasse,
                kunde_plz=kunde_input.plz,
                kunde_ort=kunde_input.ort,
            )
```

Und ersetze durch:

```python
            qr_pdf = generiere_qr_rechnung(
                betrag=gesamt,
                bestell_id=bestell_id,
                kunde_name=f"{kunde_input.vorname} {kunde_input.nachname}",
                kunde_adresse=kunde_input.strasse,
                kunde_hausnummer=kunde_input.hausnummer,
                kunde_plz=kunde_input.plz,
                kunde_ort=kunde_input.ort,
            )
```

- [ ] **Step 4: Tests ausführen — MÜSSEN PASSEN**

Run:
```bash
uv run pytest tests/test_api_bestellungen.py -v
```

Erwartung: alle Tests in der Datei PASS.

- [ ] **Step 5: Commit**

```bash
git add app/routers/bestellungen.py tests/test_api_bestellungen.py
git commit -m "$(cat <<'EOF'
feat: /bestellen akzeptiert hausnummer-Form-Parameter (#101)

Router gibt hausnummer an KundeInput und generiere_qr_rechnung weiter.
Feld optional (Default ""); bestehende Integrationen bleiben
funktionsfähig.
EOF
)"
```

---

## Task 5: Checkout-Template

**Files:**
- Modify: `tests/test_api_seiten.py` (neue Testfunktion) — wenn `test_api_seiten.py` keinen `/checkout`-Test hat, ergänzen in `tests/test_api_bestellungen.py` stattdessen
- Modify: `templates/checkout.html:27-31` (Strasse-Zeile)

- [ ] **Step 1: Failing Test für das neue Feld**

Öffne `tests/test_api_bestellungen.py` und hänge am Ende an:

```python


def test_checkout_hat_hausnummer_feld(client):
    """Das Checkout-Formular enthält ein optionales Hausnummer-Eingabefeld."""
    response = client.get("/checkout")
    assert response.status_code == 200
    assert 'name="hausnummer"' in response.text
    assert ">Nr." in response.text  # Label
    assert 'maxlength="16"' in response.text  # qrbill-Limit
    # Feld darf kein required haben — prüfe beide möglichen Attribut-Reihenfolgen
    assert 'name="hausnummer" required' not in response.text
    assert 'required name="hausnummer"' not in response.text
```

- [ ] **Step 2: Test ausführen — MUSS FAILEN**

Run:
```bash
uv run pytest tests/test_api_bestellungen.py::test_checkout_hat_hausnummer_feld -v
```

Erwartung: FAIL (`assert 'name="hausnummer"' in response.text` schlägt fehl).

- [ ] **Step 3: Checkout-Template anpassen**

In `templates/checkout.html` den Block Zeilen 27-31 ersetzen. Finde:

```html
            <div class="col-span-2">
                <label class="block text-stone-400 text-sm mb-1">Strasse *</label>
                <input type="text" name="strasse" required autocomplete="street-address"
                       class="w-full bg-stone-800 border border-stone-600 rounded px-3 py-2">
            </div>
```

Und ersetze durch:

```html
            <div class="col-span-2 grid grid-cols-4 gap-4">
                <div class="col-span-3">
                    <label class="block text-stone-400 text-sm mb-1">Strasse *</label>
                    <input type="text" name="strasse" required autocomplete="street-address"
                           class="w-full bg-stone-800 border border-stone-600 rounded px-3 py-2">
                </div>
                <div class="col-span-1">
                    <label class="block text-stone-400 text-sm mb-1">Nr. <span class="text-stone-500">(optional)</span></label>
                    <input type="text" name="hausnummer" autocomplete="off" maxlength="16"
                           class="w-full bg-stone-800 border border-stone-600 rounded px-3 py-2">
                </div>
            </div>
```

- [ ] **Step 4: Test ausführen — MUSS PASSEN**

Run:
```bash
uv run pytest tests/test_api_bestellungen.py::test_checkout_hat_hausnummer_feld -v
```

Erwartung: PASS.

- [ ] **Step 5: Visuelle Prüfung lokal**

Dev-Server starten und Checkout im Browser öffnen — prüfen ob das Layout auf Desktop UND schmalem Viewport (375 px) sauber wirkt.

Run:
```bash
make dev
```

Dann im Browser `http://localhost:8000/checkout` öffnen. Prüfen:
- Strasse-Feld und Nr.-Feld nebeneinander, 3:1 Aufteilung
- Strasse hat `required`-Indikator, Nr. hat `(optional)`-Label
- Mobile: bei Safari Responsive Mode (375 px) bleibt das Layout lesbar

Server mit Ctrl+C stoppen.

- [ ] **Step 6: Commit**

```bash
git add templates/checkout.html tests/test_api_bestellungen.py
git commit -m "$(cat <<'EOF'
feat: Checkout-Formular mit optionalem Hausnummer-Feld (#101)

Strasse-Zeile als 3:1-Grid: Strasse links, Nr. rechts. Nr. ohne
required, mit maxlength 16 (qrbill-Limit), autocomplete off.
EOF
)"
```

---

## Task 6: Admin-Detail-Ansicht

**Files:**
- Modify: `tests/test_admin_repo.py` (neue Testfunktion)
- Modify: `app/repositories/admin_repo.py:114-121` (`get_bestellung_detail`-SELECT)
- Modify: `templates/admin/bestellung_detail.html:84-85` (Strasse-Zeile)

- [ ] **Step 1: Failing Test schreiben**

Öffne `tests/test_admin_repo.py` und hänge am Ende an:

```python


def test_get_bestellung_detail_liefert_hausnummer(db):
    """get_bestellung_detail enthält die hausnummer-Spalte des Kunden."""
    from app.models import KundeInput
    from app.repositories.admin_repo import get_bestellung_detail
    from app.repositories.bestell_repo import bestellung_anlegen, kunde_anlegen

    kunde = KundeInput(
        vorname="Klara", nachname="Tester", email="klara@test.ch",
        strasse="Musterstrasse", hausnummer="42",
        plz="8001", ort="Zürich",
    )
    kunde_id = kunde_anlegen(db, kunde)
    positionen = [{"produkt_id": 1, "menge": 1, "einzelpreis_chf": 8.0}]
    bestell_id = bestellung_anlegen(
        db, kunde_id=kunde_id, positionen=positionen,
        zahlungsart="rechnung", versandart="versand",
        versandkosten=9.90, total=17.90, kommentar="",
    )

    detail = get_bestellung_detail(db, bestell_id)
    assert detail is not None
    assert detail["hausnummer"] == "42"
    assert detail["strasse"] == "Musterstrasse"
```

- [ ] **Step 2: Test ausführen — MUSS FAILEN**

Run:
```bash
uv run pytest tests/test_admin_repo.py::test_get_bestellung_detail_liefert_hausnummer -v
```

Erwartung: FAIL mit `KeyError: 'hausnummer'` (Spalte nicht im SELECT).

- [ ] **Step 3: `admin_repo.py:get_bestellung_detail` erweitern**

In `app/repositories/admin_repo.py` die Funktion `get_bestellung_detail` (Zeilen 114-134) anpassen. Finde:

```python
    row = conn.execute(
        "SELECT b.*, k.vorname, k.nachname, k.email, k.telefon, "
        "k.strasse, k.plz, k.ort "
        "FROM bestellungen b JOIN kunden k ON b.kunde_id = k.id "
        "WHERE b.id = ?",
        (bestellung_id,),
    ).fetchone()
```

Und ersetze durch:

```python
    row = conn.execute(
        "SELECT b.*, k.vorname, k.nachname, k.email, k.telefon, "
        "k.strasse, k.hausnummer, k.plz, k.ort "
        "FROM bestellungen b JOIN kunden k ON b.kunde_id = k.id "
        "WHERE b.id = ?",
        (bestellung_id,),
    ).fetchone()
```

- [ ] **Step 4: Test ausführen — MUSS PASSEN**

Run:
```bash
uv run pytest tests/test_admin_repo.py -v
```

Erwartung: alle Tests in der Datei PASS.

- [ ] **Step 5: Admin-Template erweitern**

In `templates/admin/bestellung_detail.html` die Zeile 85 anpassen. Finde:

```jinja
                <span class="text-stone-400">Strasse</span>
                <span>{{ bestellung.strasse }}</span>
```

Und ersetze durch:

```jinja
                <span class="text-stone-400">Strasse</span>
                <span>{{ bestellung.strasse }}{% if bestellung.hausnummer %} {{ bestellung.hausnummer }}{% endif %}</span>
```

- [ ] **Step 6: Template-Rendering nicht kaputt**

Der Admin-Integration-Test `tests/test_api_admin.py` sollte weiterhin grün sein. Run:

```bash
uv run pytest tests/test_api_admin.py -v
```

Erwartung: PASS (es gibt keine direkte Assertion auf die Strasse-Zeile, aber das Template wird gerendert).

- [ ] **Step 7: Commit**

```bash
git add app/repositories/admin_repo.py templates/admin/bestellung_detail.html tests/test_admin_repo.py
git commit -m "$(cat <<'EOF'
feat: Admin-Bestelldetail zeigt Hausnummer (#101)

get_bestellung_detail liefert k.hausnummer mit; Template hängt sie
an die Strasse an, nur wenn gesetzt (kein Leerzeichen-Artefakt bei
Altbestellungen).
EOF
)"
```

---

## Task 7: E2E-Test erweitern

**Files:**
- Modify: `tests/test_e2e_bestellzyklus.py:198-213` (POST-Datenblock des Rechnungs-Flows)
- Modify: `tests/test_e2e_bestellzyklus.py:222-238` (DB-Assertion-Block nach dem POST)

- [ ] **Step 1: POST-Datenblock um `hausnummer` erweitern**

In `tests/test_e2e_bestellzyklus.py` die Zeilen 198-213 (im Test `test_e2e_rechnungs_flow`) ersetzen. Finde:

```python
    cart = json.dumps([{"produkt_id": 2, "menge": 1}])
    resp_bestellen = client.post(
        "/bestellen",
        data={
            "vorname": "Beat",
            "nachname": "Rechnung",
            "email": "beat@test.ch",
            "strasse": "Rechnungsweg 7",
            "plz": "3000",
            "ort": "Bern",
            "versandart": "abholung",
            "zahlungsart": "rechnung",
            "cart_data": cart,
            "kommentar": "",
            "csrf_token": csrf,
        },
        follow_redirects=False,
    )
```

Und ersetze durch:

```python
    cart = json.dumps([{"produkt_id": 2, "menge": 1}])
    resp_bestellen = client.post(
        "/bestellen",
        data={
            "vorname": "Beat",
            "nachname": "Rechnung",
            "email": "beat@test.ch",
            "strasse": "Rechnungsweg",
            "hausnummer": "7",
            "plz": "3000",
            "ort": "Bern",
            "versandart": "abholung",
            "zahlungsart": "rechnung",
            "cart_data": cart,
            "kommentar": "",
            "csrf_token": csrf,
        },
        follow_redirects=False,
    )
```

- [ ] **Step 2: DB-Assertion um `hausnummer` erweitern**

Direkt danach, Zeilen 222-238, den DB-Check-Block erweitern. Finde:

```python
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT b.id, b.status, b.zahlungsart, b.versandkosten_chf "
            "FROM bestellungen b JOIN kunden k ON b.kunde_id = k.id "
            "WHERE k.email = 'beat@test.ch'"
        ).fetchone()
        assert row is not None
        bestell_id = row["id"]
        assert row["status"] == "neu"
        assert row["zahlungsart"] == "rechnung"
        assert row["versandkosten_chf"] == 0  # Abholung = keine Versandkosten
    finally:
        conn.close()
```

Und ersetze durch:

```python
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT b.id, b.status, b.zahlungsart, b.versandkosten_chf, "
            "k.strasse, k.hausnummer "
            "FROM bestellungen b JOIN kunden k ON b.kunde_id = k.id "
            "WHERE k.email = 'beat@test.ch'"
        ).fetchone()
        assert row is not None
        bestell_id = row["id"]
        assert row["status"] == "neu"
        assert row["zahlungsart"] == "rechnung"
        assert row["versandkosten_chf"] == 0  # Abholung = keine Versandkosten
        assert row["strasse"] == "Rechnungsweg"
        assert row["hausnummer"] == "7"
    finally:
        conn.close()
```

- [ ] **Step 3: Test ausführen — MUSS PASSEN**

Run:
```bash
uv run pytest tests/test_e2e_bestellzyklus.py::test_e2e_rechnungs_flow -v
```

Erwartung: PASS. Tasks 1-6 sind bereits implementiert, der ganze E2E-Fluss inkl. Persistenz funktioniert.

- [ ] **Step 4: Commit**

```bash
git add tests/test_e2e_bestellzyklus.py
git commit -m "$(cat <<'EOF'
test: E2E-Rechnungs-Flow prüft hausnummer-Persistenz (#101)
EOF
)"
```

---

## Task 8: Dokumentation

**Files:**
- Modify: `docs/user-stories-testplan.md` (Story 1 Schritt 7 und ähnliche)

- [ ] **Step 1: Textplan anpassen**

Öffne `docs/user-stories-testplan.md` und ersetze alle Vorkommen von:

```
Kundendaten eingeben (Vorname, Nachname, E-Mail, Strasse, PLZ, Ort)
```

durch:

```
Kundendaten eingeben (Vorname, Nachname, E-Mail, Strasse, Hausnummer, PLZ, Ort)
```

Run:
```bash
grep -n "Strasse, PLZ, Ort" docs/user-stories-testplan.md
```

Erwartung: nach der Anpassung keine Treffer mehr. Falls der genaue Wortlaut anders vorkommt („Adresse eingeben" o. ä.): die manuelle Story analog anpassen.

- [ ] **Step 2: Diff prüfen**

Run:
```bash
git diff docs/user-stories-testplan.md
```

Nur die erwarteten Textersetzungen sind drin.

- [ ] **Step 3: Commit**

```bash
git add docs/user-stories-testplan.md
git commit -m "$(cat <<'EOF'
docs: user-stories-testplan listet Hausnummer als Checkout-Feld (#101)
EOF
)"
```

---

## Task 9: Full Suite + Push

- [ ] **Step 1: Gesamte Test-Suite laufen lassen**

Run:
```bash
uv run pytest -v
```

Erwartung: alle Tests grün. Wenn nicht: fehlschlagenden Test analysieren. Typische Fälle:
- Ein Test iteriert über `dict(kunde_row).keys()` und erwartet eine feste Liste → erweitern.
- Ein Test macht `client.post("/bestellen", data=...)` ohne alle Felder → Form-Defaults sollten greifen, aber prüfen.

- [ ] **Step 2: Lint/Format**

Run:
```bash
uv run ruff check app tests
uv run ruff format --check app tests
```

Erwartung: keine Verletzungen.

- [ ] **Step 3: Dev-Server Smoke-Test**

Run:
```bash
make dev
```

Dann im Browser:
1. `http://localhost:8000/checkout` — neues Feld sichtbar
2. Eine Bestellung mit Rechnung abschicken (mit und ohne Hausnummer)
3. `http://localhost:8000/admin/login` — anmelden, neue Bestellung öffnen
4. Strasse-Zeile zeigt „Musterstrasse 42" (mit) bzw. „Musterstrasse" (ohne)

Server stoppen (Ctrl+C).

- [ ] **Step 4: Push & Deploy**

Vor dem Push: sicherstellen, dass alle Commits Teil von PR #101 sind. Nach Push deployt die CI-Pipeline automatisch nach fly.io.

Run:
```bash
git push
```

- [ ] **Step 5: SH um Verifikation bitten**

Nachricht an SH (E-Mail/Signal/was üblich ist):

> Der Fix für Issue #101 ist live auf olivalle.ch. Bitte teste zwei Rechnungs-Bestellungen mit deinen beiden Banking-Apps:
>
> 1. Eine Bestellung mit Hausnummer (z. B. Strasse „Hegibergstrasse", Nr. „98")
> 2. Eine Bestellung ohne Hausnummer (Nr. leer lassen)
>
> Scanne beide QR-Rechnungen in beiden Apps und rapportiere, ob bei der ersten das Strasse-Feld nur noch den Strassennamen zeigt (und das Nr.-Feld die Zahl). Die zweite Variante darf weiterhin den „Compat-Modus" zeigen — das ist erwartet.

- [ ] **Step 6: Nach SH-Feedback — Issue schliessen oder reopen**

**Fall A:** Variante 1 zeigt bei beiden Apps saubere Trennung → Issue schliessen mit Kommentar, der das SH-Ergebnis dokumentiert.

**Fall B:** Variante 1 zeigt weiterhin Redundanz → Bug liegt in der Banking-App. Issue mit Hinweis schliessen oder in einen Banking-App-spezifischen Workaround-Ticket überführen. Kein Code-Rollback.

---

## Definition of Done

- [ ] Alle 9 Tasks committed
- [ ] `uv run pytest` grün
- [ ] `uv run ruff check` grün
- [ ] Deployed auf olivalle.ch
- [ ] SH hat Verifikation zurückgemeldet
- [ ] Issue #101 geschlossen
- [ ] README Phase-3-Fortschritt aktualisiert (falls #101 Milestone-relevant)
