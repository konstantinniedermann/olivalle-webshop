import time

import bcrypt
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer


def parse_credentials(credentials_str: str) -> list[tuple[str, str]]:
    """Parse 'label:hash,label:hash' into [(label, hash), ...]."""
    if not credentials_str.strip():
        return []
    result = []
    for entry in credentials_str.split(","):
        if ":" not in entry:
            raise ValueError(
                f"ADMIN_CREDENTIALS: Eintrag '{entry}' enthält kein ':' "
                f"(Format: label:bcrypt_hash)"
            )
        label, bcrypt_hash = entry.split(":", 1)
        result.append((label.strip(), bcrypt_hash.strip()))
    return result


def verify_password(password: str, credentials: list[tuple[str, str]]) -> str | None:
    """Check password against all credential hashes. Return label or None."""
    for label, pw_hash in credentials:
        if bcrypt.checkpw(password.encode(), pw_hash.encode()):
            return label
    return None


def create_session(admin_label: str, *, secret: str) -> str:
    """Create a signed session token containing the admin label."""
    s = URLSafeTimedSerializer(secret)
    return s.dumps({"admin_label": admin_label})


def validate_session(token: str, *, secret: str, max_age: int = 86400) -> str | None:
    """Validate session token. Return admin_label or None."""
    if max_age <= 0:
        return None
    s = URLSafeTimedSerializer(secret)
    try:
        data = s.loads(token, max_age=max_age)
        return data.get("admin_label")
    except (BadSignature, SignatureExpired):
        return None


class BruteForceGuard:
    """In-memory brute-force protection per IP."""

    def __init__(
        self,
        max_attempts: int = 5,
        window_seconds: int = 900,
        lockout_seconds: int = 300,
    ):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.lockout_seconds = lockout_seconds
        self._failures: dict[str, list[float]] = {}

    def record_failure(self, ip: str) -> None:
        now = time.time()
        if ip not in self._failures:
            self._failures[ip] = []
        self._failures[ip].append(now)

    def is_locked(self, ip: str) -> bool:
        if ip not in self._failures:
            return False
        now = time.time()
        recent = [t for t in self._failures[ip] if now - t < self.window_seconds]
        self._failures[ip] = recent
        if len(recent) < self.max_attempts:
            return False
        last_failure = max(recent)
        return now - last_failure < self.lockout_seconds

    def reset(self, ip: str) -> None:
        self._failures.pop(ip, None)


# Module-level singleton
login_guard = BruteForceGuard()
