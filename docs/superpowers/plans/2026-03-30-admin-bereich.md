# Admin-Bereich Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Admin-Bereich für Bestellübersicht mit Login, Dashboard, Statusverwaltung und Audit-Log.

**Architecture:** Neuer Router `/admin` mit eigenen Templates, Auth-Service (bcrypt + signierte Session-Cookies), Admin-Log-Tabelle. Folgt bestehender Architektur: Router → Repository → Service.

**Tech Stack:** FastAPI, Jinja2, Tailwind CSS (CDN), SQLite, bcrypt, itsdangerous

**Spec:** `docs/superpowers/specs/2026-03-30-admin-bereich-design.md`

---

## File Structure

### Neue Dateien

| Datei | Verantwortung |
|---|---|
| `migrations/002_admin.sql` | `admin_log`-Tabelle |
| `app/services/auth_service.py` | Passwort-Prüfung, Session-Erstellung/-Validierung, Brute-Force-Schutz |
| `app/repositories/admin_repo.py` | Dashboard-Queries, Log-Einträge, Bestelldetails für Admin |
| `app/routers/admin.py` | Alle `/admin/*`-Routen |
| `templates/admin/base.html` | Admin-Base-Template (erbt von `base.html`) |
| `templates/admin/login.html` | Login-Formular |
| `templates/admin/dashboard.html` | Dashboard mit Kennzahlen + Bestelltabelle |
| `templates/admin/bestellung_detail.html` | Bestelldetail + Log + Notiz-Formular |
| `tests/test_auth_service.py` | Unit-Tests Auth-Service |
| `tests/test_admin_repo.py` | Unit-Tests Admin-Repository |
| `tests/test_api_admin.py` | Integration-Tests Admin-Routen |

### Geänderte Dateien

| Datei | Änderung |
|---|---|
| `app/config.py` | `admin_credentials` + `admin_session_max_age` Settings |
| `app/main.py` | Admin-Router einbinden |
| `pyproject.toml` | `bcrypt`-Dependency hinzufügen |
| `.env.example` | `ADMIN_CREDENTIALS`-Beispiel |
| `app/services/email_service.py` | Nach Mailversand Log-Eintrag schreiben |
| `app/routers/webhooks.py` | Nach Status-Änderung auf `bezahlt` Log-Eintrag schreiben |

---

## Task 1: Migration und Config

**Files:**
- Create: `migrations/002_admin.sql`
- Modify: `app/config.py:1-26`
- Modify: `pyproject.toml:5-14` (dependencies)
- Modify: `.env.example`

- [ ] **Step 1: Migration-Datei erstellen**

```sql
-- migrations/002_admin.sql
CREATE TABLE IF NOT EXISTS admin_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    zeitpunkt TEXT NOT NULL DEFAULT (datetime('now')),
    admin_label TEXT NOT NULL,
    aktion TEXT NOT NULL,
    details TEXT NOT NULL DEFAULT '',
    bestellung_id INTEGER REFERENCES bestellungen(id)
);

CREATE INDEX IF NOT EXISTS idx_admin_log_bestellung
    ON admin_log(bestellung_id);

CREATE INDEX IF NOT EXISTS idx_admin_log_zeitpunkt
    ON admin_log(zeitpunkt);
```

- [ ] **Step 2: Config erweitern**

In `app/config.py` zwei neue Felder in der `Settings`-Klasse ergänzen:

```python
# Nach Zeile 21 (database_path):
admin_credentials: str = ""  # "label:bcrypt_hash,label:bcrypt_hash"
admin_session_max_age: int = 86400  # 24h
```

- [ ] **Step 3: bcrypt-Dependency hinzufügen**

In `pyproject.toml`, in der `dependencies`-Liste:

```toml
"bcrypt>=4.2",
```

- [ ] **Step 4: .env.example erweitern**

Am Ende von `.env.example` hinzufügen:

```env
# Admin (bcrypt-Hashes, Format: label:hash,label:hash)
# Hash generieren: python -c "import bcrypt; print(bcrypt.hashpw(b'mein-passwort', bcrypt.gensalt()).decode())"
ADMIN_CREDENTIALS=owner:$2b$12$...,dev:$2b$12$...
```

- [ ] **Step 5: Dependencies installieren**

Run: `cd /Users/KN/Dropbox/Privat/CAS/projekte/olivalle && pip install -e ".[dev]"`
Expected: bcrypt wird installiert

- [ ] **Step 6: Migration testen**

Run: `cd /Users/KN/Dropbox/Privat/CAS/projekte/olivalle && python -c "from app.database import init_db; init_db(); print('OK')"`
Expected: `OK` (keine Fehler, `admin_log`-Tabelle wird erstellt)

- [ ] **Step 7: Commit**

```bash
git add migrations/002_admin.sql app/config.py pyproject.toml .env.example
git commit -m "feat(admin): Migration admin_log + Config-Erweiterung"
```

---

## Task 2: Auth-Service

**Files:**
- Create: `app/services/auth_service.py`
- Create: `tests/test_auth_service.py`

- [ ] **Step 1: Test-Datei erstellen — Credentials parsen**

```python
# tests/test_auth_service.py
import bcrypt
import pytest


def _make_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


class TestParseCredentials:
    def test_parse_single_credential(self):
        from app.services.auth_service import parse_credentials

        pw_hash = _make_hash("geheim")
        result = parse_credentials(f"owner:{pw_hash}")
        assert len(result) == 1
        assert result[0][0] == "owner"
        assert result[0][1] == pw_hash

    def test_parse_multiple_credentials(self):
        from app.services.auth_service import parse_credentials

        h1 = _make_hash("pass1")
        h2 = _make_hash("pass2")
        result = parse_credentials(f"owner:{h1},dev:{h2}")
        assert len(result) == 2
        assert result[0][0] == "owner"
        assert result[1][0] == "dev"

    def test_parse_empty_string(self):
        from app.services.auth_service import parse_credentials

        result = parse_credentials("")
        assert result == []
```

- [ ] **Step 2: Test ausführen — muss fehlschlagen**

Run: `cd /Users/KN/Dropbox/Privat/CAS/projekte/olivalle && python -m pytest tests/test_auth_service.py::TestParseCredentials -v`
Expected: FAIL mit `ModuleNotFoundError`

- [ ] **Step 3: parse_credentials implementieren**

```python
# app/services/auth_service.py


def parse_credentials(credentials_str: str) -> list[tuple[str, str]]:
    """Parse 'label:hash,label:hash' into [(label, hash), ...]."""
    if not credentials_str.strip():
        return []
    result = []
    for entry in credentials_str.split(","):
        label, bcrypt_hash = entry.split(":", 1)
        result.append((label.strip(), bcrypt_hash.strip()))
    return result
```

- [ ] **Step 4: Test ausführen — muss bestehen**

Run: `cd /Users/KN/Dropbox/Privat/CAS/projekte/olivalle && python -m pytest tests/test_auth_service.py::TestParseCredentials -v`
Expected: 3 PASSED

- [ ] **Step 5: Test schreiben — Passwort prüfen**

```python
# In tests/test_auth_service.py, neue Klasse am Ende:

class TestVerifyPassword:
    def test_correct_password_returns_label(self):
        from app.services.auth_service import verify_password

        h = _make_hash("geheim")
        credentials = [("owner", h)]
        assert verify_password("geheim", credentials) == "owner"

    def test_wrong_password_returns_none(self):
        from app.services.auth_service import verify_password

        h = _make_hash("geheim")
        credentials = [("owner", h)]
        assert verify_password("falsch", credentials) is None

    def test_matches_correct_credential_among_multiple(self):
        from app.services.auth_service import verify_password

        h1 = _make_hash("pass-owner")
        h2 = _make_hash("pass-dev")
        credentials = [("owner", h1), ("dev", h2)]
        assert verify_password("pass-dev", credentials) == "dev"

    def test_empty_credentials_returns_none(self):
        from app.services.auth_service import verify_password

        assert verify_password("anything", []) is None
```

