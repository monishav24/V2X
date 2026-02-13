"""
SmartV2X-CP Ultra — Collision Risk Assessment Module
=====================================================
Computes Time-to-Collision (TTC), detects trajectory intersections,
and classifies risk as LOW / MEDIUM / HIGH.
"""

import math
import logging
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


@dataclass
class CollisionAssessment:
    """Result of a single collision risk evaluation."""
    risk_level: RiskLevel
    ttc_seconds: Optional[float]              # None if no collision path
    min_distance_m: float
    intersection_point: Optional[Tuple[float, float]]
    details: str


class CollisionRiskAssessor:
    """
    Evaluates collision risk by analysing predicted trajectories
    against nearby vehicle trajectories or static obstacles.
    """

    def __init__(self, config: Dict[str, Any]):
        self.ttc_high = config.get("ttc_threshold_high", 2.0)
        self.ttc_medium = config.get("ttc_threshold_medium", 5.0)
        self.min_dist_alert = config.get("min_distance_alert_m", 10.0)
        logger.info(
            "CollisionRiskAssessor — TTC thresholds: HIGH<%.1fs, MEDIUM<%.1fs",
            self.ttc_high, self.ttc_medium,
        )

    # ── Public API ────────────────────────────────────────
    def assess(
        self,
        ego_trajectory: List[Dict[str, float]],
        other_trajectories: List[List[Dict[str, float]]],
        dt: float = 0.1,
    ) -> CollisionAssessment:
        """
        Assess collision risk of the ego vehicle against all others.

        Parameters
        ----------
        ego_trajectory : list of {x, y} waypoints
        other_trajectories : list of trajectories from nearby vehicles
        dt : time step between consecutive waypoints (seconds)

        Returns
        -------
        CollisionAssessment with combined worst-case risk.
        """
        worst = CollisionAssessment(
            risk_level=RiskLevel.LOW,
            ttc_seconds=None,
            min_distance_m=float("inf"),
            intersection_point=None,
            details="No collision risk detected",
        )

        for idx, other_traj in enumerate(other_trajectories):
            result = self._evaluate_pair(ego_trajectory, other_traj, dt)
            if result.min_distance_m < worst.min_distance_m:
                worst = result
                worst.details = f"Closest threat: vehicle #{idx}"

        return worst

    def assess_radar(
        self,
        distance_m: float,
        relative_velocity: float,
    ) -> CollisionAssessment:
        """Quick risk check based on radar distance & closure rate."""
        ttc = None
        if relative_velocity < -0.1:  # approaching
            ttc = abs(distance_m / relative_velocity)

        risk = self._classify_ttc(ttc, distance_m)
        return CollisionAssessment(
            risk_level=risk,
            ttc_seconds=ttc,
            min_distance_m=distance_m,
            intersection_point=None,
            details=f"Radar: dist={distance_m:.1f}m, TTC={ttc:.1f}s" if ttc else "No approach",
        )

    # ── Core algorithms ───────────────────────────────────
    def _evaluate_pair(
        self,
        traj_a: List[Dict[str, float]],
        traj_b: List[Dict[str, float]],
        dt: float,
    ) -> CollisionAssessment:
        """Evaluate risk between two trajectories."""
        min_dist = float("inf")
        ttc = None
        intersection = None
        n = min(len(traj_a), len(traj_b))

        for i in range(n):
            dist = self._distance(traj_a[i], traj_b[i])
            if dist < min_dist:
                min_dist = dist
                if dist < self.min_dist_alert and ttc is None:
                    ttc = i * dt
                    intersection = (
                        (traj_a[i]["x"] + traj_b[i]["x"]) / 2,
                        (traj_a[i]["y"] + traj_b[i]["y"]) / 2,
                    )

        # Check segment intersection for more precise detection
        for i in range(n - 1):
            pt = self._segment_intersection(
                traj_a[i], traj_a[i + 1],
                traj_b[i], traj_b[i + 1],
            )
            if pt is not None:
                t = i * dt
                if ttc is None or t < ttc:
                    ttc = t
                    intersection = pt

        risk = self._classify_ttc(ttc, min_dist)
        return CollisionAssessment(
            risk_level=risk,
            ttc_seconds=ttc,
            min_distance_m=min_dist,
            intersection_point=intersection,
            details="",
        )

    def _classify_ttc(
        self, ttc: Optional[float], min_dist: float
    ) -> RiskLevel:
        """Classify risk based on TTC and minimum distance."""
        if ttc is not None:
            if ttc <= self.ttc_high:
                return RiskLevel.HIGH
            if ttc <= self.ttc_medium:
                return RiskLevel.MEDIUM
        if min_dist < self.min_dist_alert:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW

    # ── Geometry helpers ──────────────────────────────────
    @staticmethod
    def _distance(a: Dict[str, float], b: Dict[str, float]) -> float:
        return math.sqrt((a["x"] - b["x"])**2 + (a["y"] - b["y"])**2)

    @staticmethod
    def _segment_intersection(
        p1: Dict[str, float], p2: Dict[str, float],
        p3: Dict[str, float], p4: Dict[str, float],
    ) -> Optional[Tuple[float, float]]:
        """
        Check if line segment (p1→p2) intersects (p3→p4).
        Returns intersection point or None.
        """
        x1, y1 = p1["x"], p1["y"]
        x2, y2 = p2["x"], p2["y"]
        x3, y3 = p3["x"], p3["y"]
        x4, y4 = p4["x"], p4["y"]

        denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if abs(denom) < 1e-10:
            return None

        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
        u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom

        if 0 <= t <= 1 and 0 <= u <= 1:
            ix = x1 + t * (x2 - x1)
            iy = y1 + t * (y2 - y1)
            return (ix, iy)
        return None

    # ── Time-to-Collision (constant velocity) ─────────────
    @staticmethod
    def compute_ttc(
        pos_ego: Tuple[float, float],
        vel_ego: Tuple[float, float],
        pos_other: Tuple[float, float],
        vel_other: Tuple[float, float],
        radius: float = 3.0,
    ) -> Optional[float]:
        """
        Analytical TTC between two circular objects.
        Returns None if no collision on current headings.
        """
        dx = pos_other[0] - pos_ego[0]
        dy = pos_other[1] - pos_ego[1]
        dvx = vel_other[0] - vel_ego[0]
        dvy = vel_other[1] - vel_ego[1]

        a = dvx**2 + dvy**2
        if a < 1e-10:
            return None
        b = 2 * (dx * dvx + dy * dvy)
        c = dx**2 + dy**2 - (2 * radius)**2

        disc = b**2 - 4 * a * c
        if disc < 0:
            return None

        sqrt_disc = math.sqrt(disc)
        t1 = (-b - sqrt_disc) / (2 * a)
        t2 = (-b + sqrt_disc) / (2 * a)

        # Return earliest positive time
        for t in sorted([t1, t2]):
            if t > 0:
                return t
        return None
