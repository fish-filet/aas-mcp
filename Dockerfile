# Minimal container for aas-mcp serving HTTP Streaming and Gradio UI

FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps (kept minimal)
RUN apt-get update -y && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml README.md LICENSE ./
COPY src ./src

# Install package
RUN pip install --upgrade pip && pip install .

# Expose MCP HTTP and UI ports
EXPOSE 8000 7860

# Default command runs HTTP streaming MCP and UI
# Override PORT/UI_PORT via environment if needed
ENV PORT=8000 UI_PORT=7860
CMD [ \
  "sh", "-lc", \
  "exec aas-mcp --transport http --host 0.0.0.0 --port ${PORT} --ui-host 0.0.0.0 --ui-port ${UI_PORT}" \
]

