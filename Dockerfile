FROM python:3.12-slim

WORKDIR /app

# Copy project metadata and source required for a production install.
COPY pyproject.toml README.md ./
COPY src/ ./src/
COPY data/ ./data/
COPY web/ ./web/

RUN pip install --no-cache-dir ".[web]"

# Cloud Run injects PORT (default 8080).
# To run the MCP stdio server instead: docker run ... python -m src.server
EXPOSE 8080
CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:${PORT:-8080} --workers 1 --timeout 120 web.app:app"]

