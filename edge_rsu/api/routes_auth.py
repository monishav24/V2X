"""
SmartV2X-CP Ultra — Authentication Routes
===========================================
POST /api/auth/register — Create a new user account
POST /api/auth/login    — Authenticate and retrieve JWT
"""

import logging
from typing import Optional
from pydantic import BaseModel

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from passlib.context import CryptContext

from edge_rsu.database.connection import get_db
from edge_rsu.database.models import User
from edge_rsu.auth.jwt_handler import create_access_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── Schemas ───────────────────────────────────────────────
class UserRegisterRequest(BaseModel):
    username: str
    password: str
    name: Optional[str] = ""
    role: Optional[str] = "viewer"  # admin, operator, viewer

class LoginRequest(BaseModel):
    username: str
    password: str

class AuthResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict

# ── Helpers ───────────────────────────────────────────────
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

# ── Routes ────────────────────────────────────────────────
@router.post("/register", response_model=AuthResponse)
async def register(req: UserRegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user."""
    # Check existing
    result = await db.execute(select(User).where(User.username == req.username))
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )

    # Create user
    new_user = User(
        username=req.username,
        password_hash=get_password_hash(req.password),
        name=req.name,
        role=req.role
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # Generate token
    token = create_access_token({
        "sub": new_user.username,
        "role": new_user.role,
        "name": new_user.name
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "username": new_user.username,
            "role": new_user.role,
            "name": new_user.name
        }
    }

@router.post("/login", response_model=AuthResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate user and return JWT."""
    # Check DB
    result = await db.execute(select(User).where(User.username == req.username))
    user = result.scalars().first()

    if not user or not verify_password(req.password, user.password_hash):
        # Fallback to demo users if not in DB (for backward compatibility/initial setup)
        from edge_rsu.auth.jwt_handler import DEMO_USERS
        demo_user = DEMO_USERS.get(req.username)
        if demo_user and demo_user["password"] == req.password:
            token = create_access_token({
                "sub": req.username,
                "role": demo_user["role"],
                "name": demo_user["name"]
            })
            return {
                "access_token": token,
                "token_type": "bearer",
                "user": {
                    "username": req.username,
                    "role": demo_user["role"],
                    "name": demo_user["name"]
                }
            }
            
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    # Generate token
    token = create_access_token({
        "sub": user.username,
        "role": user.role,
        "name": user.name
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "username": user.username,
            "role": user.role,
            "name": user.name
        }
    }
