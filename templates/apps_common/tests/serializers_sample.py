"""Serializer for the test-only SampleItem.

Validation here is deliberately minimal: ``name`` must be at least 3 chars
(drives the 400 validation_error envelope test). The model's DB-level unique
constraint is intentionally NOT mirrored as a DRF ``UniqueValidator`` so that a
duplicate name surfaces as a 409 ``Conflict`` from the view, not a 400.
"""

from rest_framework import serializers

from apps.common.tests.models import SampleItem


class SampleItemSerializer(serializers.ModelSerializer):
    name = serializers.CharField(min_length=3)

    class Meta:
        model = SampleItem
        fields = ["id", "name", "created_at"]
        read_only_fields = ["id", "created_at"]
        # No automatic UniqueValidator on `name`: the view raises Conflict (409)
        # on a duplicate so the error-envelope test sees code == "conflict".
        extra_kwargs = {"name": {"validators": []}}
