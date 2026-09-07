---
name: tdd-discipline
description: >-
  Disciplined Test-Driven Development (Red-Green-Refactor), writing failing assertion tests
  before production code, Pytest transactional database fixtures with rollback, and maintaining
  >= 85% test coverage. Use when writing tests or implementing any feature in the squad.
---

# TDD Discipline: Red-Green-Refactor Playbook

Normative instructions to enforce strict test-driven development across all backend, engine, and frontend modules.

## 1. The Red-Green-Refactor Cycle

1. **RED (Red Phase)**:
   - Read the acceptance criteria in the Spec (`Given/When/Then`).
   - Write the test in `backend/tests/test_<module>.py` asserting the expected outcome.
   - Run the test suite: `pytest backend/tests/test_<module>.py`.
   - **Mandatory assertion**: The test MUST fail with an explicit `AssertionError`, `404 Not Found` or `NameError` proving the feature does not exist yet.
2. **GREEN (Green Phase)**:
   - Write the minimal production code necessary to turn the test green.
   - Run the test suite: `pytest backend/tests/test_<module>.py`.
   - Confirm all tests pass with exit code 0.
3. **REFACTOR (Refactor Phase)**:
   - Clean up code, optimize queries, remove duplication, and ensure adherence to clean architecture.
   - Re-run full test suite to guarantee zero regression: `pytest --cov=app --cov-report=term-missing`.

## 2. Transactional Test Database Fixtures

Never leave dirty state between test runs. Use an isolated async test database session wrapped in an automatic rollback transaction:

```python
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.main import app
from app.database import get_db

@pytest.fixture
async def client(db_session: AsyncSession):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
```

## 3. Minimum Coverage Rule

- All pull requests must maintain at least **85% code coverage**.
- Run coverage verification locally before opening a PR:
  ```bash
  pytest --cov=backend/app --cov-fail-under=85
  ```