- [ ] **Step 6: Test ausführen — muss fehlschlagen**

Run: `cd /Users/KN/Dropbox/Privat/CAS/projekte/olivalle && python -m pytest tests/test_auth_service.py::TestVerifyPassword -v`
Expected: FAIL mit `ImportError`

- [ ] **Step 7: verify_password implementieren**

```python
# In app/services/auth_service.py, am Ende:
import bcrypt


def verify_password(
    password: str, credentials: list[tuple[str, str]]
) -> str | None:
    """Check password against all credential hashes. Return label or None."""
    for label, pw_hash in credentials:
        if bcrypt.checkpw(password.encode(), pw_hash.encode()):
            return label
    return None
```

- [ ] **Step 8: Test ausführen — muss bestehen**

Run: `cd /Users/KN/Dropbox/Privat/CAS/projekte/olivalle && python -m pytest tests/test_auth_service.py -v`
Expected: 7 PASSED

- [ ] **Step 9: Tests schreiben — Session erstellen und validieren**

```python
# In tests/test_auth_service.py, neue Klasse am Ende:

class TestSession:
    def test_create_and_validate_session(self):
        from app.services.auth_service import create_session, validate_session

        token = create_session("owner", secret="test-secret")
        assert isinstance(token, str)
        label = validate_session(token, secret="test-secret")
        assert label == "owner"

    def test_invalid_token_returns_none(self):
        from app.services.auth_service import validate_session

        assert validate_session("garbage", secret="test-secret") is None

    def test_expired_session_returns_none(self):
        from app.services.auth_service import create_session, validate_session

        token = create_session("owner", secret="test-secret")
        # max_age=0 means expired immediately
        assert validate_session(token, secret="test-secret", max_age=0) is None
```

- [ ] **Step 10: Test ausführen — muss fehlschlagen**

Run: `cd /Users/KN/Dropbox/Privat/CAS/projekte/olivalle && python -m pytest tests/test_auth_service.py::TestSession -v`
Expected: FAIL mit `ImportError`

- [ ] **Step 11: Session-Funktionen implementieren**

```python
# In app/services/auth_service.py, am Anfang itsdangerous importieren:
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

# Am Ende der Datei:

def create_session(admin_label: str, *, secret: str) -> str:
    """Create a signed session token containing the admin label."""
    s = URLSafeTimedSerializer(secret)
    return s.dumps({"admin_label": admin_label})


def validate_session(
    token: str, *, secret: str, max_age: int = 86400
) -> str | None:
    """Validate session token. Return admin_label or None."""
    s = URLSafeTimedSerializer(secret)
    try:
        data = s.loads(token, max_age=max_age)
        return data.get("admin_label")
    except (BadSignature, SignatureExpired):
        return None
```

- [ ] **Step 12: Test ausführen — muss bestehen**

Run: `cd /Users/KN/Dropbox/Privat/CAS/projekte/olivalle && python -m pytest tests/test_auth_service.py -v`
Expected: 10 PASSED

- [ ] **Step 13: Tests schreiben — Brute-Force-Schutz**

```python
# In tests/test_auth_service.py, neue Klasse am Ende:

class TestBruteForce:
    def test_under_limit_not_locked(self):
        from app.services.auth_service import BruteForceGuard

        guard = BruteForceGuard(max_attempts=3, window_seconds=60, lockout_seconds=30)
        for _ in range(2):
            guard.record_failure("1.2.3.4")
        assert guard.is_locked("1.2.3.4") is False

    def test_at_limit_locked(self):
        from app.services.auth_service import BruteForceGuard

        guard = BruteForceGuard(max_attempts=3, window_seconds=60, lockout_seconds=30)
        for _ in range(3):
            guard.record_failure("1.2.3.4")
        assert guard.is_locked("1.2.3.4") is True

    def test_different_ips_independent(self):
        from app.services.auth_service import BruteForceGuard

        guard = BruteForceGuard(max_attempts=3, window_seconds=60, lockout_seconds=30)
        for _ in range(3):
            guard.record_failure("1.2.3.4")
        assert guard.is_locked("5.6.7.8") is False

    def test_reset_clears_failures(self):
        from app.services.auth_service import BruteForceGuard

        guard = BruteForceGuard(max_attempts=3, window_seconds=60, lockout_seconds=30)
        for _ in range(3):
            guard.record_failure("1.2.3.4")
        guard.reset("1.2.3.4")
        assert guard.is_locked("1.2.3.4") is False
```

- [ ] **Step 14: Test ausführen — muss fehlschlagen**

Run: `cd /Users/KN/Dropbox/Privat/CAS/projekte/olivalle && python -m pytest tests/test_auth_service.py::TestBruteForce -v`
Expected: FAIL mit `ImportError`

- [ ] **Step 15: BruteForceGuard implementieren**

```python
# In app/services/auth_service.py, am Anfang time importieren:
import time

# Am Ende der Datei:

class BruteForceGuard:
    """In-memory brute-force protection per IP."""

    def __init__(
        self,
        max_attempts: int = 5,
        window_seconds: int = 900,
        lockout_seconds: int = 300,
    ):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.lockout_seconds = lockout_seconds
        self._failures: dict[str, list[float]] = {}

    def record_failure(self, ip: str) -> None:
        now = time.time()
        if ip not in self._failures:
            self._failures[ip] = []
        self._failures[ip].append(now)

    def is_locked(self, ip: str) -> bool:
        if ip not in self._failures:
            return False
        now = time.time()
        # Only count recent failures within window
        recent = [t for t in self._failures[ip] if now - t < self.window_seconds]
        self._failures[ip] = recent
        if len(recent) < self.max_attempts:
            return False
        # Check if lockout period has passed since last failure
        last_failure = max(recent)
        return now - last_failure < self.lockout_seconds

    def reset(self, ip: str) -> None:
        self._failures.pop(ip, None)


# Module-level singleton
login_guard = BruteForceGuard()
```

- [ ] **Step 16: Alle Tests ausführen**

Run: `cd /Users/KN/Dropbox/Privat/CAS/projekte/olivalle && python -m pytest tests/test_auth_service.py -v`
Expected: 14 PASSED

- [ ] **Step 17: Commit**

```bash
git add app/services/auth_service.py tests/test_auth_service.py
git commit -m "feat(admin): Auth-Service mit Passwort-Prüfung, Sessions, Brute-Force"
```

---

## Task 3: Admin-Repository

**Files:**
- Create: `app/repositories/admin_repo.py`
- Create: `tests/test_admin_repo.py`

- [ ] **Step 1: Test-Datei erstellen — Log-Eintrag schreiben**

```python
# tests/test_admin_repo.py
import pytest


class TestLogEintrag:
    def test_log_eintrag_schreiben(self, db):
        from app.repositories.admin_repo import log_eintrag_schreiben

        log_id = log_eintrag_schreiben(
            db,
            admin_label="dev",
            aktion="login",
            details="127.0.0.1",
        )
        assert log_id > 0
        row = db.execute("SELECT * FROM admin_log WHERE id = ?", (log_id,)).fetchone()
        assert row["admin_label"] == "dev"
        assert row["aktion"] == "login"
        assert row["details"] == "127.0.0.1"
        assert row["bestellung_id"] is None

    def test_log_eintrag_mit_bestellung(self, db):
        from app.repositories.admin_repo import log_eintrag_schreiben

        # Kunde + Bestellung anlegen für FK
        db.execute(
            "INSERT INTO kunden (vorname, nachname, email, strasse, plz, ort) "
            "VALUES ('Max', 'Muster', 'max@test.ch', 'Str 1', '4600', 'Olten')"
        )
        db.execute(
            "INSERT INTO bestellungen (kunde_id, zahlungsart, versandart, total_chf) "
            "VALUES (1, 'stripe', 'versand', 50.00)"
        )
        db.commit()

        log_id = log_eintrag_schreiben(
            db,
            admin_label="owner",
            aktion="status_geaendert",
            details='{"von": "neu", "nach": "bezahlt"}',
            bestellung_id=1,
        )
        row = db.execute("SELECT * FROM admin_log WHERE id = ?", (log_id,)).fetchone()
        assert row["bestellung_id"] == 1
```

