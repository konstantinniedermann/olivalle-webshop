from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer


def generiere_csrf_token(secret: str, max_age: int = 3600) -> str:
    s = URLSafeTimedSerializer(secret)
    return s.dumps("csrf")


def validiere_csrf_token(
    token: str, secret: str, max_age: int = 3600
) -> bool:
    s = URLSafeTimedSerializer(secret)
    try:
        s.loads(token, max_age=max_age)
        return True
    except (BadSignature, SignatureExpired):
        return False
