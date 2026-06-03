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

## Default permission policy (project-wide)

The scaffold sets `DEFAULT_PERMISSION_CLASSES = ["rest_framework.permissions.IsAuthenticated"]`
in `config/settings/base.py` (`REST_FRAMEWORK`), so **every endpoint is
authenticated by default**. A view that should be public opts OUT explicitly with
`permission_classes = [permissions.AllowAny]` — never by relying on a missing
default. This makes "forgot to set permissions" fail closed (401), not open.
Stack `IsAuthenticated` with object-level classes (e.g. `IsOwnerOrReadOnly`) as
shown above; authenticated-but-not-allowed still returns **403**.

## Error envelope (project-wide contract)

Every non-2xx response uses one envelope, produced by
`apps.common.exceptions.exception_handler` (wired via
`REST_FRAMEWORK["EXCEPTION_HANDLER"]` — see `apps/common/`):

```json
{"error": {"code": "<machine>", "message": "<human>", "details": <dict|null>}}
```

- `code` is a stable machine token: `validation_error` (400), `not_authenticated`
  (401), `permission_denied` (403), `not_found` (404), `conflict` (409),
  `throttled` (429), `server_error` (500).
- `details` is the **field-keyed validation dict for 400 only**; for every other
  status it is `null` (a `404`/`NotFound` must serialize `details: null`, never a
  loose string).
- Raise `apps.common.exceptions.Conflict` (409) for uniqueness/version clashes —
  do NOT mirror a model's unique constraint as a DRF `UniqueValidator` if you
  want a 409 instead of a 400.

Do not hand-build per-view error bodies; raise the appropriate DRF exception (or
`Conflict`) and let the handler render the envelope. The convention tests live in
`apps/common/tests/` (pagination, default permission, envelope, throttling).

## Testing (mandatory)

Per endpoint test: success, 400 (validation), 401 (anonymous), 403 (other user), 404, and IDOR (user A cannot touch user B's object). See @.claude/rules/testing.md.
<!-- Last reviewed/updated: 2026-05-27 -->
