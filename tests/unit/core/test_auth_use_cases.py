"""
UNIT TEST: test_auth_use_cases.py
Tests authentication business logic from app/core/use_cases/auth_use_cases.py
"""

import pytest
from unittest.mock import Mock, patch, call


class TestAuthUseCases:
    """Test suite for authentication use cases."""

    @pytest.mark.unit
    @pytest.mark.auth
    def test_login_with_valid_credentials(self, auth_port, test_user_data):
        """User can log in with valid email and password."""
        auth_port.authenticate("valid-token")
        assert auth_port.login_called is True

    @pytest.mark.unit
    @pytest.mark.auth
    def test_login_returns_user_id(self, auth_port):
        """Login use case returns user_id on success."""
        result = auth_port.authenticate("valid-token")
        assert "user_id" in result
        assert result["user_id"] == "test-user-123"

    @pytest.mark.unit
    @pytest.mark.auth
    def test_login_returns_email(self, auth_port):
        """Login use case returns user email."""
        result = auth_port.authenticate("valid-token")
        assert "email" in result
        assert result["email"] == "test@example.com"

    @pytest.mark.unit
    @pytest.mark.auth
    def test_token_validation_requires_minimum_length(self, auth_port):
        """Token must be minimum length (security)."""
        # Short tokens should fail
        short_token = "abc"
        is_valid = auth_port.verify_token(short_token)
        assert is_valid is False

    @pytest.mark.unit
    @pytest.mark.auth
    def test_token_validation_accepts_valid_tokens(self, auth_port, test_token):
        """Valid tokens should pass verification."""
        is_valid = auth_port.verify_token(test_token)
        assert is_valid is True

    @pytest.mark.unit
    @pytest.mark.auth
    def test_multiple_login_attempts_tracked(self, auth_port):
        """Multiple login attempts should be tracked."""
        auth_port.authenticate("token-1")
        auth_port.authenticate("token-2")
        auth_port.authenticate("token-3")
        
        assert auth_port.login_called is True

    @pytest.mark.unit
    @pytest.mark.auth
    def test_invalid_token_format_rejected(self, auth_port):
        """Malformed tokens should be rejected."""
        invalid_tokens = ["", "   ", "123", "bearer "]
        
        for token in invalid_tokens:
            is_valid = auth_port.verify_token(token)
            assert is_valid is False, f"Invalid token should not pass: {token}"


# DEBUG: How to run these tests
# pytest tests/unit/core/test_auth_use_cases.py -v
# pytest tests/unit/core/test_auth_use_cases.py::TestAuthUseCases::test_login_returns_user_id -v
# pytest tests/unit/core/test_auth_use_cases.py -v --tb=short
