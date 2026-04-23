"""Tests für scripts/check_tls.py (Issue #111)."""

import os
import sys
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest

# scripts/ auf sys.path, damit `import check_tls` funktioniert
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))


def _fake_cert_with_notafter(days_from_now: int) -> dict:
    """Baut ein cert-Dict im Format zurück, wie ssock.getpeercert() es liefert."""
    not_after = datetime.now(UTC) + timedelta(days=days_from_now)
    return {"notAfter": not_after.strftime("%b %d %H:%M:%S %Y GMT")}


@pytest.fixture
def env(monkeypatch):
    monkeypatch.setenv("HEALTHCHECKS_URL_TLS", "https://hc-ping.example/tls-uuid")


def test_cert_frisch_triggert_ping(env):
    import check_tls

    with (
        patch("check_tls._get_cert", return_value=_fake_cert_with_notafter(60)),
        patch("check_tls.urlopen") as mock_urlopen,
    ):
        exit_code = check_tls.main()

    assert exit_code == 0
    mock_urlopen.assert_called_once()
    url = mock_urlopen.call_args[0][0]
    assert url == "https://hc-ping.example/tls-uuid"


def test_cert_laeuft_bald_ab_kein_ping(env):
    import check_tls

    with (
        patch("check_tls._get_cert", return_value=_fake_cert_with_notafter(10)),
        patch("check_tls.urlopen") as mock_urlopen,
    ):
        exit_code = check_tls.main()

    assert exit_code == 1
    mock_urlopen.assert_not_called()


def test_cert_mit_malformed_date_wirft_klar(env):
    import check_tls

    with (
        patch("check_tls._get_cert", return_value={"notAfter": "not-a-date"}),
        pytest.raises(ValueError),
    ):
        check_tls.main()
