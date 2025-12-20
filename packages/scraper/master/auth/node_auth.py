"""
Node Authentication

节点JWT认证和密钥管理
"""

import os
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional, List
from dataclasses import dataclass

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from ...database import get_db_session
from ...models import CrawlerNode, NodeStatus

logger = logging.getLogger(__name__)

# JWT Configuration
JWT_SECRET_KEY = os.getenv("CRAWLER_JWT_SECRET", os.getenv("JWT_SECRET_KEY", "crawler-secret-key-change-in-production"))
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = int(os.getenv("CRAWLER_JWT_EXPIRE_HOURS", "24"))

# Security
security = HTTPBearer()


@dataclass
class NodeTokenPayload:
    """Node token payload"""
    node_id: str
    capabilities: List[str]
    exp: datetime
    type: str = "node"


def create_node_token(node_id: str, capabilities: List[str], expire_hours: int = None) -> tuple[str, datetime]:
    """
    Create JWT token for node authentication

    Args:
        node_id: Node ID
        capabilities: Node capabilities
        expire_hours: Token expiration hours (default from env)

    Returns:
        Tuple of (token, expires_at)
    """
    if expire_hours is None:
        expire_hours = JWT_EXPIRE_HOURS

    expires_at = datetime.utcnow() + timedelta(hours=expire_hours)

    payload = {
        "node_id": node_id,
        "type": "node",
        "capabilities": capabilities,
        "exp": expires_at,
        "iat": datetime.utcnow(),
    }

    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token, expires_at


def verify_node_token(token: str) -> Optional[NodeTokenPayload]:
    """
    Verify JWT token and extract payload

    Args:
        token: JWT token string

    Returns:
        NodeTokenPayload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])

        if payload.get("type") != "node":
            logger.warning("Token type is not 'node'")
            return None

        return NodeTokenPayload(
            node_id=payload["node_id"],
            capabilities=payload.get("capabilities", ["all"]),
            exp=datetime.fromtimestamp(payload["exp"]),
            type=payload["type"],
        )

    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        return None


def generate_node_secret() -> str:
    """
    Generate a secure random secret for node authentication

    Returns:
        32-character hex string
    """
    return secrets.token_hex(32)


def hash_node_secret(secret: str) -> str:
    """
    Hash node secret using bcrypt

    Args:
        secret: Plain text secret

    Returns:
        Bcrypt hash
    """
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(secret.encode(), salt).decode()


def verify_node_secret(secret: str, hashed: str) -> bool:
    """
    Verify node secret against hash

    Args:
        secret: Plain text secret
        hashed: Bcrypt hash

    Returns:
        True if matches
    """
    try:
        return bcrypt.checkpw(secret.encode(), hashed.encode())
    except Exception as e:
        logger.error(f"Error verifying secret: {e}")
        return False


async def get_current_node(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db_session),
) -> CrawlerNode:
    """
    FastAPI dependency to get current authenticated node

    Args:
        credentials: HTTP Bearer credentials
        db: Database session

    Returns:
        CrawlerNode if authenticated

    Raises:
        HTTPException: If authentication fails
    """
    token = credentials.credentials

    # Verify token
    payload = verify_node_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get node from database
    node = db.query(CrawlerNode).filter(
        CrawlerNode.node_id == payload.node_id
    ).first()

    if node is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Node not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check node status
    if node.status == NodeStatus.OFFLINE:
        # Update to online on valid request
        node.status = NodeStatus.ONLINE
        node.last_heartbeat = datetime.utcnow()
        db.commit()

    return node


async def get_current_node_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
    db: Session = Depends(get_db_session),
) -> Optional[CrawlerNode]:
    """
    Optional node authentication dependency

    Returns None if no token or invalid token, instead of raising exception
    """
    if credentials is None:
        return None

    try:
        return await get_current_node(credentials, db)
    except HTTPException:
        return None


async def require_authenticated(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> NodeTokenPayload:
    """
    Require valid authentication for admin endpoints

    验证Token有效性，用于管理端点的认证
    不需要特定节点，只需要有效的Token即可

    Returns:
        NodeTokenPayload if authenticated

    Raises:
        HTTPException: If authentication fails
    """
    token = credentials.credentials

    # Verify token
    payload = verify_node_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload
