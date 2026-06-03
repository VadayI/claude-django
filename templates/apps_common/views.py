"""Cross-cutting API views shared by the whole project.

Currently hosts the deploy/liveness ``health`` endpoint used by container
healthchecks, the reverse proxy, and post-deploy smoke tests. Unlike the domain
apps, ``common`` owns no business resources; everything here is infrastructure.
"""

from __future__ import annotations

from django.db import connections
from django.db.utils import OperationalError
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import permissions, status, views
from rest_framework.request import Request
from rest_framework.response import Response

from apps.common.serializers import HealthSerializer


class HealthView(views.APIView):
    """Liveness/readiness probe for deploy smoke tests and container healthchecks.

    Public (``AllowAny``) so a reverse proxy or orchestrator can hit it without
    credentials. Returns ``200`` with ``{"status": "ok"}`` when the process is up
    and the default database connection answers a trivial query; returns ``503``
    with ``{"status": "unavailable"}`` when the database is unreachable, so the
    healthcheck fails closed rather than reporting a half-up service as healthy.
    """

    permission_classes = [permissions.AllowAny]
    authentication_classes: list = []
    throttle_classes: list = []

    @extend_schema(
        operation_id="health_check",
        summary="Service health probe",
        description=(
            "Returns 200 with `{\"status\": \"ok\"}` when the process is up and "
            "the database connection is healthy; 503 with "
            "`{\"status\": \"unavailable\"}` otherwise. Public, unauthenticated, "
            "unthrottled — intended for healthchecks and deploy smoke tests."
        ),
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=HealthSerializer, description="Service is healthy."
            ),
            status.HTTP_503_SERVICE_UNAVAILABLE: OpenApiResponse(
                response=HealthSerializer,
                description="A backing service (database) is unreachable.",
            ),
        },
    )
    def get(self, request: Request) -> Response:
        """Report process liveness plus a quick database-connectivity check.

        Args:
            request: The incoming (unauthenticated) GET request.

        Returns:
            A ``Response`` with ``{"status": "ok"}`` and HTTP 200 when the default
            database answers; otherwise ``{"status": "unavailable"}`` and HTTP
            503.
        """
        if self._database_ok():
            return Response({"status": "ok"}, status=status.HTTP_200_OK)
        return Response(
            {"status": "unavailable"},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    @staticmethod
    def _database_ok() -> bool:
        """Return whether the default database answers a trivial query.

        Returns:
            ``True`` if ``SELECT 1`` on the default connection succeeds, ``False``
            if the database raises an ``OperationalError`` (down/unreachable).
        """
        try:
            with connections["default"].cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except OperationalError:
            return False
        return True
