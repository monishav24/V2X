"""
SmartV2X-CP Ultra — Health Check Endpoint (Backend)
=====================================================
"""

import time
from fastapi import APIRouter

router = APIRouter(tags=["Health"])
_START_TIME = time.time()


@router.get("/health")
async def health():
    return {
        "service": "SmartV2X-CP Ultra Backend Cloud",
        "status": "healthy",
        "uptime_seconds": round(time.time() - _START_TIME, 1),
        "timestamp": time.time(),
    }
