# QR-Rechnung: Hausnummer-Feld und Debtor-Adresse (Issue #101)

## Kontext

SH hat am 18.04.2026 zwei Banking-Apps gegen eine produktive QR-Rechnung getestet und gemeldet, dass die komplette Adresse inkl. PLZ und Ort ins **Strasse**-Feld der App übernommen wird:

| Feld in der Banking-App | Inhalt nach Scan |
|---|---|
| Name | Sandro Del Favero |
| Strasse | `Hegibergstrasse 98, 4632 Trimbach` ← Redundanz |
| Nummer | *(leer)* |
| PLZ | 4632 |
| Ort | Trimbach |

## Root-Cause-Analyse

Die Hypothese aus dem Issue ("Combined Address / K-Typ") stimmt nicht. `qrbill` erzeugt mit den aktuellen Parametern bereits eine **StructuredAddress (S-Typ)**. Verifiziert durch Dump der QR-Nutzlast:

```
Zeile 21: 'S'                    ← Adresstyp
Zeile 22: 'Sandro Del Favero'    ← Name
Zeile 23: 'Hegibergstrasse 98'   ← Strasse (inkl. Nummer)
Zeile 24: ''                     ← Hausnummer (leer)
Zeile 25: '4632'                 ← PLZ
Zeile 26: 'Trimbach'             ← Ort
Zeile 27: 'CH'                   ← Land
```

Der QR-Code enthält PLZ und Ort **nur** in den dedizierten Zeilen 25/26 — **keine** Redundanz in der Nutzlast. Die Redundanz entsteht in der Banking-App-Anzeige: wenn `house_num` (Zeile 24) leer ist, fallen viele Apps offenbar in einen „Compat-Modus" und rendern die S-Typ-Adresse wie eine K-Typ-Adresse (Strasse+Nr und PLZ+Ort in zwei Textzeilen).

**Hypothese (zu verifizieren durch SH):** Sobald Zeile 24 (`house_num`) befüllt ist, erkennt die App eine saubere S-Typ-Adresse und zeigt Strasse, Nr, PLZ, Ort getrennt an.

## Entscheidungen

| Frage | Entscheid | Begründung |
|---|---|---|
| Lösungsansatz | Option B: separates Hausnummer-Feld im Checkout | Regex-Extraktion (Option A) ist fehleranfällig bei Edge-Cases. Ein separates Feld erzeugt saubere Daten ohne Heuristik. |
| Pflicht oder optional | **Optional** | ~1–3% der CH-Adressen haben keine Hausnummer (Dorfadressen, PO-Boxen, "Im Hof"). Optional entspricht dem UX-Muster des Telefon-Felds. |
| Migration alter Kundendaten | Keine | Alte Bestellungen sind abgeschlossen; `hausnummer` bleibt leer. Kein Backfill per Regex. |
| Verifikation | Durch SH nach Deploy | Konstantin kann das Problem in seinen Apps nicht reproduzieren. SH scannt produktiv. |
| Autocomplete-Token | `off` | HTML5 hat kein passendes Token; `address-line2` meint Apartment, nicht Hausnummer. |
| DB-Migration | Idempotent via `_add_column_if_not_exists` | Gleiche Mechanik wie bei `rabattcode_id`. Keine neue SQL-Datei. |

## Nicht-Ziele

- Keine Regex-basierte Extraktion aus bestehenden `strasse`-Werten.
- Keine Änderung an Stripe-Checkout (Stripe sammelt die Adresse selbst ab).
- Kein Umbau zur Trennung von Liefer- und Rechnungsadresse (bleibt eine Adresse).
- Keine neue Validierung für Sonderzeichen in der Hausnummer. `qrbill` limitiert `house_num` auf 16 Zeichen — unsere `max_length=16` harmonisiert damit. Das reicht auch für "34-36", "12a" oder "1er-Mars 12a".

## Komponenten & Datenfluss

