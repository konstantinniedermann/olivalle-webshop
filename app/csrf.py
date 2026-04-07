from fastapi import Form, HTTPException
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.config import settings


def generiere_csrf_token(secret: str, max_age: int = 3600) -> str:
    s = URLSafeTimedSerializer(secret)
    return s.dumps("csrf")


def require_csrf(csrf_token: str = Form("")) -> None:
    if not validiere_csrf_token(csrf_token, settings.secret_key):
        raise HTTPException(status_code=403, detail="Ungültiges CSRF-Token")


def validiere_csrf_token(
    token: str, secret: str, max_age: int = 3600
) -> bool:
    s = URLSafeTimedSerializer(secret)
    try:
        s.loads(token, max_age=max_age)
        return True
    except (BadSignature, SignatureExpired):
        return False
