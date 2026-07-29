"""
Micetro REST API async client.

Uses a singleton session token that is refreshed automatically on expiry.
All DNS operations go through this client — never call httpx directly from
other modules.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

import httpx

from app.config import get_settings
from app.micetro.exceptions import MicetroAuthError, MicetroError, MicetroNotFoundError

logger = logging.getLogger(__name__)
settings = get_settings()

_SESSION_LOCK = asyncio.Lock()


class MicetroClient:
    """
    Low-level HTTP client for the Micetro REST API.

    Lifecycle:
    - Call ``await client.ensure_session()`` before any API call.
    - The session token is stored as an instance variable and renewed
      automatically when it expires (based on MICETRO_SESSION_TIMEOUT).
    - A module-level singleton is exposed as ``micetro_client``.
    """

    def __init__(self) -> None:
        self._session_token: str | None = None
        self._session_expires_at: datetime | None = None
        self._http: httpx.AsyncClient | None = None

    @property
    def _base_url(self) -> str:
        return settings.MICETRO_BASE_URL.rstrip("/")

    def _get_http_client(self) -> httpx.AsyncClient:
        if self._http is None or self._http.is_closed:
            self._http = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=30.0,
                verify=settings.MICETRO_VERIFY_SSL,
            )
        return self._http

    # ── Session management ────────────────────────────────────────────────

    async def _create_session(self) -> str:
        """Authenticate with Micetro and return a new session token."""
        client = self._get_http_client()
        try:
            response = await client.post(
                "/sessions",
                json={
                    "username": settings.MICETRO_USERNAME,
                    "password": settings.MICETRO_PASSWORD,
                    "loginAs": settings.MICETRO_USERNAME,
                },
            )
            response.raise_for_status()
            data = response.json()
            token = data.get("result", {}).get("session")
            if not token:
                raise MicetroAuthError("No session token in Micetro response.")
            return token
        except httpx.HTTPStatusError as exc:
            raise MicetroAuthError(
                f"Micetro authentication failed (HTTP {exc.response.status_code})."
            ) from exc
        except httpx.RequestError as exc:
            raise MicetroAuthError(f"Could not reach Micetro: {exc}") from exc

    async def ensure_session(self) -> None:
        """Ensure a valid session token exists, refreshing if needed."""
        async with _SESSION_LOCK:
            now = datetime.now(tz=timezone.utc)
            if (
                self._session_token is None
                or self._session_expires_at is None
                or now >= self._session_expires_at
            ):
                logger.info("Refreshing Micetro session token.")
                self._session_token = await self._create_session()
                self._session_expires_at = now + timedelta(
                    seconds=settings.MICETRO_SESSION_TIMEOUT - 60
                )

    async def _headers(self) -> dict[str, str]:
        await self.ensure_session()
        return {"Authorization": f"Bearer {self._session_token}"}

    # ── Generic request helpers ───────────────────────────────────────────

    async def get(self, path: str, params: dict | None = None) -> dict:
        return await self._request("GET", path, params=params)

    async def post(self, path: str, body: dict) -> dict:
        return await self._request("POST", path, json=body)

    async def put(self, path: str, body: dict) -> dict:
        return await self._request("PUT", path, json=body)

    async def delete(self, path: str) -> dict:
        return await self._request("DELETE", path)

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict | None = None,
        json: dict | None = None,
    ) -> dict:
        client = self._get_http_client()
        headers = await self._headers()
        try:
            response = await client.request(
                method, path, headers=headers, params=params, json=json
            )
            if response.status_code == 404:
                raise MicetroNotFoundError(f"Micetro: {path} not found.")
            response.raise_for_status()
            return response.json()
        except MicetroNotFoundError:
            raise
        except httpx.HTTPStatusError as exc:
            raise MicetroError(
                f"Micetro API error {exc.response.status_code}: {exc.response.text[:200]}"
            ) from exc
        except httpx.RequestError as exc:
            raise MicetroError(f"Could not reach Micetro: {exc}") from exc

    async def close(self) -> None:
        if self._http and not self._http.is_closed:
            await self._http.aclose()


# ── Module-level singleton ────────────────────────────────────────────────────
micetro_client = MicetroClient()
