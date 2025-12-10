"""
Tests for JWT authentication utilities
"""

import pytest
from datetime import timedelta
import time
from apps.api.auth.jwt import (
    create_access_token,
    verify_token,
    get_password_hash,
    verify_password
)


class TestJWT:
    """Test cases for JWT token operations"""

    def test_create_and_verify_token(self):
        """Test token creation and verification"""
        payload = {"user_id": 1, "username": "admin", "role": "admin"}
        token = create_access_token(payload)

        # Verify token
        decoded = verify_token(token)

        assert decoded["user_id"] == 1
        assert decoded["username"] == "admin"
        assert decoded["role"] == "admin"
        assert "exp" in decoded  # Contains expiration time

    def test_token_expiration(self):
        """Test token expiration"""
        payload = {"user_id": 1}

        # Create token that expires in 1 second
        token = create_access_token(payload, expires_delta=timedelta(seconds=1))

        # Immediate verification should succeed
        decoded = verify_token(token)
        assert decoded["user_id"] == 1

        # Wait 2 seconds and verification should fail
        time.sleep(2)

        with pytest.raises(ValueError, match="Token 验证失败"):
            verify_token(token)

    def test_invalid_token(self):
        """Test invalid token handling"""
        with pytest.raises(ValueError, match="Token 验证失败"):
            verify_token("invalid.token.here")

    def test_password_hashing(self):
        """Test password hashing"""
        password = "test_password_123"

        # Generate hash
        hashed = get_password_hash(password)

        # Hash should be different from original password
        assert hashed != password

        # Verify correct password
        assert verify_password(password, hashed) is True

        # Verify wrong password
        assert verify_password("wrong_password", hashed) is False

    def test_bcrypt_salt(self):
        """Test bcrypt salt (each hash is different)"""
        password = "same_password"

        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        # Two hashes should be different (due to different salt)
        assert hash1 != hash2

        # But both should verify successfully
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True

    def test_token_with_custom_expiration(self):
        """Test token with custom expiration time"""
        from datetime import datetime as dt
        payload = {"user_id": 1}

        # Record current time
        now_before = dt.utcnow()

        # Create token that expires in 1 hour
        token = create_access_token(payload, expires_delta=timedelta(hours=1))

        decoded = verify_token(token)
        assert decoded["user_id"] == 1

        # Check that expiration exists
        assert "exp" in decoded

        # Convert exp timestamp to UTC datetime
        exp_time = dt.utcfromtimestamp(decoded["exp"])

        # Time difference should be approximately 1 hour
        time_diff = (exp_time - now_before).total_seconds()
        assert 3500 < time_diff < 3700  # 1 hour ± 100 seconds
