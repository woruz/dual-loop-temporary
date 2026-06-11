"""
HOW TO DEBUG YOUR CODE WITH PYTEST

This guide shows you exactly where to find debug info and how to solve problems.
"""

# ============================================================================
# 1. FOLDER STRUCTURE — Where Everything Lives
# ============================================================================

"""
tests/
├── conftest.py                           ← Shared fixtures & Mock classes
│
├── unit/                                 ← Pure logic tests (no external deps)
│   ├── core/
│   │   ├── test_user_entity.py          ← Tests User domain entity (7 tests)
│   │   └── test_auth_use_cases.py       ← Tests auth business logic (7 tests)
│   │
│   └── infrastructure/
│       └── test_token_service.py        ← Tests JWT token handling (8 tests)
│
├── integration/                          ← Tests with HTTP / real services
│   └── test_auth_endpoints.py           ← Tests auth HTTP endpoints (14 tests)
│
└── debug_checks/                         ← SAFETY GUARDRAILS for deployment
    └── test_config_safety.py            ← Checks DEBUG mode, secrets, etc. (25 tests)


pytest.ini                                ← Configuration file (project root)
requirements-test.txt                     ← Testing dependencies (project root)
"""

# ============================================================================
# 2. INSTALLATION — Get pytest running
# ============================================================================

# First, activate your virtual environment:
# .venv\Scripts\Activate.ps1

# Install testing dependencies:
# pip install -r requirements-test.txt

# Verify pytest is installed:
# pytest --version

# ============================================================================
# 3. RUNNING TESTS — The command-line reference
# ============================================================================

# ──── RUN EVERYTHING ─────────────────────────────────────────────────────
# pytest                              # Run all tests
# pytest -v                           # Run all tests, verbose output
# pytest -v --tb=long                # Run with detailed error traces

# ──── RUN BY FOLDER ──────────────────────────────────────────────────────
# pytest tests/unit/                  # Run only unit tests
# pytest tests/integration/           # Run only integration tests
# pytest tests/debug_checks/          # Run only debug/config checks

# ──── RUN BY FILE ────────────────────────────────────────────────────────
# pytest tests/unit/core/test_auth_use_cases.py -v
# pytest tests/debug_checks/test_config_safety.py -v

# ──── RUN BY CLASS ───────────────────────────────────────────────────────
# pytest tests/unit/core/test_auth_use_cases.py::TestAuthUseCases -v
# pytest tests/debug_checks/test_config_safety.py::TestDebugMode -v

# ──── RUN BY SPECIFIC TEST ───────────────────────────────────────────────
# pytest tests/unit/core/test_auth_use_cases.py::TestAuthUseCases::test_login_returns_user_id -v

# ──── RUN BY MARKER (label) ──────────────────────────────────────────────
# pytest -m unit                      # Run all tests marked @pytest.mark.unit
# pytest -m integration               # Run all integration tests
# pytest -m auth                      # Run all authentication tests
# pytest -m debug                     # Run debug checks
# pytest -m "not slow"                # Run everything except slow tests

# ──── RUN WITH FILTERING ─────────────────────────────────────────────────
# pytest -k "auth"                    # Run tests with "auth" in the name
# pytest -k "test_login"              # Run tests with "login" in the name
# pytest -k "not slow"                # Run all except tests with "slow"

# ──── RUN WITH STOP-ON-FIRST-FAILURE ─────────────────────────────────────
# pytest -x                           # Stop at first failure
# pytest --maxfail=3                  # Stop after 3 failures

# ──── SHOW PRINT OUTPUT ──────────────────────────────────────────────────
# pytest -s                           # Show all print() statements
# pytest -s -v tests/unit/core/test_user_entity.py::TestUserEntity::test_user_creation_with_required_fields

# ============================================================================
# 4. UNDERSTANDING THE TEST FILES
# ============================================================================

# ──── tests/conftest.py ──────────────────────────────────────────────────
# This file provides:
#   • MockAuthPort — fake authentication for testing
#   • MockNotificationPort — fake notification service
#   • MockTelemetryRepo — fake database
#   • auth_port, notification_port, telemetry_repo fixtures
#   • test_user_data, test_token fixtures
#   • mock_env, production_env fixtures for env variables
#
# Usage in your tests:
#   def test_something(auth_port, test_user_data):  # ← fixtures injected automatically


# ──── tests/debug_checks/test_config_safety.py ──────────────────────────
# This file ANSWERS YOUR QUESTION: "Is debug mode on or not?"
#
# Tests check:
#   TestDebugMode.test_debug_is_false_in_production()
#       ↳ ENVIRONMENT=production must have DEBUG=False
#
#   TestSecretKey.test_secret_key_is_not_placeholder()
#       ↳ SECRET_KEY cannot be the development placeholder
#
#   TestDatabaseConfig.test_production_database_not_localhost()
#       ↳ DATABASE_URL cannot point to localhost in production
#
#   TestCORSConfig.test_production_cors_not_wildcard()
#       ↳ ALLOWED_ORIGINS cannot be * in production
#
# RUN THESE BEFORE DEPLOYING:
#   ENVIRONMENT=production pytest tests/debug_checks/ -v


