"""Throwaway model exercising the project DRF conventions in tests only.

``SampleItem`` is NOT a domain entity and ships no production migration. It is
given a table at test time via ``MIGRATION_MODULES = {"common":
"apps.common.tests.migrations"}`` in the dev/test settings, so the convention
suite (pagination, default permission, error envelope, throttling) has a real
queryset to page over and a real unique constraint to violate.
"""

from django.db import models


class SampleItem(models.Model):
    """A minimal record with a unique ``name`` used only by the convention tests.

    The unique constraint on ``name`` lets the error-envelope tests trigger a
    409 on duplicate create; ``created_at`` gives a stable ordering for the
    pagination tests.
    """

    name = models.CharField(max_length=120, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "common"
        ordering = ["id"]

    def __str__(self) -> str:
        return self.name
