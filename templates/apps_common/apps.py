"""App configuration for the cross-cutting ``common`` app."""

from django.apps import AppConfig


class CommonAppConfig(AppConfig):
    """Registers the ``common`` app that hosts project-wide infrastructure.

    Owns the error envelope (``exceptions``), its OpenAPI documentation
    (``serializers``, ``schema``), and any future cross-cutting base classes.
    It declares no domain models of its own in production; the sample model used
    by the convention tests lives under ``apps.common.tests``.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.common"
    label = "common"
