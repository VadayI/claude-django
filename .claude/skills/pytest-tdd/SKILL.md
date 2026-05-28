---
name: pytest-tdd
description: TDD with pytest + pytest-django for Django/DRF — fixtures, factories, APIClient, the RED-GREEN-REFACTOR pattern. Always activate during testing.
---

# pytest + TDD

## Cycle
RED (failing test) → GREEN (minimal code) → REFACTOR. No code without a test first.

## Tools
- `@pytest.mark.django_db`, `pytest-django` fixtures (`client`, `settings`).
- DRF: `from rest_framework.test import APIClient`.
- `factory_boy` for factories; `pytest-cov` for coverage.

## Feature test example
```python
import pytest
from rest_framework.test import APIClient

@pytest.mark.django_db
def test_register_creates_user_when_payload_valid():
    client = APIClient()
    resp = client.post("/api/v1/auth/register/", {
        "email": "a@b.com", "password": "Str0ngPass!"
    }, format="json")
    assert resp.status_code == 201
    assert resp.data["email"] == "a@b.com"
    assert "password" not in resp.data

@pytest.mark.django_db
def test_register_rejects_duplicate_email():
    ...  # 409 / 400
```

## What to cover
success, 400, 401, 403, 404, conflicts, edge cases, model/serializer business logic.

## Commands
```bash
docker compose exec backend pytest --cov=apps --cov-report=term-missing
```
<!-- Last reviewed/updated: 2026-05-27 -->
