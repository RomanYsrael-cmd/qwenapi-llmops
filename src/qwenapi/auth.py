"""Small, side-effect-free API-key helpers suitable for middleware tests."""

from __future__ import annotations

import secrets


def is_authorized(authorization: str | None, expected_api_key: str) -> bool:
    """Validate an exact Bearer token without leaking comparison details."""

    if not expected_api_key or not authorization:
        return False
    return secrets.compare_digest(authorization, f"Bearer {expected_api_key}")
