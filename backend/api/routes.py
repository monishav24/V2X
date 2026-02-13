"""
SmartV2X-CP Ultra — Backend API Routes
========================================
Cloud-level analytics, collision history, and vehicle management.
"""

import time
import logging
from typing import Optional
from pydantic import BaseModel, Field

from fastapi import APIRouter, Depends

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Backend API"])

# ── In-memory stores (production would use DB queries) ────
_collision_history = []
_registered_vehicles = {}


class VehicleRegisterRequest(BaseModel):
    vehicle_id: str
    device_name: str = ""
    firmware_version: str = ""
    city: str = ""
    tenant_id: str = "default"

class VehicleUpdateRequest(BaseModel):
    vehicle_id: str
    timestamp: float
    position: dict = Field(default_factory=dict)
    state: dict = Field(default_factory=dict)
    risk: dict = Field(default_factory=dict)


@router.get("/analytics")
async def analytics():
    """Analytics summary across all vehicles and events."""
    risk_dist = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}
    for v in _registered_vehicles.values():
        level = v.get("risk", {}).get("level", "LOW")
        risk_dist[level] = risk_dist.get(level, 0) + 1

    return {
        "total_vehicles": len(_registered_vehicles),
        "total_collision_events": len(_collision_history),
        "risk_distribution": risk_dist,
        "cities": list(set(v.get("city", "unknown") for v in _registered_vehicles.values())),
        "timestamp": time.time(),
    }


@router.get("/collision-history")
async def collision_history(limit: int = 100, offset: int = 0):
    """Paginated collision event history."""
    events = _collision_history[offset:offset + limit]
    return {
        "events": events,
        "total": len(_collision_history),
        "limit": limit,
        "offset": offset,
    }


@router.post("/vehicle/register")
async def register_vehicle(req: VehicleRegisterRequest):
    """Register a vehicle in the cloud database."""
    _registered_vehicles[req.vehicle_id] = {
        "vehicle_id": req.vehicle_id,
        "device_name": req.device_name,
        "firmware_version": req.firmware_version,
        "city": req.city,
        "tenant_id": req.tenant_id,
        "registered_at": time.time(),
        "last_seen": time.time(),
        "risk": {"level": "LOW"},
    }
    logger.info("Cloud: Vehicle registered — %s (city=%s)", req.vehicle_id, req.city)
    return {"status": "ok", "message": f"Vehicle {req.vehicle_id} registered in cloud"}


@router.post("/vehicle/update")
async def update_vehicle(req: VehicleUpdateRequest):
    """Receive vehicle state update from edge server."""
    if req.vehicle_id in _registered_vehicles:
        _registered_vehicles[req.vehicle_id].update({
            "position": req.position,
            "state": req.state,
            "risk": req.risk,
            "last_seen": time.time(),
        })

    # Log high-risk events
    if req.risk.get("level") == "HIGH":
        _collision_history.append({
            "vehicle_id": req.vehicle_id,
            "risk": req.risk,
            "position": req.position,
            "timestamp": time.time(),
        })

    return {"status": "ok"}
