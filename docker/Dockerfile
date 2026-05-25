# ── Stage 1: build Python deps ───────────────────────────────────────────────
FROM ghcr.io/astral-sh/uv:0.7-python3.12-bookworm-slim AS py-builder

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

COPY pyproject.toml uv.lock README.md ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev --frozen --no-install-project

COPY src/ ./src/
COPY resources/ ./resources/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev --frozen


# ── Stage 2: build React frontend ────────────────────────────────────────────
FROM node:22-slim AS fe-builder

WORKDIR /fe

COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --prefer-offline

COPY frontend/ ./
RUN npm run build


# ── Stage 3: runtime ─────────────────────────────────────────────────────────
FROM python:3.12-slim-bookworm AS runtime

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH" \
    TZ=Asia/Seoul

RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        libcairo2 \
        tzdata \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid appuser --no-create-home appuser

COPY --from=py-builder --chown=appuser:appuser /app/.venv /app/.venv
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser resources/ ./resources/

# React build output served as static files by FastAPI
COPY --from=fe-builder --chown=appuser:appuser /fe/dist ./frontend/dist

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["uvicorn", "thatnightsky.api.main:app", \
     "--host", "0.0.0.0", "--port", "8000"]
