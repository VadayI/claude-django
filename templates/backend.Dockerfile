# Place as backend/Dockerfile
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

# Which optional-dependency group to install: "dev" (default, local image with
# the test/lint toolchain) or "prod" (staging image with gunicorn, no dev tools).
# docker-compose.staging.yml passes INSTALL_EXTRA=prod.
ARG INSTALL_EXTRA=dev

COPY pyproject.toml ./
RUN pip install --upgrade pip && pip install -e ".[${INSTALL_EXTRA}]"

COPY . .

EXPOSE 8000
# Dev default. Staging overrides this with gunicorn (see docker-compose.staging.yml);
# never use runserver in production (Django deployment checklist).
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
# Last reviewed/updated: 2026-06-03
