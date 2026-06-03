"""Documentation-only serializers describing the project error envelope.

These serializers carry no runtime validation duty — every error response is
built by ``apps.common.exceptions.exception_handler``. They exist so
``drf-spectacular`` can render the envelope shape in the OpenAPI schema (see
``apps.common.schema``), giving API consumers a typed contract for failures.
"""

from rest_framework import serializers


class ErrorDetailSerializer(serializers.Serializer):
    """The ``error`` object inside every non-2xx response body.

    Mirrors the envelope produced by ``apps.common.exceptions.exception_handler``:
    a stable machine code, a human-readable message, and an optional field-keyed
    ``details`` map (present only for ``400 validation_error``).
    """

    code = serializers.CharField(
        help_text="Stable machine-readable error token, e.g. ``validation_error``.",
    )
    message = serializers.CharField(
        help_text="Human-readable description of the error.",
    )
    details = serializers.DictField(
        required=False,
        allow_null=True,
        help_text="Field-keyed validation errors for 400; null for other codes.",
    )


class ErrorEnvelopeSerializer(serializers.Serializer):
    """The top-level error envelope: ``{\"error\": {code, message, details}}``.

    Referenced by the ``drf-spectacular`` postprocessing hook in
    ``apps.common.schema`` to attach a consistent error schema to 4xx/5xx
    responses across the API.
    """

    error = ErrorDetailSerializer()


class HealthSerializer(serializers.Serializer):
    """The body returned by ``apps.common.views.HealthView``.

    Documentation-only: the view builds the dict directly. ``status`` is a short
    machine token — ``"ok"`` on a 200 (process up, database reachable) or
    ``"unavailable"`` on a 503 (a backing service is down).
    """

    status = serializers.CharField(
        help_text='Health token: "ok" (200) or "unavailable" (503).',
    )
