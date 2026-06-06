# 19. Refresh-токен у тілі відповіді (D2) — XSS trade-off

- **Status:** Accepted
- **Date:** 2026-06-06
- **Deciders:** Project maintainer
- **Tags:** security, auth, contract

## Контекст

REQUIREMENTS D2 (підтверджено): access — у `Authorization: Bearer`, refresh — **у тілі відповіді** `login`/`refresh`. Робить контракт самодостатнім і mock тривіальним.

## Рішення

Backend віддає refresh у тілі відповіді (не httpOnly-cookie). Для S2S-профілю (D5) XSS-ризик відсутній — секрети сервісів не живуть у браузері. Для браузерного SPA (`claude-react-mui`) refresh зберігається на клієнті (memory/localStorage), що слабше проти XSS за httpOnly-cookie.

## Наслідки

- (+) Самодостатній контракт; автономний mock; єдина форма для всіх типів клієнтів.
- (−) Для браузерного споживача — слабший XSS-захист за cookie-підхід.
- **Перемикач:** похідний проєкт має могти свідомо перейти на httpOnly-cookie auth-mode — фіксується окремим auth-mode рішенням у похідному репо. Базовий шаблон лишає refresh-у-тілі дефолтом.
