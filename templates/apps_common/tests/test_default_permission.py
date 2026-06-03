"""Default permission convention: IsAuthenticated applies without per-view config."""

import pytest

from apps.common.tests.models import SampleItem


@pytest.mark.django_db
def test_anonymous_list_is_401(api_client):
    """An anonymous request to a view with no explicit permission is rejected 401."""
    resp = api_client.get("/sample-items/")
    assert resp.status_code == 401


@pytest.mark.django_db
def test_authenticated_list_is_200(auth_client):
    """An authenticated request to the same view succeeds."""
    SampleItem.objects.create(name="visible")
    resp = auth_client.get("/sample-items/")
    assert resp.status_code == 200


@pytest.mark.django_db
def test_non_staff_forbidden_is_403(auth_client):
    """An authenticated-but-unauthorised user gets 403, not 401."""
    resp = auth_client.get("/forbidden/")
    assert resp.status_code == 403


@pytest.mark.django_db
def test_anonymous_forbidden_is_401(api_client):
    """The same forbidden view returns 401 to an anonymous caller."""
    resp = api_client.get("/forbidden/")
    assert resp.status_code == 401
