FROM python:3.12-slim

WORKDIR /app

# Install dependencies first (layer-cached until pyproject.toml changes)
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

# Copy source (after deps so code changes don't bust the dep cache)
COPY src/ ./src/
COPY data/ ./data/

CMD ["python", "-m", "src.server"]

