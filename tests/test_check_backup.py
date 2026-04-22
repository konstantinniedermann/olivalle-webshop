"""Tests für scripts/check_backup.py (Issue #118)."""
import os
import sys
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

# scripts/ auf sys.path, damit `import check_backup` funktioniert
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))


def _make_s3_with_object(age: timedelta | None) -> MagicMock:
    """Fake S3-Client. age=None → leerer Bucket, sonst ein Objekt mit
    gegebenem Alter (LastModified = now - age)."""
    fake = MagicMock()
    if age is None:
        fake.list_objects_v2.return_value = {}
    else:
        fake.list_objects_v2.return_value = {
            "Contents": [
                {
                    "Key": "olivalle/snapshot-latest",
                    "LastModified": datetime.now(UTC) - age,
                }
            ]
        }
    return fake


@pytest.fixture
def env(monkeypatch):
    """Setzt die 3 Env-Vars, die das Skript erwartet."""
    monkeypatch.setenv("LITESTREAM_ACCESS_KEY_ID", "test-key")
    monkeypatch.setenv("LITESTREAM_SECRET_ACCESS_KEY", "test-secret")
    monkeypatch.setenv("HEALTHCHECKS_URL", "https://hc-ping.example/abc")


def test_fresh_object_triggers_ping(env):
    """Frisches Objekt (1h alt) → Ping wird gesendet."""
    import check_backup

    fake_s3 = _make_s3_with_object(timedelta(hours=1))
    with patch.object(check_backup.boto3, "client", return_value=fake_s3), \
         patch("urllib.request.urlopen") as mock_urlopen:
        rc = check_backup.main()

    assert rc == 0
    mock_urlopen.assert_called_once()
    args, _ = mock_urlopen.call_args
    assert args[0] == "https://hc-ping.example/abc"
