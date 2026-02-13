"""
SmartV2X-CP Ultra — Radar / Distance Sensor Driver
====================================================
Provides range-to-target and relative velocity data.
Supports real UART hardware and simulation mode.
"""

import random
import time
import logging
from typing import Any, Dict

from .base import SensorBase, SensorReading

logger = logging.getLogger(__name__)


class RadarSensor(SensorBase):
    """Radar / ultrasonic distance sensor."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__("Radar", config)
        self._serial_conn = None
        self._max_range = config.get("max_range_m", 200)
        # Simulation state
        self._sim_distance = 100.0

    def connect(self) -> bool:
        if self.is_simulation:
            logger.info("Radar connected in SIMULATION mode")
            self.is_connected = True
            return True
        try:
            import serial  # type: ignore
            self._serial_conn = serial.Serial(
                port=self.config.get("port", "/dev/ttyUSB2"),
                baudrate=self.config.get("baud_rate", 115200),
                timeout=1,
            )
            self.is_connected = True
            logger.info("Radar connected on %s", self.config["port"])
            return True
        except Exception as exc:
            logger.error("Radar connection failed: %s", exc)
            return False

    def read(self) -> SensorReading:
        if self.is_simulation:
            return self._simulate()
        return self._read_hardware()

    def calibrate(self) -> bool:
        logger.info("Radar calibration — point sensor at known distance …")
        return True

    def close(self) -> None:
        if self._serial_conn:
            self._serial_conn.close()
        self.is_connected = False
        logger.info("Radar sensor closed")

    # ── Simulation ────────────────────────────────────────
    def _simulate(self) -> SensorReading:
        self._sim_distance += random.uniform(-5, 4)
        self._sim_distance = max(2, min(self._max_range, self._sim_distance))
        rel_velocity = random.uniform(-2, 2)

        return SensorReading(
            timestamp=time.time(),
            sensor_type="radar",
            data={
                "distance_m": round(self._sim_distance, 2),
                "relative_velocity_mps": round(rel_velocity, 2),
                "signal_strength_db": round(random.uniform(-60, -20), 1),
                "target_detected": self._sim_distance < self._max_range * 0.9,
            },
            quality=round(random.uniform(0.8, 1.0), 3),
        )

    # ── Real hardware ─────────────────────────────────────
    def _read_hardware(self) -> SensorReading:
        """Read from real radar UART. Protocol is device-specific."""
        raw = b""
        if self._serial_conn and self._serial_conn.in_waiting:
            raw = self._serial_conn.readline()
        distance = self._parse_distance(raw)
        return SensorReading(
            timestamp=time.time(),
            sensor_type="radar",
            data={
                "distance_m": distance,
                "relative_velocity_mps": 0.0,
                "target_detected": distance < self._max_range,
            },
            quality=1.0,
            raw=raw or None,
        )

    @staticmethod
    def _parse_distance(raw: bytes) -> float:
        """Parse distance from raw bytes — adapt per radar model."""
        try:
            return float(raw.decode("ascii", errors="replace").strip())
        except (ValueError, AttributeError):
            return 0.0
