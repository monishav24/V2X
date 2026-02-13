"""
SmartV2X-CP Ultra — GPS Sensor Driver
======================================
Supports both real serial GPS (NMEA) and simulation mode.
"""

import math
import random
import time
import logging
from typing import Any, Dict, Optional

from .base import SensorBase, SensorReading

logger = logging.getLogger(__name__)


class GPSSensor(SensorBase):
    """GPS sensor — provides latitude, longitude, speed, heading."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__("GPS", config)
        self._serial_conn = None
        # Simulation state — start near a configurable point
        self._sim_lat = 28.6139       # New Delhi default
        self._sim_lon = 77.2090
        self._sim_speed = 0.0
        self._sim_heading = 0.0

    # ── Interface implementation ──────────────────────────
    def connect(self) -> bool:
        if self.is_simulation:
            logger.info("GPS connected in SIMULATION mode")
            self.is_connected = True
            return True
        try:
            import serial  # type: ignore
            self._serial_conn = serial.Serial(
                port=self.config.get("port", "/dev/ttyUSB0"),
                baudrate=self.config.get("baud_rate", 9600),
                timeout=1,
            )
            self.is_connected = True
            logger.info("GPS connected on %s", self.config["port"])
            return True
        except Exception as exc:
            logger.error("GPS connection failed: %s", exc)
            return False

    def read(self) -> SensorReading:
        if self.is_simulation:
            return self._simulate()
        return self._read_hardware()

    def calibrate(self) -> bool:
        logger.info("GPS calibration — waiting for satellite fix …")
        return True

    def close(self) -> None:
        if self._serial_conn:
            self._serial_conn.close()
        self.is_connected = False
        logger.info("GPS sensor closed")

    # ── Simulation ────────────────────────────────────────
    def _simulate(self) -> SensorReading:
        """Generate realistic GPS movement with small random walk."""
        self._sim_speed = max(0, self._sim_speed + random.uniform(-0.5, 0.6))
        self._sim_heading += random.uniform(-5, 5)
        heading_rad = math.radians(self._sim_heading)
        # Move ~speed m/s converted to degrees
        self._sim_lat += math.cos(heading_rad) * self._sim_speed * 1e-5
        self._sim_lon += math.sin(heading_rad) * self._sim_speed * 1e-5

        return SensorReading(
            timestamp=time.time(),
            sensor_type="gps",
            data={
                "latitude": round(self._sim_lat, 7),
                "longitude": round(self._sim_lon, 7),
                "speed_mps": round(self._sim_speed, 2),
                "heading_deg": round(self._sim_heading % 360, 2),
                "altitude_m": 220.0 + random.uniform(-1, 1),
                "satellites": random.randint(6, 12),
                "hdop": round(random.uniform(0.8, 2.5), 2),
            },
            quality=round(random.uniform(0.85, 1.0), 3),
        )

    # ── Real hardware ─────────────────────────────────────
    def _read_hardware(self) -> SensorReading:
        """Parse NMEA sentences from serial port."""
        line = ""
        if self._serial_conn and self._serial_conn.in_waiting:
            raw = self._serial_conn.readline()
            line = raw.decode("ascii", errors="replace").strip()

        lat, lon, speed, heading = self._parse_nmea(line)

        return SensorReading(
            timestamp=time.time(),
            sensor_type="gps",
            data={
                "latitude": lat,
                "longitude": lon,
                "speed_mps": speed,
                "heading_deg": heading,
            },
            quality=1.0,
            raw=line.encode() if line else None,
        )

    @staticmethod
    def _parse_nmea(sentence: str):
        """Minimal GPRMC parser — returns (lat, lon, speed, heading)."""
        if not sentence.startswith("$GPRMC"):
            return 0.0, 0.0, 0.0, 0.0
        parts = sentence.split(",")
        try:
            lat_raw = float(parts[3])
            lat_dir = parts[4]
            lon_raw = float(parts[5])
            lon_dir = parts[6]
            speed_knots = float(parts[7]) if parts[7] else 0.0
            heading = float(parts[8]) if parts[8] else 0.0

            lat = GPSSensor._nmea_to_decimal(lat_raw, lat_dir)
            lon = GPSSensor._nmea_to_decimal(lon_raw, lon_dir)
            speed_mps = speed_knots * 0.514444
            return lat, lon, speed_mps, heading
        except (IndexError, ValueError):
            return 0.0, 0.0, 0.0, 0.0

    @staticmethod
    def _nmea_to_decimal(raw: float, direction: str) -> float:
        degrees = int(raw / 100)
        minutes = raw - degrees * 100
        decimal = degrees + minutes / 60.0
        if direction in ("S", "W"):
            decimal *= -1
        return round(decimal, 7)
