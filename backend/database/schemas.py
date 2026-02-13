"""Backend Pydantic Schemas"""
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class VehicleSchema(BaseModel):
    vehicle_id: str
    device_name: str = ""
    firmware_version: str = ""
    city: str = ""
    tenant_id: str = "default"


class CollisionEventSchema(BaseModel):
    vehicle_a: str
    vehicle_b: Optional[str] = None
    risk_level: str
    risk_score: float = 0.0
    ttc_seconds: Optional[float] = None
    distance_m: Optional[float] = None
    city: str = ""
    tenant_id: str = "default"