- [ ] **Step 2: Test ausführen — muss fehlschlagen**

Run: `cd /Users/KN/Dropbox/Privat/CAS/projekte/olivalle && python -m pytest tests/test_admin_repo.py::TestLogEintrag -v`
Expected: FAIL mit `ModuleNotFoundError`

- [ ] **Step 3: log_eintrag_schreiben implementieren**

```python
# app/repositories/admin_repo.py
import sqlite3


def log_eintrag_schreiben(
    conn: sqlite3.Connection,
    *,
    admin_label: str,
    aktion: str,
    details: str = "",
    bestellung_id: int | None = None,
) -> int:
    cursor = conn.execute(
        "INSERT INTO admin_log (admin_label, aktion, details, bestellung_id) "
        "VALUES (?, ?, ?, ?)",
        (admin_label, aktion, details, bestellung_id),
    )
    conn.commit()
    return cursor.lastrowid
```

- [ ] **Step 4: Test ausführen — muss bestehen**

Run: `cd /Users/KN/Dropbox/Privat/CAS/projekte/olivalle && python -m pytest tests/test_admin_repo.py::TestLogEintrag -v`
Expected: 2 PASSED

- [ ] **Step 5: Tests schreiben — Dashboard-Queries**

```python
# In tests/test_admin_repo.py, Hilfsfunktion + neue Klasse:

def _seed_bestellungen(db, count=3):
    """Seed-Daten: ein Kunde und mehrere Bestellungen."""
    db.execute(
        "INSERT INTO kunden (vorname, nachname, email, strasse, plz, ort) "
        "VALUES ('Max', 'Muster', 'max@test.ch', 'Str 1', '4600', 'Olten')"
    )
    stati = ["neu", "bezahlt", "versendet"]
    for i in range(count):
        db.execute(
            "INSERT INTO bestellungen "
            "(kunde_id, status, zahlungsart, versandart, total_chf, erstellt_am) "
            "VALUES (1, ?, 'stripe', 'versand', ?, datetime('now'))",
            (stati[i % len(stati)], 50.00 + i * 10),
        )
        db.execute(
            "INSERT INTO bestellpositionen "
            "(bestellung_id, produkt_id, menge, einzelpreis_chf) "
            "VALUES (?, 1, 2, 8.00)",
            (i + 1,),
        )
    db.commit()


class TestDashboardQueries:
    def test_get_dashboard_stats(self, db):
        from app.repositories.admin_repo import get_dashboard_stats

        _seed_bestellungen(db, 3)
        stats = get_dashboard_stats(db)
        assert stats["offene_bestellungen"] == 2  # neu + bezahlt
        assert stats["umsatz_monat"] > 0
        assert stats["bestellungen_heute"] == 3

    def test_get_bestellungen_liste(self, db):
        from app.repositories.admin_repo import get_bestellungen_liste

        _seed_bestellungen(db, 3)
        rows = get_bestellungen_liste(db)
        assert len(rows) == 3
        # Neueste zuerst
        assert rows[0]["id"] >= rows[1]["id"]

    def test_get_bestellungen_liste_filter_status(self, db):
        from app.repositories.admin_repo import get_bestellungen_liste

        _seed_bestellungen(db, 3)
        rows = get_bestellungen_liste(db, status="neu")
        assert len(rows) == 1
        assert rows[0]["status"] == "neu"

    def test_get_bestellungen_liste_suche(self, db):
        from app.repositories.admin_repo import get_bestellungen_liste

        _seed_bestellungen(db, 3)
        rows = get_bestellungen_liste(db, suche="Muster")
        assert len(rows) == 3
        rows = get_bestellungen_liste(db, suche="gibts-nicht")
        assert len(rows) == 0
```

- [ ] **Step 6: Test ausführen — muss fehlschlagen**

Run: `cd /Users/KN/Dropbox/Privat/CAS/projekte/olivalle && python -m pytest tests/test_admin_repo.py::TestDashboardQueries -v`
Expected: FAIL mit `ImportError`

- [ ] **Step 7: Dashboard-Queries implementieren**

```python
# In app/repositories/admin_repo.py, am Ende:


def get_dashboard_stats(conn: sqlite3.Connection) -> dict:
    offene = conn.execute(
        "SELECT COUNT(*) as c FROM bestellungen WHERE status IN ('neu', 'bezahlt')"
    ).fetchone()["c"]

    umsatz = conn.execute(
        "SELECT COALESCE(SUM(total_chf), 0) as s FROM bestellungen "
        "WHERE status != 'storniert' "
        "AND strftime('%Y-%m', erstellt_am) = strftime('%Y-%m', 'now')"
    ).fetchone()["s"]

    heute = conn.execute(
        "SELECT COUNT(*) as c FROM bestellungen "
        "WHERE date(erstellt_am) = date('now')"
    ).fetchone()["c"]

    return {
        "offene_bestellungen": offene,
        "umsatz_monat": umsatz,
        "bestellungen_heute": heute,
    }


def get_bestellungen_liste(
    conn: sqlite3.Connection,
    *,
    status: str = "",
    suche: str = "",
    datum_von: str = "",
    datum_bis: str = "",
) -> list[dict]:
    query = (
        "SELECT b.id, b.erstellt_am, b.status, b.zahlungsart, b.versandart, "
        "b.total_chf, k.vorname, k.nachname, k.email "
        "FROM bestellungen b JOIN kunden k ON b.kunde_id = k.id "
        "WHERE 1=1"
    )
    params: list = []

    if status:
        query += " AND b.status = ?"
        params.append(status)
    if suche:
        query += (
            " AND (k.vorname || ' ' || k.nachname LIKE ? "
            "OR k.email LIKE ? OR CAST(b.id AS TEXT) = ?)"
        )
        params.extend([f"%{suche}%", f"%{suche}%", suche])
    if datum_von:
        query += " AND date(b.erstellt_am) >= ?"
        params.append(datum_von)
    if datum_bis:
        query += " AND date(b.erstellt_am) <= ?"
        params.append(datum_bis)

    query += " ORDER BY b.erstellt_am DESC"

    return [dict(row) for row in conn.execute(query, params).fetchall()]
```

- [ ] **Step 8: Test ausführen — muss bestehen**

Run: `cd /Users/KN/Dropbox/Privat/CAS/projekte/olivalle && python -m pytest tests/test_admin_repo.py -v`
Expected: 6 PASSED

- [ ] **Step 9: Tests schreiben — Bestelldetail und Status-Update**

