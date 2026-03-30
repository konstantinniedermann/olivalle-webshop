from unittest.mock import MagicMock, patch

import stripe


@patch("app.services.email_service.resend.Emails.send", return_value={"id": "test"})
@patch("app.routers.webhooks.stripe.Webhook.construct_event")
def test_webhook_checkout_completed(mock_construct, mock_email, client, db):
    # Testbestellung anlegen
    db.execute(
        "INSERT INTO kunden (vorname, nachname, email, strasse, plz, ort) "
        "VALUES ('Max', 'Muster', 'max@test.ch', 'Str 1', '4600', 'Olten')"
    )
    db.execute(
        "INSERT INTO bestellungen"
        " (kunde_id, zahlungsart, versandart, total_chf,"
        " stripe_session_id, status) "
        "VALUES (1, 'stripe', 'versand', 25.90, 'cs_test_123', 'neu')"
    )
    db.execute(
        "INSERT INTO bestellpositionen"
        " (bestellung_id, produkt_id, menge, einzelpreis_chf) "
        "VALUES (1, 1, 2, 8.0)"
    )
    db.commit()

    mock_construct.return_value = MagicMock(
        type="checkout.session.completed",
        data=MagicMock(object=MagicMock(id="cs_test_123")),
    )

    response = client.post(
        "/webhook/stripe",
        content=b'{"type": "checkout.session.completed"}',
        headers={"stripe-signature": "test_sig"},
    )
    assert response.status_code == 200

    row = db.execute("SELECT status FROM bestellungen WHERE id = 1").fetchone()
    assert dict(row)["status"] == "bezahlt"


@patch("app.routers.webhooks.stripe.Webhook.construct_event")
def test_webhook_ungueltige_signatur(mock_construct, client):
    """Ungültige Stripe-Signatur → 400."""
    mock_construct.side_effect = stripe.SignatureVerificationError(
        "Invalid signature", "sig_header"
    )

    response = client.post(
        "/webhook/stripe",
        content=b'{"type": "checkout.session.completed"}',
        headers={"stripe-signature": "bad_sig"},
    )
    assert response.status_code == 400


@patch("app.services.email_service.resend.Emails.send", return_value={"id": "test"})
@patch("app.routers.webhooks.stripe.Webhook.construct_event")
def test_webhook_bestellung_nicht_gefunden(mock_construct, mock_email, client):
    """Session-ID ohne passende Bestellung → 200, keine E-Mail."""
    mock_construct.return_value = MagicMock(
        type="checkout.session.completed",
        data=MagicMock(object=MagicMock(id="cs_unknown_999")),
    )

    response = client.post(
        "/webhook/stripe",
        content=b'{"type": "checkout.session.completed"}',
        headers={"stripe-signature": "test_sig"},
    )
    assert response.status_code == 200
    mock_email.assert_not_called()


@patch("app.services.email_service.resend.Emails.send", return_value={"id": "test"})
@patch("app.routers.webhooks.stripe.Webhook.construct_event")
def test_webhook_doppelt_kein_doppelte_email(
    mock_construct, mock_email, client, db
):
    """Doppelter Webhook → E-Mail nur einmal, Status bleibt bezahlt."""
    # Testbestellung anlegen
    db.execute(
        "INSERT INTO kunden (vorname, nachname, email, strasse, plz, ort) "
        "VALUES ('Max', 'Muster', 'max@test.ch', 'Str 1', '4600', 'Olten')"
    )
    db.execute(
        "INSERT INTO bestellungen"
        " (kunde_id, zahlungsart, versandart, total_chf,"
        " stripe_session_id, status) "
        "VALUES (1, 'stripe', 'versand', 25.90, 'cs_test_doppelt', 'neu')"
    )
    db.execute(
        "INSERT INTO bestellpositionen"
        " (bestellung_id, produkt_id, menge, einzelpreis_chf) "
        "VALUES (1, 1, 2, 8.0)"
    )
    db.commit()

    mock_construct.return_value = MagicMock(
        type="checkout.session.completed",
        data=MagicMock(object=MagicMock(id="cs_test_doppelt")),
    )

    # Erster Webhook
    response1 = client.post(
        "/webhook/stripe",
        content=b'{"type": "checkout.session.completed"}',
        headers={"stripe-signature": "test_sig"},
    )
    assert response1.status_code == 200
    assert mock_email.call_count == 1

    row = db.execute("SELECT status FROM bestellungen WHERE id = 1").fetchone()
    assert dict(row)["status"] == "bezahlt"

    # Zweiter Webhook (Duplikat)
    response2 = client.post(
        "/webhook/stripe",
        content=b'{"type": "checkout.session.completed"}',
        headers={"stripe-signature": "test_sig"},
    )
    assert response2.status_code == 200
    # E-Mail darf nicht erneut gesendet werden
    assert mock_email.call_count == 1

    row = db.execute("SELECT status FROM bestellungen WHERE id = 1").fetchone()
    assert dict(row)["status"] == "bezahlt"
