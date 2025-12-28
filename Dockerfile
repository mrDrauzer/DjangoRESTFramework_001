FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DJANGO_SETTINGS_MODULE=config.settings \
    PYTHONPATH=/app

WORKDIR /app

# system deps for building wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# install deps into a clean prefix to copy later
COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip \
    && pip install --prefix=/install -r requirements.txt

# ----------------------
# Runtime image
# ----------------------
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DJANGO_SETTINGS_MODULE=config.settings \
    PYTHONPATH=/app

WORKDIR /app

# runtime system deps (only what we need at runtime)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg62-turbo \
    zlib1g \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# copy python packages from builder layer
COPY --from=builder /install /usr/local

# copy project code
COPY . /app

# create media/static dirs (static used for prod collectstatic)
RUN mkdir -p /app/media /app/static

# create non-root user
RUN useradd -ms /bin/sh appuser \
    && chown -R appuser:appuser /app

# entrypoints
COPY scripts/entrypoint.sh /entrypoint.sh
COPY scripts/entrypoint.prod.sh /entrypoint.prod.sh
RUN chmod +x /entrypoint.sh /entrypoint.prod.sh

EXPOSE 8000

USER appuser

CMD ["/entrypoint.sh"]
