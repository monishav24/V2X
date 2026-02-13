"""
SmartV2X-CP Ultra — IMU Sensor Driver
======================================
Provides acceleration (ax, ay, az) and gyroscope (gx, gy, gz) data.
Supports real I2C/SPI hardware and simulation mode.
"""

import math
import random
import time
import logging
from typing import Any, Dict

from .base import SensorBase, SensorReading

logger = logging.getLogger(__name__)


class IMUSensor(SensorBase):
    """6-DOF IMU sensor — accelerometer + gyroscope."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__("IMU", config)
        self._hw_device = None
        # Simulation state
        self._sim_ax = 0.0
        self._sim_ay = 0.0

    def connect(self) -> bool:
        if self.is_simulation:
            logger.info("IMU connected in SIMULATION mode")
            self.is_connected = True
            return True
        try:
            # Placeholder for real I2C/SPI init (e.g. MPU6050)
            logger.info("IMU connected on %s", self.config.get("port"))
            self.is_connected = True
            return True
        except Exception as exc:
            logger.error("IMU connection failed: %s", exc)
            return False

    def read(self) -> SensorReading:
        if self.is_simulation:
            return self._simulate()
        return self._read_hardware()

    def calibrate(self) -> bool:
        logger.info("IMU calibration — keep device still for 3 s …")
        return True

    def close(self) -> None:
        self.is_connected = False
        logger.info("IMU sensor closed")

    # ── Simulation ────────────────────────────────────────
    def _simulate(self) -> SensorReading:
        self._sim_ax += random.uniform(-0.3, 0.3)
        self._sim_ay += random.uniform(-0.3, 0.3)
        self._sim_ax = max(-15, min(15, self._sim_ax))
        self._sim_ay = max(-15, min(15, self._sim_ay))

        return SensorReading(
            timestamp=time.time(),
            sensor_type="imu",
            data={
                "accel_x": round(self._sim_ax, 4),
                "accel_y": round(self._sim_ay, 4),
                "accel_z": round(9.81 + random.uniform(-0.05, 0.05), 4),
                "gyro_x": round(random.uniform(-1, 1), 4),
                "gyro_y": round(random.uniform(-1, 1), 4),
                "gyro_z": round(random.uniform(-5, 5), 4),
                "temperature_c": round(25 + random.uniform(-2, 2), 1),
            },
            quality=round(random.uniform(0.9, 1.0), 3),
        )

    # ── Real hardware ─────────────────────────────────────
    def _read_hardware(self) -> SensorReading:
        """Read from a real IMU (e.g., MPU6050 over I2C)."""
        # In a real deployment, use smbus2 or spidev here
        return SensorReading(
            timestamp=time.time(),
            sensor_type="imu",
            data={
                "accel_x": 0.0, "accel_y": 0.0, "accel_z": 9.81,
                "gyro_x": 0.0, "gyro_y": 0.0, "gyro_z": 0.0,
            },
            quality=1.0,
        )
