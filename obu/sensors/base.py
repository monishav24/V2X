"""
SmartV2X-CP Ultra — Hardware Abstraction Layer (HAL)
====================================================
Abstract base class for all sensor drivers. Provides a uniform
interface so sensors can be swapped without changing upstream code.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
import time
import logging

logger = logging.getLogger(__name__)


@dataclass
class SensorReading:
    """Standardised container for a single sensor reading."""
    timestamp: float                          # Unix epoch seconds
    sensor_type: str                          # "gps", "imu", "radar", "camera"
    data: Dict[str, Any] = field(default_factory=dict)
    quality: float = 1.0                      # 0.0 – 1.0 confidence score
    raw: Optional[bytes] = None               # Optional raw bytes


class SensorBase(ABC):
    """
    Abstract sensor interface.

    Every concrete sensor driver MUST implement:
      • connect()     — open hardware port / simulation
      • read()        — return a SensorReading
      • calibrate()   — run calibration routine
      • close()       — release resources

    The class provides a thin wrapper (safe_read) that catches
    hardware errors and returns None instead of crashing the loop.
    """

    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.is_connected = False
        self.is_simulation = config.get("simulation", True)
        self._last_reading: Optional[SensorReading] = None
        logger.info(
            "Sensor [%s] initialised (simulation=%s)", name, self.is_simulation
        )

    # ── Abstract methods ──────────────────────────────────
    @abstractmethod
    def connect(self) -> bool:
        """Open the hardware connection. Return True on success."""
        ...

    @abstractmethod
    def read(self) -> SensorReading:
        """Return the latest sensor reading."""
        ...

    @abstractmethod
    def calibrate(self) -> bool:
        """Execute sensor-specific calibration. Return True on success."""
        ...

    @abstractmethod
    def close(self) -> None:
        """Release hardware resources."""
        ...

    # ── Convenience helpers ───────────────────────────────
    def safe_read(self) -> Optional[SensorReading]:
        """Read with automatic error handling — never raises."""
        try:
            reading = self.read()
            self._last_reading = reading
            return reading
        except Exception as exc:
            logger.error("Sensor [%s] read error: %s", self.name, exc)
            return None

    @property
    def last_reading(self) -> Optional[SensorReading]:
        return self._last_reading

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} name={self.name} "
            f"connected={self.is_connected} sim={self.is_simulation}>"
        )
