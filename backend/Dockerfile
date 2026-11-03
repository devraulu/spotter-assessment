FROM python:3.13-alpine AS build

COPY --from=ghcr.io/astral-sh/uv:0.11.29 /uv /bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

FROM python:3.13-alpine

ENV PYTHONUNBUFFERED=1 PATH="/app/.venv/bin:$PATH"

WORKDIR /app
COPY --from=build /app/.venv ./.venv
COPY api ./api
COPY trips ./trips
COPY manage.py ./

RUN adduser -S -D -h /home/app app
USER app

ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "exec gunicorn api.wsgi --bind 0.0.0.0:$PORT --workers 1 --threads 8 --timeout 60 --access-logfile -"]
