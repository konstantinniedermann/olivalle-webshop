"""Helper zum Ermitteln der echten Client-IP hinter einem Reverse Proxy.

Hintergrund: Auf fly.io terminiert ein Edge-Proxy TLS und reicht den Request
an die App weiter. ``request.client.host`` zeigt dann immer auf die Proxy-IP,
nicht auf die echte Client-IP. Damit funktionieren IP-basierte Schutzmechanismen
(BruteForceGuard, Rate-Limit) nicht mehr individuell.

fly.io setzt zwei relevante Header:
- ``Fly-Client-IP``: eindeutige Client-IP, vom Edge gesetzt
- ``X-Forwarded-For``: Standard-Header, kommagetrennte Kette (links = Client)

Beide Header sind nur vertrauenswürdig, wenn die App tatsächlich hinter einem
kontrollierten Proxy läuft. Lokal/im Test darf das Vertrauen abgeschaltet
werden, sonst kann jeder Client seine IP frei wählen.
"""

from __future__ import annotations

from fastapi import Request

from app.config import settings


def get_client_ip(request: Request) -> str:
    """Liefert die echte Client-IP.

    Reihenfolge (nur wenn ``settings.trust_proxy_headers`` aktiv):
    1. ``Fly-Client-IP`` (fly.io-spezifisch, eindeutig)
    2. erstes Element von ``X-Forwarded-For``
    3. ``request.client.host`` als Fallback
    """
    if settings.trust_proxy_headers:
        fly_ip = request.headers.get("fly-client-ip")
        if fly_ip:
            return fly_ip.strip()

        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            first = forwarded.split(",")[0].strip()
            if first:
                return first

    if request.client and request.client.host:
        return request.client.host
    return "unknown"
