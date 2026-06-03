"""Fixtures for the DRF convention tests.

Provides API clients (anonymous + authenticated), regular/staff users, mounts
the sample override urlconf for the whole package, and clears the throttle cache
between tests so rate limits do not leak across cases.
"""

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APIClient

SAMPLE_URLCONF = "apps.common.tests.urls_sample"


@pytest.fixture(autouse=True)
def _use_sample_urlconf(settings):
    """Mount the sample override urlconf for every test in this package."""
    settings.ROOT_URLCONF = SAMPLE_URLCONF


@pytest.fixture(autouse=True)
def _clear_throttle_cache():
    """Reset DRF throttle counters (cache-backed) before and after each test."""
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def api_client():
    """An unauthenticated DRF APIClient."""
    return APIClient()


@pytest.fixture
def user(db):
    """A regular (non-staff) user."""
    return get_user_model().objects.create_user(
        username="alice", password="pw-alice-12345"
    )


@pytest.fixture
def staff_user(db):
    """A staff user (passes the IsStaff sample permission)."""
    return get_user_model().objects.create_user(
        username="boss", password="pw-boss-12345", is_staff=True
    )


@pytest.fixture
def auth_client(api_client, user):
    """An APIClient authenticated as the regular ``user`` fixture."""
    api_client.force_authenticate(user=user)
    return api_client
