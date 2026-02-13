"""
SmartV2X-CP Ultra — Vehicle API Routes
========================================
POST /api/vehicle/register — register a new OBU
POST /api/vehicle/update  — receive real-time vehicle update
POST /api/vehicle/heartbeat — heartbeat keep-alive
GET  /api/vehicle/list     — list all active vehicles
"""

import time
import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from fastapi import APIRouter, Depends, HTTPException, status

from edge_rsu.auth.jwt_handler import get_current_user
from edge_rsu.auth.rbac import RoleChecker

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/vehicle", tags=["Vehicle"])

# ── In-memory vehicle store (backed by Redis in production) ──
_vehicles: Dict[str, Dict[str, Any]] = {}


# ── Pydantic schemas ──────────────────────────────────────
class VehicleRegisterRequest(BaseModel):
    vehicle_id: str
    device_name: str = ""
    firmware_version: str = ""

class VehicleUpdateRequest(BaseModel):
    vehicle_id: str
    timestamp: float
    position: Dict[str, float] = Field(default_factory=dict)
    state: Dict[str, float] = Field(default_factory=dict)
    risk: Dict[str, Any] = Field(default_factory=dict)
    trajectory: list = Field(default_factory=list)

class HeartbeatRequest(BaseModel):
    vehicle_id: str
    timestamp: float

class VehicleResponse(BaseModel):
    status: str
    message: str
    data: Optional[Dict] = None


# ── Routes ────────────────────────────────────────────────
@router.post("/register", response_model=VehicleResponse)
async def register_vehicle(
    req: VehicleRegisterRequest,
    user: dict = Depends(get_current_user),
):
    """Register a new OBU device with the edge server."""
    _vehicles[req.vehicle_id] = {
        "vehicle_id": req.vehicle_id,
        "device_name": req.device_name,
        "firmware_version": req.firmware_version,
        "registered_at": time.time(),
        "last_seen": time.time(),
        "status": "online",
        "position": {},
        "state": {},
        "risk": {"level": "LOW"},
    }
    logger.info("Vehicle registered: %s by %s", req.vehicle_id, user["username"])
    return VehicleResponse(
        status="ok",
        message=f"Vehicle {req.vehicle_id} registered",
        data={"vehicle_id": req.vehicle_id},
    )


@router.post("/update", response_model=VehicleResponse)
async def update_vehicle(
    req: VehicleUpdateRequest,
    user: dict = Depends(get_current_user),
):
    """Receive real-time vehicle state update."""
    if req.vehicle_id not in _vehicles:
        # Auto-register if unknown
        _vehicles[req.vehicle_id] = {
            "vehicle_id": req.vehicle_id,
            "registered_at": time.time(),
            "status": "online",
        }

    _vehicles[req.vehicle_id].update({
        "last_seen": time.time(),
        "position": req.position,
        "state": req.state,
        "risk": req.risk,
        "trajectory": req.trajectory,
        "status": "online",
    })

    # Broadcast via WebSocket (imported lazily to avoid circular imports)
    from edge_rsu.api.websocket import broadcast_vehicle_update
    await broadcast_vehicle_update(req.vehicle_id, _vehicles[req.vehicle_id])

    return VehicleResponse(status="ok", message="Update received")


@router.post("/heartbeat", response_model=VehicleResponse)
async def heartbeat(
    req: HeartbeatRequest,
    user: dict = Depends(get_current_user),
):
    """Heartbeat keep-alive from OBU device."""
    if req.vehicle_id in _vehicles:
        _vehicles[req.vehicle_id]["last_seen"] = time.time()
        _vehicles[req.vehicle_id]["status"] = "online"
    return VehicleResponse(status="ok", message="Heartbeat acknowledged")


@router.get("/list")
async def list_vehicles(user: dict = Depends(get_current_user)):
    """List all registered vehicles and their latest state."""
    # Mark offline vehicles (no heartbeat > 30 s)
    now = time.time()
    for v in _vehicles.values():
        if now - v.get("last_seen", 0) > 30:
            v["status"] = "offline"
    return {"vehicles": list(_vehicles.values()), "count": len(_vehicles)}


def get_vehicles_store() -> Dict[str, Dict[str, Any]]:
    """Expose the vehicle store to other modules."""
    return _vehicles