```python
# In tests/test_admin_repo.py, neue Klasse am Ende:


class TestBestellDetail:
    def test_get_bestellung_detail(self, db):
        from app.repositories.admin_repo import get_bestellung_detail

        _seed_bestellungen(db, 1)
        detail = get_bestellung_detail(db, 1)
        assert detail is not None
        assert detail["id"] == 1
        assert detail["vorname"] == "Max"
        assert len(detail["positionen"]) == 1

    def test_get_bestellung_detail_nicht_gefunden(self, db):
        from app.repositories.admin_repo import get_bestellung_detail

        assert get_bestellung_detail(db, 999) is None

    def test_update_status(self, db):
        from app.repositories.admin_repo import update_bestellung_status

        _seed_bestellungen(db, 1)
        update_bestellung_status(db, bestellung_id=1, neuer_status="versendet")
        row = db.execute("SELECT status FROM bestellungen WHERE id = 1").fetchone()
        assert row["status"] == "versendet"

    def test_get_log_fuer_bestellung(self, db):
        from app.repositories.admin_repo import (
            get_log_fuer_bestellung,
            log_eintrag_schreiben,
        )

        _seed_bestellungen(db, 1)
        log_eintrag_schreiben(
            db, admin_label="dev", aktion="notiz_hinzugefuegt",
            details="Testnotiz", bestellung_id=1,
        )
        logs = get_log_fuer_bestellung(db, 1)
        assert len(logs) == 1
        assert logs[0]["aktion"] == "notiz_hinzugefuegt"
```

- [ ] **Step 10: Test ausführen — muss fehlschlagen**

Run: `cd /Users/KN/Dropbox/Privat/CAS/projekte/olivalle && python -m pytest tests/test_admin_repo.py::TestBestellDetail -v`
Expected: FAIL mit `ImportError`

- [ ] **Step 11: Bestelldetail-Queries implementieren**

```python
# In app/repositories/admin_repo.py, am Ende:


def get_bestellung_detail(
    conn: sqlite3.Connection, bestellung_id: int
) -> dict | None:
    row = conn.execute(
        "SELECT b.*, k.vorname, k.nachname, k.email, k.telefon, "
        "k.strasse, k.plz, k.ort "
        "FROM bestellungen b JOIN kunden k ON b.kunde_id = k.id "
        "WHERE b.id = ?",
        (bestellung_id,),
    ).fetchone()

    if not row:
        return None

    detail = dict(row)
    positionen = conn.execute(
        "SELECT bp.menge, bp.einzelpreis_chf, p.name "
        "FROM bestellpositionen bp JOIN produkte p ON bp.produkt_id = p.id "
        "WHERE bp.bestellung_id = ?",
        (bestellung_id,),
    ).fetchall()
    detail["positionen"] = [dict(p) for p in positionen]
    return detail


def update_bestellung_status(
    conn: sqlite3.Connection, *, bestellung_id: int, neuer_status: str
) -> None:
    conn.execute(
        "UPDATE bestellungen SET status = ? WHERE id = ?",
        (neuer_status, bestellung_id),
    )
    conn.commit()


def get_log_fuer_bestellung(
    conn: sqlite3.Connection, bestellung_id: int
) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM admin_log WHERE bestellung_id = ? "
        "ORDER BY zeitpunkt DESC",
        (bestellung_id,),
    ).fetchall()
    return [dict(r) for r in rows]
```

- [ ] **Step 12: Alle Tests ausführen**

Run: `cd /Users/KN/Dropbox/Privat/CAS/projekte/olivalle && python -m pytest tests/test_admin_repo.py -v`
Expected: 10 PASSED

- [ ] **Step 13: Commit**

```bash
git add app/repositories/admin_repo.py tests/test_admin_repo.py
git commit -m "feat(admin): Repository mit Dashboard-Queries, Bestelldetail, Log"
```

---

## Task 4: Admin-Templates

**Files:**
- Create: `templates/admin/base.html`
- Create: `templates/admin/login.html`
- Create: `templates/admin/dashboard.html`
- Create: `templates/admin/bestellung_detail.html`

- [ ] **Step 1: Admin-Base-Template erstellen**

```html
{# templates/admin/base.html #}
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Admin{% endblock %} — Olivalle</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    colors: { accent: '#f1d600' },
                    fontFamily: {
                        display: ['"Amatic SC"', 'cursive'],
                        body: ['Lora', 'serif'],
                    },
                }
            }
        }
    </script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Amatic+SC:wght@400;700&family=Lora:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet">
</head>
<body class="bg-stone-800 text-white min-h-screen flex flex-col font-body">
    <header class="sticky top-0 z-50 bg-stone-800/90 backdrop-blur-sm border-b border-stone-700 py-4">
        <div class="max-w-6xl mx-auto px-4 flex items-center justify-between">
            <div class="flex items-center gap-3">
                <a href="/admin/" class="font-display text-4xl font-bold text-accent">Olivalle</a>
                <span class="text-stone-400 text-sm border border-stone-600 rounded px-2 py-0.5">Admin</span>
            </div>
            <div class="flex items-center gap-4 text-sm">
                <span class="text-stone-400">{{ admin_label }}</span>
                <form method="post" action="/admin/logout">
                    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
                    <button type="submit" class="text-stone-300 hover:text-accent transition-colors">Abmelden</button>
                </form>
            </div>
        </div>
    </header>
    <main class="flex-1 max-w-6xl mx-auto px-4 py-8 w-full">
        {% block content %}{% endblock %}
    </main>
    <footer class="border-t border-stone-700 py-4 text-center text-stone-500 text-xs">
        Olivalle Admin
    </footer>
</body>
</html>
```

- [ ] **Step 2: Login-Template erstellen**

```html
{# templates/admin/login.html #}
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login — Olivalle Admin</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    colors: { accent: '#f1d600' },
                    fontFamily: {
                        display: ['"Amatic SC"', 'cursive'],
                        body: ['Lora', 'serif'],
                    },
                }
            }
        }
    </script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Amatic+SC:wght@400;700&family=Lora:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet">
</head>
<body class="bg-stone-800 text-white min-h-screen flex items-center justify-center font-body">
    <div class="bg-stone-700 rounded-lg p-8 shadow-md w-full max-w-sm">
        <h1 class="font-display text-4xl font-bold text-accent text-center mb-6">Olivalle Admin</h1>
        {% if error %}
        <div class="bg-red-600/20 text-red-400 rounded p-3 mb-4 text-sm">{{ error }}</div>
        {% endif %}
        <form method="post" action="/admin/login">
            <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
            <label for="password" class="block text-sm text-stone-300 mb-2">Passwort</label>
            <input type="password" id="password" name="password" required autofocus
                   class="w-full rounded bg-stone-600 border border-stone-500 px-3 py-2 text-white focus:outline-none focus:border-accent">
            <button type="submit"
                    class="w-full mt-4 bg-accent text-stone-900 font-bold py-2 rounded hover:bg-yellow-400 transition-colors">
                Anmelden
            </button>
        </form>
    </div>
</body>
</html>
```

- [ ] **Step 3: Dashboard-Template erstellen**

