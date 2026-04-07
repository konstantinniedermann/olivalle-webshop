import bcrypt


def _make_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


class TestParseCredentials:
    def test_parse_single_credential(self):
        from app.services.auth_service import parse_credentials

        pw_hash = _make_hash("geheim")
        result = parse_credentials(f"owner:{pw_hash}")
        assert len(result) == 1
        assert result[0][0] == "owner"
        assert result[0][1] == pw_hash

    def test_parse_multiple_credentials(self):
        from app.services.auth_service import parse_credentials

        h1 = _make_hash("pass1")
        h2 = _make_hash("pass2")
        result = parse_credentials(f"owner:{h1},dev:{h2}")
        assert len(result) == 2
        assert result[0][0] == "owner"
        assert result[1][0] == "dev"

    def test_parse_empty_string(self):
        from app.services.auth_service import parse_credentials

        result = parse_credentials("")
        assert result == []

    def test_parse_invalid_entry_raises(self):
        import pytest

        from app.services.auth_service import parse_credentials

        with pytest.raises(ValueError, match="enthält kein ':'"):
            parse_credentials("kein-doppelpunkt")


class TestVerifyPassword:
    def test_correct_password_returns_label(self):
        from app.services.auth_service import verify_password

        h = _make_hash("geheim")
        credentials = [("owner", h)]
        assert verify_password("geheim", credentials) == "owner"

    def test_wrong_password_returns_none(self):
        from app.services.auth_service import verify_password

        h = _make_hash("geheim")
        credentials = [("owner", h)]
        assert verify_password("falsch", credentials) is None

    def test_matches_correct_credential_among_multiple(self):
        from app.services.auth_service import verify_password

        h1 = _make_hash("pass-owner")
        h2 = _make_hash("pass-dev")
        credentials = [("owner", h1), ("dev", h2)]
        assert verify_password("pass-dev", credentials) == "dev"

    def test_empty_credentials_returns_none(self):
        from app.services.auth_service import verify_password

        assert verify_password("anything", []) is None


class TestSession:
    def test_create_and_validate_session(self):
        from app.services.auth_service import create_session, validate_session

        token = create_session("owner", secret="test-secret")
        assert isinstance(token, str)
        label = validate_session(token, secret="test-secret")
        assert label == "owner"

    def test_invalid_token_returns_none(self):
        from app.services.auth_service import validate_session

        assert validate_session("garbage", secret="test-secret") is None

    def test_expired_session_returns_none(self):
        from app.services.auth_service import create_session, validate_session

        token = create_session("owner", secret="test-secret")
        assert validate_session(token, secret="test-secret", max_age=0) is None


class TestBruteForce:
    def test_under_limit_not_locked(self):
        from app.services.auth_service import BruteForceGuard

        guard = BruteForceGuard(max_attempts=3, window_seconds=60, lockout_seconds=30)
        for _ in range(2):
            guard.record_failure("1.2.3.4")
        assert guard.is_locked("1.2.3.4") is False

    def test_at_limit_locked(self):
        from app.services.auth_service import BruteForceGuard

        guard = BruteForceGuard(max_attempts=3, window_seconds=60, lockout_seconds=30)
        for _ in range(3):
            guard.record_failure("1.2.3.4")
        assert guard.is_locked("1.2.3.4") is True

    def test_different_ips_independent(self):
        from app.services.auth_service import BruteForceGuard

        guard = BruteForceGuard(max_attempts=3, window_seconds=60, lockout_seconds=30)
        for _ in range(3):
            guard.record_failure("1.2.3.4")
        assert guard.is_locked("5.6.7.8") is False

    def test_reset_clears_failures(self):
        from app.services.auth_service import BruteForceGuard

        guard = BruteForceGuard(max_attempts=3, window_seconds=60, lockout_seconds=30)
        for _ in range(3):
            guard.record_failure("1.2.3.4")
        guard.reset("1.2.3.4")
        assert guard.is_locked("1.2.3.4") is False
