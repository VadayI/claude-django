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

## Authentication (Bearer/JWT + service-flow)

The API is **token-based, not session/cookie** — the primary client profile is
service-to-service (ADR `0018`, D5). `DEFAULT_AUTHENTICATION_CLASSES` is
`rest_framework_simplejwt.authentication.JWTAuthentication`; clients send
`Authorization: Bearer <access>`. Endpoints, codes and bodies are defined by the
external contract (`@.claude/rules/api-docs.md`); this section is the
implementation doctrine.

**User-flow endpoints** (contract `claude-api-contract`, D1):

| Method + path | Security | Returns |
|---|---|---|
| `POST /api/v1/auth/register` | public | user (+ optional tokens) |
| `POST /api/v1/auth/login` | public | `access` + `refresh` (refresh in the response **body**, D2/ADR `0019`) |
| `POST /api/v1/auth/refresh` | public | new `access` (+ optional rotated `refresh`) |
| `POST /api/v1/auth/logout` | bearer | 204; blacklists the refresh token |

**Service-flow endpoint** (machine-to-machine, D5):

| Method + path | Security | Request | Returns |
|---|---|---|---|
| `POST /api/v1/auth/token` | public | `grant_type=client_credentials`, `client_id`, `client_secret` (+ optional `scope`) | scoped `access` (+ `expires_in`, `scope`) |

- **JWT library:** `djangorestframework-simplejwt` for the user-flow (access +
  refresh-in-body) with `rest_framework_simplejwt.token_blacklist` for
  revocation. The service-flow `/auth/token` is a small custom view that
  authenticates a stored service credential (`client_id`/`client_secret`) and
  issues a JWT whose `scope` claim lists the granted scopes. **Upgrade path:**
  `django-oauth-toolkit` when a project needs standards-compliant OAuth2
  (external client registration, introspection) — record the switch in an ADR.
- **Scopes, not roles, for services.** Non-public endpoints declare the scopes
  they need and enforce them with `apps.common.permissions.HasScope` (reads the
  token's space-delimited `scope` claim), stacked on `IsAuthenticated`:

  ```python
  class OrderViewSet(viewsets.ModelViewSet):
      permission_classes = [permissions.IsAuthenticated, HasScope]
      required_scopes = ["orders:write"]
  ```

- **Short access + revocation.** Keep access lifetimes short (minutes) and rotate
  refresh tokens; blacklist on logout/rotation — a leaked service secret must not
  grant broad, long-lived access.
- **Rate limiting.** Throttle sensitive endpoints (login, register, token) via
  `throttle_classes`; a throttled request returns **429** with a `Retry-After`
  header and the `{"detail": ...}` envelope. Services hit the API harder than
  humans, so the limit must be explicit and predictable.

## Default permission policy (project-wide)

The scaffold sets `DEFAULT_PERMISSION_CLASSES = ["rest_framework.permissions.IsAuthenticated"]`
in `config/settings/base.py` (`REST_FRAMEWORK`), so **every endpoint is
authenticated by default**. A view that should be public opts OUT explicitly with
`permission_classes = [permissions.AllowAny]` — never by relying on a missing
default. This makes "forgot to set permissions" fail closed (401), not open.
Stack `IsAuthenticated` with object-level classes (e.g. `IsOwnerOrReadOnly`) as
shown above; authenticated-but-not-allowed still returns **403**.

## Error envelope (project-wide contract)

Every non-2xx response uses the external contract's envelope (ADR `0020`),
produced by `apps.common.exceptions.exception_handler` (wired via
`REST_FRAMEWORK["EXCEPTION_HANDLER"]` — see `apps/common/`). Two shapes:

- **Validation errors (400):**

  ```json
  {"errors": [{"field": "<name|null>", "code": "<machine>", "message": "<human>"}]}
  ```

- **Every other handled error (401/403/404/409/429/5xx):**

  ```json
  {"detail": "<human>"}
  ```

- For 400, each entry maps one offending field to its DRF error `code` and
  message; non-field (cross-field) errors use `field: null`; nested serializer
  fields are dotted (`address.zip`).
- `detail` is a single human-readable sentence with no per-field structure (a
  `404`/`NotFound` serializes `{"detail": ...}`, never a loose string or a field
  map).
- Raise `apps.common.exceptions.Conflict` (409) for uniqueness/version clashes —
  do NOT mirror a model's unique constraint as a DRF `UniqueValidator` if you
  want a 409 instead of a 400.
- **429** responses carry a `Retry-After` header alongside the `{"detail": ...}`
  body, per the S2S rate-limit contract (see *Authentication* above).

Do not hand-build per-view error bodies; raise the appropriate DRF exception (or
`Conflict`) and let the handler render the envelope. The convention tests live in
`apps/common/tests/` (pagination, default permission, envelope, throttling).

## Testing (mandatory)

Per endpoint test: success, 400 (validation), 401 (anonymous), 403 (other user), 404, and IDOR (user A cannot touch user B's object). See @.claude/rules/testing.md.
<!-- Last reviewed/updated: 2026-05-27 -->
