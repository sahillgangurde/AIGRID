"""
Authentication, Token Management, and Role Authorization Service for FRAME.
Provides PBKDF2-HMAC-SHA256 password hashing, JWT tokens, username normalization,
reserved username protection, and FastAPI security dependencies.
"""

import os
import re
import hmac
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, List
import jwt
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from server.db.session import get_db
from server.db.models import Profile, AuditLog

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "frame_super_secret_production_key_2026_jwt_auth_token")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7

RESERVED_USERNAMES = {
    "admin", "root", "system", "frame", "support", "moderator",
    "official", "api", "auth", "security", "help", "billing", "platform"
}

security = HTTPBearer(auto_error=False)


class AuthService:
    @staticmethod
    def normalize_username(username: str) -> str:
        """Normalizes username to lower-case, stripped string."""
        return username.lower().strip()

    @classmethod
    def validate_username(cls, username: str) -> str:
        """
        Validates that a username conforms to platform policy:
        - 3-30 characters
        - Lowercase alphanumeric, underscores, hyphens
        - Not in reserved list
        """
        normalized = cls.normalize_username(username)
        if not re.match(r"^[a-z0-9_-]{3,30}$", normalized):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username must be 3-30 characters and contain only lowercase letters, numbers, underscores, and hyphens."
            )
        if normalized in RESERVED_USERNAMES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"The username '{normalized}' is reserved by the platform."
            )
        return normalized

    @staticmethod
    def hash_password(password: str) -> str:
        """Generates a secure PBKDF2-HMAC-SHA256 password hash with unique salt."""
        salt = secrets.token_hex(16)
        key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
        return f"{salt}:{key.hex()}"

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verifies a plain password against the stored salt & hash."""
        try:
            salt, key_hex = hashed_password.split(":")
            key = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), 100000)
            return hmac.compare_digest(key.hex(), key_hex)
        except Exception:
            return False

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Generates a signed JWT access token."""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + (expires_delta or timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS))
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    def decode_token(token: str) -> dict:
        """Decodes and validates a JWT access token."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired. Please log in again.")
        except jwt.PyJWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization token.")


def get_current_user_optional(
    auth_header: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[Profile]:
    """Returns the authenticated Profile if token is provided, or None."""
    if not auth_header or not auth_header.credentials:
        return None
    try:
        payload = AuthService.decode_token(auth_header.credentials)
        user_id = payload.get("sub")
        if not user_id:
            return None
        user = db.query(Profile).filter(Profile.id == user_id).first()
        if not user or user.account_status == "suspended":
            return None
        return user
    except Exception:
        return None


def get_current_user(
    auth_header: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Profile:
    """FastAPI dependency: Enforces a valid authenticated session."""
    if not auth_header or not auth_header.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = AuthService.decode_token(auth_header.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Malformed token.")

    user = db.query(Profile).filter(Profile.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.")
    if user.account_status == "suspended":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This account has been suspended.")

    return user


def require_role(allowed_roles: List[str]):
    """FastAPI dependency factory: Enforces specific roles (admin always permitted)."""
    def role_checker(current_user: Profile = Depends(get_current_user)) -> Profile:
        if current_user.role != "admin" and current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Requires one of roles: {', '.join(allowed_roles)}"
            )
        return current_user
    return role_checker


def require_admin(current_user: Profile = Depends(get_current_user)) -> Profile:
    """FastAPI dependency: strictly requires admin role."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required for this action."
        )
    return current_user