```
templates/checkout.html          (neues Feld "Nr.", optional)
        │
        ▼
POST /bestellen  (Form-Parameter hausnummer)
        │
        ▼
KundeInput       (neues Feld hausnummer, max_length=16)
        │
        ├─► kunde_anlegen()    → INSERT in kunden.hausnummer
        │
        └─► generiere_qr_rechnung(kunde_hausnummer=...)
                     │
                     ▼
                QRBill(debtor={street, house_num, pcode, city})
                     │
                     ▼
                QR-Nutzlast Zeile 23=Strasse, Zeile 24=Nummer
```

Rückwärtskompatibilität: leere Hausnummer → QR-Code wie bisher (keine Regression für bestehende Rechnungs-Flows, die ohne `hausnummer` aufgerufen werden).

## UI-Details (Checkout)

Die Strasse-Zeile wird zu einem 3:1-Grid mit Strasse (`col-span-3`) und Hausnummer (`col-span-1`), eingebettet in das bestehende 2-Spalten-Grid der Lieferadresse:

```html
<div class="col-span-2 grid grid-cols-4 gap-4">
  <div class="col-span-3">
    <label class="...">Strasse *</label>
    <input name="strasse" required autocomplete="street-address" ...>
  </div>
  <div class="col-span-1">
    <label class="...">Nr. <span class="text-stone-500">(optional)</span></label>
    <input name="hausnummer" autocomplete="off" maxlength="16" ...>
  </div>
</div>
```

Mobile: 3:1-Aufteilung bleibt lesbar (Nummer braucht typischerweise 2–4 Zeichen, Strasse den Rest).

## Persistenz

### DB-Migration (`app/database.py:init_db`)

```python
_add_column_if_not_exists(
    conn, "kunden", "hausnummer",
    "TEXT NOT NULL DEFAULT ''",
)
```

Idempotent; neue und bestehende Deployments identisch. Keine neue SQL-Datei.

### Repository (`app/repositories/bestell_repo.py:kunde_anlegen`)

INSERT um eine Spalte erweitert:

```python
"INSERT INTO kunden (vorname, nachname, email, telefon, "
"strasse, hausnummer, plz, ort) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
```

### Model (`app/models.py:KundeInput`)

```python
hausnummer: str = Field(default="", max_length=16)
```

## QR-Service

### `app/services/qr_service.py:generiere_qr_rechnung`

Neuer optionaler Parameter `kunde_hausnummer`; wird als `house_num` an `QRBill(debtor=...)` gegeben:

```python
def generiere_qr_rechnung(
    betrag: float, bestell_id: int,
    kunde_name: str, kunde_adresse: str,
    kunde_plz: str, kunde_ort: str,
    kunde_hausnummer: str = "",
) -> bytes:
    ...
    debtor={
        "name": kunde_name,
        "street": kunde_adresse,
        "house_num": kunde_hausnummer,
        "pcode": kunde_plz,
        "city": kunde_ort,
        "country": "CH",
    },
```

Default `""` hält bestehende Aufrufer kompatibel.

## Router

`app/routers/bestellungen.py:POST /bestellen`:
- Form-Parameter: `hausnummer: str = Form("")`
- Weitergabe an `KundeInput`
- Bei `zahlungsart="rechnung"`: zusätzlicher Parameter `kunde_hausnummer=kunde_input.hausnummer` an `generiere_qr_rechnung(...)`

## Admin-Anzeige

`templates/admin/bestellung_detail.html`:

```jinja
{{ strasse }}{% if hausnummer %} {{ hausnummer }}{% endif %}
```

`app/repositories/admin_repo.py`: sicherstellen, dass `hausnummer` im SELECT der Bestelldetails mitgeliefert wird.

## Tests (pytest)

### `tests/test_qr_service.py`
- **Neu:** Test mit `kunde_hausnummer="42"`; Assert dass die QR-Nutzlast in Zeile 24 (Index 23 nach `\r\n`-Split) `"42"` enthält und Zeile 23 `"Musterstrasse"` ohne Nummer.
- **Neu:** Regressionstest ohne Hausnummer — Zeile 23 enthält den Komplett-Text, Zeile 24 bleibt leer.

