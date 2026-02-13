"""
SmartV2X-CP Ultra — WebSocket Real-Time Broadcast
===================================================
Manages connected dashboard clients and broadcasts vehicle
updates and collision alerts in real-time.
"""

import json
import time
import logging
from typing import Dict, Any, List

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)
router = APIRouter(tags=["WebSocket"])

# ── Connection manager ────────────────────────────────────
class ConnectionManager:
    """Manage active WebSocket connections."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(
            "WebSocket client connected (total: %d)", len(self.active_connections)
        )

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(
            "WebSocket client disconnected (total: %d)", len(self.active_connections)
        )

    async def broadcast(self, message: dict):
        """Send message to all connected clients."""
        dead = []
        data = json.dumps(message)
        for conn in self.active_connections:
            try:
                await conn.send_text(data)
            except Exception:
                dead.append(conn)
        for conn in dead:
            self.disconnect(conn)


manager = ConnectionManager()


# ── WebSocket endpoint ────────────────────────────────────
@router.websocket("/ws/live")
async def websocket_live(websocket: WebSocket):
    """
    Real-time live feed for the dashboard.
    Sends vehicle updates and alert events.
    """
    await manager.connect(websocket)
    try:
        while True:
            # Keep alive — optionally receive client messages
            data = await websocket.receive_text()
            # Echo or handle client commands if needed
            logger.debug("WS received: %s", data[:100])
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as exc:
        logger.error("WebSocket error: %s", exc)
        manager.disconnect(websocket)


# ── Broadcast helpers (called from routes) ────────────────
async def broadcast_vehicle_update(vehicle_id: str, vehicle_data: Dict[str, Any]):
    """Broadcast a vehicle state update to all connected dashboards."""
    await manager.broadcast({
        "type": "vehicle_update",
        "vehicle_id": vehicle_id,
        "data": {
            "position": vehicle_data.get("position", {}),
            "state": vehicle_data.get("state", {}),
            "risk": vehicle_data.get("risk", {}),
            "status": vehicle_data.get("status", "unknown"),
            "last_seen": vehicle_data.get("last_seen", 0),
        },
        "timestamp": time.time(),
    })


async def broadcast_alert(alert_data: Dict[str, Any]):
    """Broadcast a collision/risk alert."""
    await manager.broadcast({
        "type": "alert",
        "data": alert_data,
        "timestamp": time.time(),
    })
