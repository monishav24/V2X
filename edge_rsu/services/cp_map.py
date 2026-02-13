"""
SmartV2X-CP Ultra — Collision Probability Map (CP-Map)
=======================================================
Maintains a dynamic spatial grid where each cell holds an
aggregated collision probability score that decays over time.
"""

import math
import time
import logging
from typing import Dict, Any, List, Tuple, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


class CollisionProbabilityMap:
    """
    Spatial grid-based collision probability map.

    - Grid cells are indexed as (row, col).
    - Each cell stores a risk score in [0, 1].
    - Scores decay exponentially over time.
    """

    def __init__(
        self,
        grid_size: float = 50.0,       # metres per cell
        decay_rate: float = 0.05,      # exponential decay per second
        lat_ref: float = 28.6139,
        lon_ref: float = 77.2090,
    ):
        self.grid_size = grid_size
        self.decay_rate = decay_rate
        self.lat_ref = lat_ref
        self.lon_ref = lon_ref

        # {(row, col): {"score": float, "updated_at": float, "vehicles": set}}
        self._grid: Dict[Tuple[int, int], Dict[str, Any]] = defaultdict(
            lambda: {"score": 0.0, "updated_at": time.time(), "vehicles": set()}
        )
        logger.info("CP-Map initialised (cell=%.0fm, decay=%.3f/s)", grid_size, decay_rate)

    # ── Coordinate conversion ─────────────────────────────
    def _latlon_to_cell(self, lat: float, lon: float) -> Tuple[int, int]:
        dx = (lon - self.lon_ref) * 111_320 * math.cos(math.radians(self.lat_ref))
        dy = (lat - self.lat_ref) * 110_540
        col = int(dx // self.grid_size)
        row = int(dy // self.grid_size)
        return (row, col)

    # ── Update ────────────────────────────────────────────
    def update(
        self,
        vehicle_id: str,
        lat: float,
        lon: float,
        risk_score: float,
    ):
        """Update a cell with a vehicle's risk contribution."""
        cell = self._latlon_to_cell(lat, lon)
        entry = self._grid[cell]
        entry["score"] = min(1.0, entry["score"] + risk_score * 0.3)
        entry["updated_at"] = time.time()
        entry["vehicles"].add(vehicle_id)

    # ── Query ─────────────────────────────────────────────
    def get_risk_at(self, lat: float, lon: float) -> float:
        """Get the current decayed risk score at a location."""
        cell = self._latlon_to_cell(lat, lon)
        if cell not in self._grid:
            return 0.0
        entry = self._grid[cell]
        elapsed = time.time() - entry["updated_at"]
        decayed = entry["score"] * math.exp(-self.decay_rate * elapsed)
        return round(decayed, 4)

    def get_hotspots(self, threshold: float = 0.3) -> List[Dict[str, Any]]:
        """Return all cells with risk above threshold."""
        now = time.time()
        hotspots = []
        for cell, entry in self._grid.items():
            elapsed = now - entry["updated_at"]
            current = entry["score"] * math.exp(-self.decay_rate * elapsed)
            if current > threshold:
                hotspots.append({
                    "cell": cell,
                    "risk_score": round(current, 4),
                    "vehicles": list(entry["vehicles"]),
                })
        return sorted(hotspots, key=lambda h: h["risk_score"], reverse=True)

    def decay_all(self):
        """Apply decay to all cells and remove dead ones."""
        now = time.time()
        dead = []
        for cell, entry in self._grid.items():
            elapsed = now - entry["updated_at"]
            entry["score"] *= math.exp(-self.decay_rate * elapsed)
            entry["updated_at"] = now
            if entry["score"] < 0.01:
                dead.append(cell)
        for cell in dead:
            del self._grid[cell]

    @property
    def active_cells(self) -> int:
        return len(self._grid)
