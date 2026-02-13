"""
SmartV2X-CP Ultra — Role-Based Access Control (RBAC)
=====================================================
FastAPI dependency that enforces role requirements per endpoint.
"""

import logging
from typing import List

from fastapi import Depends, HTTPException, status

from edge_rsu.auth.jwt_handler import get_current_user

logger = logging.getLogger(__name__)

# Role hierarchy: admin > operator > device > viewer
ROLE_HIERARCHY = {
    "admin": 4,
    "operator": 3,
    "device": 2,
    "viewer": 1,
}


class RoleChecker:
    """
    FastAPI dependency class for role-based endpoint protection.

    Usage:
        @router.get("/admin-only", dependencies=[Depends(RoleChecker(["admin"]))])
    """

    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    async def __call__(self, user: dict = Depends(get_current_user)):
        if user["role"] not in self.allowed_roles:
            logger.warning(
                "Access denied for user '%s' (role=%s) — required: %s",
                user["username"], user["role"], self.allowed_roles,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user['role']}' not authorised. Required: {self.allowed_roles}",
            )
        return user


def require_role(*roles: str):
    """Shortcut to create a RoleChecker dependency."""
    return Depends(RoleChecker(list(roles)))
