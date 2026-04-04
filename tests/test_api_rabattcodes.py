

def test_rabattcode_pruefen_gueltig(client):
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
    response = client.post(
        "/api/rabattcode/pruefen",
        json={"code": "GIBTSNICHT", "email": "test@example.com", "subtotal": 26.00},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["gueltig"] is False
    assert "fehler" in data


def test_bestellung_mit_rabattcode(client, csrf_token):
    from app.database import get_db

    conn = get_db()
    conn.execute(
        "INSERT INTO rabattcodes (code, rabattart, rabattwert, gueltig_von, gueltig_bis) "
        "VALUES ('WILLKOMMEN', 'fixbetrag', 5.0, '2026-01-01', '2026-12-31')"
    )
    conn.commit()
    conn.close()

    import json

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
    assert response.status_code in (200, 303)

    conn = get_db()
    row = conn.execute(
        "SELECT rabattbetrag_chf, total_chf FROM bestellungen WHERE id = 1"
    ).fetchone()
    conn.close()
    assert row["rabattbetrag_chf"] == 5.00
    assert row["total_chf"] == 11.00  # 16 - 5 + 0 Versand


def test_bestellung_ohne_rabattcode(client, csrf_token):
    import json

    from app.database import get_db

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
    row = conn.execute(
        "SELECT rabattbetrag_chf, total_chf FROM bestellungen WHERE id = 1"
    ).fetchone()
    conn.close()
    assert row["rabattbetrag_chf"] == 0
    assert row["total_chf"] == 8.00