### `tests/test_models.py`
- `KundeInput(..., hausnummer="42")` akzeptiert.
- Ohne `hausnummer` → Default `""`.
- `max_length=16` → 17 Zeichen wirft `ValidationError`.

### `tests/test_bestell_repo.py`
- `kunde_anlegen` mit `hausnummer="42"` → DB-Zeile `hausnummer="42"`.
- `kunde_anlegen` ohne Hausnummer → DB-Zeile `hausnummer=""`.

### `tests/test_api_bestellungen.py`
- POST mit `hausnummer="42"` → 303/200 wie heute.
- POST ohne `hausnummer` → kein 422 (Feld ist optional).

### `tests/test_e2e_bestellzyklus.py`
- Durchlauf mit gesetzter Hausnummer: Mail hat QR-Anhang, Admin-Sicht zeigt Hausnummer.

## TDD-Reihenfolge

1. QR-Nutzlast-Test rot → grün durch `qr_service.py`
2. Model-Test rot → grün durch `KundeInput`
3. Repo-Test rot → grün durch `kunde_anlegen` + DB-Migration
4. API-Test rot → grün durch Router-Änderung
5. Integration/E2E-Test rot → grün (Template + Admin)

## Verifikation nach Deploy

- Olivalle auf fly.io deployen.
- SH macht zwei Test-Bestellungen mit Zahlungsart „Rechnung":
  1. Mit Hausnummer
  2. Ohne Hausnummer
- SH scannt beide QR-Rechnungen in den **gleichen** zwei Banking-Apps, die den ursprünglichen Bug gezeigt haben.
- **Akzeptanz bestanden:** Bei der Bestellung *mit* Hausnummer zeigt die App Strasse-Feld nur mit Strassennamen und Nummer-Feld mit der Nummer; keine PLZ/Ort im Strasse-Feld.
- **Akzeptanz weich:** Bei der Bestellung *ohne* Hausnummer darf das Strasse-Feld weiterhin den Komplett-Text enthalten (Compat-Modus, bewusst in Kauf genommen bei optionaler Hausnummer).

## Rollback-Plan

Falls SH-Verifikation fehlschlägt (auch mit gefülltem `house_num` bleibt die Redundanz):
- Bug liegt in der Banking-App, nicht bei uns.
- Kein Code-Rollback nötig — das separate Feld ist auch für die Admin-Sicht und saubere Datenhaltung sinnvoll.
- Issue #101 neu bewerten, ggf. schliessen mit Hinweis auf Banking-App-Verhalten.

## Dokumentation

- `docs/user-stories-testplan.md`: Story 1 (Schritt 7) und ähnliche Stellen anpassen — „Strasse, Hausnummer, PLZ, Ort" statt „Strasse, PLZ, Ort".
- README/ARC42: kein Eintrag nötig (interne Feldtrennung, keine architektonische Änderung).

## Dateien (neu/geändert)

- geändert: `templates/checkout.html` (neues Feld, Grid-Anpassung)
- geändert: `app/models.py` (KundeInput.hausnummer)
- geändert: `app/routers/bestellungen.py` (Form-Parameter, QR-Call)
- geändert: `app/repositories/bestell_repo.py` (INSERT-Spalte)
- geändert: `app/repositories/admin_repo.py` (SELECT mit hausnummer)
- geändert: `app/database.py` (Migration-Helper-Aufruf)
- geändert: `app/services/qr_service.py` (Parameter + house_num)
- geändert: `templates/admin/bestellung_detail.html` (Anzeige)
- geändert: `tests/test_qr_service.py`
- geändert: `tests/test_models.py`
- geändert: `tests/test_bestell_repo.py`
- geändert: `tests/test_api_bestellungen.py`
- geändert: `tests/test_e2e_bestellzyklus.py`
- geändert: `docs/user-stories-testplan.md`
