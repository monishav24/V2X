"""
SmartV2X-CP Ultra — Backend Cloud Server Entry Point
======================================================
Run:
  uvicorn backend.main:app --host 0.0.0.0 --port 8001 --reload
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.api.routes import router as api_router
from backend.api.health import router as health_router
from backend.database.connection import init_db

os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("backend")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("══════════════════════════════════════════")
    logger.info("  SmartV2X-CP Ultra — Backend Cloud Server")
    logger.info("══════════════════════════════════════════")
    await init_db()
    os.makedirs(settings.MODEL_STORAGE_DIR, exist_ok=True)
    yield
    logger.info("Backend server shutting down")


app = FastAPI(
    title="SmartV2X-CP Ultra — Backend Cloud",
    description="Cloud analytics and model management server",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
app.include_router(health_router)


@app.get("/")
async def root():
    return {
        "service": "SmartV2X-CP Ultra Backend Cloud",
        "version": "1.0.0",
        "docs": "/docs",
    }
