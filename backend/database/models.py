"""
SmartV2X-CP Ultra — Backend Database Models
=============================================
Cloud-level models extending edge schema with multi-tenant fields.
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, Text, JSON,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Vehicle(Base):
    __tablename__ = "cloud_vehicles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_id = Column(String(64), unique=True, nullable=False, index=True)
    device_name = Column(String(128), default="")
    firmware_version = Column(String(32), default="")
    city = Column(String(64), default="", index=True)
    tenant_id = Column(String(64), default="default", index=True)
    registered_at = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    status = Column(String(16), default="offline")


class CollisionEvent(Base):
    __tablename__ = "cloud_collision_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_a = Column(String(64), nullable=False, index=True)
    vehicle_b = Column(String(64), nullable=True)
    risk_level = Column(String(8), nullable=False)
    risk_score = Column(Float, default=0.0)
    ttc_seconds = Column(Float, nullable=True)
    distance_m = Column(Float, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    city = Column(String(64), default="")
    tenant_id = Column(String(64), default="default")
    details = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    version = Column(String(32), unique=True, nullable=False)
    model_path = Column(String(256), nullable=False)
    metrics = Column(JSON, default=dict)
    description = Column(Text, default="")
    status = Column(String(16), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
