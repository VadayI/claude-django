# 20. Error-envelope: перехід на {detail} / {errors:[{field,code,message}]}

- **Status:** Proposed
- **Date:** 2026-06-06
- **Deciders:** Project maintainer
- **Tags:** api, contract, errors

## Контекст

claude-django наразі релізить власний envelope `{"error":{"code","message","details"}}` (`apps.common.exceptions`, schema-hook, тести, CI). REQUIREMENTS §12 пропонує для контракту іншу форму: `{detail}` для простих помилок + `{errors:[{field,code,message}]}` для валідаційних, щоб усі 4xx мали передбачувану структуру, узгоджену з дефолтом DRF.

Оскільки за ADR 0017 контракт стає джерелом істини, форми мусять збігтися. Maintainer обрав: **django переходить на §12-форму**.

## Рішення

Замінити error-envelope backend на контрактну форму:
- прості/не-валідаційні 4xx/5xx: `{ "detail": "<human>" }`;
- валідаційні (400): `{ "errors": [ { "field", "code", "message" } ] }`;
- `429` Too Many Requests — частина error-envelope разом із заголовком `Retry-After` (D5/§12).

Переписати `templates/apps_common/{exceptions.py, schema.py, serializers.py}` + тести (`tests/test_*`), оновити `rules/serializers-permissions.md` (секція error-envelope) і відповідні згадки в `rules`/скілах.

## Наслідки

- (+) Backend conformant до зовнішнього контракту; форма ближча до DRF-дефолту (менше адаптації в самій реалізації в'юх).
- (−) Одноразова робота з переписування наявного envelope + тестів; стара форма `{error:{...}}` повністю знімається (не back-compat — це шаблон, не живий API).
- Залежність: фінальна форма має дослівно збігтися з тим, що зафіксує `claude-api-contract` у `spec/models/` (envelope) — синхронізувати при доведенні contract@v0.1.0.
