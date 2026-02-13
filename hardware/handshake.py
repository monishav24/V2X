"""
SmartV2X-CP Ultra — Device Handshake Protocol
================================================
Challenge-response handshake for authenticating OBU hardware
devices with the edge server.
"""

import hashlib
import hmac
import secrets
import time
import logging
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class DeviceHandshake:
    """
    Challenge-response handshake protocol.

    Flow:
      1. Device → Server: HELLO {device_id, firmware_version}
      2. Server → Device: CHALLENGE {nonce}
      3. Device → Server: RESPONSE {HMAC(nonce, shared_secret)}
      4. Server → Device: AUTH_OK {api_token} or AUTH_FAIL

    Shared secret is pre-provisioned per device.
    """

    def __init__(self, shared_secret: str = "default-shared-secret"):
        self._secret = shared_secret.encode()
        self._pending_challenges: Dict[str, Tuple[str, float]] = {}

    # ── Server-side methods ───────────────────────────────
    def generate_challenge(self, device_id: str) -> str:
        """Generate a random nonce challenge for a device."""
        nonce = secrets.token_hex(32)
        self._pending_challenges[device_id] = (nonce, time.time())
        logger.info("Challenge generated for device %s", device_id)
        return nonce

    def verify_response(self, device_id: str, response_hmac: str) -> bool:
        """Verify the HMAC response from a device."""
        if device_id not in self._pending_challenges:
            logger.warning("No pending challenge for device %s", device_id)
            return False

        nonce, timestamp = self._pending_challenges.pop(device_id)

        # Challenge expires after 30 seconds
        if time.time() - timestamp > 30:
            logger.warning("Challenge expired for device %s", device_id)
            return False

        expected = hmac.new(self._secret, nonce.encode(), hashlib.sha256).hexdigest()
        if hmac.compare_digest(expected, response_hmac):
            logger.info("Device %s authenticated successfully", device_id)
            return True
        else:
            logger.warning("HMAC mismatch for device %s", device_id)
            return False

    # ── Device-side methods ───────────────────────────────
    def compute_response(self, nonce: str) -> str:
        """Compute HMAC response for a given challenge nonce."""
        return hmac.new(self._secret, nonce.encode(), hashlib.sha256).hexdigest()


def perform_handshake_demo():
    """Demonstrate the handshake flow."""
    hs = DeviceHandshake(shared_secret="my-device-secret-2024")
    device_id = "OBU-001"

    # Step 1-2: Server generates challenge
    nonce = hs.generate_challenge(device_id)
    print(f"[Server] Challenge: {nonce[:16]}...")

    # Step 3: Device computes response
    response = hs.compute_response(nonce)
    print(f"[Device] Response: {response[:16]}...")

    # Step 4: Server verifies
    ok = hs.verify_response(device_id, response)
    print(f"[Server] Auth result: {'✓ OK' if ok else '✗ FAIL'}")


if __name__ == "__main__":
    perform_handshake_demo()
