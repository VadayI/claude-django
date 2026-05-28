# Migrations & Background Tasks (Celery)

## Migration conventions

- Generate with `makemigrations`; review before committing. One logical change per migration.
- **Never edit an already-applied/committed migration** — create a new one.
- Migrations must be reversible. For `RunPython`, always provide a reverse callable (or `noop` deliberately).
- **Data migrations** are separate from schema migrations and are tested.
- Integrity at the DB level: `constraints`, `unique`, indexes — not only in code.

### Safe changes on large tables

Avoid long locks. Add a column in steps:

1. Add the column **nullable** (fast).
2. Backfill in a data migration (batched if huge).
3. Add the `NOT NULL`/constraint in a follow-up migration.

```python
from django.db import migrations, models

def backfill_slug(apps, schema_editor):
    Post = apps.get_model("blog", "Post")
    for post in Post.objects.filter(slug="").iterator():
        post.slug = slugify(post.title)
        post.save(update_fields=["slug"])

class Migration(migrations.Migration):
    dependencies = [("blog", "0002_post_slug")]
    operations = [
        migrations.RunPython(backfill_slug, migrations.RunPython.noop),
    ]
```

## Background tasks (Celery)

Tasks live in `apps/<domain>/tasks.py`. Broker URL via env. Keep tasks thin — heavy logic in services/models.

```python
from celery import shared_task

@shared_task(bind=True, max_retries=3, default_retry_delay=30, acks_late=True)
def process_post_analytics(self, post_id: int) -> None:
    # must be idempotent
    PostAnalytics.objects.update_or_create(
        post_id=post_id, defaults={"processed_at": timezone.now()},
    )
```

- **Idempotency**: a task run twice must yield the same result (`update_or_create`, dedupe keys).
- **Retries**: bounded `max_retries` with backoff; set `time_limit` for long tasks.
- **Triggering**: dispatch from signals/services deliberately; do not do guaranteed work inline in the request cycle.
- **Periodic**: schedule via `celery beat`.

## Testing (mandatory)

- Migrations with data logic: test the transform and its reverse.
- Tasks: run synchronously with `CELERY_TASK_ALWAYS_EAGER=True`; test idempotency and that the trigger enqueues the task. See @.claude/rules/testing.md and @.claude/rules/tdd.md.
<!-- Last reviewed/updated: 2026-05-27 -->
