"""Reusable authorization base classes shared across domain apps.

``HasScope`` enforces token scopes for the service-to-service profile (D5, ADR
0018): a JWT carries a space-delimited ``scope`` claim, and an endpoint declares
the scopes it requires via ``required_scopes``. See
``.claude/rules/serializers-permissions.md``.
"""

from __future__ import annotations

from typing import Any

from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView


def _token_scopes(token: Any) -> set[str]:
    """Return the set of scopes carried by ``token`` (its ``scope`` claim).

    Accepts a simplejwt token (mapping-like), a plain dict, or an object with a
    ``scope`` attribute. A missing/empty claim yields the empty set.

    Args:
        token: The value of ``request.auth`` (validated token), or ``None``.

    Returns:
        The granted scopes as a set of strings.
    """
    if token is None:
        return set()
    try:
        raw = token.get("scope")  # type: ignore[union-attr]
    except (AttributeError, TypeError):
        raw = getattr(token, "scope", None)
    if not raw:
        return set()
    if isinstance(raw, (list, tuple, set)):
        return {str(s) for s in raw}
    return set(str(raw).split())


class HasScope(BasePermission):
    """Grant access only when the token carries every scope the view requires.

    The view lists required scopes in ``required_scopes`` (a list/tuple); the
    granted scopes are read from the authenticated token's ``scope`` claim on
    ``request.auth``. A view with no ``required_scopes`` imposes no scope check
    (stack with ``IsAuthenticated`` for the authentication requirement). Missing
    or insufficient scope → 403.
    """

    message = "Token is missing a required scope."

    def has_permission(self, request: Request, view: APIView) -> bool:
        """Return whether the request's token satisfies the view's scopes.

        Args:
            request: The incoming request (``request.auth`` holds the token).
            view: The target view; reads ``required_scopes``.

        Returns:
            ``True`` when no scopes are required or all required scopes are
            granted; ``False`` otherwise.
        """
        required = set(getattr(view, "required_scopes", []) or [])
        if not required:
            return True
        return required.issubset(_token_scopes(request.auth))
