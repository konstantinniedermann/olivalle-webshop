"""Issue #167: Versandkosten-Konstante propagiert aus einer Quelle in Templates + JS.

Sichert ab, dass Anzeige (Templates, cart.js-Data-Attribute) und Berechnung
(bestell_service) denselben Wert nutzen — kein Drift mehr über 5+ Stellen.
"""

from app.services.bestell_service import GRATIS_AB_CHF, VERSANDKOSTEN_CHF


def test_warenkorb_body_hat_versand_dataattribute(client):
    """cart.js liest die Werte aus body-Data-Attributen statt hartkodiert."""
    html = client.get("/warenkorb").text
    assert f'data-versandkosten="{VERSANDKOSTEN_CHF}"' in html
    assert f'data-gratis-ab="{GRATIS_AB_CHF}"' in html


def test_agb_zeigt_konstante_versandkosten(client):
    html = client.get("/agb").text
    assert f"CHF {VERSANDKOSTEN_CHF:.2f} pauschal" in html
    assert f"ab einem Bestellwert von CHF {GRATIS_AB_CHF:.2f}" in html


def test_checkout_zeigt_konstante_versandkosten(client):
    html = client.get("/checkout").text
    assert f"CHF {VERSANDKOSTEN_CHF:.2f}" in html
    assert f"ab CHF {GRATIS_AB_CHF:.0f} gratis" in html
