# 9. Робота з /mnt (Windows-диск) повноцінно підтримується

- **Status:** Accepted
- **Date:** 2026-06-01
- **Deciders:** Project maintainer
- **Tags:** environment, wsl2, developer-experience, doctor

## Контекст

Раннє керівництво (`environment.md`, `docker-commands.md`, README) радило тримати проєкт у **нативній файловій системі WSL2** (`~/projects/<slug>`), а не під `/mnt/c`/`/mnt/d`, бо на 9p-mount Windows-диска: повільніші Docker bind-mounts, можливі CRLF↔LF переходи, застарілі mtime і блокування `git index.lock`. Через це `/doctor` і агенти видавали рекомендацію **перенести проєкт**, напр.:

```
2. ⚠️  Перенести проєкт (необов'язково, але рекомендовано):
   cp -r "/mnt/d/Dev/.../carlsberg-ir-data-service" ~/projects/carlsberg-ir-data-service
```

Maintainer тримає всі свої проєкти на Windows-диску (`D:\Dev\...`), редагує їх рідними Windows-інструментами й не хоче ні переносити їх, ні бачити повторювані нагадування про це. Перенос не є вимогою для проходження platform-гейту — WSL2-нативний `claude`, запущений з `/mnt/d`, дає `platform: linux, is_wsl2: true, platform_supported: true`.

## Рішення

Робота з проєктом під `/mnt/c`/`/mnt/d` (Windows-диск) — **повноцінно підтримуваний, штатний сценарій**. Скасовується попередня рекомендація «тримати в WSL2 FS».

1. `/doctor` і агенти **не пропонують** переносити проєкт у `~/projects`. Каталог під `/mnt` репортиться як ✅, не ⚠️.
2. Залишається **одна нейтральна інформаційна нотатка** про відомі caveats `/mnt` (повільніші bind-mounts; CRLF; `git index.lock` на 9p — тому git-операції краще робити з host-шела). Це не «проблема, яку треба виправити переносом», а характеристика середовища.
3. `~/projects/<slug>` лишається **опційним** варіантом для тих, кому критична максимальна швидкість Docker bind-mount — але ніколи не вимогою і не дефолтною рекомендацією.

Це не торкається ADR `0005` (WSL2-only, без PowerShell): запускати треба так само WSL2-нативний `claude`; змінюється лише ставлення до **розташування** проєкту в межах підтримуваного рантайму.

## Наслідки

**Плюси.** Менше тертя й нульове нагадування для тих, хто тримає код на Windows-диску. Менше плутанини між «UNSUPPORTED_PLATFORM» (справжній блокер) і «working-dir warning» (косметика).

**Мінуси.** На `/mnt` Docker bind-mounts повільніші, а 9p дає реальні quirks (CRLF, `index.lock`). Вони лишаються — просто більше не подаються як привід переносити. Пом'якшення: git-операції з host-шела (PowerShell/Git Bash) уникають `index.lock`; `.gitattributes` нормалізує перенос рядків.

**Відкинуті альтернативи.** Лишити рекомендацію переносу — відхилено: суперечить тому, як maintainer фактично працює, і генерує шум. Прибрати будь-яку згадку про caveats — відхилено: реальні проблеми 9p (особливо `index.lock`) варто лишити задокументованими, щоб вони не дивували.

## Наслідки для файлів

- `.claude/rules/environment.md` — Scope 1 «Working dir» рядок: `/mnt` = ✅ supported; runner-trap абзац без «moving removes the warning».
- `.claude/commands/doctor.md` — інструкція не репортити `/mnt` як ⚠️ і не пропонувати перенос.
- `.claude/rules/docker-commands.md` — прибрати «NOT under /mnt», лишити нейтральну нотатку.
- `README.md` — callout «Before you start», крок «Keep the project in WSL2 FS», Troubleshooting `/mnt` рядок, Prerequisites.
