"""Default pagination convention: PageNumberPagination with PAGE_SIZE=20."""

import pytest

from apps.common.tests.models import SampleItem


@pytest.mark.django_db
def test_list_is_paginated_envelope(auth_client):
    """A list response uses the DRF page envelope (count/next/previous/results)."""
    SampleItem.objects.bulk_create(
        [SampleItem(name=f"item-{i:03d}") for i in range(5)]
    )
    resp = auth_client.get("/sample-items/")
    assert resp.status_code == 200
    body = resp.json()
    assert set(body) == {"count", "next", "previous", "results"}
    assert body["count"] == 5
    assert len(body["results"]) == 5


@pytest.mark.django_db
def test_page_size_caps_results_at_20(auth_client):
    """With 25 items the first page returns exactly PAGE_SIZE (20) results."""
    SampleItem.objects.bulk_create(
        [SampleItem(name=f"item-{i:03d}") for i in range(25)]
    )
    resp = auth_client.get("/sample-items/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 25
    assert len(body["results"]) == 20
    assert body["next"] is not None


@pytest.mark.django_db
def test_second_page_returns_remainder(auth_client):
    """Page 2 returns the remaining 5 items and a null ``next``."""
    SampleItem.objects.bulk_create(
        [SampleItem(name=f"item-{i:03d}") for i in range(25)]
    )
    resp = auth_client.get("/sample-items/?page=2")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["results"]) == 5
    assert body["next"] is None
