"""Test settings: dev settings plus test-only overrides.

Place as ``config/settings/test.py``. Used by pytest via
``DJANGO_SETTINGS_MODULE = config.settings.test`` (set in ``backend/pyproject.toml``
``[tool.pytest.ini_options]``). It inherits the full local/dev configuration and
layers on two test-only concerns:

* ``MIGRATION_MODULES`` redirects the cross-cutting ``common`` app's migrations to
  the test-only package ``apps.common.tests.migrations`` so the ``SampleItem``
  convention model gets a table without shipping a production ``common``
  migration. This override belongs to the test runtime, NOT to ``dev.py`` or
  ``staging.py`` (production ``common`` ships no models).
* A fast password hasher, because the default PBKDF2 hasher dominates the runtime
  of any test that creates a user.

Keeping these here (rather than in ``dev.py``) means running the dev server never
pays for the test-only migration redirect, and the test configuration is a single
explicit module.
"""

from config.settings.dev import *  # noqa: F401,F403

# Test-only: SampleItem (apps/common/tests/models.py) exercises the DRF
# conventions. Its migration lives under tests/ and is applied ONLY here, never
# shipped as a production `common` migration.
MIGRATION_MODULES = {"common": "apps.common.tests.migrations"}

# Speed: skip the slow default PBKDF2 hasher for test user creation.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
