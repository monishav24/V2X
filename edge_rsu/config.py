"""
SmartV2X-CP Ultra — Edge RSU Server Configuration
===================================================
Centralised settings loaded from environment variables with defaults.
"""

import os
from typing import List


class Settings:
    """Edge RSU configuration — reads from environment or uses defaults."""

    # ── Server ────────────────────────────────────────────
    HOST: str = os.getenv("EDGE_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("EDGE_PORT", "8000"))
    DEBUG: bool = os.getenv("EDGE_DEBUG", "false").lower() == "true"
    CORS_ORIGINS: List[str] = os.getenv(
        "CORS_ORIGINS", "http://localhost:5173,http://localhost:3000"
    ).split(",")

    # ── JWT ────────────────────────────────────────────────
    JWT_SECRET: str = os.getenv("JWT_SECRET", "smartv2x-ultra-secret-change-me")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_SECONDS: int = int(os.getenv("JWT_EXPIRY", "3600"))

    # ── Redis ─────────────────────────────────────────────
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # ── PostgreSQL ────────────────────────────────────────
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://smartv2x:smartv2x@localhost:5432/smartv2x_edge",
    )

    # ── Rate Limiting ─────────────────────────────────────
    RATE_LIMIT_PER_SECOND: int = int(os.getenv("RATE_LIMIT", "100"))

    # ── Logging ───────────────────────────────────────────
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/edge_rsu.log")


settings = Settings()
