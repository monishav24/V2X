"""
SmartV2X-CP Ultra — Extended Kalman Filter (EKF)
=================================================
Fuses GPS + IMU + Radar data into a coherent state estimate.

State vector x = [x, y, vx, vy, ax, ay]  (6-dimensional)
"""

import numpy as np
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ExtendedKalmanFilter:
    """
    6-state EKF for vehicle localisation and motion estimation.

    Prediction uses a constant-acceleration model.
    Update supports GPS (position), IMU (acceleration), and
    radar (range) measurement sources.
    """

    def __init__(self, config: Dict[str, Any]):
        self.dt = 0.1  # default time-step (overridden per call)

        # ── State vector & covariance ─────────────────────
        self.x = np.zeros(6)                               # [x, y, vx, vy, ax, ay]
        self.P = np.eye(6) * 10.0                          # initial uncertainty

        # ── Process noise ─────────────────────────────────
        q = config.get("process_noise", 0.1)
        self.Q = np.eye(6) * q
        self.Q[4, 4] = q * 2  # acceleration is noisier
        self.Q[5, 5] = q * 2

        # ── Measurement noise per sensor ──────────────────
        self.R_gps = np.eye(2) * config.get("measurement_noise_gps", 1.0)
        self.R_imu = np.eye(2) * config.get("measurement_noise_imu", 0.5)
        self.R_radar = np.eye(1) * 2.0

        self._initialised = False
        logger.info("EKF initialised — state_dim=6, dt=%.3f", self.dt)

    # ── Public API ────────────────────────────────────────
    def predict(self, dt: Optional[float] = None) -> np.ndarray:
        """Time-update (prediction) step."""
        if dt is not None:
            self.dt = dt
        F = self._state_transition()
        self.x = F @ self.x
        self.P = F @ self.P @ F.T + self.Q
        return self.x.copy()

    def update_gps(self, lat: float, lon: float) -> np.ndarray:
        """Measurement-update with GPS position (x, y proxy)."""
        # Convert lat/lon to local x, y (simplified flat-earth)
        x_m, y_m = self._latlon_to_metres(lat, lon)
        z = np.array([x_m, y_m])
        H = np.zeros((2, 6))
        H[0, 0] = 1.0  # observe x
        H[1, 1] = 1.0  # observe y
        self._ekf_update(z, H, self.R_gps)
        if not self._initialised:
            self.x[0], self.x[1] = x_m, y_m
            self._initialised = True
        return self.x.copy()

    def update_imu(self, ax: float, ay: float) -> np.ndarray:
        """Measurement-update with IMU acceleration."""
        z = np.array([ax, ay])
        H = np.zeros((2, 6))
        H[0, 4] = 1.0  # observe ax
        H[1, 5] = 1.0  # observe ay
        self._ekf_update(z, H, self.R_imu)
        return self.x.copy()

    def update_radar(self, distance: float) -> np.ndarray:
        """Measurement-update with radar range (distance from origin)."""
        z = np.array([distance])
        # h(x) = sqrt(x^2 + y^2) — nonlinear, so we linearise
        px, py = self.x[0], self.x[1]
        r = max(np.sqrt(px**2 + py**2), 1e-6)
        H = np.zeros((1, 6))
        H[0, 0] = px / r
        H[0, 1] = py / r
        self._ekf_update(z, H, self.R_radar)
        return self.x.copy()

    def get_state(self) -> Dict[str, float]:
        """Return the current state as a readable dict."""
        return {
            "x": float(self.x[0]),
            "y": float(self.x[1]),
            "vx": float(self.x[2]),
            "vy": float(self.x[3]),
            "ax": float(self.x[4]),
            "ay": float(self.x[5]),
            "speed": float(np.sqrt(self.x[2]**2 + self.x[3]**2)),
        }

    # ── Private helpers ───────────────────────────────────
    def _state_transition(self) -> np.ndarray:
        """Constant-acceleration state transition matrix F."""
        dt = self.dt
        F = np.eye(6)
        F[0, 2] = dt        # x  += vx * dt
        F[1, 3] = dt        # y  += vy * dt
        F[0, 4] = 0.5 * dt**2
        F[1, 5] = 0.5 * dt**2
        F[2, 4] = dt        # vx += ax * dt
        F[3, 5] = dt        # vy += ay * dt
        return F

    def _ekf_update(self, z: np.ndarray, H: np.ndarray, R: np.ndarray):
        """Standard Kalman update: innovation → gain → correct."""
        y = z - H @ self.x                              # innovation
        S = H @ self.P @ H.T + R                        # innovation covariance
        try:
            K = self.P @ H.T @ np.linalg.inv(S)         # Kalman gain
        except np.linalg.LinAlgError:
            logger.warning("EKF update: singular S matrix, skipping")
            return
        self.x = self.x + K @ y
        I = np.eye(self.P.shape[0])
        self.P = (I - K @ H) @ self.P

    # ── Coordinate helpers ────────────────────────────────
    _REF_LAT: float = 28.6139
    _REF_LON: float = 77.2090

    @classmethod
    def _latlon_to_metres(cls, lat: float, lon: float):
        """Flat-earth conversion relative to a reference point."""
        dx = (lon - cls._REF_LON) * 111_320 * np.cos(np.radians(cls._REF_LAT))
        dy = (lat - cls._REF_LAT) * 110_540
        return dx, dy
