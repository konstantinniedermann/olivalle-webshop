"""Tests für app.client_ip.get_client_ip."""

from types import SimpleNamespace

import pytest

from app import client_ip as client_ip_module
from app.client_ip import get_client_ip


def _make_request(headers: dict[str, str] | None = None, host: str | None = "1.2.3.4"):
    """Minimaler Stub eines Starlette-Requests."""
    return SimpleNamespace(
        headers=headers or {},
        client=SimpleNamespace(host=host) if host else None,
    )


@pytest.fixture
def trust_proxy(monkeypatch):
    monkeypatch.setattr(client_ip_module.settings, "trust_proxy_headers", True)


@pytest.fixture
def distrust_proxy(monkeypatch):
    monkeypatch.setattr(client_ip_module.settings, "trust_proxy_headers", False)


def test_fly_client_ip_bevorzugt(trust_proxy):
    req = _make_request({"fly-client-ip": "9.9.9.9", "x-forwarded-for": "8.8.8.8"})
    assert get_client_ip(req) == "9.9.9.9"


def test_x_forwarded_for_erstes_element(trust_proxy):
    req = _make_request({"x-forwarded-for": "203.0.113.5, 10.0.0.1, 10.0.0.2"})
    assert get_client_ip(req) == "203.0.113.5"


def test_fallback_auf_request_client(trust_proxy):
    req = _make_request(headers={}, host="1.2.3.4")
    assert get_client_ip(req) == "1.2.3.4"


def test_unknown_wenn_nichts_verfuegbar(trust_proxy):
    req = _make_request(headers={}, host=None)
    assert get_client_ip(req) == "unknown"


def test_distrust_ignoriert_header(distrust_proxy):
    req = _make_request(
        {"fly-client-ip": "9.9.9.9", "x-forwarded-for": "8.8.8.8"},
        host="1.2.3.4",
    )
    assert get_client_ip(req) == "1.2.3.4"


def test_unabhaengige_counter_pro_ip(trust_proxy):
    """Sicherheitskern: zwei verschiedene XFF-Werte führen zu verschiedenen IPs."""
    req_a = _make_request({"x-forwarded-for": "1.1.1.1"})
    req_b = _make_request({"x-forwarded-for": "2.2.2.2"})
    assert get_client_ip(req_a) != get_client_ip(req_b)
