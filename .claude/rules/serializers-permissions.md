# Serializers & Permissions (DRF)

Validation lives in **serializers**. Authorization lives in **permission classes**. Views stay thin and orchestrate only.

## Serializer validation

Never validate in the view body. Use field- and object-level validators.

```python
from rest_framework import serializers
from .models import Post

class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ["id", "title", "body", "author", "created_at"]
        read_only_fields = ["id", "author", "created_at"]

    def validate_title(self, value: str) -> str:
        if len(value) < 3:
            raise serializers.ValidationError("Title must be at least 3 characters.")
        return value

    def validate(self, attrs):
        # cross-field checks here
        return attrs
```

- Split read/write serializers when shapes differ. Use `read_only`/`write_only`.
- Never expose sensitive fields (password, hashes, tokens).
- Set the owner from `request.user` in the view (`perform_create`), not from client input.

## Permission classes

Authorization is separate, testable classes in `apps/<domain>/permissions.py`.

```python
from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author_id == request.user.id
```

Wire on the view explicitly:

```python
class PostViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
```

## Rules

- Every endpoint declares `permission_classes` explicitly — never rely on defaults by accident.
- Anonymous → **401**; authenticated-but-not-allowed → **403**.
- Prevent **IDOR**: object-level checks (`has_object_permission`) for anything addressed by id; never trust client-supplied owner/ids.
- Validation errors → **400** with field-keyed messages; conflicts (e.g. duplicate unique) → **409**.
- Throttle sensitive endpoints (login, registration) via `throttle_classes`.

## Testing (mandatory)

Per endpoint test: success, 400 (validation), 401 (anonymous), 403 (other user), 404, and IDOR (user A cannot touch user B's object). See @.claude/rules/testing.md.
<!-- Last reviewed/updated: 2026-05-27 -->
