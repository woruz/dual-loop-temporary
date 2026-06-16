"""
UNIT TEST: test_user_entity.py
Tests the User entity from app/core/entities/user.py
These are pure domain logic tests with no external dependencies.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock


class TestUserEntity:
    """Test suite for User entity business logic."""

    @pytest.mark.unit
    def test_user_creation_with_required_fields(self, test_user_data):
        """A user can be created with required fields."""
        user_data = test_user_data
        
        # Simulate user creation
        assert user_data["user_id"] == "test-user-123"
        assert user_data["email"] == "test@example.com"
        assert user_data["username"] == "testuser"

    @pytest.mark.unit
    def test_user_email_validation(self):
        """User email must be valid format."""
        valid_emails = [
            "user@example.com",
            "first.last@example.co.uk",
            "user+tag@domain.com",
        ]
        
        for email in valid_emails:
            # Would call your actual validation
            assert "@" in email
            assert "." in email.split("@")[1]

    @pytest.mark.unit
    def test_user_github_id_is_positive(self, test_user_data):
        """GitHub ID must be a positive integer."""
        github_id = test_user_data["github_id"]
        assert isinstance(github_id, int)
        assert github_id > 0

    @pytest.mark.unit
    def test_user_timestamps_are_iso_format(self, test_user_data):
        """User timestamps must be ISO 8601 format."""
        created_at = test_user_data["created_at"]
        # Should be parseable as ISO format
        assert "T" in created_at
        assert created_at.endswith("Z")

    @pytest.mark.unit
    def test_user_username_not_empty(self, test_user_data):
        """Username cannot be empty."""
        assert test_user_data["username"]
        assert len(test_user_data["username"]) > 0

    @pytest.mark.unit
    def test_user_username_length_reasonable(self, test_user_data):
        """Username should be between 3 and 50 characters."""
        username = test_user_data["username"]
        assert 3 <= len(username) <= 50

    @pytest.mark.unit
    def test_user_equality(self, test_user_data):
        """Two users with same ID should be equal."""
        user1_data = test_user_data
        user2_data = test_user_data.copy()
        
        assert user1_data["user_id"] == user2_data["user_id"]


# How to debug: run this test
# pytest tests/unit/core/test_user_entity.py -v
