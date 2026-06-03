"""Error-envelope convention: every 4xx body is {"error": {code, message, details}}.

``details`` is a field-keyed dict for 400 validation errors and ``null`` for
401 / 403 / 404 / 409.
"""

import pytest

from apps.common.tests.models import SampleItem


def _assert_envelope(body, expected_code):
    assert set(body) == {"error"}
    error = body["error"]
    assert set(error) == {"code", "message", "details"}
    assert error["code"] == expected_code
    assert isinstance(error["message"], str) and error["message"]


@pytest.mark.django_db
def test_validation_error_400_has_field_details(auth_client):
    """A too-short name yields code=validation_error with a field-keyed details dict."""
    resp = auth_client.post("/sample-items/", {"name": "ab"}, format="json")
    assert resp.status_code == 400
    body = resp.json()
    _assert_envelope(body, "validation_error")
    assert isinstance(body["error"]["details"], dict)
    assert "name" in body["error"]["details"]


@pytest.mark.django_db
def test_not_authenticated_401_details_null(api_client):
    """An anonymous request yields code=not_authenticated and details=null."""
    resp = api_client.get("/sample-items/")
    assert resp.status_code == 401
    body = resp.json()
    _assert_envelope(body, "not_authenticated")
    assert body["error"]["details"] is None


@pytest.mark.django_db
def test_permission_denied_403_details_null(auth_client):
    """A forbidden request yields code=permission_denied and details=null."""
    resp = auth_client.get("/forbidden/")
    assert resp.status_code == 403
    body = resp.json()
    _assert_envelope(body, "permission_denied")
    assert body["error"]["details"] is None


@pytest.mark.django_db
def test_not_found_404_details_null(auth_client):
    """A missing object yields code=not_found and details=null (not a stray string)."""
    resp = auth_client.get("/sample-items/999999/")
    assert resp.status_code == 404
    body = resp.json()
    _assert_envelope(body, "not_found")
    assert body["error"]["details"] is None


@pytest.mark.django_db
def test_conflict_409_details_null(auth_client):
    """A duplicate name yields code=conflict (409) and details=null."""
    SampleItem.objects.create(name="dupe")
    resp = auth_client.post("/sample-items/", {"name": "dupe"}, format="json")
    assert resp.status_code == 409
    body = resp.json()
    _assert_envelope(body, "conflict")
    assert body["error"]["details"] is None
