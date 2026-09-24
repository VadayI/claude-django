"""CI-only settings for live API contract conformance.

This module inherits the normal development configuration and raises the
configured DRF throttle rates so Schemathesis can generate its request volume
without CI fuzzing results being masked by local development limits. Use it
only for the isolated CI conformance server; pytest uses ``test.py`` and
production or staging processes must never use this module.
"""

from config.settings import dev as _dev_settings
from config.settings.dev import *  # noqa: F401,F403

REST_FRAMEWORK = {
    **_dev_settings.REST_FRAMEWORK,
    "DEFAULT_THROTTLE_RATES": {
        scope: "100000/min"
        for scope in _dev_settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]
    },
}