```html
{# templates/admin/dashboard.html #}
{% extends "admin/base.html" %}

{% block title %}Dashboard{% endblock %}

{% block content %}
<h1 class="font-display text-5xl font-bold text-accent mb-8">Dashboard</h1>

{# Kennzahlen #}
<div class="grid gap-6 sm:grid-cols-3 mb-8">
    <div class="bg-stone-700 rounded-lg p-6 shadow-md">
        <div class="font-display text-5xl font-bold text-accent">{{ stats.offene_bestellungen }}</div>
        <div class="text-stone-400 text-sm mt-1">Offene Bestellungen</div>
    </div>
    <div class="bg-stone-700 rounded-lg p-6 shadow-md">
        <div class="font-display text-5xl font-bold text-accent">CHF {{ "%.2f"|format(stats.umsatz_monat) }}</div>
        <div class="text-stone-400 text-sm mt-1">Umsatz diesen Monat</div>
    </div>
    <div class="bg-stone-700 rounded-lg p-6 shadow-md">
        <div class="font-display text-5xl font-bold text-accent">{{ stats.bestellungen_heute }}</div>
        <div class="text-stone-400 text-sm mt-1">Bestellungen heute</div>
    </div>
</div>

{# Filter #}
<form method="get" action="/admin/" class="flex flex-wrap gap-3 mb-6 items-end">
    <div>
        <label class="block text-xs text-stone-400 mb-1">Status</label>
        <select name="status" class="rounded bg-stone-700 border border-stone-600 px-3 py-2 text-sm text-white">
            <option value="">Alle</option>
            {% for s in alle_status %}
            <option value="{{ s }}" {% if s == filter_status %}selected{% endif %}>{{ s }}</option>
            {% endfor %}
        </select>
    </div>
    <div>
        <label class="block text-xs text-stone-400 mb-1">Von</label>
        <input type="date" name="datum_von" value="{{ filter_datum_von }}"
               class="rounded bg-stone-700 border border-stone-600 px-3 py-2 text-sm text-white">
    </div>
    <div>
        <label class="block text-xs text-stone-400 mb-1">Bis</label>
        <input type="date" name="datum_bis" value="{{ filter_datum_bis }}"
               class="rounded bg-stone-700 border border-stone-600 px-3 py-2 text-sm text-white">
    </div>
    <div>
        <label class="block text-xs text-stone-400 mb-1">Suche</label>
        <input type="text" name="suche" value="{{ filter_suche }}" placeholder="Name, Email, Nr."
               class="rounded bg-stone-700 border border-stone-600 px-3 py-2 text-sm text-white">
    </div>
    <button type="submit" class="bg-accent text-stone-900 font-bold px-4 py-2 rounded hover:bg-yellow-400 transition-colors text-sm">
        Filtern
    </button>
</form>

{# Bestelltabelle #}
<div class="bg-stone-700 rounded-lg shadow-md overflow-x-auto">
    <table class="w-full text-sm">
        <thead>
            <tr class="border-b border-stone-600 text-left text-stone-400">
                <th class="px-4 py-3">Nr.</th>
                <th class="px-4 py-3">Datum</th>
                <th class="px-4 py-3">Kunde</th>
                <th class="px-4 py-3">Status</th>
                <th class="px-4 py-3">Zahlung</th>
                <th class="px-4 py-3">Versand</th>
                <th class="px-4 py-3 text-right">Total</th>
            </tr>
        </thead>
        <tbody>
            {% for b in bestellungen %}
            <tr class="border-b border-stone-600/50 hover:bg-stone-600 cursor-pointer transition-colors"
                onclick="window.location='/admin/bestellungen/{{ b.id }}'">
                <td class="px-4 py-3 font-mono">#{{ b.id }}</td>
                <td class="px-4 py-3">{{ b.erstellt_am[:16] }}</td>
                <td class="px-4 py-3">{{ b.vorname }} {{ b.nachname }}</td>
                <td class="px-4 py-3">
                    {% if b.status in ['neu'] %}
                    <span class="bg-yellow-600/20 text-yellow-400 px-2 py-1 rounded text-xs">{{ b.status }}</span>
                    {% elif b.status in ['bezahlt'] %}
                    <span class="bg-green-600/20 text-green-400 px-2 py-1 rounded text-xs">{{ b.status }}</span>
                    {% elif b.status in ['in_bearbeitung', 'versendet', 'abholbereit'] %}
                    <span class="bg-blue-600/20 text-blue-400 px-2 py-1 rounded text-xs">{{ b.status }}</span>
                    {% elif b.status == 'storniert' %}
                    <span class="bg-red-600/20 text-red-400 px-2 py-1 rounded text-xs">{{ b.status }}</span>
                    {% else %}
                    <span class="bg-stone-600/20 text-stone-400 px-2 py-1 rounded text-xs">{{ b.status }}</span>
                    {% endif %}
                </td>
                <td class="px-4 py-3">{{ b.zahlungsart }}</td>
                <td class="px-4 py-3">{{ b.versandart }}</td>
                <td class="px-4 py-3 text-right font-mono">CHF {{ "%.2f"|format(b.total_chf) }}</td>
            </tr>
            {% else %}
            <tr><td colspan="7" class="px-4 py-8 text-center text-stone-400">Keine Bestellungen gefunden.</td></tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}
```

- [ ] **Step 4: Bestelldetail-Template erstellen**

```html
{# templates/admin/bestellung_detail.html #}
{% extends "admin/base.html" %}

{% block title %}Bestellung #{{ bestellung.id }}{% endblock %}

{% block content %}
<a href="/admin/" class="text-stone-400 hover:text-accent text-sm transition-colors">&larr; Zurück zum Dashboard</a>

<h1 class="font-display text-5xl font-bold text-accent mt-4 mb-8">Bestellung #{{ bestellung.id }}</h1>

<div class="grid gap-6 lg:grid-cols-2">
    {# Linke Spalte: Kunde + Positionen #}
    <div class="space-y-6">
        {# Kundendaten #}
        <div class="bg-stone-700 rounded-lg p-6 shadow-md">
            <h2 class="font-display text-2xl font-bold text-accent mb-4">Kunde</h2>
            <div class="text-sm space-y-1">
                <div>{{ bestellung.vorname }} {{ bestellung.nachname }}</div>
                <div>{{ bestellung.strasse }}</div>
                <div>{{ bestellung.plz }} {{ bestellung.ort }}</div>
                <div class="mt-2">
                    <a href="mailto:{{ bestellung.email }}" class="text-accent hover:underline">{{ bestellung.email }}</a>
                </div>
                {% if bestellung.telefon %}
                <div>{{ bestellung.telefon }}</div>
                {% endif %}
            </div>
        </div>

        {# Positionen #}
        <div class="bg-stone-700 rounded-lg p-6 shadow-md">
            <h2 class="font-display text-2xl font-bold text-accent mb-4">Positionen</h2>
            <table class="w-full text-sm">
                <thead>
                    <tr class="border-b border-stone-600 text-stone-400">
                        <th class="text-left pb-2">Produkt</th>
                        <th class="text-right pb-2">Menge</th>
                        <th class="text-right pb-2">Preis</th>
                        <th class="text-right pb-2">Summe</th>
                    </tr>
                </thead>
                <tbody>
                    {% for pos in bestellung.positionen %}
                    <tr class="border-b border-stone-600/50">
                        <td class="py-2">{{ pos.name }}</td>
                        <td class="py-2 text-right">{{ pos.menge }}</td>
                        <td class="py-2 text-right font-mono">CHF {{ "%.2f"|format(pos.einzelpreis_chf) }}</td>
                        <td class="py-2 text-right font-mono">CHF {{ "%.2f"|format(pos.menge * pos.einzelpreis_chf) }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
                <tfoot>
                    <tr class="border-b border-stone-600/50 text-stone-400">
                        <td colspan="3" class="py-2">Versand ({{ bestellung.versandart }})</td>
                        <td class="py-2 text-right font-mono">CHF {{ "%.2f"|format(bestellung.versandkosten_chf) }}</td>
                    </tr>
                    <tr class="font-bold">
                        <td colspan="3" class="py-2">Total</td>
                        <td class="py-2 text-right font-mono text-accent">CHF {{ "%.2f"|format(bestellung.total_chf) }}</td>
                    </tr>
                </tfoot>
            </table>
            <div class="mt-3 text-sm text-stone-400">
                Zahlungsart: {{ bestellung.zahlungsart }} · Erstellt: {{ bestellung.erstellt_am[:16] }}
            </div>
            {% if bestellung.kommentar %}
            <div class="mt-3 text-sm">
                <span class="text-stone-400">Kommentar:</span> {{ bestellung.kommentar }}
            </div>
            {% endif %}
        </div>
    </div>

    {# Rechte Spalte: Status + Log #}
    <div class="space-y-6">
        {# Status ändern #}
        <div class="bg-stone-700 rounded-lg p-6 shadow-md">
            <h2 class="font-display text-2xl font-bold text-accent mb-4">Status</h2>
            <form method="post" action="/admin/bestellungen/{{ bestellung.id }}/status" class="flex gap-3">
                <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
                <select name="neuer_status" class="flex-1 rounded bg-stone-600 border border-stone-500 px-3 py-2 text-sm text-white">
                    {% for s in alle_status %}
                    <option value="{{ s }}" {% if s == bestellung.status %}selected{% endif %}>{{ s }}</option>
                    {% endfor %}
                </select>
                <button type="submit"
                        class="bg-accent text-stone-900 font-bold px-4 py-2 rounded hover:bg-yellow-400 transition-colors text-sm">
                    Ändern
                </button>
            </form>
        </div>

        {# Notiz hinzufügen #}
        <div class="bg-stone-700 rounded-lg p-6 shadow-md">
            <h2 class="font-display text-2xl font-bold text-accent mb-4">Notiz hinzufügen</h2>
            <form method="post" action="/admin/bestellungen/{{ bestellung.id }}/notiz">
                <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
                <div class="mb-3">
                    <select name="typ" class="w-full rounded bg-stone-600 border border-stone-500 px-3 py-2 text-sm text-white">
                        <option value="notiz_hinzugefuegt">Notiz</option>
                        <option value="email_eingang">Email-Eingang</option>
                    </select>
                </div>
                <textarea name="text" rows="3" required placeholder="Notiz eingeben..."
                          class="w-full rounded bg-stone-600 border border-stone-500 px-3 py-2 text-sm text-white resize-y"></textarea>
                <button type="submit"
                        class="mt-2 bg-accent text-stone-900 font-bold px-4 py-2 rounded hover:bg-yellow-400 transition-colors text-sm">
                    Speichern
                </button>
            </form>
        </div>

        {# Log #}
        <div class="bg-stone-700 rounded-lg p-6 shadow-md">
            <h2 class="font-display text-2xl font-bold text-accent mb-4">Verlauf</h2>
            {% if logs %}
            <div class="space-y-3">
                {% for log in logs %}
                <div class="border-l-2 border-stone-600 pl-4 py-2">
                    <div class="flex items-center gap-2 text-xs text-stone-400">
                        <span>{{ log.zeitpunkt[:16] }}</span>
                        <span class="bg-stone-600 rounded px-1.5 py-0.5">{{ log.admin_label }}</span>
                        <span>{{ log.aktion }}</span>
                    </div>
                    {% if log.details %}
                    <div class="text-sm mt-1">{{ log.details }}</div>
                    {% endif %}
                </div>
                {% endfor %}
            </div>
            {% else %}
            <p class="text-stone-400 text-sm">Noch keine Einträge.</p>
            {% endif %}
        </div>
    </div>
</div>
{% endblock %}
```

