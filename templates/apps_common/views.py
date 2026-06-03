"""Cross-cutting views for the ``common`` app: the service health check."""

from django.db import connection
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthView(APIView):
    """Public liveness/readiness probe for proxies and post-deploy smoke tests.

    Returns 200 with ``{"status": "ok", "database": "up"}`` when the process is
    up and the default database answers a trivial query. If the database check
    fails it returns 503 with ``{"status": "unavailable", "database": "down"}``
    so a load balancer or the staging smoke step can detect an unready instance.

    Deliberately public (``AllowAny``) and unauthenticated: a health endpoint
    behind auth cannot be probed by infrastructure. It exposes no data beyond the
    up/down status. Wired at ``/health/`` via ``apps.common.urls`` (see
    ``docs/guides/admin.md`` for the deploy smoke check).
    """

    authentication_classes: list = []
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        """Return service health, pinging the default database connection.

        Returns:
            A DRF ``Response``: 200 when the DB answers ``SELECT 1``; 503 when the
            connection raises, signalling the instance is not ready to serve.
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except Exception:
            # Any database error means the instance is not ready — report 503
            # rather than letting the probe 500, so infra can route around it.
            return Response(
                {"status": "unavailable", "database": "down"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response({"status": "ok", "database": "up"})
