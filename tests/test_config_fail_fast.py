"""Tests fuer die Produktions-Konfigurationspruefung (#161)."""

from app.config import Settings, pruefe_produktionskonfig


def _vollstaendige_settings(**overrides) -> Settings:
    """Settings mit allen Pflichtfeldern gesetzt; overrides fuer Einzelfaelle."""
    werte = {
        "secret_key": "ein-echtes-langes-geheimnis",
        "base_url": "https://olivalle.ch",
        "stripe_secret_key": "sk_live_x",
        "stripe_webhook_secret": "whsec_x",
        "brevo_api_key": "brevo_x",
        "admin_credentials": "inhaber:$2b$hash",
        "qr_iban": "CH0000000000000000000",
    }
    werte.update(overrides)
    return Settings(**werte)


def test_vollstaendige_konfig_keine_probleme():
    assert pruefe_produktionskonfig(_vollstaendige_settings()) == []


def test_default_secret_key_wird_erkannt():
    probleme = pruefe_produktionskonfig(_vollstaendige_settings(secret_key="change-me"))
    assert any("SECRET_KEY" in p for p in probleme)


def test_leerer_secret_key_wird_erkannt():
    probleme = pruefe_produktionskonfig(_vollstaendige_settings(secret_key=""))
    assert any("SECRET_KEY" in p for p in probleme)


def test_localhost_base_url_wird_erkannt():
    probleme = pruefe_produktionskonfig(
        _vollstaendige_settings(base_url="http://localhost:8000")
    )
    assert any("BASE_URL" in p for p in probleme)


def test_leeres_pflichtsecret_wird_erkannt():
    probleme = pruefe_produktionskonfig(_vollstaendige_settings(brevo_api_key=""))
    assert any("BREVO_API_KEY" in p for p in probleme)


def test_mehrere_probleme_werden_gesammelt():
    probleme = pruefe_produktionskonfig(
        _vollstaendige_settings(
            secret_key="change-me", stripe_secret_key="", admin_credentials=""
        )
    )
    assert len(probleme) == 3
