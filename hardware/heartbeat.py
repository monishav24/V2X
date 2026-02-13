"""
SmartV2X-CP Ultra — Heartbeat & Offline Detection
====================================================
Periodic heartbeat sender (OBU-side) and checker (server-side)
with configurable offline detection threshold.
"""

import asyncio
import time
import logging
from typing import Dict, Optional, Callable

logger = logging.getLogger(__name__)


class HeartbeatSender:
    """OBU-side heartbeat sender."""

    def __init__(
        self,
        vehicle_id: str,
        send_func: Callable,
        interval_sec: float = 10.0,
    ):
        self.vehicle_id = vehicle_id
        self._send = send_func
        self.interval = interval_sec
        self._running = False

    async def start(self):
        """Start sending heartbeats."""
        self._running = True
        logger.info("Heartbeat started for %s (every %.0fs)", self.vehicle_id, self.interval)
        while self._running:
            try:
                await self._send(self.vehicle_id)
                logger.debug("Heartbeat sent: %s", self.vehicle_id)
            except Exception as exc:
                logger.warning("Heartbeat send failed: %s", exc)
            await asyncio.sleep(self.interval)

    def stop(self):
        self._running = False


class HeartbeatChecker:
    """Server-side heartbeat checker for offline detection."""

    def __init__(self, timeout_sec: float = 30.0):
        self.timeout = timeout_sec
        self._last_seen: Dict[str, float] = {}
        self._callbacks: list = []

    def on_offline(self, callback: Callable):
        """Register a callback for when a device goes offline."""
        self._callbacks.append(callback)

    def register_heartbeat(self, vehicle_id: str) -> None:
        """Record a heartbeat from a device."""
        was_offline = (
            vehicle_id in self._last_seen
            and time.time() - self._last_seen[vehicle_id] > self.timeout
        )
        self._last_seen[vehicle_id] = time.time()
        if was_offline:
            logger.info("Device %s came back online", vehicle_id)

    def is_online(self, vehicle_id: str) -> bool:
        """Check if a device is currently online."""
        last = self._last_seen.get(vehicle_id, 0)
        return (time.time() - last) < self.timeout

    def get_offline_devices(self) -> list:
        """Return list of offline device IDs."""
        now = time.time()
        return [
            vid for vid, last in self._last_seen.items()
            if (now - last) > self.timeout
        ]

    async def check_loop(self, interval: float = 10.0):
        """Periodically check for offline devices and fire callbacks."""
        while True:
            offline = self.get_offline_devices()
            for vid in offline:
                for cb in self._callbacks:
                    try:
                        cb(vid)
                    except Exception as exc:
                        logger.error("Offline callback error: %s", exc)
            if offline:
                logger.warning("Offline devices: %s", offline)
            await asyncio.sleep(interval)
