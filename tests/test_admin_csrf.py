"""Tests: Admin-POST-Endpoints lehnen Requests ohne/ungültiges CSRF-Token ab."""

import pytest


@pytest.fixture()
def order_id(admin_client):
    """Erstellt eine Bestellung direkt in der DB und gibt die ID zurück."""
    from app.database import get_db

    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO kunden"
            " (id, vorname, nachname, email, strasse, plz, ort)"
            " VALUES"
            " (1, 'Test', 'Kunde', 'test@example.ch', 'Teststr 1', '3000', 'Bern')"
        )
        conn.execute(
            "INSERT INTO bestellungen"
            " (id, kunde_id, zahlungsart, versandart, total_chf, status)"
            " VALUES (1, 1, 'stripe', 'versand', 50.00, 'neu')"
        )
        conn.commit()
    finally:
        conn.close()
    return 1


@pytest.mark.parametrize(
    "path,data",
    [
        ("/admin/login", {"password": "testpass"}),
        ("/admin/logout", {}),
    ],
)
def test_admin_post_ohne_csrf_token_403(admin_client, path, data):
    resp = admin_client.post(path, data=data)
    assert resp.status_code == 403


@pytest.mark.parametrize(
    "path,data",
    [
        ("/admin/login", {"password": "testpass", "csrf_token": "garbage"}),
        ("/admin/logout", {"csrf_token": "garbage"}),
    ],
)
def test_admin_post_ungueltiges_csrf_token_403(admin_client, path, data):
    resp = admin_client.post(path, data=data)
    assert resp.status_code == 403


def test_status_endpoint_ohne_csrf_403(admin_client, order_id):
    resp = admin_client.post(
        f"/admin/bestellungen/{order_id}/status",
        data={"neuer_status": "bezahlt"},
    )
    assert resp.status_code == 403


def test_status_endpoint_ungueltiges_csrf_403(admin_client, order_id):
    resp = admin_client.post(
        f"/admin/bestellungen/{order_id}/status",
        data={"neuer_status": "bezahlt", "csrf_token": "garbage"},
    )
    assert resp.status_code == 403


def test_notiz_endpoint_ohne_csrf_403(admin_client, order_id):
    resp = admin_client.post(
        f"/admin/bestellungen/{order_id}/notiz",
        data={"typ": "notiz_hinzugefuegt", "text": "x"},
    )
    assert resp.status_code == 403


def test_notiz_endpoint_ungueltiges_csrf_403(admin_client, order_id):
    resp = admin_client.post(
        f"/admin/bestellungen/{order_id}/notiz",
        data={"typ": "notiz_hinzugefuegt", "text": "x", "csrf_token": "garbage"},
    )
    assert resp.status_code == 403
