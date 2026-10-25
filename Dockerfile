FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.11 /uv /bin/uv

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_NO_DEV=1 HF_HOME=/app/.hf
WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-install-project
COPY src ./src
RUN uv sync --frozen

# Bake the model into the image: no download at start-up, no Hub calls at runtime.
RUN .venv/bin/python -c "from georeset_viz.embedder import Embedder; Embedder.from_hub()"
ENV HF_HUB_OFFLINE=1

COPY data ./data
EXPOSE 7860
CMD [".venv/bin/georeset-viz"]
