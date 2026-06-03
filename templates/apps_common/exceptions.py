"""Project-wide DRF exception handling: a single error envelope for all 4xx/5xx.

Every error response from the API has the shape::

    {"error": {"code": <machine>, "message": <human>, "details": <dict|null>}}

``code`` is a stable machine-readable token (``validation_error``,
``not_authenticated``, ``permission_denied``, ``not_found``, ``conflict``,
``throttled``, ``server_error``). ``details`` carries field-keyed validation
errors for ``400`` responses and is ``null`` for every other status. This module
is wired via ``REST_FRAMEWORK["EXCEPTION_HANDLER"]`` so the envelope applies to
the whole project without per-view code.
"""

from __future__ import annotations

from typing import Any

from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

# Maps an HTTP status code to the stable machine-readable ``error.code`` token.
# Anything not listed here (any other 5xx) falls back to ``server_error``.
_STATUS_TO_CODE: dict[int, str] = {
    status.HTTP_400_BAD_REQUEST: "validation_error",
    status.HTTP_401_UNAUTHORIZED: "not_authenticated",
    status.HTTP_403_FORBIDDEN: "permission_denied",
    status.HTTP_404_NOT_FOUND: "not_found",
    status.HTTP_409_CONFLICT: "conflict",
    status.HTTP_429_TOO_MANY_REQUESTS: "throttled",
}


class Conflict(APIException):
    """A 409 Conflict, e.g. a uniqueness clash the client can resolve and retry.

    Raise this from serializers, services, or views when a request collides with
    existing state (duplicate unique key, version conflict). It renders through
    the project envelope with ``code == "conflict"`` and ``details == null``.
    """

    status_code = status.HTTP_409_CONFLICT
    default_detail = "The request conflicts with the current state of the resource."
    default_code = "conflict"


def _human_message(data: Any, fallback: str) -> str:
    """Return a single human-readable sentence describing the error.

    DRF packs error detail in several shapes (a bare string, a list of strings,
    or a ``{field: [msgs]}`` dict). This collapses any of them to one line for
    the envelope's ``message`` field; the structured field errors are preserved
    separately in ``details``.

    Args:
        data: The ``response.data`` produced by DRF's default handler.
        fallback: Message to use when ``data`` carries no usable text.

    Returns:
        A non-empty human-readable string.
    """
    if isinstance(data, dict):
        detail = data.get("detail")
        if detail is not None:
            return str(detail)
        for value in data.values():
            if isinstance(value, (list, tuple)) and value:
                return str(value[0])
            if value:
                return str(value)
        return fallback
    if isinstance(data, (list, tuple)) and data:
        return str(data[0])
    if data:
        return str(data)
    return fallback


def _field_details(data: Any) -> dict[str, Any] | None:
    """Return field-keyed validation errors for a 400, or ``None`` otherwise.

    Only ``validation_error`` (400) responses expose ``details``. A DRF
    ``ValidationError`` whose payload is a ``{field: [...]}`` dict is passed
    through as-is (minus the non-field ``detail`` key); a non-dict 400 payload
    (a bare string/list) carries no per-field structure, so ``details`` is
    ``null``.

    Args:
        data: The ``response.data`` produced by DRF's default handler.

    Returns:
        The field-error dict, or ``None`` when there is no per-field structure.
    """
    if isinstance(data, dict):
        details = {key: value for key, value in data.items() if key != "detail"}
        return details or None
    return None


def exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    """Render every handled DRF exception in the project's error envelope.

    Delegates to DRF's default handler to classify the exception and pick the
    status code, then rewrites the body to
    ``{"error": {"code", "message", "details"}}``. ``details`` is the field-error
    dict only for ``400 validation_error``; for ``401/403/404/409/429`` (and any
    other handled status) it is ``null``. Returns ``None`` for exceptions DRF
    does not handle (genuine ``500``s), letting Django produce the default
    server-error response unchanged.

    Args:
        exc: The exception raised while processing the request.
        context: DRF handler context (``view``, ``request``, ``args``, ...).

    Returns:
        A ``Response`` with the enveloped body, or ``None`` if unhandled.
    """
    response = drf_exception_handler(exc, context)
    if response is None:
        return None

    code = _STATUS_TO_CODE.get(response.status_code, "server_error")
    message = _human_message(response.data, fallback=str(exc) or "Error.")
    details = (
        _field_details(response.data)
        if response.status_code == status.HTTP_400_BAD_REQUEST
        else None
    )

    response.data = {
        "error": {
            "code": code,
            "message": message,
            "details": details,
        }
    }
    return response
