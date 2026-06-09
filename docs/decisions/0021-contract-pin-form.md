# 21. Форма пінування контракту: тег + vendored-копія + CI drift-gate

- **Status:** Accepted
- **Date:** 2026-06-09
- **Deciders:** Project maintainer
- **Tags:** api, contract, ci

## Контекст

За ADR 0017 контракт пінується через `CONTRACT_VERSION=vX.Y.Z` (git tag + raw URL), а vendored-копія `docs/api/openapi.yml` комітиться в репо і переглядається при bump-PR. Проте два ризики лишались невирішеними:

1. **Зсув/force-push тега** в `claude-api-contract`: якщо мейнтейнер force-push-не тег `vX.Y.Z` на інший коміт, `scripts/pull_contract.sh` при наступному виклику тягне інший файл — без будь-якого попередження.
2. **Ручне редагування** vendored-копії `docs/api/openapi.yml` поза `pull_contract.sh`: файл у репо відходить від реального контракту тихо, і CI цього не ловить.

Відкрите питання (Plan 0011, §57): чи потрібна явна контрольна сума `CONTRACT_SHA256` у `.env` — як у frontend-підході ADR 0007 §2 — щоб зафіксувати очікуваний дайджест файлу разом із версією.

## Рішення

1. **Форма піна** = `CONTRACT_VERSION=vX.Y.Z` (git tag + raw URL у `scripts/pull_contract.sh`). Жодного окремого `CONTRACT_SHA256`.

2. **Якір цілісності** = закомічена `docs/api/openapi.yml`. Вона є машиночитаним артефактом контракту в репо і переглядається reviewerом при кожному bump-PR — це і є gate на «свідомий bump».

3. **CI drift-gate**: новий режим `bash scripts/pull_contract.sh --check` (re-pull `openapi.yml` у `/tmp` + diff з `docs/api/openapi.yml`), запускається у `backend-ci.yml` як окремий крок `drift`. Ловить обидва ризики: зсув/force-push тега і ручне редагування vendored-копії — без будь-якого нового артефакту для синхронізації.

4. **Явна відмова від `CONTRACT_SHA256`**: diff-перевірка в CI покриває ту саму загрозу (детектує будь-яку розбіжність між тегованим файлом і vendored-копією). Третій артефакт потребував би синхронізації на кожному bump і не додає захисту понад drift-gate.

## Наслідки

- (+) CI drift-gate ловить зсув/force-push тега в `claude-api-contract` і ручне редагування `docs/api/openapi.yml` без нового артефакту для підтримки.
- (+) Форма `.env` не ускладнюється: bump-PR = одна зміна: `CONTRACT_VERSION=vX.Y.Z` + оновлена vendored-копія.
- (+) `docs/api/openapi.yml` лишається єдиним машиночитаним артефактом контракту в репо; всі агенти та CI-кроки читають один файл.
- (−) CI drift-крок потребує мережевого доступу до `raw.githubusercontent.com`; при недоступності зовнішнього репо — step `skipped` (graceful: умова `if: vars.CONTRACT_VERSION != ''` відпрацьовує коректно, блокуючи лише за реальної розбіжності).
- Зачіпає: `templates/scripts/pull_contract.sh` (новий режим `--check`), `templates/.github/workflows/backend-ci.yml` (новий крок `drift`); уточнює ADR 0017; закриває Plan 0011 open question §57.
