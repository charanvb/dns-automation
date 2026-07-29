from __future__ import annotations

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.config import get_settings

settings = get_settings()

_ALGORITHM = settings.JWT_ALGORITHM
_SECRET = settings.JWT_SECRET_KEY
_EXPIRE_MINUTES = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES

COOKIE_NAME = "access_token"


def create_access_token(subject: str, extra_claims: dict | None = None) -> str:
    """Create a signed JWT. `subject` is the user's UUID as a string."""
    now = datetime.now(tz=timezone.utc)
    payload: dict = {
        "sub": subject,
        "iat": now,
        "exp": now + timedelta(minutes=_EXPIRE_MINUTES),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, _SECRET, algorithm=_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """
    Decode and verify a JWT. Returns the full payload dict.
    Raises ``jose.JWTError`` if the token is invalid or expired.
    """
    return jwt.decode(token, _SECRET, algorithms=[_ALGORITHM])


def get_subject_from_token(token: str) -> str | None:
    """Convenience helper; returns the `sub` claim or None on any error."""
    try:
        payload = decode_access_token(token)
        return payload.get("sub")
    except JWTError:
        return None