- [ ] **Step 5: Commit**

```bash
git add templates/admin/
git commit -m "feat(admin): Templates für Login, Dashboard, Bestelldetail"
```

---

## Task 5: Admin-Router

**Files:**
- Create: `app/routers/admin.py`
- Modify: `app/main.py:22-28`
- Create: `tests/test_api_admin.py`

- [ ] **Step 1: Test-Datei erstellen — Login und Auth**

```python
# tests/test_api_admin.py
import bcrypt
import pytest
from fastapi.testclient import TestClient


def _make_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


@pytest.fixture()
def admin_client(tmp_path, monkeypatch):
    pw_hash = _make_hash("testpass")
    monkeypatch.setattr("app.config.settings.database_path", str(tmp_path / "test.db"))
    monkeypatch.setattr("app.config.settings.admin_credentials", f"dev:{pw_hash}")
    from app.database import init_db
    init_db()
    from app.main import app
    return TestClient(app)


class TestAdminLogin:
    def test_login_page_renders(self, admin_client):
        resp = admin_client.get("/admin/login")
        assert resp.status_code == 200
        assert "Passwort" in resp.text

    def test_login_success_redirects_to_dashboard(self, admin_client):
        resp = admin_client.post(
            "/admin/login",
            data={"password": "testpass", "csrf_token": ""},
            follow_redirects=False,
        )
        assert resp.status_code == 303
        assert resp.headers["location"] == "/admin/"
        assert "admin_session" in resp.cookies

    def test_login_wrong_password(self, admin_client):
        resp = admin_client.post(
            "/admin/login",
            data={"password": "falsch", "csrf_token": ""},
        )
        assert resp.status_code == 200
        assert "Falsches Passwort" in resp.text or "Ungültig" in resp.text

    def test_dashboard_requires_login(self, admin_client):
        resp = admin_client.get("/admin/", follow_redirects=False)
        assert resp.status_code == 303
        assert "/admin/login" in resp.headers["location"]


class TestAdminDashboard:
    def _login(self, client):
        resp = client.post(
            "/admin/login",
            data={"password": "testpass", "csrf_token": ""},
            follow_redirects=False,
        )
        return resp.cookies

    def test_dashboard_renders(self, admin_client):
        cookies = self._login(admin_client)
        admin_client.cookies = cookies
        resp = admin_client.get("/admin/")
        assert resp.status_code == 200
        assert "Dashboard" in resp.text

    def test_logout_clears_session(self, admin_client):
        cookies = self._login(admin_client)
        admin_client.cookies = cookies
        resp = admin_client.post(
            "/admin/logout",
            data={"csrf_token": ""},
            follow_redirects=False,
        )
        assert resp.status_code == 303
        admin_client.cookies = resp.cookies
        resp2 = admin_client.get("/admin/", follow_redirects=False)
        assert resp2.status_code == 303
```

- [ ] **Step 2: Tests ausführen — müssen fehlschlagen**

Run: `cd /Users/KN/Dropbox/Privat/CAS/projekte/olivalle && python -m pytest tests/test_api_admin.py -v`
Expected: FAIL (Routen existieren noch nicht)

- [ ] **Step 3: Admin-Router implementieren**

