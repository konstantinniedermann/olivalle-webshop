"""Tests für Bezahlung bei Abholung und Stakeholder-Benachrichtigung."""

from unittest.mock import MagicMock, patch

import bcrypt
import pytest
from fastapi.testclient import TestClient

from app.services.email_service import sende_stakeholder_benachrichtigung


def _make_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


@pytest.fixture()
def client(tmp_path, monkeypatch):
    pw_hash = _make_hash("testpass")
    monkeypatch.setattr("app.config.settings.database_path", str(tmp_path / "test.db"))
    monkeypatch.setattr("app.config.settings.admin_credentials", f"dev:{pw_hash}")
    from app.database import init_db

    init_db()
    from app.main import app

    return TestClient(app)


@patch("app.services.email_service.brevo_client")
def test_stakeholder_mail_wird_gesendet(mock_client):
    """Stakeholder-Mail enthält Bestelldaten und wird an SH-Adresse geschickt."""
    mock_client.transactional_emails.send_transac_email.return_value = MagicMock(
        message_id="sh_1"
    )
    sende_stakeholder_benachrichtigung(
        bestell_id=42,
        kunde={"vorname": "Anna", "nachname": "Test", "email": "anna@test.ch"},
        positionen=[{"name": "Olivenöl 750ml", "menge": 2, "einzelpreis_chf": 18.0}],
        versandkosten=0.0,
        total=36.0,
        zahlungsart="abholung_bar",
        versandart="abholung",
    )
    mock_client.transactional_emails.send_transac_email.assert_called_once()
    call_kwargs = mock_client.transactional_emails.send_transac_email.call_args.kwargs
    assert call_kwargs["to"][0]["email"] == "olivalle.olten@outlook.com"
    assert "#42" in call_kwargs["subject"]


@patch("app.services.email_service.brevo_client")
def test_bestellen_abholung_bar(mock_email, client):
    """POST /bestellen mit zahlungsart=abholung_bar speichert Bestellung und sendet
    Mails."""
    import json

    from tests.conftest import _checkout_csrf

    csrf = _checkout_csrf(client)

    cart = json.dumps([{"produkt_id": 1, "menge": 2}])
    resp = client.post(
        "/bestellen",
        data={
            "vorname": "Clara",
            "nachname": "Bar",
            "email": "clara@test.ch",
            "strasse": "Barweg 1",
            "plz": "4600",
            "ort": "Olten",
            "versandart": "abholung",
            "zahlungsart": "abholung_bar",
            "cart_data": cart,
            "kommentar": "Bitte nachmittags",
            "csrf_token": csrf,
        },
        follow_redirects=False,
    )

    assert resp.status_code == 200
    assert "bestell" in resp.text.lower()

    # 2 E-Mails: Kundenbestätigung + Stakeholder-Benachrichtigung
    assert mock_email.transactional_emails.send_transac_email.call_count == 2

    from app.database import get_db

    conn = get_db()
    try:
        row = conn.execute(
            "SELECT status, zahlungsart, versandart, versandkosten_chf "
            "FROM bestellungen WHERE id = 1"
        ).fetchone()
        assert row["status"] == "neu"
        assert row["zahlungsart"] == "abholung_bar"
        assert row["versandart"] == "abholung"
        assert row["versandkosten_chf"] == 0
    finally:
        conn.close()


@patch("app.services.email_service.brevo_client")
def test_bestellen_abholung_bar_mit_versand_abgelehnt(mock_email, client):
    """abholung_bar + versandart=versand wird abgelehnt (HTTP 400)."""
    import json

    from tests.conftest import _checkout_csrf

    csrf = _checkout_csrf(client)

    cart = json.dumps([{"produkt_id": 1, "menge": 1}])
    resp = client.post(
        "/bestellen",
        data={
            "vorname": "David",
            "nachname": "Fehler",
            "email": "david@test.ch",
            "strasse": "Fehlerweg 1",
            "plz": "8000",
            "ort": "Zürich",
            "versandart": "versand",
            "zahlungsart": "abholung_bar",
            "cart_data": cart,
            "kommentar": "",
            "csrf_token": csrf,
        },
        follow_redirects=False,
    )

    assert resp.status_code == 400


@patch("app.services.email_service.brevo_client")
def test_stakeholder_mail_stripe(mock_client):
    """Stakeholder-Mail funktioniert auch für Stripe-Bestellungen."""
    mock_client.transactional_emails.send_transac_email.return_value = MagicMock(
        message_id="sh_2"
    )
    sende_stakeholder_benachrichtigung(
        bestell_id=43,
        kunde={"vorname": "Beat", "nachname": "Stripe", "email": "beat@test.ch"},
        positionen=[{"name": "Olivenöl 250ml", "menge": 1, "einzelpreis_chf": 8.0}],
        versandkosten=9.90,
        total=17.90,
        zahlungsart="stripe",
        versandart="versand",
    )
    mock_client.transactional_emails.send_transac_email.assert_called_once()
    call_kwargs = mock_client.transactional_emails.send_transac_email.call_args.kwargs
    assert call_kwargs["to"][0]["email"] == "olivalle.olten@outlook.com"
