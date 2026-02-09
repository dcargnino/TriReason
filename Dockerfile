FROM python:3.12-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e ".[dev]"

# Copy source
COPY src/ src/
COPY alembic/ alembic/
COPY alembic.ini ./

# Run migrations then start
CMD ["sh", "-c", "alembic upgrade head && python -m trireason"]
