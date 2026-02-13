"""
SmartV2X-CP Ultra — Pydantic Schemas for API Validation
=========================================================
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class PositionSchema(BaseModel):
    latitude: float = 0.0
    longitude: float = 0.0


class VehicleStateSchema(BaseModel):
    x: float = 0.0
    y: float = 0.0
    vx: float = 0.0
    vy: float = 0.0
    ax: float = 0.0
    ay: float = 0.0
    speed: float = 0.0


class RiskSchema(BaseModel):
    level: str = "LOW"
    ttc: Optional[float] = None
    min_distance: Optional[float] = None


class VehicleUpdateSchema(BaseModel):
    vehicle_id: str
    timestamp: float
    position: PositionSchema = Field(default_factory=PositionSchema)
    state: VehicleStateSchema = Field(default_factory=VehicleStateSchema)
    risk: RiskSchema = Field(default_factory=RiskSchema)
    trajectory: List[Dict[str, float]] = Field(default_factory=list)


class CollisionEventSchema(BaseModel):
    vehicle_a: str
    vehicle_b: Optional[str] = None
    risk_level: str
    risk_score: float = 0.0
    ttc_seconds: Optional[float] = None
    distance_m: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    details: str = ""
