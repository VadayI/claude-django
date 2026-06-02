# Code style

## Python / Django

- Python 3.13, typing where appropriate. Linter and formatter — **ruff** (`ruff check .`, `ruff format .`).
- Imports ordered (ruff isort). No unused imports.
- Naming: `snake_case` for functions/variables, `PascalCase` for classes, `UPPER_CASE` for constants.
- Django: `verbose_name`, `related_name` explicit; `Meta.ordering` where needed; `__str__` on models.
- DRF: serializers validate input; views are thin; permissions are separate classes.
- No "magic numbers" — move them to constants/enums (`models.TextChoices`).
- Secrets configuration — only via env (`django-environ` / `os.environ`), never in code.
- **Every public function/method/class has a docstring** — see *Docstrings* below.
- **Every Django app has a `README.md`** at `backend/apps/<app>/README.md` — see `@.claude/rules/app-readme.md`.

## Docstrings (mandatory, Google style)

Every public module, class, function, and method in `backend/apps/` MUST carry a docstring in **Google style**. Private members (`_underscored`) are exempt. Tests, migrations, and `__init__.py` are exempt by ruff `per-file-ignores`. Enforced by ruff `D` rule set with `convention = "google"` — a missing docstring fails lint and CI.

A docstring captures **why** the unit exists and the contract callers depend on (inputs, outputs, side effects, errors), not the *how* of the implementation.

```python
def split_invoice(invoice: Invoice, max_lines: int = 100) -> list[Invoice]:
    """Split an invoice into chunks of at most ``max_lines`` line items.

    Used by the export pipeline to keep generated PDFs under the printer's
    per-document limit. Splitting preserves invoice metadata (number, customer,
    totals) on every chunk; chunk numbering is appended as ``-N``.

    Args:
        invoice: A persisted ``Invoice`` with at least one line item.
        max_lines: Maximum line items per chunk. Must be > 0.

    Returns:
        List of new ``Invoice`` instances (not yet saved). Order matches the
        original line-item order; the first chunk inherits the original ``id``
        as its parent reference.

    Raises:
        ValueError: ``max_lines`` is <= 0 or the invoice has no line items.
        PermissionError: The caller is not the invoice owner.
    """
```

Rules of thumb:

- **Subject of the first line is the *function*, not the *action*** — "Split…", "Compute…", "Return…", "Raise…".
- The first line is a single sentence ending with `.` and fits ≤ 88 chars.
- **Args / Returns / Raises** sections present when there are non-trivial inputs/outputs/exceptions; omit empty sections.
- Cross-reference related units with backticks: ``See ``ranking.services.rank``.``
- For Django models: docstring on the class describes the domain entity, not column types (those are in `verbose_name` / `help_text`).
- For DRF views and serializers: docstring states the contract (resource, allowed methods, who can call) — the schema is in OpenAPI (`@.claude/rules/api-docs.md`), not the docstring.

## File size limit (max 800 lines, enforced)

No source file may exceed **800 lines**. A file that grows past the limit is a signal it carries more than one responsibility — split it into smaller, cohesively-named modules and **group them in a package (folder)** instead of letting one file sprawl.

- The limit counts **all lines** of the file (code, comments, and blank lines), measured as `wc -l`.
- **Only auto-generated migrations are exempt** (`backend/apps/**/migrations/`). Everything else under `backend/` — models, serializers, views, services, permissions, tests, settings — is in scope. Tests are NOT exempt: a 800+ line test file splits by scenario/resource just like production code.
- Enforced by the CI gate **`scripts/check_file_size.sh`** (run in `backend-ci.yml` and locally before pushing) — any non-migration `*.py` over 800 lines fails the PR. `reviewer` also flags files approaching the limit at the Quality Gate.

### How to split (group into folders)

When a module gets large, convert it into a package and split by cohesion — never by arbitrary line cuts:

```
apps/billing/views.py            ->  apps/billing/views/
                                       __init__.py        # re-export the public names
                                       invoices.py
                                       payments.py
                                       refunds.py
```

- Turn `models.py` -> `models/` (one module per aggregate), `serializers.py` -> `serializers/`, `services.py` -> `services/`, `tests.py` / `tests/test_x.py` -> more focused `tests/test_<topic>.py`.
- Keep the **public import path stable** via `__init__.py` re-exports (`from .invoices import InvoiceViewSet`) so callers and routers do not change.
- Split along domain seams (one resource / one concern per file), not by counting lines. Each resulting file keeps a single responsibility.
- `code-structure-auditor` performs this audit on demand (`/structure-audit`) and proposes the concrete split; `django-refactoring-expert` executes large splits under green tests.

## General

- Comments inside the body explain *why*, not *what* (let names and the docstring carry *what*).
- Small functions with a single responsibility.
- Conventional commits (see @.claude/rules/git-operations.md).

<!-- Last reviewed/updated: 2026-06-02 (added File size limit: max 800 lines, check_file_size.sh gate) -->
