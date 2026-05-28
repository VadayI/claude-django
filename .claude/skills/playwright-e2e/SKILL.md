---
name: playwright-e2e
description: End-to-end browser testing with Playwright for the Vite+React mini-client and full user flows (incl. mobile viewport via staging). Activate for E2E/browser tests (used by the qa agent).
---

# Playwright E2E

Browser automation for full user journeys against the running stack. This is ABOVE pytest API tests (`pytest-tdd`), not a replacement.

## Setup

```bash
cd frontend
npm install -D @playwright/test
npx playwright install --with-deps chromium
```
`playwright.config.js`: set `use.baseURL` from env (local `http://localhost:5173` or the staging subdomain); add a `mobile-chrome` project (`devices['Pixel 7']`) for mobile checks.

## Principles

- Stable selectors: prefer `getByRole`/`getByLabel`/`data-testid` over CSS/text.
- No flaky waits: rely on Playwright auto-waiting and web-first assertions (`await expect(locator).toBeVisible()`).
- Each test independent; reset state via API setup where possible.
- Cover key journeys only (login, create, list, error states) — don't duplicate API-level assertions from pytest.

## Example

```js
import { test, expect } from "@playwright/test";

test("user can register", async ({ page }) => {
  await page.goto("/register");
  await page.getByLabel("Email").fill("a@b.com");
  await page.getByLabel("Password").fill("Str0ngPass!");
  await page.getByRole("button", { name: "Sign up" }).click();
  await expect(page.getByText("Welcome")).toBeVisible();
});
```

## Commands

```bash
npx playwright test
npx playwright test --project=mobile-chrome
npx playwright test --ui   # debug
```
<!-- Last reviewed/updated: 2026-05-27 -->
