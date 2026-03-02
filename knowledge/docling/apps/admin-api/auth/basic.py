"""
Basic authentication for Admin Portal.
Uses HTTP Basic Auth for login, JWT tokens for session management.
"""

from datetime import datetime, timedelta, UTC
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials, HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from config import settings


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security schemes
basic_security = HTTPBasic()
bearer_security = HTTPBearer(auto_error=False)


class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime


class User(BaseModel):
    """Authenticated user."""
    username: str


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(username: str, expires_delta: Optional[timedelta] = None) -> Token:
    """Create a JWT access token."""
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.jwt_expire_minutes)

    expire = datetime.now(UTC) + expires_delta
    to_encode = {"sub": username, "exp": expire}

    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )

    return Token(access_token=encoded_jwt, expires_at=expire)


def authenticate_user(username: str, password: str) -> Optional[User]:
    """Authenticate user with username/password."""
    # Compare with configured admin credentials
    if username != settings.admin_username:
        return None

    # For simplicity, compare password directly (in production, hash it)
    if password != settings.admin_password:
        return None

    return User(username=username)


async def get_current_user_from_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_security),
) -> Optional[User]:
    """Extract user from JWT token (optional - for protected routes)."""
    if credentials is None:
        return None

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        username: str = payload.get("sub")
        if username is None:
            return None
        return User(username=username)
    except JWTError:
        return None


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_security),
) -> User:
    """Get current authenticated user (required - raises 401 if not authenticated)."""
    user = await get_current_user_from_token(credentials)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def login_for_access_token(
    credentials: HTTPBasicCredentials = Depends(basic_security),
) -> Token:
    """Login with HTTP Basic Auth, return JWT token."""
    user = authenticate_user(credentials.username, credentials.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return create_access_token(user.username)
