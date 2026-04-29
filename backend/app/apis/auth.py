"""
Authentication API — register, login, token verification.
Uses bcrypt for passwords and JWT for session tokens.
Existing backend APIs remain completely unchanged.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator
from jose import JWTError, jwt
import bcrypt
from sqlalchemy.orm import Session

from app.core import get_db
from app.models import User

# ── Config ───────────────────────────────────────────────────────────────────
SECRET_KEY = os.getenv("AUTH_SECRET_KEY", "hrtech-platform-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


# ── Schemas ───────────────────────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def email_format(cls, v: str) -> str:
        v = v.strip().lower()
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Invalid email address")
        return v

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v

    @field_validator("username")
    @classmethod
    def username_not_empty(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Username must be at least 2 characters")
        return v


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    email: str


class VerifyResponse(BaseModel):
    valid: bool
    username: str | None = None
    email: str | None = None


# ── Helpers ───────────────────────────────────────────────────────────────────
def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def _create_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def _decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


def _ensure_db_ready() -> None:
    """Return a clean 503 if the backend database could not be initialized."""
    from app.main import _database_ready

    if not _database_ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service is starting. Please try again in a few seconds."
        )


# ── Endpoints ─────────────────────────────────────────────────────────────────
@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user account."""
    _ensure_db_ready()

    existing = db.query(User).filter(User.email == body.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists."
        )

    user = User(
        username=body.username.strip(),
        email=body.email,
        hashed_password=_hash_password(body.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = _create_token({"sub": user.email, "username": user.username})
    return TokenResponse(access_token=token, username=user.username, email=user.email)


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate a user and return a JWT token."""
    _ensure_db_ready()

    user = db.query(User).filter(User.email == body.email).first()
    if not user or not _verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated."
        )

    token = _create_token({"sub": user.email, "username": user.username})
    return TokenResponse(access_token=token, username=user.username, email=user.email)


@router.get("/verify", response_model=VerifyResponse)
def verify(token: str, db: Session = Depends(get_db)):
    """Verify a JWT token and return user info."""
    try:
        _ensure_db_ready()
        payload = _decode_token(token)
        email: str = payload.get("sub", "")
        username: str = payload.get("username", "")
        user = db.query(User).filter(User.email == email, User.is_active == True).first()
        if not user:
            return VerifyResponse(valid=False)
        return VerifyResponse(valid=True, username=username, email=email)
    except JWTError:
        return VerifyResponse(valid=False)