# ──── tests/unit/core/test_auth_use_cases.py ─────────────────────────────
# Tests the BUSINESS LOGIC of authentication
# Tests:
#   test_login_with_valid_credentials()
#   test_login_returns_user_id()
#   test_token_validation_requires_minimum_length()
#   ... etc
#
# Each test is ISOLATED — no database, no HTTP, just pure logic


# ──── tests/unit/infrastructure/test_token_service.py ─────────────────────
# Tests JWT TOKEN handling (real JWT behavior)
# Tests:
#   test_token_has_three_parts() — JWT format: header.payload.signature
#   test_token_expiry_in_future()
#   test_expired_token_rejected()
#   ... etc


# ──── tests/integration/test_auth_endpoints.py ──────────────────────────
# Tests the HTTP ENDPOINTS (the actual API responses)
# Tests:
#   test_login_endpoint_returns_200_on_valid_credentials()
#   test_login_endpoint_returns_token_on_success()
#   test_protected_endpoint_requires_token()
#   ... etc
#
# These tests simulate HTTP requests to your FastAPI app


# ============================================================================
# 5. COMMON DEBUGGING SCENARIOS
# ============================================================================

# SCENARIO 1: "My code has a bug in login logic"
# SOLUTION:
#   1. Run the auth tests: pytest tests/unit/core/test_auth_use_cases.py -v
#   2. Find which test fails
#   3. The test name tells you what's broken
#   4. Example: If test_login_returns_user_id fails, then login() doesn't return user_id
#   5. Open: app/core/use_cases/auth_use_cases.py
#   6. Find the login function and fix it
#   7. Run the test again: pytest tests/unit/core/test_auth_use_cases.py::TestAuthUseCases::test_login_returns_user_id -v


# SCENARIO 2: "Is my code in debug mode?"
# SOLUTION:
#   1. Run: pytest tests/debug_checks/ -v
#   2. If any test fails, you have a security issue
#   3. Look at the failure message — it tells you exactly what to fix
#   4. Example failure:
#      FAILED tests/debug_checks/test_config_safety.py::TestDebugMode::test_debug_is_false_in_production
#      AssertionError: CRITICAL: DEBUG=True but ENVIRONMENT=production!
#   5. Fix: Set DEBUG=False in your .env file
#   6. Run the test again


# SCENARIO 3: "The HTTP endpoints are broken"
# SOLUTION:
#   1. Run: pytest tests/integration/test_auth_endpoints.py -v
#   2. Find which endpoint test fails
#   3. Example: If test_login_endpoint_returns_200_on_valid_credentials fails
#   4. Open: app/server/routers/auth_router.py
#   5. Check the login endpoint implementation
#   6. Fix the code
#   7. Run test again


# SCENARIO 4: "I want to test just ONE thing"
# SOLUTION:
#   # Add a simple test file or modify existing test:
#   pytest tests/unit/core/test_user_entity.py::TestUserEntity::test_user_creation_with_required_fields -v -s
#   # The -s flag shows print() output
#   # The -v flag shows verbose output


# ============================================================================
# 6. PYTEST OUTPUT EXPLAINED
# ============================================================================

"""
$ pytest tests/unit/core/test_auth_use_cases.py::TestAuthUseCases::test_login_returns_user_id -v

tests/unit/core/test_auth_use_cases.py::TestAuthUseCases::test_login_returns_user_id PASSED

─ PASSED  = Test succeeded ✓
─ FAILED  = Test failed ✗
─ SKIPPED = Test was skipped
─ ERROR   = Test crashed (not a test failure, but an error)

Example output:
    ======================== test session starts ========================
    collected 1 item
    
    tests/unit/core/test_auth_use_cases.py::TestAuthUseCases::test_login_returns_user_id PASSED
    
    ======================== 1 passed in 0.15s =========================
    
    ✓ 1 test ran
    ✓ It took 0.15 seconds
    ✓ It passed


FAILED TEST OUTPUT:
    ======================== FAILURES ===================================
    ____________ TestAuthUseCases::test_login_returns_user_id ___________
    
    def test_login_returns_user_id(self, auth_port):
        result = auth_port.authenticate("valid-token")
>       assert "user_id" in result
    E       AssertionError: assert 'user_id' in {}
    
    tests/unit/core/test_auth_use_cases.py:24: AssertionError
    
    ✓ The > arrow shows the line that failed
    ✓ The E line shows what went wrong
    ✓ The assertion shows: {} means the result is empty dict (no user_id)
    ✓ FIX: Update authenticate() to return {"user_id": ...}
"""


# ============================================================================
# 7. FIXTURES EXPLAINED
# ============================================================================