```python
# app/routers/admin.py
import json

from fastapi import APIRouter, Cookie, Form, Request
from fastapi.responses import RedirectResponse, Response

from app.config import settings
from app.csrf import generiere_csrf_token, validiere_csrf_token
from app.database import get_db
from app.repositories.admin_repo import (
    get_bestellung_detail,
    get_bestellungen_liste,
    get_dashboard_stats,
    get_log_fuer_bestellung,
    log_eintrag_schreiben,
    update_bestellung_status,
)
from app.services.auth_service import (
    create_session,
    login_guard,
    parse_credentials,
    validate_session,
    verify_password,
)
from app.templating import templates

router = APIRouter(prefix="/admin")

ALLE_STATUS = [
    "neu", "bezahlt", "in_bearbeitung",
    "versendet", "abholbereit", "abgeschlossen", "storniert",
]


def _get_admin_label(admin_session: str | None) -> str | None:
    """Validate session cookie and return admin label or None."""
    if not admin_session:
        return None
    return validate_session(
        admin_session,
        secret=settings.secret_key,
        max_age=settings.admin_session_max_age,
    )


def _require_login(admin_session: str | None) -> str:
    """Return admin_label or raise redirect to login."""
    label = _get_admin_label(admin_session)
    if not label:
        raise _redirect_login()
    return label


def _redirect_login():
    """Return a redirect exception-like object. Used via raise pattern."""
    from fastapi import HTTPException
    # We use a workaround: return RedirectResponse from route handlers
    # This helper is called differently — see route handlers
    return RedirectResponse("/admin/login", status_code=303)


# --- Routes ---


@router.get("/login")
def admin_login_page(request: Request):
    csrf_token = generiere_csrf_token(settings.secret_key)
    return templates.TemplateResponse(
        request, "admin/login.html", {"csrf_token": csrf_token}
    )


@router.post("/login")
def admin_login(
    request: Request,
    password: str = Form(),
    csrf_token: str = Form(""),
):
    client_ip = request.client.host if request.client else "unknown"

    if login_guard.is_locked(client_ip):
        csrf = generiere_csrf_token(settings.secret_key)
        return templates.TemplateResponse(
            request, "admin/login.html",
            {"csrf_token": csrf, "error": "Zu viele Fehlversuche. Bitte warten."},
        )

    credentials = parse_credentials(settings.admin_credentials)
    label = verify_password(password, credentials)

    conn = get_db()
    try:
        if not label:
            login_guard.record_failure(client_ip)
            log_eintrag_schreiben(
                conn, admin_label="?", aktion="login_fehlgeschlagen", details=client_ip
            )
            csrf = generiere_csrf_token(settings.secret_key)
            return templates.TemplateResponse(
                request, "admin/login.html",
                {"csrf_token": csrf, "error": "Ungültiges Passwort."},
            )

        login_guard.reset(client_ip)
        log_eintrag_schreiben(
            conn, admin_label=label, aktion="login", details=client_ip
        )
    finally:
        conn.close()

    token = create_session(label, secret=settings.secret_key)
    response = RedirectResponse("/admin/", status_code=303)
    response.set_cookie(
        "admin_session",
        token,
        httponly=True,
        samesite="strict",
        max_age=settings.admin_session_max_age,
    )
    return response


@router.post("/logout")
def admin_logout(
    request: Request,
    admin_session: str | None = Cookie(None),
    csrf_token: str = Form(""),
):
    label = _get_admin_label(admin_session) or "?"
    conn = get_db()
    try:
        log_eintrag_schreiben(conn, admin_label=label, aktion="logout")
    finally:
        conn.close()

    response = RedirectResponse("/admin/login", status_code=303)
    response.delete_cookie("admin_session")
    return response


@router.get("/")
def admin_dashboard(
    request: Request,
    admin_session: str | None = Cookie(None),
    status: str = "",
    suche: str = "",
    datum_von: str = "",
    datum_bis: str = "",
):
    label = _get_admin_label(admin_session)
    if not label:
        return RedirectResponse("/admin/login", status_code=303)

    conn = get_db()
    try:
        stats = get_dashboard_stats(conn)
        bestellungen = get_bestellungen_liste(
            conn, status=status, suche=suche,
            datum_von=datum_von, datum_bis=datum_bis,
        )
    finally:
        conn.close()

    csrf = generiere_csrf_token(settings.secret_key)
    return templates.TemplateResponse(
        request, "admin/dashboard.html",
        {
            "admin_label": label,
            "csrf_token": csrf,
            "stats": stats,
            "bestellungen": bestellungen,
            "alle_status": ALLE_STATUS,
            "filter_status": status,
            "filter_suche": suche,
            "filter_datum_von": datum_von,
            "filter_datum_bis": datum_bis,
        },
    )


@router.get("/bestellungen/{bestellung_id}")
def admin_bestellung_detail(
    request: Request,
    bestellung_id: int,
    admin_session: str | None = Cookie(None),
):
    label = _get_admin_label(admin_session)
    if not label:
        return RedirectResponse("/admin/login", status_code=303)

    conn = get_db()
    try:
        bestellung = get_bestellung_detail(conn, bestellung_id)
        if not bestellung:
            from fastapi import HTTPException
            raise HTTPException(404, "Bestellung nicht gefunden")
        logs = get_log_fuer_bestellung(conn, bestellung_id)
    finally:
        conn.close()

    csrf = generiere_csrf_token(settings.secret_key)
    return templates.TemplateResponse(
        request, "admin/bestellung_detail.html",
        {
            "admin_label": label,
            "csrf_token": csrf,
            "bestellung": bestellung,
            "logs": logs,
            "alle_status": ALLE_STATUS,
        },
    )


@router.post("/bestellungen/{bestellung_id}/status")
def admin_status_aendern(
    request: Request,
    bestellung_id: int,
    neuer_status: str = Form(),
    csrf_token: str = Form(""),
    admin_session: str | None = Cookie(None),
):
    label = _get_admin_label(admin_session)
    if not label:
        return RedirectResponse("/admin/login", status_code=303)

    conn = get_db()
    try:
        bestellung = get_bestellung_detail(conn, bestellung_id)
        if not bestellung:
            from fastapi import HTTPException
            raise HTTPException(404, "Bestellung nicht gefunden")

        alter_status = bestellung["status"]
        if alter_status != neuer_status:
            update_bestellung_status(conn, bestellung_id=bestellung_id, neuer_status=neuer_status)
            log_eintrag_schreiben(
                conn,
                admin_label=label,
                aktion="status_geaendert",
                details=json.dumps({"von": alter_status, "nach": neuer_status}),
                bestellung_id=bestellung_id,
            )
    finally:
        conn.close()

    return RedirectResponse(f"/admin/bestellungen/{bestellung_id}", status_code=303)


@router.post("/bestellungen/{bestellung_id}/notiz")
def admin_notiz_hinzufuegen(
    request: Request,
    bestellung_id: int,
    typ: str = Form(),
    text: str = Form(),
    csrf_token: str = Form(""),
    admin_session: str | None = Cookie(None),
):
    label = _get_admin_label(admin_session)
    if not label:
        return RedirectResponse("/admin/login", status_code=303)

    conn = get_db()
    try:
        log_eintrag_schreiben(
            conn,
            admin_label=label,
            aktion=typ,
            details=text,
            bestellung_id=bestellung_id,
        )
    finally:
        conn.close()

    return RedirectResponse(f"/admin/bestellungen/{bestellung_id}", status_code=303)
```

- [ ] **Step 4: Router in main.py einbinden**

In `app/main.py`, nach den bestehenden Imports (Zeile 22) und Router-Einbindungen:

```python
from app.routers import admin, bestellungen, produkte, seiten, warenkorb, webhooks

app.include_router(admin.router)
app.include_router(produkte.router)
# ... rest bleibt gleich
```

- [ ] **Step 5: Tests ausführen**

Run: `cd /Users/KN/Dropbox/Privat/CAS/projekte/olivalle && python -m pytest tests/test_api_admin.py -v`
Expected: 6 PASSED

- [ ] **Step 6: Alle Tests ausführen (Regression)**

Run: `cd /Users/KN/Dropbox/Privat/CAS/projekte/olivalle && python -m pytest -v`
Expected: Alle bestehenden + neuen Tests bestehen

- [ ] **Step 7: Commit**

```bash
git add app/routers/admin.py app/main.py tests/test_api_admin.py
git commit -m "feat(admin): Router mit Login, Dashboard, Bestelldetail, Statusänderung"
```

---

## Task 6: Email-Logging und Webhook-Logging

**Files:**
- Modify: `app/services/email_service.py:14-46`
- Modify: `app/routers/webhooks.py:22-58`

- [ ] **Step 1: Test schreiben — Email-Logging**

```python
# In tests/test_api_admin.py, neue Klasse am Ende:


class TestEmailLogging:
    def test_email_service_logs_ausgang(self, db, monkeypatch):
        """After sending an email, an email_ausgang log entry should exist."""
        # Mock resend to avoid actual API calls
        monkeypatch.setattr("app.services.email_service.resend.Emails.send", lambda **kw: {"id": "mock"})

        from app.services.email_service import sende_bestellbestaetigung

        # Create test order for FK
        db.execute(
            "INSERT INTO kunden (vorname, nachname, email, strasse, plz, ort) "
            "VALUES ('Max', 'Muster', 'max@test.ch', 'Str 1', '4600', 'Olten')"
        )
        db.execute(
            "INSERT INTO bestellungen (kunde_id, zahlungsart, versandart, total_chf) "
            "VALUES (1, 'stripe', 'versand', 50.00)"
        )
        db.commit()

        sende_bestellbestaetigung(
            empfaenger="max@test.ch",
            bestell_id=1,
            kunde={"vorname": "Max", "nachname": "Muster"},
            positionen=[{"name": "Öl 250ml", "menge": 2, "einzelpreis_chf": 8.0}],
            versandkosten=9.90,
            total=25.90,
            conn=db,
        )

        log = db.execute(
            "SELECT * FROM admin_log WHERE aktion = 'email_ausgang'"
        ).fetchone()
        assert log is not None
        assert "max@test.ch" in log["details"]
```

