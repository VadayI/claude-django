"""Health endpoint convention: public, 200 + status payload, DB-backed readiness.

Mounts the real ``apps.common.urls`` (not the sample urlconf) inside each test
body via the ``settings`` fixture, which runs after the package-level autouse
fixture in ``conftest.py`` and therefore wins.
"""

import pytest

COMMON_URLCONF = "apps.common.urls"


@pytest.mark.django_db
def test_health_is_public_and_200(api_client, settings):
    """Anonymous GET /health/ returns 200 despite the IsAuthenticated default."""
    settings.ROOT_URLCONF = COMMON_URLCONF
    resp = api_client.get("/health/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.django_db
def test_health_reports_database_up(api_client, settings):
    """A healthy instance reports the database as reachable."""
    settings.ROOT_URLCONF = COMMON_URLCONF
    resp = api_client.get("/health/")
    assert resp.json()["database"] == "up"


@pytest.mark.django_db
def test_health_does_not_require_auth_token(api_client, settings):
    """No credentials are needed: the route is not behind the auth wall (401)."""
    settings.ROOT_URLCONF = COMMON_URLCONF
    resp = api_client.get("/health/")
    assert resp.status_code != 401
