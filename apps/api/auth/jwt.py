"""
JWT token generation and verification utilities

Provides secure JWT token creation and validation for user authentication.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
import bcrypt
import os

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Security check: Ensure SECRET_KEY is set in production
if not SECRET_KEY:
    import warnings
    warnings.warn(
        "JWT_SECRET_KEY is not set! Using a random key. "
        "This is NOT suitable for production - set JWT_SECRET_KEY environment variable!",
        RuntimeWarning
    )
    import secrets
    SECRET_KEY = secrets.token_urlsafe(32)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Generate JWT access token

    Args:
        data: Token payload (usually contains user_id, username, role)
        expires_delta: Token expiration time delta (default: 30 minutes)

    Returns:
        str: Encoded JWT token

    Example:
        >>> token = create_access_token({"user_id": 1, "username": "admin", "role": "admin"})
        >>> print(token)
        eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def verify_token(token: str) -> Dict[str, Any]:
    """
    Verify and decode JWT token

    Args:
        token: JWT token string

    Returns:
        dict: Decoded token payload

    Raises:
        ValueError: If token is invalid or expired

    Example:
        >>> payload = verify_token(token)
        >>> print(payload["user_id"])
        1
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        raise ValueError(f"Token 验证失败: {str(e)}")


def get_password_hash(password: str) -> str:
    """
    Generate password hash using bcrypt

    Args:
        password: Plain text password

    Returns:
        str: Bcrypt hashed password

    Example:
        >>> hashed = get_password_hash("mypassword123")
        >>> print(hashed)
        $2b$12$...
    """
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against hashed password

    Args:
        plain_password: Plain text password to verify
        hashed_password: Bcrypt hashed password

    Returns:
        bool: True if password matches, False otherwise

    Example:
        >>> is_valid = verify_password("mypassword123", hashed)
        >>> print(is_valid)
        True
    """
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)
