# --- Stage 1: Build Stage ---
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

# Optimized UV settings for Docker
# Use system python to ensure symlinks in .venv point to /usr/local/bin/python
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_PREFERENCE=system

WORKDIR /app

# 1. Install dependencies first for better layer caching
# This only re-runs if uv.lock or pyproject.toml changes
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

# 2. Copy the rest of the application
COPY . /app

# 3. Final sync to include the local 'app' package
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# --- Stage 2: Final Production Stage ---
FROM python:3.12-slim-bookworm

WORKDIR /app

# Copy only the virtual environment from the builder
COPY --from=builder /app/.venv /app/.venv

# Ensure the app code is available in the final image
COPY ./app /app/app

# Place the virtual environment in the PATH
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

# Expose the FastAPI default port
EXPOSE 8000

# Start the application using uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]