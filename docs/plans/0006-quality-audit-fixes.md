# План 0006 — правки claude-django за аудитом carlsberg

**Джерело:** `docs/reviews/quality-audit-carlsberg-20260601.md`
**Мета:** усунути дефекти «останньої милі» (доставка + глибина quality-gate) і один баг скафолда.
**Природа змін:** правки конфігурації шаблону (markdown-команди/агенти/правила + `templates/pyproject.toml`). Це НЕ проходить feature-pipeline Django; кожна група йде окремою гілкою → PR (правило `git-operations.md`).

---

## Кореневі причини (уточнено реальним станом файлів)

1. **HANDOFF лишився `{TODO}`** не тому, що `/wrap-up` зламаний, а тому, що заповнення HANDOFF робить ОКРЕМА команда `/handoff`, якої користувач не запускав. При цьому `templates/HANDOFF.md:54` каже *«Update cadence: … via /wrap-up»* — пряма суперечність. Split-brain між двома командами.
2. **WORKLOG перебільшує merge-статус**, бо `/wrap-up` (крок 2) дописує WORKLOG без жодної звірки через `gh`. `/handoff` звіряється з `gh pr list`, але пише лише в HANDOFF.md.
3. **Баг install** — `templates/pyproject.toml` не має ні `[build-system]`, ні `[tool.setuptools.packages.find]`.
4. **Quality-gate неглибокий** — `reviewer.md` і `tester.md` не згадують класів помилок, що пройшли (широкий except, content-vs-format, `IntegrityError→409`, 409/кодування/порожні поля).

---

## P0 — критичні (доставка + гарантований баг install)

### Крок 1. Полагодити шов `/wrap-up` ↔ `/handoff`
**Проблема:** HANDOFF не оновлюється наприкінці сесії; cadence-рядок бреше.
**Файли:**
- `.claude/commands/wrap-up.md` — у крок 2 («Persist context») додати під-крок: **«Регенерувати `docs/HANDOFF.md`, викликавши логіку `/handoff` (або делегувавши `docs-writer`), ПЕРЕД пропозицією commit-меседжа»**. HANDOFF має входити в той самий набір змін, що показується в кроці 4 (git status).
- `templates/HANDOFF.md:54` — лишити «via `/wrap-up`» коректним (після фіксу воно стане правдою) АБО уточнити: *«via `/wrap-up` (який викликає `/handoff`)»*.
**Перевірка:** прогнати `/wrap-up` на тестовій гілці → `docs/HANDOFF.md` не містить жодного `{TODO}`; `grep -c '{TODO}' docs/HANDOFF.md` = 0.
**Ризик:** дублювання логіки. Мітигація — `/wrap-up` делегує, а не копіює кроки `/handoff`.

