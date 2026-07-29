"""
Secrets provider abstraction.

All secrets access goes through `get_secret()`.  Currently reads from environment
variables / .env file via Pydantic Settings.  To switch to GCP Secret Manager,
replace the body of `get_secret()` — no other code changes required.
"""
from __future__ import annotations

import os


def get_secret(name: str, default: str | None = None) -> str:
    """
    Retrieve a secret by name.

    Precedence:
    1. Environment variable (already loaded from .env by pydantic-settings)
    2. ``default`` if provided
    3. Raise KeyError

    When GCP Secret Manager is needed, replace this function body with the
    google-cloud-secret-manager SDK call.  The interface stays the same.
    """
    value = os.environ.get(name, default)
    if value is None:
        raise KeyError(
            f"Secret '{name}' not found in environment. "
            "Set it in .env or as an environment variable."
        )
    return value
