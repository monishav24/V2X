"""
SmartV2X-CP Ultra — JWT Authentication Handler
================================================
Token creation, validation, and FastAPI dependency for extracting
the current user from the Authorization header.
"""

import time
import logging
from typing import Dict, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

from edge_rsu.config import settings

logger = logging.getLogger(__name__)
security_scheme = HTTPBearer()

# ── Demo users (replace with DB in production) ────────────
DEMO_USERS: Dict[str, Dict] = {
    "admin": {
        "password": "admin123",
        "role": "admin",
        "name": "System Administrator",
    },
    "operator": {
        "password": "operator123",
        "role": "operator",
        "name": "Control Room Operator",
    },
    "viewer": {
        "password": "viewer123",
        "role": "viewer",
        "name": "Dashboard Viewer",
    },
    "obu_device": {
        "password": "obu_secret",
        "role": "device",
        "name": "OBU Device",
    },
}


def create_access_token(
    data: Dict,
    expires_in: Optional[int] = None,
) -> str:
    """Create a signed JWT token."""
    expires_in = expires_in or settings.JWT_EXPIRY_SECONDS
    payload = {
        **data,
        "iat": int(time.time()),
        "exp": int(time.time()) + expires_in,
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token


def decode_access_token(token: str) -> Dict:
    """Decode and validate a JWT token. Raises on failure."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {e}",
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
) -> Dict:
    """FastAPI dependency — extract user info from bearer token."""
    payload = decode_access_token(credentials.credentials)
    username = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing 'sub' claim",
        )
    return {
        "username": username,
        "role": payload.get("role", "viewer"),
        "name": payload.get("name", ""),
    }


def authenticate_user(username: str, password: str) -> Optional[Dict]:
    """Verify credentials against demo user store."""
    user = DEMO_USERS.get(username)
    if user and user["password"] == password:
        return {
            "username": username,
            "role": user["role"],
            "name": user["name"],
        }
    return None
