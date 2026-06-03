"""URL routes for cross-cutting ``common`` endpoints.

Currently exposes the public health check. Wired into the project root urlconf
in ``config/urls.py`` with ``path("", include("apps.common.urls"))`` so the route
resolves at ``/health/``.
"""

from django.urls import path

from apps.common.views import HealthView

app_name = "common"

urlpatterns = [
    path("health/", HealthView.as_view(), name="health"),
]