"""
A fixture is a "helper object" that pytest injects into your tests.

Example fixture:
    @pytest.fixture
    def auth_port():
        return MockAuthPort()

Usage in your test:
    def test_something(auth_port):    # ← auth_port is automatically provided
        result = auth_port.authenticate("token")
        assert result["user_id"] == "test-user-123"

Available fixtures in conftest.py:
    • auth_port — Mock authentication service
    • notification_port — Mock notification service
    • telemetry_repo — Mock database
    • test_user_data — Sample user dict
    • test_token — Sample JWT token
    • mock_env — Development environment variables
    • production_env — Production environment variables

How to use multiple fixtures:
    def test_something(auth_port, test_user_data, notification_port):
        # Now you have all three available
        ...
"""


# ============================================================================
# 8. MARKERS EXPLAINED
# ============================================================================

"""
A marker is a label you put on tests.

@pytest.mark.unit
def test_something():
    ...

Why markers?
    • Organize tests by category
    • Run specific categories
    • Skip categories in CI

Available markers (from pytest.ini):
    • @pytest.mark.unit — Pure logic tests
    • @pytest.mark.integration — Tests with HTTP/real services
    • @pytest.mark.slow — Slow running tests
    • @pytest.mark.debug — Debug checks
    • @pytest.mark.auth — Authentication tests
    • @pytest.mark.config — Configuration tests

Usage:
    pytest -m unit              # Run only unit tests
    pytest -m integration       # Run only integration tests
    pytest -m "not slow"        # Skip slow tests
    pytest -m "auth or config"  # Run auth OR config tests
"""


# ============================================================================
# 9. EXAMPLE: ADDING YOUR OWN TEST
# ============================================================================

"""
Let's say you want to test a function from app/core/use_cases/calculate_gap.py

Step 1: Create a test file or add to existing file
    # File: tests/unit/core/test_calculate_gap.py
    
    import pytest
    from app.core.use_cases.calculate_gap import calculate_gap
    
    class TestCalculateGap:
        @pytest.mark.unit
        def test_calculate_gap_with_zero_values(self):
            # Arrange: set up test data
            value1 = 0
            value2 = 10
            
            # Act: call the function
            gap = calculate_gap(value1, value2)
            
            # Assert: check the result
            assert gap == 10
        
        @pytest.mark.unit
        def test_calculate_gap_negative_values(self):
            gap = calculate_gap(-5, 5)
            assert gap == 10

Step 2: Run your new test
    pytest tests/unit/core/test_calculate_gap.py -v

Step 3: If it fails, the test output tells you what's wrong
    AssertionError: assert 5 == 10
    ↳ This means calculate_gap returned 5 but you expected 10
    ↳ Go fix the calculate_gap function in app/core/use_cases/calculate_gap.py
"""


# ============================================================================
# 10. QUICK START SUMMARY
# ============================================================================

"""
1. Install dependencies:
   pip install -r requirements-test.txt

2. Check if debug mode is on (before deploying):
   pytest tests/debug_checks/ -v

3. Run all tests:
   pytest -v

4. Debug specific area:
   pytest tests/unit/core/ -v          # Test business logic
   pytest tests/integration/ -v        # Test HTTP endpoints

5. Run one test:
   pytest tests/unit/core/test_auth_use_cases.py::TestAuthUseCases::test_login_returns_user_id -v

6. See details when something fails:
   pytest -v --tb=long

7. Show print() output:
   pytest -s
"""


# ============================================================================
# 11. TROUBLESHOOTING
# ============================================================================

"""
ERROR: "ModuleNotFoundError: No module named 'pytest'"
SOLUTION: pip install pytest

ERROR: "No tests collected"
SOLUTION: 
    - Check file names: must be test_*.py or *_test.py
    - Check class names: must be Test*
    - Check function names: must be test_*

ERROR: "fixture 'auth_port' not found"
SOLUTION:
    - Make sure conftest.py exists in tests/ folder
    - Reload VS Code
    - Make sure the fixture name matches exactly

ERROR: "test_config_safety.py::TestDebugMode::test_debug_is_false_in_production FAILED"
SOLUTION:
    - Read the assertion error message
    - Example: "DEBUG=True but ENVIRONMENT=production!"
    - Fix: Open .env and set DEBUG=False
    - Run test again

ERROR: Tests work locally but fail in CI
SOLUTION:
    - CI uses environment variables from .env file
    - Check that your CI .env matches production settings
    - Run: ENVIRONMENT=production pytest tests/debug_checks/ -v
"""


# ============================================================================
# 12. NEXT STEPS
# ============================================================================

"""
Now that you have the test structure:

1. Add YOUR code to app/core/entities/, app/core/use_cases/, etc.

2. Write tests for YOUR code:
   • One test file per source file
   • Place in tests/unit/ or tests/integration/

3. Before deploying:
   pytest tests/debug_checks/ -v

4. Before committing:
   pytest -v

5. In CI/CD:
   # Run all tests
   pytest -v
   
   # Or just safety checks
   ENVIRONMENT=production pytest tests/debug_checks/ -v


Good luck debugging! 🚀
"""
