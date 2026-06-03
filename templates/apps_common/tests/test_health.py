"""Health endpoint convention: public 200/ok when up, 503 when the DB is down."""

from unittest import mock

import pytest


@pytest.mark.django_db
def test_health_is_public_and_ok(api_client):
    """An anonymous GET /health/ returns 200 with status ok (no auth required)."""
    resp = api_client.get("/health/")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.django_db
def test_health_reports_503_when_database_down(api_client):
    """When the DB connectivity check fails, /health/ fails closed with 503."""
    target = "apps.common.views.HealthView._database_ok"
    with mock.patch(target, return_value=False):
        resp = api_client.get("/health/")
    assert resp.status_code == 503
    assert resp.json() == {"status": "unavailable"}


@pytest.mark.django_db
def test_health_does_not_throttle(api_client):
    """Repeated probes are not rate-limited (throttling disabled on the view)."""
    for _ in range(10):
        resp = api_client.get("/health/")
        assert resp.status_code == 200
