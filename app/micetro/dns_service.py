"""
DNS-specific Micetro operations.
All zone and record interactions go through this service layer.
Module 3 will expand this with full CRUD implementations.
"""
from __future__ import annotations

import logging

from app.micetro.client import micetro_client

logger = logging.getLogger(__name__)


class MicetroDNSService:
    """High-level DNS operations against Micetro."""

    # ── Zones ─────────────────────────────────────────────────────────────

    async def search_zones(self, query: str = "", limit: int = 50) -> list[dict]:
        """Search DNS zones by name fragment."""
        params: dict = {"limit": limit}
        if query:
            params["filter"] = query
        result = await micetro_client.get("/dnsZones", params=params)
        return result.get("result", {}).get("dnsZones", [])

    async def get_zone(self, zone_ref: str) -> dict:
        """Fetch a single zone by its Micetro ref."""
        result = await micetro_client.get(f"/dnsZones/{zone_ref}")
        return result.get("result", {})

    # ── Records ───────────────────────────────────────────────────────────

    async def get_zone_records(
        self,
        zone_ref: str,
        record_type: str | None = None,
    ) -> list[dict]:
        """Fetch all DNS records within a zone, optionally filtered by type."""
        params: dict = {}
        if record_type:
            params["type"] = record_type
        result = await micetro_client.get(
            f"/dnsZones/{zone_ref}/dnsRecords", params=params
        )
        return result.get("result", {}).get("dnsRecords", [])

    async def check_spf_exists(self, zone_ref: str) -> bool:
        """Return True if any TXT record starting with 'v=spf1' exists in the zone."""
        records = await self.get_zone_records(zone_ref, record_type="TXT")
        return any(
            r.get("data", "").strip().startswith("v=spf1")
            for r in records
        )

    async def create_record(self, zone_ref: str, record: dict) -> dict:
        """Create a DNS record in Micetro. ``record`` must follow Micetro schema."""
        result = await micetro_client.post(f"/dnsZones/{zone_ref}/dnsRecords", record)
        return result.get("result", {})

    async def modify_record(self, record_ref: str, record: dict) -> dict:
        """Modify an existing DNS record by its Micetro ref."""
        result = await micetro_client.put(f"/dnsRecords/{record_ref}", record)
        return result.get("result", {})

    async def delete_record(self, record_ref: str) -> None:
        """Delete a DNS record by its Micetro ref."""
        await micetro_client.delete(f"/dnsRecords/{record_ref}")


# Singleton for use across the application
dns_service = MicetroDNSService()
