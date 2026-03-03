FROM python:3.13-slim

ENV POETRY_VIRTUALENVS_CREATE=false
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    dos2unix \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml poetry.lock* ./
RUN pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --no-root

COPY README.md ./
COPY settings ./settings
COPY src ./src
RUN poetry install --no-interaction --no-ansi

COPY entrypoint.sh ./
RUN dos2unix entrypoint.sh 2>/dev/null || true && chmod +x entrypoint.sh

RUN useradd --create-home fastapiuser && \
    chown -R fastapiuser /app
USER fastapiuser

EXPOSE 8080
CMD ["./entrypoint.sh"]
