"""
SmartV2X-CP Ultra — Risk Aggregation Engine
=============================================
Computes pairwise collision probabilities across all active
vehicles and updates the CP-Map accordingly.
"""

import math
import time
import logging
from typing import Dict, Any, List, Tuple

logger = logging.getLogger(__name__)


class RiskAggregator:
    """
    Aggregates risk across all active vehicles.

    For every pair of vehicles, computes:
      • Euclidean distance
      • Relative velocity
      • Estimated TTC
      • Combined risk score
    """

    def __init__(self, distance_threshold: float = 200.0):
        self.distance_threshold = distance_threshold  # metres
        self._pair_cache: Dict[Tuple[str, str], float] = {}

    def aggregate(
        self,
        vehicles: Dict[str, Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Compute pairwise risk for all active vehicles.

        Returns a list of risk records sorted by severity.
        """
        ids = list(vehicles.keys())
        risks: List[Dict[str, Any]] = []

        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                v1 = vehicles[ids[i]]
                v2 = vehicles[ids[j]]
                record = self._compute_pair_risk(ids[i], v1, ids[j], v2)
                if record:
                    risks.append(record)

        risks.sort(key=lambda r: r["risk_score"], reverse=True)
        return risks

    def _compute_pair_risk(
        self,
        id_a: str, va: Dict[str, Any],
        id_b: str, vb: Dict[str, Any],
    ) -> Dict[str, Any] | None:
        """Compute risk between two vehicles."""
        pos_a = va.get("state", {})
        pos_b = vb.get("state", {})

        xa, ya = pos_a.get("x", 0), pos_a.get("y", 0)
        xb, yb = pos_b.get("x", 0), pos_b.get("y", 0)

        dist = math.sqrt((xa - xb)**2 + (ya - yb)**2)
        if dist > self.distance_threshold:
            return None

        # Relative velocity
        vxa, vya = pos_a.get("vx", 0), pos_a.get("vy", 0)
        vxb, vyb = pos_b.get("vx", 0), pos_b.get("vy", 0)
        rel_speed = math.sqrt((vxa - vxb)**2 + (vya - vyb)**2)

        # Approximate TTC
        ttc = dist / rel_speed if rel_speed > 0.1 else float("inf")

        # Risk score: inversely proportional to TTC and distance
        if ttc < 100:
            risk_score = min(1.0, (1.0 / (ttc + 0.1)) * (1.0 / (dist + 1.0)) * 50)
        else:
            risk_score = 0.0

        # Classify
        if risk_score > 0.7:
            level = "HIGH"
        elif risk_score > 0.3:
            level = "MEDIUM"
        else:
            level = "LOW"

        pair_key = tuple(sorted([id_a, id_b]))
        self._pair_cache[pair_key] = risk_score

        return {
            "vehicle_a": id_a,
            "vehicle_b": id_b,
            "distance_m": round(dist, 2),
            "relative_speed_mps": round(rel_speed, 2),
            "ttc_seconds": round(ttc, 2) if ttc < 1000 else None,
            "risk_score": round(risk_score, 4),
            "risk_level": level,
            "timestamp": time.time(),
        }
