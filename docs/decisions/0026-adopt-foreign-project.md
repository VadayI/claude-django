# 0026 — `/adopt`: адитивне приєднання конфігу до чужого існуючого Django-проєкту

- Статус: прийнято
- Дата: 2026-07-07

## Контекст

Шаблон покривав два сценарії: створення нового проєкту (README Quick start + `/bootstrap`
Mode A), доведення недобутстрапленого похідного (Mode B) і оновлення похідного
(`/update-from-template`, ADR `0014`). Аудит v2 (`docs/reviews/2026-07-07-deep-audit-v2.md`,
§3) показав, що третій заявлений сценарій — «додати команди/агентів/скіли в уже існуючий,
НЕ похідний проєкт» — не мав першокласного шляху:

- `install.sh` сліпо перезаписував кореневі файли чужого проєкту (`CLAUDE.md`, `Makefile`,
  `docker-compose.yml`, `.gitignore`, CI-воркфлоу) — втрата даних;
- `/bootstrap` Mode B приймав чужий проєкт за недобутстраплений шаблонний і PR-ив шматки,
  що не лягають у чужу розкладку; `BACKEND_WITHOUT_GIT` був глухим кутом;
- `/doctor` не мав сценарію для чужого проєкту; README оверселив
  («attach the config to an existing project» — фактично greenfield).

## Рішення

1. **Нова команда `/adopt`** (`.claude/commands/adopt.md`): клон апстріму → layout survey
   (розташування `manage.py`, `settings.py` vs `settings/`, deps-файл, наявні CI/CLAUDE.md) →
   feature branch → диспатч `template-sync` у `MODE=adopt` → звіт → **PR**.
2. **`template-sync` отримав Adopt mode** — адитивність: нові файли копіюються; існуючі
   НІКОЛИ не перезаписуються (поруч кладеться `<name>.adopt-proposed` + diff у звіті);
   `templates/` не копіюється wholesale; `apps.common`/роутер/контракт-пін — задокументовані
   ручні follow-ups, не автоправки чужого коду. Наприкінці пишеться
   `.claude/memory/template-sync.json` з `mode: adopt` — створює lineage, тож подальші
   оновлення йдуть звичайним `/update-from-template`.
3. **`/doctor`**: пʼятий сценарій `foreign-django` (Django-код є, lineage немає) →
   рекомендує `/adopt`; `existing-incomplete` уточнено як template-derived.
4. **`/bootstrap`**: guard у Mode B (backend без шаблонної форми і без lineage → STOP,
   `/adopt`); `BACKEND_WITHOUT_GIT`-глухий кут тепер вказує на `/adopt`.
5. **`install.sh`**: відмовляється сідити в теку з існуючим проєктом (`manage.py`,
   `CLAUDE.md`, `Makefile`, `docker-compose.yml`, `.gitignore`) без `--force`; з `--force`
   зберігає `*.bak`-копії відмінних файлів (хелпер `seed()`).
6. **README**: Quick start чесно перейменовано (greenfield), додано розділ про `/adopt`.

## Наслідки

- «Додати в існуючий проєкт» — першокласний, безпечний, PR-only шлях без втрати даних.
- Adopt створює lineage → єдиний канал подальших оновлень (ADR `0014`) працює і для
  адоптованих проєктів.
- Свідомі межі v1: error envelope (`apps.common`), `DefaultRouter(trailing_slash=False)`
  і contract-пін НЕ вносяться в чужий код автоматично — лише як follow-ups у звіті
  adopt-PR (чужий код чіпає тільки людина або окремий узгоджений PR).
