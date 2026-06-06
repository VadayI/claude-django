"""Documentation-only serializers describing the project error envelopes.

These serializers carry no runtime validation duty — every error response is
built by ``apps.common.exceptions.exception_handler``. They exist so
``drf-spectacular`` can render the envelope shapes in the OpenAPI schema (see
``apps.common.schema``), giving API consumers a typed contract for failures.
"""

from rest_framework import serializers


class FieldErrorSerializer(serializers.Serializer):
    """One entry in the 400 validation envelope's ``errors`` array.

    Maps a single offending field to its DRF error ``code`` and human message;
    ``field`` is ``null`` for non-field (cross-field) errors.
    """

    field = serializers.CharField(
        allow_null=True,
        help_text="Offending field path (dotted for nested); null for non-field errors.",
    )
    code = serializers.CharField(
        help_text="Stable machine-readable error token, e.g. ``invalid``, ``required``.",
    )
    message = serializers.CharField(
        help_text="Human-readable description of the field error.",
    )


class ValidationErrorEnvelopeSerializer(serializers.Serializer):
    """The 400 body: ``{"errors": [{field, code, message}]}``.

    Referenced by the ``drf-spectacular`` hook in ``apps.common.schema`` to attach
    the validation-error schema to documented 400 responses.
    """

    errors = FieldErrorSerializer(many=True)


class DetailErrorSerializer(serializers.Serializer):
    """The non-validation error body: ``{"detail": "<human>"}``.

    Used for 401/403/404/409/429/5xx; carries no per-field structure.
    """

    detail = serializers.CharField(
        help_text="Human-readable description of the error.",
    )


class HealthSerializer(serializers.Serializer):
    """The body returned by ``apps.common.views.HealthView``.

    Documentation-only: the view builds the dict directly. ``status`` is a short
    machine token — ``"ok"`` on a 200 (process up, database reachable) or
    ``"unavailable"`` on a 503 (a backing service is down).
    """

    status = serializers.CharField(
        help_text='Health token: "ok" (200) or "unavailable" (503).',
    )
