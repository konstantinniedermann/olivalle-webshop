"""Prüft, ob Tigris-Backup frisch ist, und pingt Healthchecks.io.

Issue #118. Entwurfsdokument:
docs/superpowers/specs/2026-04-22-issue-118-backup-monitoring-design.md
"""

from __future__ import annotations

import os
import sys
import urllib.request
from datetime import UTC, datetime, timedelta

import boto3

BUCKET = "olivalle-backup"
PREFIX = "olivalle/"
ENDPOINT = "https://fly.storage.tigris.dev"
THRESHOLD_HOURS = 24


def _newest_object_age(s3) -> timedelta | None:
    """Alter des neuesten Objekts im Bucket. None falls Bucket leer."""
    resp = s3.list_objects_v2(Bucket=BUCKET, Prefix=PREFIX)
    contents = resp.get("Contents", [])
    if not contents:
        return None
    newest = max(o["LastModified"] for o in contents)
    return datetime.now(UTC) - newest


def main() -> int:
    s3 = boto3.client(
        "s3",
        endpoint_url=ENDPOINT,
        region_name="auto",
        aws_access_key_id=os.environ["LITESTREAM_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["LITESTREAM_SECRET_ACCESS_KEY"],
    )
    age = _newest_object_age(s3)
    if age is None or age > timedelta(hours=THRESHOLD_HOURS):
        print(f"[check_backup] stale or empty: age={age}")
        return 0
    urllib.request.urlopen(os.environ["HEALTHCHECKS_URL"], timeout=10)
    print(f"[check_backup] ok, ping sent. age={age}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
