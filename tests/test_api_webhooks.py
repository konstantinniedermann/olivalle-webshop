from unittest.mock import MagicMock, patch


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
