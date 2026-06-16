# 🧪 Testing Guide — Debug Your Code

## Quick Start

```bash
# Install testing tools
pip install -r requirements-test.txt

# Run ALL tests
pytest -v

# Answer your question: "Is debug mode on?"
pytest tests/debug_checks/ -v

# Test just authentication logic
pytest tests/unit/core/test_auth_use_cases.py -v

# Test just HTTP endpoints
pytest tests/integration/test_auth_endpoints.py -v
```

---

## 📁 Folder Structure

| Folder | Purpose | Tests | Example |
|--------|---------|-------|---------|
| `tests/unit/core/` | **Business Logic** — Pure Python logic, no database | 15+ | `test_user_entity.py`, `test_auth_use_cases.py` |
| `tests/unit/infrastructure/` | **Adapters & Services** — JWT tokens, DB connections | 8+ | `test_token_service.py` |
| `tests/integration/` | **HTTP Endpoints** — Full request/response cycle | 14+ | `test_auth_endpoints.py` |
| `tests/debug_checks/` | **Safety Guardrails** — Pre-deployment checks | 25+ | `test_config_safety.py` |

---

## ❓ How to Debug: Common Scenarios

### Scenario 1: "My login is broken"
```bash
# Run auth tests
pytest tests/unit/core/test_auth_use_cases.py -v

# Test fails? Example:
# FAILED test_login_returns_user_id
# AssertionError: assert 'user_id' in {}

# Solution: Fix app/core/use_cases/auth_use_cases.py
# The test shows you EXACTLY what's wrong
```

### Scenario 2: "Is DEBUG mode on in production?"
```bash
# Run safety checks
pytest tests/debug_checks/ -v

# Look for failures like:
# FAILED test_debug_is_false_in_production
# CRITICAL: DEBUG=True but ENVIRONMENT=production!

# Solution: Set DEBUG=False in .env
```

### Scenario 3: "HTTP endpoints don't work"
```bash
# Run integration tests
pytest tests/integration/test_auth_endpoints.py -v

# FAILED test_login_endpoint_returns_200_on_valid_credentials
# Solution: Check app/server/routers/auth_router.py
```

---

## 🎯 Run Tests by Category

```bash
# Run ONLY unit tests (fast, pure logic)
pytest tests/unit/ -v

# Run ONLY integration tests (slower, real HTTP)
pytest tests/integration/ -v

# Run ONLY safety checks (before deploying!)
pytest tests/debug_checks/ -v

# Run tests with specific marker
pytest -m unit              # all unit tests
pytest -m auth              # all auth tests
pytest -m "not slow"        # skip slow tests
```

---

## 🔍 Run ONE Test (for debugging)

```bash
# Run specific test file
pytest tests/unit/core/test_auth_use_cases.py -v

# Run specific test class
pytest tests/unit/core/test_auth_use_cases.py::TestAuthUseCases -v

# Run specific test function
pytest tests/unit/core/test_auth_use_cases.py::TestAuthUseCases::test_login_returns_user_id -v

# Show print() output
pytest tests/unit/core/test_auth_use_cases.py -v -s

# Detailed error trace
pytest tests/unit/core/test_auth_use_cases.py -v --tb=long
```

---

## 📝 Fixtures — Helper Objects in Your Tests

See `tests/conftest.py` for:

| Fixture | What it does | Usage |
|---------|-------------|-------|
| `auth_port` | Fake authentication service | `def test_something(auth_port):` |
| `notification_port` | Fake notification service | `def test_something(notification_port):` |
| `telemetry_repo` | Fake database | `def test_something(telemetry_repo):` |
| `test_user_data` | Sample user dictionary | `def test_something(test_user_data):` |
| `test_token` | Sample JWT token | `def test_something(test_token):` |
| `mock_env` | Development env variables | `def test_something(mock_env):` |
| `production_env` | Production env variables | `def test_something(production_env):` |

---

## 🚨 Pre-Deployment Checklist

**ALWAYS run this before deploying to production:**

```bash
# Set production environment
ENVIRONMENT=production pytest tests/debug_checks/ -v

# All tests must PASS:
# ✓ DEBUG is False
# ✓ SECRET_KEY is not placeholder
# ✓ GitHub credentials are set
# ✓ Database URL points to production
# ✓ CORS doesn't allow wildcard
# ✓ No localhost in production config
```

If any test fails, **DO NOT DEPLOY**. Fix it first.

---

## 📖 Detailed Guide

For complete commands, markers, fixtures, and troubleshooting, see: [PYTEST_GUIDE.py](../PYTEST_GUIDE.py)

---

## ✅ Test Summary

- **Unit Tests**: 30+
- **Integration Tests**: 14+
- **Safety Checks**: 25+
- **Total**: 70+ tests covering your entire app

---

## 💡 Next Steps

1. **Write your app logic** in `app/core/` and `app/infrastructure/`
2. **Add tests** in corresponding `tests/` folder
3. **Run tests frequently** while developing
4. **Fix failures** immediately (test tells you what's wrong!)
5. **Before deploying**: `pytest tests/debug_checks/ -v`

Happy testing! 🚀
