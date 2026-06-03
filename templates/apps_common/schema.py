"""drf-spectacular postprocessing hook: document the error envelope in OpenAPI.

The runtime error envelope is produced by
``apps.common.exceptions.exception_handler``; the generated schema does not know
about it unless we say so. This hook registers the ``ErrorEnvelope`` component
(from ``apps.common.serializers``) and points every 4xx/5xx response that has no
explicit body at it, so the published contract matches what the API actually
returns on failure.

Wire it in settings::

    SPECTACULAR_SETTINGS = {
        ...,
        "POSTPROCESSING_HOOKS": [
            "apps.common.schema.add_error_envelope_responses",
        ],
    }
"""

from __future__ import annotations

from typing import Any

from drf_spectacular.plumbing import build_basic_type
from drf_spectacular.utils import OpenApiTypes

# Inline JSON-Schema for the envelope. Inlined (rather than a $ref to a generated
# component) so the hook has no ordering dependency on serializer registration.
_ERROR_ENVELOPE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "error": {
            "type": "object",
            "properties": {
                "code": build_basic_type(OpenApiTypes.STR),
                "message": build_basic_type(OpenApiTypes.STR),
                "details": {
                    "type": "object",
                    "additionalProperties": True,
                    "nullable": True,
                },
            },
            "required": ["code", "message", "details"],
        }
    },
    "required": ["error"],
}


def add_error_envelope_responses(
    result: dict[str, Any],
    generator: Any,
    request: Any,
    public: bool,
) -> dict[str, Any]:
    """Attach the error-envelope schema to documented 4xx/5xx responses.

    Iterates every operation in the generated OpenAPI ``result`` and, for each
    response whose status code starts with ``4`` or ``5`` but carries no JSON
    body schema, sets an ``application/json`` content type pointing at the shared
    error envelope. Responses that already declare a body are left untouched, so
    hand-annotated error shapes win.

    Args:
        result: The OpenAPI document built by ``drf-spectacular`` so far.
        generator: The active schema generator (unused; part of the hook API).
        request: The request driving generation, or ``None`` (unused).
        public: Whether a public schema is being generated (unused).

    Returns:
        The same ``result`` dict, mutated in place, for hook chaining.
    """
    paths = result.get("paths", {})
    for path_item in paths.values():
        for operation in path_item.values():
            if not isinstance(operation, dict):
                continue
            responses = operation.get("responses")
            if not isinstance(responses, dict):
                continue
            for code, response in responses.items():
                if not (str(code).startswith("4") or str(code).startswith("5")):
                    continue
                if not isinstance(response, dict):
                    continue
                if response.get("content"):
                    continue
                response["content"] = {
                    "application/json": {"schema": dict(_ERROR_ENVELOPE_SCHEMA)}
                }
    return result
