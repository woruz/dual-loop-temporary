"""
Shared pytest fixtures and mock classes used across all tests.
This file is automatically discovered by pytest.
"""

import pytest
from unittest.mock import Mock, patch
from typing import Generator


# ─── Mock Classes ───────────────────────────────────────────────────────────


class MockAuthPort:
    """Mock authentication port for testing auth use cases."""
    
    def __init__(self):
        self.login_called = False
        self.user_id = None
    
    def authenticate(self, token: str) -> dict:
        self.login_called = True
        return {"user_id": "test-user-123", "email": "test@example.com"}
    
    def verify_token(self, token: str) -> bool:
        return len(token) > 10


class MockNotificationPort:
    """Mock notification port for testing notifications."""
    
    def __init__(self):
        self.sent_notifications = []
    
    def send(self, user_id: str, message: str, title: str = None) -> bool:
        self.sent_notifications.append({
            "user_id": user_id,
            "message": message,
            "title": title
        })
        return True
    
    def send_batch(self, notifications: list) -> int:
        self.sent_notifications.extend(notifications)
        return len(notifications)


class MockTelemetryRepo:
    """Mock telemetry repository for testing data persistence."""
    
    def __init__(self):
        self.data_store = {}
        self.queries = []
    
    def save(self, user_id: str, event: dict) -> bool:
        self.data_store[user_id] = event
        return True
    
    def get(self, user_id: str) -> dict:
        self.queries.append(("get", user_id))
        return self.data_store.get(user_id)
    
    def get_all(self) -> list:
        self.queries.append(("get_all",))
        return list(self.data_store.values())


# ─── Fixtures ───────────────────────────────────────────────────────────────


@pytest.fixture
def auth_port():
    """Fixture providing a mock authentication port."""
    return MockAuthPort()


@pytest.fixture
def notification_port():
    """Fixture providing a mock notification port."""
    return MockNotificationPort()


@pytest.fixture
def telemetry_repo():
    """Fixture providing a mock telemetry repository."""
    return MockTelemetryRepo()


@pytest.fixture
def test_user_data():
    """Fixture providing sample user data for testing."""
    return {
        "user_id": "test-user-123",
        "email": "test@example.com",
        "username": "testuser",
        "github_id": 12345,
        "created_at": "2024-01-01T00:00:00Z"
    }


@pytest.fixture
def test_token():
    """Fixture providing a test JWT token."""
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0LXVzZXItMTIzIn0.test"


@pytest.fixture
def mock_env():
    """Fixture to mock environment variables for testing."""
    with patch.dict('os.environ', {
        'SECRET_KEY': '134e27c2886d36c9713900223b7df02fab9d59c87a1b2963153df965aaa554b6',
        'DATABASE_URL': 'postgresql://user:password@localhost:5432/testdb',
        'GITHUB_CLIENT_ID': 'test-client-id',
        'GITHUB_CLIENT_SECRET': 'test-client-secret-40-char-length-xxx',
        'DEBUG': 'False',
        'ENVIRONMENT': 'development',
        'LOG_LEVEL': 'INFO',
    }) as mock:
        yield mock


@pytest.fixture
def production_env():
    """Fixture for production environment variables."""
    with patch.dict('os.environ', {
        'SECRET_KEY': 'prod-secret-key-very-long-and-secure-134e27c2886d36c9713900223b7df02fab9d59c87a1b2963153df965aaa554b6',
        'DATABASE_URL': 'postgresql://user:password@prod-db.example.com:5432/proddb',
        'GITHUB_CLIENT_ID': 'prod-client-id',
        'GITHUB_CLIENT_SECRET': 'prod-client-secret-40-char-length-xxxxx',
        'DEBUG': 'False',
        'ENVIRONMENT': 'production',
        'LOG_LEVEL': 'WARNING',
        'ALLOWED_ORIGINS': 'https://example.com,https://www.example.com',
        'FRONTEND_URL': 'https://example.com',
    }) as mock:
        yield mock


# ─── Helper Functions ───────────────────────────────────────────────────────


@pytest.fixture
def assert_called_with_args():
    """Helper fixture for asserting mock calls with better error messages."""
    def _assert(mock_obj, *args, **kwargs):
        try:
            mock_obj.assert_called_with(*args, **kwargs)
        except AssertionError as e:
            pytest.fail(f"Mock assertion failed: {e}")
    return _assert


# ─── Markers ────────────────────────────────────────────────────────────────

def pytest_configure(config):
    """Register custom pytest markers."""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "debug: mark test as a debug check")
