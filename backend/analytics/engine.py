"""
SmartV2X-CP Ultra — Analytics Engine
=======================================
Aggregation and analysis over collision data — hotspot detection,
time-series trends, and city-level statistics.
"""

import time
import logging
from typing import Dict, Any, List
from collections import defaultdict

logger = logging.getLogger(__name__)


class AnalyticsEngine:
    """Processes and aggregates collision and vehicle data for insights."""

    def __init__(self):
        self._event_buffer: List[Dict[str, Any]] = []

    def ingest_event(self, event: Dict[str, Any]):
        """Add a collision/risk event to the analytics pipeline."""
        event["ingested_at"] = time.time()
        self._event_buffer.append(event)

    def hotspot_analysis(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """
        Identify geographic locations with highest collision risk.
        Groups events by rounded lat/lon.
        """
        grid: Dict[str, Dict] = defaultdict(lambda: {"count": 0, "total_risk": 0.0})

        for ev in self._event_buffer:
            lat = round(ev.get("latitude", 0), 3)
            lon = round(ev.get("longitude", 0), 3)
            key = f"{lat},{lon}"
            grid[key]["count"] += 1
            grid[key]["total_risk"] += ev.get("risk_score", 0)
            grid[key]["lat"] = lat
            grid[key]["lon"] = lon

        hotspots = sorted(grid.values(), key=lambda x: x["total_risk"], reverse=True)
        return hotspots[:top_n]

    def time_series(self, bucket_minutes: int = 60) -> List[Dict[str, Any]]:
        """Aggregate events into time buckets."""
        buckets: Dict[int, int] = defaultdict(int)
        for ev in self._event_buffer:
            ts = ev.get("ingested_at", 0)
            bucket_key = int(ts // (bucket_minutes * 60))
            buckets[bucket_key] += 1

        return [
            {"bucket": k, "count": v}
            for k, v in sorted(buckets.items())
        ]

    def risk_distribution(self) -> Dict[str, int]:
        """Count events by risk level."""
        dist: Dict[str, int] = defaultdict(int)
        for ev in self._event_buffer:
            dist[ev.get("risk_level", "LOW")] += 1
        return dict(dist)

    @property
    def total_events(self) -> int:
        return len(self._event_buffer)
