"""TLS-Cert-Monitoring für olivalle.ch (Issue #111).

Prüft die Restlaufzeit des TLS-Zertifikats und pingt Healthchecks.io
bei mindestens `THRESHOLD_DAYS` Tagen Restlaufzeit. Bei Unterschreitung
wird kein Ping abgesetzt — Healthchecks.io alarmiert dann nach Ablauf
der Grace-Period per E-Mail.
"""

import os
import socket
import ssl
import sys
from datetime import UTC, datetime
from urllib.request import urlopen

HOST = "olivalle.ch"
PORT = 443
THRESHOLD_DAYS = 30


def _get_cert(host: str, port: int) -> dict:
    """TLS-Handshake + Peer-Cert holen. Isoliert für Test-Mocking."""
    ctx = ssl.create_default_context()
    with (
        socket.create_connection((host, port), timeout=10) as sock,
        ctx.wrap_socket(sock, server_hostname=host) as ssock,
    ):
        return ssock.getpeercert()


def _days_until_expiry(cert: dict) -> int:
    not_after = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z").replace(
        tzinfo=UTC
    )
    return (not_after - datetime.now(UTC)).days


def main() -> int:
    cert = _get_cert(HOST, PORT)
    days_left = _days_until_expiry(cert)
    print(f"TLS cert for {HOST}: {days_left} days left (threshold: {THRESHOLD_DAYS})")

    if days_left < THRESHOLD_DAYS:
        return 1

    ping_url = os.environ["HEALTHCHECKS_URL_TLS"]
    with urlopen(ping_url, timeout=10) as resp:
        print(f"Healthchecks.io ping: {resp.status}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
