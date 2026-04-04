

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
