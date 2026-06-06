"""Error-envelope convention: 400 is {"errors": [...]}; other 4xx are {"detail": ...}.

Validation errors carry a list of ``{field, code, message}`` entries; every other
handled status (401/403/404/409) carries a single ``{"detail": <human>}`` (ADR 0020).
"""

import pytest

from apps.common.tests.models import SampleItem


def _assert_detail(body):
    assert set(body) == {"detail"}
    assert isinstance(body["detail"], str) and body["detail"]


@pytest.mark.django_db
def test_validation_error_400_has_errors_list(auth_client):
    """A too-short name yields a 400 with a field-keyed ``errors`` list."""
    resp = auth_client.post("/sample-items/", {"name": "ab"}, format="json")
    assert resp.status_code == 400
    body = resp.json()
    assert set(body) == {"errors"}
    assert isinstance(body["errors"], list) and body["errors"]
    item = body["errors"][0]
    assert set(item) == {"field", "code", "message"}
    assert any(e["field"] == "name" for e in body["errors"])
    assert all(isinstance(e["message"], str) and e["message"] for e in body["errors"])


@pytest.mark.django_db
def test_not_authenticated_401_detail(api_client):
    """An anonymous request yields 401 with a {"detail": ...} body."""
    resp = api_client.get("/sample-items/")
    assert resp.status_code == 401
    _assert_detail(resp.json())


@pytest.mark.django_db
def test_permission_denied_403_detail(auth_client):
    """A forbidden request yields 403 with a {"detail": ...} body."""
    resp = auth_client.get("/forbidden/")
    assert resp.status_code == 403
    _assert_detail(resp.json())


@pytest.mark.django_db
def test_not_found_404_detail(auth_client):
    """A missing object yields 404 with a {"detail": ...} body (not a stray string)."""
    resp = auth_client.get("/sample-items/999999/")
    assert resp.status_code == 404
    _assert_detail(resp.json())


@pytest.mark.django_db
def test_conflict_409_detail(auth_client):
    """A duplicate name yields 409 with a {"detail": ...} body."""
    SampleItem.objects.create(name="dupe")
    resp = auth_client.post("/sample-items/", {"name": "dupe"}, format="json")
    assert resp.status_code == 409
    _assert_detail(resp.json())
