FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

COPY . .

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

COPY scripts/apply_migrations.sh /usr/local/bin/apply_migrations.sh
RUN chmod +x /usr/local/bin/apply_migrations.sh

ENV PATH="/app/.venv/bin:$PATH"
ENTRYPOINT ["/usr/local/bin/apply_migrations.sh"]

CMD ["granian", "--interface", "asgi", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "main:app"]
