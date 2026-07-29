"""Micetro-specific exceptions."""
from __future__ import annotations

from app.exceptions import MicetroError, MicetroAuthError


class MicetroNotFoundError(MicetroError):
    status_code = 404
    detail = "The requested Micetro resource was not found."


class MicetroConflictError(MicetroError):
    status_code = 409
    detail = "A conflict occurred in Micetro."


class MicetroValidationError(MicetroError):
    status_code = 422
    detail = "Micetro rejected the DNS record data."


__all__ = [
    "MicetroError",
    "MicetroAuthError",
    "MicetroNotFoundError",
    "MicetroConflictError",
    "MicetroValidationError",
]
