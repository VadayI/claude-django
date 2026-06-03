"""Gunicorn configuration for the staging (and production-like) backend.

Loaded by ``gunicorn config.wsgi:application --config /app/gunicorn.conf.py``
(see docker-compose.staging.yml). WSGI is the canonical runtime for this
backend — Django's synchronous request/response cycle maps onto gunicorn's
sync/gthread workers. Every value can be overridden from the environment so the
same image works across VPS sizes without rebuilding.

ASGI note:
    If the project later adds async views, channels, or websockets, switch to an
    ASGI server instead of gunicorn-sync — e.g. uvicorn workers under gunicorn::

        gunicorn config.asgi:application -k uvicorn.workers.UvicornWorker \\
            --config /app/gunicorn.conf.py

    That needs ``uvicorn`` in the dependencies and ``config/asgi.py`` as the
    entrypoint. Until then, plain WSGI below is correct and simplest.
"""

import multiprocessing
import os

# --- Networking -------------------------------------------------------------
# Bind inside the container; the host reverse proxy (nginx/Traefik) forwards to
# this address over the compose network. Never expose this straight to 0.0.0.0
# on the host without a proxy in front.
bind = os.environ.get("GUNICORN_BIND", "0.0.0.0:8000")

# --- Workers ----------------------------------------------------------------
# Sync workers: a common starting point is (2 * CPU cores) + 1. Override with
# GUNICORN_WORKERS on small VPS instances to avoid oversubscribing memory.
workers = int(
    os.environ.get("GUNICORN_WORKERS", (multiprocessing.cpu_count() * 2) + 1)
)
# Threads per worker help with I/O-bound views (DB waits) without extra procs.
threads = int(os.environ.get("GUNICORN_THREADS", "2"))
worker_class = os.environ.get("GUNICORN_WORKER_CLASS", "gthread")

# --- Timeouts ---------------------------------------------------------------
# Kill and replace a worker stuck longer than `timeout` seconds (default 30).
# Raise it only for known-slow endpoints; prefer pushing slow work to Celery.
timeout = int(os.environ.get("GUNICORN_TIMEOUT", "30"))
graceful_timeout = int(os.environ.get("GUNICORN_GRACEFUL_TIMEOUT", "30"))
# Keep-alive for connections held open by the upstream proxy.
keepalive = int(os.environ.get("GUNICORN_KEEPALIVE", "5"))

# --- Worker recycling -------------------------------------------------------
# Recycle workers periodically to bound the impact of slow memory leaks. The
# jitter spreads restarts so they do not all happen at once.
max_requests = int(os.environ.get("GUNICORN_MAX_REQUESTS", "1000"))
max_requests_jitter = int(os.environ.get("GUNICORN_MAX_REQUESTS_JITTER", "100"))

# --- Logging ----------------------------------------------------------------
# Log to stdout/stderr ("-") so the container runtime (docker logs / journald)
# captures them; do not write log files inside the container.
accesslog = os.environ.get("GUNICORN_ACCESS_LOG", "-")
errorlog = os.environ.get("GUNICORN_ERROR_LOG", "-")
loglevel = os.environ.get("GUNICORN_LOG_LEVEL", "info")
# Include the X-Forwarded-For the proxy sets so access logs show real client IPs.
access_log_format = (
    '%({x-forwarded-for}i)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s '
    '"%(f)s" "%(a)s" %(D)sus'
)

# --- Proxy trust ------------------------------------------------------------
# Trust X-Forwarded-* only from the reverse proxy. "*" assumes the proxy is the
# sole ingress on the private compose network; tighten to the proxy IP/CIDR if
# the network is shared. Pairs with SECURE_PROXY_SSL_HEADER in settings/staging.
forwarded_allow_ips = os.environ.get("GUNICORN_FORWARDED_ALLOW_IPS", "*")
