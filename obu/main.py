"""
SmartV2X-CP Ultra — OBU Main Entry Point
==========================================
Orchestrates the full vehicle pipeline:
  Sensor read → EKF fusion → Trajectory prediction
  → Collision risk → Send to Edge RSU

Usage:
  python -m obu.main                 # normal mode
  python -m obu.main --simulate      # all sensors in simulation mode
"""

import asyncio
import argparse
import logging
import os
import sys
import time
import yaml
from typing import Dict, Any

# ── Local imports ─────────────────────────────────────────
from obu.sensors import GPSSensor, IMUSensor, RadarSensor
from obu.fusion import ExtendedKalmanFilter
from obu.prediction import TrajectoryPredictor
from obu.collision import CollisionRiskAssessor
from obu.communication import EdgeAPIClient

# ── Logging setup ─────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("obu.main")


def load_config(path: str = "obu/config.yaml") -> Dict[str, Any]:
    """Load YAML configuration file."""
    if not os.path.exists(path):
        logger.error("Config file not found: %s", path)
        sys.exit(1)
    with open(path, "r") as f:
        return yaml.safe_load(f)


async def main_loop(config: Dict[str, Any]):
    """Core OBU processing loop."""
    # ── Initialise components ─────────────────────────────
    gps = GPSSensor(config["sensors"]["gps"])
    imu = IMUSensor(config["sensors"]["imu"])
    radar = RadarSensor(config["sensors"]["radar"])
    ekf = ExtendedKalmanFilter(config["fusion"])
    predictor = TrajectoryPredictor(config["prediction"])
    risk_assessor = CollisionRiskAssessor(config["collision"])
    api_client = EdgeAPIClient(config["edge_server"])

    # Connect sensors
    for sensor in [gps, imu, radar]:
        if not sensor.connect():
            logger.error("Failed to connect %s — aborting", sensor.name)
            return

    # Connect to edge server
    try:
        await api_client.connect()
    except Exception as exc:
        logger.warning("Edge server unavailable: %s — running offline", exc)

    vehicle_id = config["device"].get("vehicle_id", "OBU-SIM-001")
    interval = config["loop"]["interval_ms"] / 1000.0
    logger.info("═══ OBU %s starting main loop (%.0f Hz) ═══", vehicle_id, 1 / interval)

    cycle = 0
    try:
        while True:
            t0 = time.time()
            cycle += 1

            # ① Read sensors
            gps_data = gps.safe_read()
            imu_data = imu.safe_read()
            radar_data = radar.safe_read()

            # ② EKF fusion
            ekf.predict(dt=interval)
            if gps_data:
                ekf.update_gps(
                    gps_data.data["latitude"],
                    gps_data.data["longitude"],
                )
            if imu_data:
                ekf.update_imu(
                    imu_data.data["accel_x"],
                    imu_data.data["accel_y"],
                )
            if radar_data:
                ekf.update_radar(radar_data.data["distance_m"])

            state = ekf.get_state()

            # ③ Trajectory prediction
            predictor.push_state(state)
            trajectory = predictor.predict()

            # ④ Collision risk assessment
            risk_result = None
            if trajectory:
                risk_result = risk_assessor.assess(trajectory, [])

            if radar_data:
                radar_risk = risk_assessor.assess_radar(
                    radar_data.data["distance_m"],
                    radar_data.data.get("relative_velocity_mps", 0),
                )
                if risk_result is None or radar_risk.risk_level.value > (
                    risk_result.risk_level.value if risk_result else ""
                ):
                    risk_result = radar_risk

            # ⑤ Send to edge server
            payload = {
                "vehicle_id": vehicle_id,
                "timestamp": time.time(),
                "position": {
                    "latitude": gps_data.data["latitude"] if gps_data else 0,
                    "longitude": gps_data.data["longitude"] if gps_data else 0,
                },
                "state": state,
                "risk": {
                    "level": risk_result.risk_level.value if risk_result else "LOW",
                    "ttc": risk_result.ttc_seconds if risk_result else None,
                    "min_distance": risk_result.min_distance_m if risk_result else None,
                },
                "trajectory": trajectory[:10] if trajectory else [],
            }

            try:
                await api_client.send_update(payload)
            except Exception as exc:
                if cycle % 50 == 0:
                    logger.warning("Edge send failed: %s", exc)

            # ⑥ Log periodically
            if cycle % 10 == 0:
                risk_str = risk_result.risk_level.value if risk_result else "N/A"
                logger.info(
                    "Cycle %d | pos=(%.4f, %.4f) | speed=%.2f m/s | risk=%s",
                    cycle,
                    state["x"], state["y"],
                    state["speed"],
                    risk_str,
                )

            # ⑦ Heartbeat every 100 cycles
            if cycle % 100 == 0:
                await api_client.send_heartbeat(vehicle_id)

            # Sleep to maintain loop rate
            elapsed = time.time() - t0
            sleep_time = max(0, interval - elapsed)
            await asyncio.sleep(sleep_time)

    except KeyboardInterrupt:
        logger.info("OBU shutting down …")
    finally:
        gps.close()
        imu.close()
        radar.close()
        await api_client.close()


def cli():
    parser = argparse.ArgumentParser(description="SmartV2X-CP Ultra OBU")
    parser.add_argument("--config", default="obu/config.yaml", help="Config file path")
    parser.add_argument("--simulate", action="store_true", help="Force simulation mode")
    args = parser.parse_args()

    config = load_config(args.config)

    if args.simulate:
        for sensor_cfg in config["sensors"].values():
            if isinstance(sensor_cfg, dict):
                sensor_cfg["simulation"] = True
        logger.info("All sensors forced to SIMULATION mode")

    asyncio.run(main_loop(config))


if __name__ == "__main__":
    cli()
