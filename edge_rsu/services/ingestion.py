"""
SmartV2X-CP Ultra — Real-Time Ingestion Service
==================================================
Pre-processes incoming vehicle data, validates payloads, and
routes them to the CP-Map and Risk Aggregator.
"""

import time
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class IngestionService:
    """Validates and routes incoming vehicle payloads."""

    def __init__(self):
        self._processed_count = 0
        self._last_latency_ms = 0.0

    async def process(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and enrich a vehicle update payload.

        Returns the enriched payload with server-side timestamp and
        latency measurement.
        """
        t_start = time.time()

        # ── Validation ─────────────────────────────────────
        vehicle_id = payload.get("vehicle_id")
        if not vehicle_id:
            raise ValueError("Missing vehicle_id in payload")

        # ── Enrichment ─────────────────────────────────────
        client_ts = payload.get("timestamp", 0)
        server_ts = time.time()
        latency_ms = (server_ts - client_ts) * 1000 if client_ts else 0

        enriched = {
            **payload,
            "server_timestamp": server_ts,
            "ingestion_latency_ms": round(latency_ms, 2),
        }

        self._processed_count += 1
        self._last_latency_ms = latency_ms

        if self._processed_count % 100 == 0:
            logger.info(
                "Ingested %d updates — last latency: %.1f ms",
                self._processed_count, latency_ms,
            )

        return enriched

    @property
    def stats(self) -> Dict[str, Any]:
        return {
            "processed_count": self._processed_count,
            "last_latency_ms": self._last_latency_ms,
        }
