"""
SmartV2X-CP Ultra — Edge API Communication Client
===================================================
Secure HTTPS client with JWT authentication, exponential backoff
retry logic, and heartbeat support.
"""

import asyncio
import time
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


class EdgeAPIClient:
    """
    Async HTTP client for OBU ↔ Edge RSU communication.

    Features:
      • JWT bearer-token authentication with auto-refresh
      • Exponential backoff retry on failure
      • Vehicle registration & update endpoints
      • Heartbeat keep-alive
    """

    def __init__(self, config: Dict[str, Any]):
        self.base_url: str = config.get("url", "https://localhost:8000")
        self.api_prefix: str = config.get("api_prefix", "/api")
        self.auth_endpoint: str = config.get("auth_endpoint", "/api/auth/login")
        self.update_endpoint: str = config.get("update_endpoint", "/api/vehicle/update")
        self.register_endpoint: str = config.get("register_endpoint", "/api/vehicle/register")
        self.heartbeat_endpoint: str = config.get("heartbeat_endpoint", "/api/vehicle/heartbeat")
        self.timeout: float = config.get("timeout_sec", 5)
        self.retry_max: int = config.get("retry_max", 3)
        self.retry_backoff: float = config.get("retry_backoff", 1.5)

        self._username: str = config.get("username", "")
        self._password: str = config.get("password", "")
        self._token: Optional[str] = None
        self._token_expiry: float = 0.0
        self._client: Optional[httpx.AsyncClient] = None

    # ── Lifecycle ─────────────────────────────────────────
    async def connect(self):
        """Create HTTP client and authenticate."""
        if not HTTPX_AVAILABLE:
            raise ImportError("httpx is required — pip install httpx")
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            verify=False,  # Set True in production with proper certs
        )
        await self._authenticate()
        logger.info("EdgeAPIClient connected to %s", self.base_url)

    async def close(self):
        if self._client:
            await self._client.aclose()
            logger.info("EdgeAPIClient closed")

    # ── Authentication ────────────────────────────────────
    async def _authenticate(self):
        """Get JWT token from edge server."""
        try:
            resp = await self._client.post(
                self.auth_endpoint,
                json={"username": self._username, "password": self._password},
            )
            resp.raise_for_status()
            data = resp.json()
            self._token = data.get("access_token")
            self._token_expiry = time.time() + data.get("expires_in", 3600)
            logger.info("Authenticated — token expires in %ds", data.get("expires_in", 3600))
        except Exception as exc:
            logger.error("Authentication failed: %s", exc)
            raise

    def _auth_headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self._token}"} if self._token else {}

    async def _ensure_token(self):
        if time.time() > self._token_expiry - 60:
            await self._authenticate()

    # ── Vehicle registration ──────────────────────────────
    async def register_vehicle(self, vehicle_data: Dict[str, Any]) -> Dict:
        """Register this OBU with the edge server."""
        return await self._post_with_retry(self.register_endpoint, vehicle_data)

    # ── Vehicle update ────────────────────────────────────
    async def send_update(self, payload: Dict[str, Any]) -> Dict:
        """Send vehicle state update to edge server."""
        return await self._post_with_retry(self.update_endpoint, payload)

    # ── Heartbeat ─────────────────────────────────────────
    async def send_heartbeat(self, vehicle_id: str) -> bool:
        """Send heartbeat signal."""
        try:
            resp = await self._post_with_retry(
                self.heartbeat_endpoint,
                {"vehicle_id": vehicle_id, "timestamp": time.time()},
            )
            return resp.get("status") == "ok"
        except Exception:
            return False

    # ── Retry logic ───────────────────────────────────────
    async def _post_with_retry(
        self, endpoint: str, payload: Dict[str, Any]
    ) -> Dict:
        """POST with exponential backoff retry."""
        await self._ensure_token()
        last_exc = None

        for attempt in range(1, self.retry_max + 1):
            try:
                resp = await self._client.post(
                    endpoint,
                    json=payload,
                    headers=self._auth_headers(),
                )
                resp.raise_for_status()
                return resp.json()
            except Exception as exc:
                last_exc = exc
                wait = self.retry_backoff ** attempt
                logger.warning(
                    "POST %s attempt %d failed: %s — retry in %.1fs",
                    endpoint, attempt, exc, wait,
                )
                await asyncio.sleep(wait)

        logger.error("POST %s failed after %d attempts", endpoint, self.retry_max)
        raise ConnectionError(
            f"Edge server unreachable after {self.retry_max} retries"
        ) from last_exc