- [ ] **Step 2: Test ausführen — muss fehlschlagen**

Run: `cd /Users/KN/Dropbox/Privat/CAS/projekte/olivalle && python -m pytest tests/test_api_admin.py::TestEmailLogging -v`
Expected: FAIL (email_service hat keinen conn-Parameter)

- [ ] **Step 3: email_service.py erweitern**

In `app/services/email_service.py` den `conn`-Parameter optional hinzufügen und nach Versand loggen:

```python
# app/services/email_service.py
import sqlite3
from pathlib import Path

import resend
from jinja2 import Environment, FileSystemLoader

from app.config import settings

resend.api_key = settings.resend_api_key

TEMPLATE_DIR = Path(__file__).resolve().parent.parent.parent / "templates" / "emails"
env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))


def sende_bestellbestaetigung(
    empfaenger: str,
    bestell_id: int,
    kunde: dict,
    positionen: list[dict],
    versandkosten: float,
    total: float,
    anhang: bytes | None = None,
    conn: sqlite3.Connection | None = None,
) -> dict:
    template = env.get_template("bestellbestaetigung.html")
    html = template.render(
        kunde=kunde,
        bestell_id=bestell_id,
        positionen=positionen,
        versandkosten=versandkosten,
        total=total,
    )

    betreff = f"Olivalle — Bestellbestätigung #{bestell_id}"

    params = {
        "from": "Olivalle <bestellung@olivalle.ch>",
        "to": [empfaenger],
        "reply_to": "olivalle.olten@outlook.com",
        "subject": betreff,
        "html": html,
    }

    if anhang:
        params["attachments"] = [{
            "filename": f"rechnung-{bestell_id}.svg",
            "content": list(anhang),
        }]

    result = resend.Emails.send(**params)

    # Log email_ausgang if connection provided
    if conn:
        from app.repositories.admin_repo import log_eintrag_schreiben
        log_eintrag_schreiben(
            conn,
            admin_label="system",
            aktion="email_ausgang",
            details=f"An: {empfaenger} — {betreff}",
            bestellung_id=bestell_id,
        )

    return result
```

- [ ] **Step 4: Test ausführen — muss bestehen**

Run: `cd /Users/KN/Dropbox/Privat/CAS/projekte/olivalle && python -m pytest tests/test_api_admin.py::TestEmailLogging -v`
Expected: PASS

- [ ] **Step 5: webhooks.py erweitern — conn an email_service weitergeben + Status-Log**

In `app/routers/webhooks.py`, den Webhook-Handler so anpassen, dass `conn` an den Email-Service und ein Log-Eintrag für die Statusänderung geschrieben wird:

```python
# app/routers/webhooks.py
import stripe
from fastapi import APIRouter, HTTPException, Request

from app.config import settings
from app.database import get_db

router = APIRouter()


@router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig, settings.stripe_webhook_secret
        )
    except (ValueError, stripe.SignatureVerificationError) as err:
        raise HTTPException(400, "Ungültige Webhook-Signatur") from err

    if event.type == "checkout.session.completed":
        session = event.data.object
        conn = get_db()
        try:
            conn.execute(
                "UPDATE bestellungen SET status = 'bezahlt' "
                "WHERE stripe_session_id = ?",
                (session.id,),
            )
            conn.commit()

            bestellung = conn.execute(
                "SELECT b.*, k.vorname, k.nachname, k.email "
                "FROM bestellungen b JOIN kunden k ON b.kunde_id = k.id "
                "WHERE b.stripe_session_id = ?",
                (session.id,),
            ).fetchone()
            if bestellung:
                best = dict(bestellung)

                # Log status change
                from app.repositories.admin_repo import log_eintrag_schreiben
                log_eintrag_schreiben(
                    conn,
                    admin_label="system",
                    aktion="status_geaendert",
                    details='{"von": "neu", "nach": "bezahlt"}',
                    bestellung_id=best["id"],
                )

                positionen = conn.execute(
                    "SELECT bp.*, p.name FROM bestellpositionen bp "
                    "JOIN produkte p ON bp.produkt_id = p.id "
                    "WHERE bp.bestellung_id = ?",
                    (best["id"],),
                ).fetchall()
                from app.services.email_service import sende_bestellbestaetigung
                sende_bestellbestaetigung(
                    empfaenger=best["email"],
                    bestell_id=best["id"],
                    kunde={"vorname": best["vorname"], "nachname": best["nachname"]},
                    positionen=[dict(p) for p in positionen],
                    versandkosten=best["versandkosten_chf"],
                    total=best["total_chf"],
                    conn=conn,
                )
        finally:
            conn.close()

    return {"status": "ok"}
```

- [ ] **Step 6: bestellungen.py — conn an email_service weitergeben**

In `app/routers/bestellungen.py`, Zeile 116 den `sende_bestellbestaetigung`-Aufruf um `conn=conn` erweitern:

```python
            sende_bestellbestaetigung(
                empfaenger=kunde_input.email,
                bestell_id=bestell_id,
                kunde={
                    "vorname": kunde_input.vorname,
                    "nachname": kunde_input.nachname,
                },
                positionen=positionen,
                versandkosten=versandkosten,
                total=gesamt,
                anhang=qr_pdf,
                conn=conn,
            )
```

- [ ] **Step 7: Alle Tests ausführen (Regression)**

Run: `cd /Users/KN/Dropbox/Privat/CAS/projekte/olivalle && python -m pytest -v`
Expected: Alle Tests bestehen

- [ ] **Step 8: Commit**

```bash
git add app/services/email_service.py app/routers/webhooks.py app/routers/bestellungen.py tests/test_api_admin.py
git commit -m "feat(admin): Email-Ausgang und Statusänderungen automatisch loggen"
```

---

## Task 7: Ruff-Check und finaler Regressiontest

**Files:** Keine neuen Dateien

- [ ] **Step 1: Ruff laufen lassen**

Run: `cd /Users/KN/Dropbox/Privat/CAS/projekte/olivalle && python -m ruff check app/ tests/`
Expected: Keine Fehler. Falls Fehler: beheben.

- [ ] **Step 2: Ruff Format-Check**

Run: `cd /Users/KN/Dropbox/Privat/CAS/projekte/olivalle && python -m ruff format --check app/ tests/`
Expected: Alle Dateien korrekt formatiert. Falls nicht: `ruff format app/ tests/` ausführen.

- [ ] **Step 3: Komplette Testsuite**

Run: `cd /Users/KN/Dropbox/Privat/CAS/projekte/olivalle && python -m pytest -v`
Expected: Alle Tests bestehen

- [ ] **Step 4: Manueller Smoke-Test**

Run: `cd /Users/KN/Dropbox/Privat/CAS/projekte/olivalle && python -c "
import bcrypt
pw = bcrypt.hashpw(b'admin123', bcrypt.gensalt()).decode()
print(f'ADMIN_CREDENTIALS=dev:{pw}')
"`

Diesen Wert in `.env` eintragen, dann:

Run: `cd /Users/KN/Dropbox/Privat/CAS/projekte/olivalle && uvicorn app.main:app --reload`

Im Browser:
1. `http://localhost:8000/admin/` → Redirect auf Login
2. Login mit `admin123` → Dashboard
3. Falls Bestellungen existieren: Klick auf eine → Detailansicht
4. Status ändern → Verlauf prüfen

- [ ] **Step 5: Commit (falls Ruff-Fixes)**

```bash
git add -u
git commit -m "fix(admin): Ruff-Fixes und Formatierung"
```
