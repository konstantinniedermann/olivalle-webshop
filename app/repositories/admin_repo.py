import sqlite3
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

ZURICH_TZ = ZoneInfo("Europe/Zurich")
_UTC = ZoneInfo("UTC")


def _to_utc_str(dt: datetime) -> str:
    """TZ-aware datetime → SQLite-kompatibles UTC-String-Format."""
    return dt.astimezone(_UTC).strftime("%Y-%m-%d %H:%M:%S")


def _next_month_start(dt: datetime) -> datetime:
    if dt.month == 12:
        return dt.replace(year=dt.year + 1, month=1)
    return dt.replace(month=dt.month + 1)


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


def get_dashboard_stats(conn: sqlite3.Connection) -> dict:
    # erstellt_am wird als UTC gespeichert (SQLite datetime('now')).
    # Für "heute" und "aktueller Monat" in Europe/Zurich rechnen wir
    # die lokalen Grenzen in Python aus und vergleichen als UTC-Strings.
    now_zh = datetime.now(tz=ZURICH_TZ)
    today_start_zh = now_zh.replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow_start_zh = today_start_zh + timedelta(days=1)
    month_start_zh = today_start_zh.replace(day=1)
    next_month_start_zh = _next_month_start(month_start_zh)

    offene = conn.execute(
        "SELECT COUNT(*) as c FROM bestellungen WHERE status IN ('neu', 'bezahlt')"
    ).fetchone()["c"]

    umsatz = conn.execute(
        "SELECT COALESCE(SUM(total_chf), 0) as s FROM bestellungen "
        "WHERE status != 'storniert' "
        "AND erstellt_am >= ? AND erstellt_am < ?",
        (_to_utc_str(month_start_zh), _to_utc_str(next_month_start_zh)),
    ).fetchone()["s"]

    heute = conn.execute(
        "SELECT COUNT(*) as c FROM bestellungen "
        "WHERE erstellt_am >= ? AND erstellt_am < ?",
        (_to_utc_str(today_start_zh), _to_utc_str(tomorrow_start_zh)),
    ).fetchone()["c"]

    return {
        "offene_bestellungen": offene,
        "umsatz_monat": umsatz,
        "bestellungen_heute": heute,
    }


# Hartes Cap für die Admin-Bestellliste (#170): schützt Speicher/Rendering
# vor unbegrenztem fetchall() bei wachsender Historie. Ältere Bestellungen
# bleiben über die Suche erreichbar (Filter greift vor dem Cap).
ADMIN_LISTE_LIMIT = 200


def get_bestellungen_liste(
    conn: sqlite3.Connection,
    *,
    status: str = "",
    suche: str = "",
    datum_von: str = "",
    datum_bis: str = "",
    limit: int = ADMIN_LISTE_LIMIT,
) -> tuple[list[dict], bool]:
    """Gefilterte Bestellliste, neueste zuerst, auf ``limit`` gedeckelt.

    Returns ``(zeilen, abgeschnitten)`` — ``abgeschnitten`` ist True, wenn
    mehr als ``limit`` Treffer existieren (präzise via fetch ``limit + 1``).
    """
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
        # Zurich-Datum → UTC-Startzeitpunkt
        dv = datetime.strptime(datum_von, "%Y-%m-%d").replace(tzinfo=ZURICH_TZ)
        query += " AND b.erstellt_am >= ?"
        params.append(_to_utc_str(dv))
    if datum_bis:
        # Zurich-Datum (inklusiv) → UTC-Startzeitpunkt des Folgetages
        db_end = datetime.strptime(datum_bis, "%Y-%m-%d").replace(
            tzinfo=ZURICH_TZ
        ) + timedelta(days=1)
        query += " AND b.erstellt_am < ?"
        params.append(_to_utc_str(db_end))

    query += " ORDER BY b.erstellt_am DESC, b.id DESC"

    # Ein Datumsfilter grenzt die Ergebnismenge natürlich ein (Buchhaltung /
    # Export) — dort greift der Cap NICHT, damit im gewählten Zeitraum keine
    # Bestellungen unsichtbar werden. Nur beim ungefilterten Blättern (oder
    # einer breiten Suche) schützt der Cap vor unbegrenztem fetchall (#170).
    if datum_von or datum_bis:
        rows = [dict(row) for row in conn.execute(query, params).fetchall()]
        return rows, False

    params.append(limit + 1)
    rows = [dict(row) for row in conn.execute(query + " LIMIT ?", params).fetchall()]
    abgeschnitten = len(rows) > limit
    return rows[:limit], abgeschnitten


def get_bestellung_detail(conn: sqlite3.Connection, bestellung_id: int) -> dict | None:
    row = conn.execute(
        "SELECT b.*, k.vorname, k.nachname, k.email, k.telefon, "
        "k.strasse, k.hausnummer, k.plz, k.ort "
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


def get_log_fuer_bestellung(conn: sqlite3.Connection, bestellung_id: int) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM admin_log WHERE bestellung_id = ? ORDER BY zeitpunkt DESC",
        (bestellung_id,),
    ).fetchall()
    return [dict(r) for r in rows]
