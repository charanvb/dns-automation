"""
Custom application exceptions.

All domain-specific errors should derive from AppError so that the global
exception handler can translate them to the correct HTTP response codes.
"""
from __future__ import annotations


class AppError(Exception):
    """Base for all application-level errors."""

    status_code: int = 500
    detail: str = "An unexpected error occurred."

    def __init__(self, detail: str | None = None) -> None:
        self.detail = detail or self.__class__.detail
        super().__init__(self.detail)


class NotFoundError(AppError):
    status_code = 404
    detail = "The requested resource was not found."


class ForbiddenError(AppError):
    status_code = 403
    detail = "You do not have permission to perform this action."


class UnauthorizedError(AppError):
    status_code = 401
    detail = "Authentication required."


class ConflictError(AppError):
    status_code = 409
    detail = "A conflict occurred with the current state."


class ValidationError(AppError):
    status_code = 422
    detail = "The submitted data failed validation."


class RateLimitError(AppError):
    status_code = 429
    detail = "You have exceeded the request rate limit."


class BlacklistedDomainError(AppError):
    status_code = 403
    detail = "This domain cannot be managed through self-service."


class MicetroError(AppError):
    status_code = 502
    detail = "An error occurred communicating with Micetro."


class MicetroAuthError(MicetroError):
    status_code = 502
    detail = "Failed to authenticate with Micetro."
