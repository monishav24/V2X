"""
SmartV2X-CP Ultra — Backend Cloud Server Configuration
========================================================
"""

import os


class Settings:
    HOST: str = os.getenv("BACKEND_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("BACKEND_PORT", "8001"))
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://smartv2x:smartv2x@localhost:5432/smartv2x_cloud",
    )
    JWT_SECRET: str = os.getenv("JWT_SECRET", "smartv2x-ultra-secret-change-me")
    JWT_ALGORITHM: str = "HS256"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    MODEL_STORAGE_DIR: str = os.getenv("MODEL_DIR", "models/")
    CORS_ORIGINS: list = os.getenv(
        "CORS_ORIGINS", "http://localhost:5173,http://localhost:3000"
    ).split(",")


settings = Settings()
