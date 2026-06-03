"""Override ROOT_URLCONF mounting the sample views for the convention tests.

Activated per-test with ``@override_settings(ROOT_URLCONF=...)`` or pytest
``settings.ROOT_URLCONF = "apps.common.tests.urls_sample"``. Never referenced by
the project's real ``config/urls.py``.
"""

from django.urls import path

from apps.common.tests.views_sample import (
    ForbiddenView,
    LoginThrottledView,
    SampleItemListCreateView,
    SampleItemRetrieveView,
)

urlpatterns = [
    path("sample-items/", SampleItemListCreateView.as_view(), name="sample-item-list"),
    path(
        "sample-items/<int:pk>/",
        SampleItemRetrieveView.as_view(),
        name="sample-item-detail",
    ),
    path("login/", LoginThrottledView.as_view(), name="sample-login"),
    path("forbidden/", ForbiddenView.as_view(), name="sample-forbidden"),
]
