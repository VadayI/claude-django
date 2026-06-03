"""URL routes exposed by the cross-cutting ``common`` app.

Mounted under the project API prefix from ``config/urls.py`` (e.g.
``path("api/v1/", include("apps.common.urls"))``), so the health probe is
reachable at ``/api/v1/health/``. Domain resources live in their own apps; this
module only wires the project-wide infrastructure endpoints.
"""

from django.urls import path

from apps.common.views import HealthView

app_name = "common"

urlpatterns = [
    path("health/", HealthView.as_view(), name="health"),
]
