"""Sample DRF views used only by the convention tests (override urlconf).

These are never mounted in ``config/urls.py`` (Variant B: the sample surface
lives in tests, the cross-cutting infrastructure lives in production). Each view
exercises one project convention:

* ``SampleItemListCreateView`` -> default pagination + default IsAuthenticated +
  Conflict(409) on duplicate.
* ``SampleItemRetrieveView``   -> 404 -> not_found envelope.
* ``LoginThrottledView``       -> ScopedRateThrottle("login") -> 429 throttled.
* ``ForbiddenView``            -> IsStaff -> 403 permission_denied.
"""

from django.db import IntegrityError
from rest_framework import generics, permissions, views
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from apps.common.exceptions import Conflict
from apps.common.tests.models import SampleItem
from apps.common.tests.permissions_sample import IsStaff
from apps.common.tests.serializers_sample import SampleItemSerializer


class SampleItemListCreateView(generics.ListCreateAPIView):
    queryset = SampleItem.objects.all()
    serializer_class = SampleItemSerializer

    def perform_create(self, serializer):
        try:
            serializer.save()
        except IntegrityError as exc:
            raise Conflict("A SampleItem with this name already exists.") from exc


class SampleItemRetrieveView(generics.RetrieveAPIView):
    queryset = SampleItem.objects.all()
    serializer_class = SampleItemSerializer


class LoginThrottledView(views.APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    def post(self, request: Request) -> Response:
        return Response({"ok": True})


class ForbiddenView(views.APIView):
    permission_classes = [IsStaff]

    def get(self, request: Request) -> Response:
        return Response({"ok": True})
