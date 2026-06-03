"""Permission used by the sample "forbidden" view to assert 403 behaviour."""

from rest_framework import permissions


class IsStaff(permissions.BasePermission):
    def has_permission(self, request, view) -> bool:
        return bool(request.user and request.user.is_staff)
