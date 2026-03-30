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
        "SELECT COUNT(*) as c FROM bestellungen WHERE date(erstellt_am) = date('now')"
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

    query += " ORDER BY b.erstellt_am DESC, b.id DESC"

    return [dict(row) for row in conn.execute(query, params).fetchall()]


def get_bestellung_detail(conn: sqlite3.Connection, bestellung_id: int) -> dict | None:
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


def get_log_fuer_bestellung(conn: sqlite3.Connection, bestellung_id: int) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM admin_log WHERE bestellung_id = ? ORDER BY zeitpunkt DESC",
        (bestellung_id,),
    ).fetchall()
    return [dict(r) for r in rows]
