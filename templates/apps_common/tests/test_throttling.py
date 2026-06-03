"""Throttling convention: the login scope is capped at 5 requests/min -> 429.

The 6th request in a window returns 429 with the throttled error envelope.
"""

import pytest


@pytest.mark.django_db
def test_login_scope_throttles_after_five(api_client):
    """Five POSTs succeed; the sixth is throttled with code=throttled."""
    for _ in range(5):
        ok = api_client.post("/login/", {}, format="json")
        assert ok.status_code == 200
    blocked = api_client.post("/login/", {}, format="json")
    assert blocked.status_code == 429
    body = blocked.json()
    assert body["error"]["code"] == "throttled"
    assert body["error"]["details"] is None
