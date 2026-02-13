"""
SmartV2X-CP Ultra — Unique Vehicle ID Generator
==================================================
Generates unique, deterministic Vehicle IDs from hardware
characteristics (MAC address, serial number).
"""

import uuid
import hashlib
import platform
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def generate_vehicle_id(
    mac_address: Optional[str] = None,
    serial_number: Optional[str] = None,
    prefix: str = "V2X",
) -> str:
    """
    Generate a unique vehicle ID.

    Uses MAC address and serial number for deterministic IDs
    (same hardware → same ID). Falls back to UUID4 if no
    hardware info is available.
    """
    if mac_address or serial_number:
        # Deterministic: hash of hardware attributes
        seed = f"{mac_address or ''}-{serial_number or ''}-smartv2x"
        hash_digest = hashlib.sha256(seed.encode()).hexdigest()[:12].upper()
        vehicle_id = f"{prefix}-{hash_digest[:4]}-{hash_digest[4:8]}-{hash_digest[8:12]}"
    else:
        # Random UUID-based
        uid = uuid.uuid4().hex[:12].upper()
        vehicle_id = f"{prefix}-{uid[:4]}-{uid[4:8]}-{uid[8:12]}"

    logger.info("Generated Vehicle ID: %s", vehicle_id)
    return vehicle_id


def get_system_mac() -> str:
    """Get the MAC address of the current system."""
    mac_int = uuid.getnode()
    mac_str = ':'.join(
        f'{(mac_int >> (8 * (5 - i))) & 0xFF:02x}' for i in range(6)
    )
    return mac_str


def get_device_fingerprint() -> dict:
    """Collect device hardware fingerprint."""
    return {
        "mac_address": get_system_mac(),
        "platform": platform.system(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "node": platform.node(),
    }


if __name__ == "__main__":
    fp = get_device_fingerprint()
    print(f"Device Fingerprint: {fp}")
    vid = generate_vehicle_id(mac_address=fp["mac_address"])
    print(f"Vehicle ID: {vid}")
