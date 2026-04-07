import hashlib
import hmac

from fastapi import Form, HTTPException, Request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.config import settings

CSRF_COOKIE_NAME = "csrf_id"


def generiere_csrf_token(secret: str, identity: str, max_age: int = 3600) -> str:
    s = URLSafeTimedSerializer(secret)
    return s.dumps(identity)


def validiere_csrf_token(
    token: str,
    secret: str,
    expected_identity: str,
    max_age: int = 3600,
) -> bool:
    if not token or not expected_identity:
        return False
    s = URLSafeTimedSerializer(secret)
    try:
        payload = s.loads(token, max_age=max_age)
    except (BadSignature, SignatureExpired):
        return False
    if not isinstance(payload, str):
        return False
    return hmac.compare_digest(payload, expected_identity)


def admin_identity(admin_session_cookie: str) -> str:
    """Stabile, nicht-reversible Identity aus dem Admin-Session-Cookie."""
    digest = hashlib.sha256(admin_session_cookie.encode("utf-8")).hexdigest()
    return f"admin:{digest[:32]}"


def resolve_identity(request: Request) -> str | None:
    admin_cookie = request.cookies.get("admin_session")
    if admin_cookie:
        return admin_identity(admin_cookie)
    csrf_id = request.cookies.get(CSRF_COOKIE_NAME)
    if csrf_id:
        return f"anon:{csrf_id}"
    return None


def require_csrf(request: Request, csrf_token: str = Form("")) -> None:
    identity = resolve_identity(request)
    if not identity or not validiere_csrf_token(
        csrf_token, settings.secret_key, expected_identity=identity
    ):
        raise HTTPException(status_code=403, detail="Ungültiges CSRF-Token")
