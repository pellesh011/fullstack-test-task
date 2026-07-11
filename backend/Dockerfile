FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_NO_DEV=1 \
    UV_PROJECT_ENVIRONMENT=/usr/local
WORKDIR /backend

COPY pyproject.toml uv.lock ./
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
RUN apt-get update && apt-get install -y libmagic1 postgresql-client && rm -rf /var/lib/apt/lists/*
RUN uv sync --locked

COPY src ./src
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
