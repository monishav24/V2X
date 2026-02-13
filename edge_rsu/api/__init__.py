# SmartV2X-CP Ultra — API Routes Package
from .routes_vehicle import router as vehicle_router
from .routes_health import router as health_router
from .websocket import router as ws_router

__all__ = ["vehicle_router", "health_router", "ws_router"]
