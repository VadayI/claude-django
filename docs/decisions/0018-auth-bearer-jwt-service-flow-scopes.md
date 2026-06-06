# 18. Auth: Bearer/JWT + service-flow (client_credentials) + scopes

- **Status:** Proposed
- **Date:** 2026-06-06
- **Deciders:** Project maintainer
- **Tags:** security, auth, api, contract

## Контекст

Основний профіль клієнтів похідних API — **service-to-service** (REQUIREMENTS D5): API споживають інші сервіси, mobile, сторонні клієнти. Cookie/CSRF прив'язані до браузера й тут не підходять. Контракт `claude-api-contract` описує auth-ендпоінти, щоб mock віддавав токени, а споживачі логінились автономно (§5).

## Рішення

Backend реалізує auth за контрактом:

1. **User-flow (D1=B):** `POST /auth/register` · `/auth/login` · `/auth/refresh` · `/auth/logout`, security scheme `bearerAuth` (`type: http`, `scheme: bearer`, `bearerFormat: JWT`).
2. **Service-flow (D5):** `POST /auth/token` з `grant_type=client_credentials` (`client_id`/`client_secret` + опц. `scope`); модель/сторедж клієнтських облікових даних сервісів.
3. **Scope-based permissions:** DRF permission-класи перевіряють scopes токена, а не лише ролі користувача (узгоджено зі `security` в контракті: `[{ serviceAuth: ["orders:write"] }]`).
4. **Короткий access (хвилини) + revocation-стратегія** (blacklist/rotation) — політика в налаштуваннях.
5. **Rate limiting** (DRF throttling) → `429` + `Retry-After`, форма за error-envelope (ADR 0020).

## Наслідки

- (+) Один auth-механізм для людей і сервісів; гранульована авторизація через scopes.
- (−) Більша поверхня (client-credentials модель, scope-перевірки, revocation) — складніше за дефолтний `IsAuthenticated`.
- Відкрите: бібліотека JWT (`djangorestframework-simplejwt` + blacklist vs власна під scopes) — вирішується на PR3.
- Зачіпає `rules/serializers-permissions.md`, агентів `integration-architect`/`security-scanner`, скафолд auth-додатку, налаштування.
