"""Password hashing, JWT issuing and the current-user dependencies."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt
from fastapi import Cookie, Depends, HTTPException, Request, status

from . import config
from .database import db_dependency


# --------------------------------------------------------------------------- #
# Passwords
# --------------------------------------------------------------------------- #
def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


# --------------------------------------------------------------------------- #
# Tokens
# --------------------------------------------------------------------------- #
def create_access_token(user_id: int, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": now,
        "exp": now + timedelta(hours=config.TOKEN_TTL_HOURS),
    }
    return jwt.encode(payload, config.SECRET_KEY, algorithm=config.JWT_ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, config.SECRET_KEY, algorithms=[config.JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None


def _token_from_request(request: Request, cookie_token: Optional[str]) -> Optional[str]:
    if cookie_token:
        return cookie_token
    header = request.headers.get("Authorization", "")
    if header.lower().startswith("bearer "):
        return header[7:].strip()
    return None


# --------------------------------------------------------------------------- #
# Dependencies
# --------------------------------------------------------------------------- #
def get_current_user(
    request: Request,
    sh_session: Optional[str] = Cookie(default=None),
    conn: sqlite3.Connection = Depends(db_dependency),
) -> Optional[sqlite3.Row]:
    """Attach a user when a valid cookie/token exists, otherwise None (public pages)."""
    token = _token_from_request(request, sh_session)
    if not token:
        return None
    payload = decode_token(token)
    if not payload or "sub" not in payload:
        return None
    row = conn.execute("SELECT * FROM users WHERE id = ?", (int(payload["sub"]),)).fetchone()
    return row


def require_user(user: Optional[sqlite3.Row] = Depends(get_current_user)) -> sqlite3.Row:
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Please sign in to continue.")
    return user


def require_admin(user: Optional[sqlite3.Row] = Depends(get_current_user)) -> sqlite3.Row:
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Please sign in to continue.")
    if user["role"] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrator access required.")
    return user