### Крок 2. Звірка merge-статусу у `/wrap-up`
**Проблема:** WORKLOG записує наміри («PR #N merged / готовий») як факт.
**Файл:** `.claude/commands/wrap-up.md` — у крок 2 (WORKLOG-append) додати обовʼязковий probe перед формулюванням «Done/Next»:
```
gh pr list --head "$BRANCH" --state all --json number,state,mergedAt
git branch --merged origin/main
```
і правило формулювання: гілку без `mergedAt` описувати як **«open / not merged»**, ніколи як «merged». Додати рядок-застереження: *«не записувати merge як доконаний без `gh`-підтвердження»*.
**Перевірка:** на гілці з незмердженим PR WORKLOG-чернетка містить «not merged», а не «merged».
**Ризик:** `gh` недоступний → fallback на `git branch --merged` + явна позначка «unverified».

### Крок 3. Виправити `templates/pyproject.toml` (баг install)
**Проблема:** flat-layout автодискавері падає на двох top-level пакетах (`apps/`, `config/`).
**Файл:** `templates/pyproject.toml` — додати:
```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["."]
include = ["apps*", "config*"]
```
(розмістити узгоджено з рештою секцій; не чіпати `[tool.ruff]`).
**Перевірка:** у свіжому `/bootstrap` `pip install -e backend` (або CI install-крок) проходить без «multiple top-level packages discovered».
**Ризик:** мінімальний; це стандартна секція. Звірити, що `backend-ci.yml` справді робить editable-install (інакше баг латентний, але фікс однаково потрібен).

---

## P1 — важливі (глибина quality-gate)

### Крок 4. Розширити чеклист `reviewer`
**Файл:** `.claude/agents/reviewer.md` — у блок «What you check» додати явні 🔴/🟡-тригери:
- широкий `except Exception` / `except:` що ковтає помилку і повертає success-статус (німий провал);
- запис у БД без звірки content-vs-declared-format (напр. import за форматом без валідації заголовків/обовʼязкових полів);
- незахищений `perform_create`/`save()` від `IntegrityError` там, де очікується 409;
- будь-який ендпоінт, що повертає 2xx на частково невдалій пакетній операції без машинно-читаного маркера помилки.
**Перевірка:** додати ці пункти в опис; (опц.) внести приклади в `skills/code-reviewer`.
**Ризик:** надмірні спрацювання — позначити як «evaluate severity», не авто-🔴.

### Крок 5. Розширити чеклист `tester`
**Файл:** `.claude/agents/tester.md:26` — замінити розпливчасте «conflicts» на явний перелік і додати кейси:
- **409** явно (конфлікт унікальності на create і update);
- **обидва напрямки** mismatch формату/вмісту (CSV-as-JSON і JSON-as-CSV);
- кодування (не-UTF-8 вхід → коректний 400, не 500);
- порожні/відсутні обовʼязкові поля (напр. `name`, `source_id`);
- конкурентний конфлікт (де доречно) — або хоча б тест, що фіксує очікувану поведінку при дублі.
**Перевірка:** наступна згенерована фіча з імпортом має ці тести з коробки.
**Ризик:** перелік стає довгим — згрупувати як «для ендпоінтів парсингу/завантаження файлів».

### Крок 6. README/STUBS у docs-фазі + звірка узгодженості
**Файли:**
- `.claude/rules/app-readme.md` (анкер — рядки 18-19) — додати: після GREEN, у тому ж PR, прибрати «RED phase / target» формулювання і **звірити перелік ендпоінтів README ↔ `docs/api/INDEX.md` ↔ OpenAPI** (одне джерело правди — код/OpenAPI).
- `.claude/agents/docs-writer` (або відповідний крок pipeline) — зробити цю звірку обовʼязковою перед `gh pr create`.
- `.claude/rules/no-stubs.md` — додати: на bootstrap `docs/STUBS.md` ініціалізується **порожнім реєстром під назвою проєкту** (без прикладового рядка-шаблону), щоб «незайманий шаблон» не лишався у проді.
- `.claude/commands/bootstrap.md` (крок копіювання, ~рядок 228) — після копіювання `templates/STUBS.md` → `docs/STUBS.md` очистити прикладові рядки / підставити заголовок проєкту.
**Перевірка:** свіжий `/bootstrap` дає `docs/STUBS.md` без прикладового рядка; згенерована фіча лишає README без «RED phase».
**Ризик:** низький.

---

## P2 — дрібні (гігієна середовища)

### Крок 7. Авточистка stale `.git/index.lock`
**Проблема:** порожній `index.lock` на `/mnt`-дисках блокує git; зараз лікується вручну в HANDOFF.
**Файл:** `scripts/session-start.sh` — додати безпечний крок: видаляти `.git/index.lock`, **лише якщо** він порожній і старший за N хвилин (щоб не зачепити активний git-процес):
```bash
[ -f .git/index.lock ] && [ ! -s .git/index.lock ] && find .git/index.lock -mmin +5 -delete 2>/dev/null || true
```
**Перевірка:** після штучного `touch .git/index.lock` і паузи сесія стартує без блокування git.
**Ризик:** видалити лок активного процесу — мітигація умовами «порожній + старший за 5 хв».

---

## Порядок виконання та групування в PR

| PR | Гілка | Кроки | Чому разом |
|----|-------|-------|-----------|
| 1 | `fix/pyproject-packages` | 3 | Ізольований баг скафолда; найшвидше й найкритичніше для нових проєктів |
| 2 | `fix/wrap-up-handoff-merge` | 1, 2 | Один логічний шов доставки (wrap-up ↔ handoff ↔ WORKLOG) |
| 3 | `feat/quality-gate-depth` | 4, 5 | Поглиблення reviewer+tester — одна тема |
| 4 | `docs/readme-stubs-consistency` | 6 | Docs-узгодженість + ініціалізація реєстру |
| 5 | `chore/index-lock-cleanup` | 7 | Дрібна гігієна, окремо |

**Загальна верифікація після всіх PR:** повторити повний сценарій на новому тестовому проєкті (clone → `/doctor` → `/bootstrap` → фіча з імпортом → `/wrap-up`) і підтвердити: install проходить, HANDOFF без `{TODO}`, WORKLOG не перебільшує merge, згенерована фіча має нові тести й валідації, README/INDEX/OpenAPI узгоджені.

**Відкриті питання до користувача:**
1. Чи `/wrap-up` має сам **комітити** свої doc-зміни, чи лишати незакоміченими (поточний дизайн — навмисно не комітити; це конфліктує з очікуванням «чисте дерево після wrap-up»)?
2. Чи додавати реальний upload-size-limit/throttle на import-ендпоінт у дефолтний скафолд, чи лишати на рівні фічі?
