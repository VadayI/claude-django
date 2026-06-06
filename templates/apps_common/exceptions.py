"""Project-wide DRF exception handling: the contract error envelope for 4xx/5xx.

Two shapes, per the external contract (ADR 0020, ``.claude/rules/api-docs.md``):

- **Validation errors (400)**::

      {"errors": [{"field": <str|null>, "code": <machine>, "message": <human>}]}

- **Every other handled error (401/403/404/409/429/5xx)**::

      {"detail": <human>}

Wired via ``REST_FRAMEWORK["EXCEPTION_HANDLER"]`` so the envelope applies to the
whole project without per-view code.
"""

from __future__ import annotations

from typing import Any

from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

# Sentinel field name DRF uses for errors not tied to a single field.
_NON_FIELD = "non_field_errors"


class Conflict(APIException):
    """A 409 Conflict, e.g. a uniqueness clash the client can resolve and retry.

    Raise this from serializers, services, or views when a request collides with
    existing state (duplicate unique key, version conflict). It renders through
    the project envelope as ``{"detail": ...}`` with HTTP 409.
    """

    status_code = status.HTTP_409_CONFLICT
    default_detail = "The request conflicts with the current state of the resource."
    default_code = "conflict"


def _error_item(field: str | None, value: Any) -> dict[str, Any]:
    """Build one ``{field, code, message}`` entry from a DRF error value.

    The DRF ``ErrorDetail`` is a ``str`` subclass carrying a ``.code``; plain
    strings fall back to ``"invalid"``.

    Args:
        field: Field path the error belongs to, or ``None`` for non-field errors.
        value: A DRF ``ErrorDetail`` or plain string message.

    Returns:
        A dict with ``field``, ``code`` and ``message`` keys.
    """
    code = getattr(value, "code", None) or "invalid"
    return {"field": field, "code": str(code), "message": str(value)}


def _flatten_errors(data: Any, field: str | None = None) -> list[dict[str, Any]]:
    """Flatten a DRF validation payload into a list of ``{field, code, message}``.

    DRF packs validation detail as nested ``{field: [...]}`` dicts, lists, or bare
    strings. This walks the structure, dotting nested field paths
    (``address.zip``) and mapping the ``non_field_errors`` key to ``field: null``.

    Args:
        data: The ``response.data`` produced by DRF's default handler for a 400.
        field: Accumulated field path during recursion.

    Returns:
        A flat list of field-error entries (possibly empty).
    """
    items: list[dict[str, Any]] = []
    if isinstance(data, dict):
        for key, value in data.items():
            child = field if key == _NON_FIELD else (key if field is None else f"{field}.{key}")
            items.extend(_flatten_errors(value, field=child))
    elif isinstance(data, (list, tuple)):
        for element in data:
            if isinstance(element, (dict, list, tuple)):
                items.extend(_flatten_errors(element, field=field))
            else:
                items.append(_error_item(field, element))
    else:
        items.append(_error_item(field, data))
    return items


def _detail_message(data: Any, fallback: str) -> str:
    """Collapse a DRF error payload to one human-readable sentence.

    Used for non-validation responses (401/403/404/409/429/5xx), whose envelope
    carries only ``detail``.

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


def exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    """Render every handled DRF exception in the contract's error envelope.

    Delegates to DRF's default handler to classify the exception and pick the
    status code, then rewrites the body: a ``400`` becomes
    ``{"errors": [{field, code, message}]}``; every other handled status becomes
    ``{"detail": <human>}``. Returns ``None`` for exceptions DRF does not handle
    (genuine ``500``s), letting Django produce the default response unchanged.

    Args:
        exc: The exception raised while processing the request.
        context: DRF handler context (``view``, ``request``, ``args``, ...).

    Returns:
        A ``Response`` with the enveloped body, or ``None`` if unhandled.
    """
    response = drf_exception_handler(exc, context)
    if response is None:
        return None

    if response.status_code == status.HTTP_400_BAD_REQUEST:
        errors = _flatten_errors(response.data)
        if not errors:
            errors = [_error_item(None, str(exc) or "Invalid request.")]
        response.data = {"errors": errors}
    else:
        response.data = {"detail": _detail_message(response.data, fallback=str(exc) or "Error.")}
    return response
