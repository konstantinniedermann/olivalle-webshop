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
