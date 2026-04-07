# PLZ-Autocomplete (Issue #52)

## Ziel
Beim Checkout wird das Ort-Feld automatisch gefüllt, sobald eine 4-stellige Schweizer PLZ eingegeben wurde. Reduziert Tipparbeit (Persona Marco).

## Nicht-Ziele
- Kein Dropdown für mehrdeutige PLZs (KISS).
- Keine Validierung "PLZ existiert" als Pflicht — Fail silent, User kann manuell tippen.
- Keine Strassen-/Adress-Vervollständigung.

## Datenquelle
- Statische Datei `data/plz_ch.json`, Format `{"<plz>": "<ort>"}`.
- Quelle: Swiss Post Amtliches Ortschaftenverzeichnis (OpenData, gemeinfrei).
- Bei mehrdeutigen PLZs: Hauptort. Bei zweisprachigen Regionen: deutsche Bezeichnung (Freiburg, Biel, Siders, …).
- Build-Skript `scripts/build_plz_data.py` (einmalig/manuell ausgeführt, generiert die JSON aus dem offiziellen Datensatz). Skript und JSON beide ins Repo.
- Grösse: ~80–120 KB.

## Backend
- Neuer Router `app/routers/plz.py`:
  - `GET /api/plz/{plz}` → `200 {"ort": "Olten"}`
  - `404` wenn unbekannt
  - `422` wenn nicht 4 Ziffern (FastAPI-Validierung via `Path(..., regex="^[0-9]{4}$")`)
- Daten werden beim Modul-Import einmalig aus `data/plz_ch.json` in ein dict geladen. Kein Caching-Layer, keine DB.
- Router wird in `app/main.py` registriert.

## Frontend
- `templates/checkout.html`: Inline `<script>` am Ende des Formulars.
- Listener `input` auf `#plz` (id ergänzen falls nötig):
  - Bei genau 4 Ziffern → `fetch('/api/plz/' + plz)`
  - Bei Erfolg → Ort-Feld nur füllen, wenn aktuell leer (User-Eingabe respektieren)
  - Bei Fehler/404 → nichts tun
- Kein Spinner, keine Fehlermeldung.

## Tests (pytest)
- `tests/test_plz_router.py`:
  - gültige PLZ → 200 + erwarteter Ort (`4600` → `Olten`)
  - unbekannte PLZ → 404
  - ungültiges Format (`abcd`, `123`, `12345`) → 422

## Abhängigkeiten
- Keine neuen Python-Packages.
- Keine JS-Libraries.
- Keine externen API-Calls zur Laufzeit.

## Dateien (neu/geändert)
- neu: `data/plz_ch.json`
- neu: `scripts/build_plz_data.py`
- neu: `app/routers/plz.py`
- neu: `tests/test_plz_router.py`
- geändert: `app/main.py` (Router registrieren)
- geändert: `templates/checkout.html` (Inline-JS + ggf. `id="plz"`)
